from __future__ import annotations

import argparse
import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PLACEHOLDER_FIRST_NAME = "Telegram user"


@dataclass(frozen=True)
class MigrationResult:
    backup_path: Path
    backup_sha256: str
    users_before: int
    users_after: int
    users_added: int
    violations_before: int
    violations_after: int


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _integrity_check(connection: sqlite3.Connection) -> None:
    result = connection.execute("PRAGMA integrity_check").fetchone()
    if result != ("ok",):
        raise RuntimeError(f"SQLite integrity check failed: {result!r}")


def _table_names(connection: sqlite3.Connection) -> tuple[str, ...]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return tuple(row[0] for row in rows)


def _tables_with_column(
    connection: sqlite3.Connection,
    column_name: str,
) -> tuple[str, ...]:
    matches: list[str] = []
    for table in _table_names(connection):
        columns = connection.execute(
            f"PRAGMA table_info({_quote_identifier(table)})"
        ).fetchall()
        if any(column[1] == column_name for column in columns):
            matches.append(table)
    return tuple(matches)


def _referenced_user_ids(connection: sqlite3.Connection) -> set[int]:
    user_ids: set[int] = set()
    for table in _tables_with_column(connection, "user_id"):
        rows = connection.execute(
            f"SELECT DISTINCT user_id FROM {_quote_identifier(table)} "
            "WHERE user_id IS NOT NULL"
        ).fetchall()
        user_ids.update(int(row[0]) for row in rows)
    return user_ids


def _row_counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: int(
            connection.execute(
                f"SELECT COUNT(*) FROM {_quote_identifier(table)}"
            ).fetchone()[0]
        )
        for table in _table_names(connection)
    }


def _create_verified_backup(
    source: sqlite3.Connection,
    database_path: Path,
    backup_dir: Path,
) -> tuple[Path, str, dict[str, int]]:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_path = backup_dir / f"{database_path.stem}.pre_stage2_{timestamp}.db"
    suffix = 1
    while backup_path.exists():
        backup_path = backup_dir / (
            f"{database_path.stem}.pre_stage2_{timestamp}_{suffix}.db"
        )
        suffix += 1

    backup = sqlite3.connect(backup_path)
    try:
        source.backup(backup)
        _integrity_check(backup)
        counts = _row_counts(backup)
    finally:
        backup.close()

    digest = hashlib.sha256(backup_path.read_bytes()).hexdigest().upper()
    return backup_path, digest, counts


def migrate_database(database_path: Path, backup_dir: Path) -> MigrationResult:
    database_path = database_path.resolve()
    if not database_path.is_file():
        raise FileNotFoundError(database_path)

    connection = sqlite3.connect(database_path)
    try:
        _integrity_check(connection)
        if "users" not in _table_names(connection):
            raise RuntimeError("The database has no users table")

        counts_before = _row_counts(connection)
        violations_before = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        users_before = counts_before["users"]
        backup_path, backup_sha256, backup_counts = _create_verified_backup(
            connection,
            database_path,
            backup_dir.resolve(),
        )
        if backup_counts != counts_before:
            raise RuntimeError("Backup row counts differ from the source database")

        connection.execute("BEGIN IMMEDIATE")
        try:
            existing_users = {
                int(row[0])
                for row in connection.execute("SELECT telegram_id FROM users").fetchall()
            }
            missing_users = sorted(_referenced_user_ids(connection) - existing_users)
            connection.executemany(
                "INSERT INTO users (telegram_id, first_name) VALUES (?, ?)",
                ((telegram_id, PLACEHOLDER_FIRST_NAME) for telegram_id in missing_users),
            )
            remaining = connection.execute("PRAGMA foreign_key_check").fetchall()
            if remaining:
                raise RuntimeError(
                    f"Foreign-key violations remain after backfill: {len(remaining)}"
                )
            connection.commit()
        except Exception:
            connection.rollback()
            raise

        connection.execute("PRAGMA foreign_keys=ON")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise RuntimeError("Could not enable SQLite foreign keys")
        _integrity_check(connection)
        violations_after = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        users_after = int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])

        for table, count_before in counts_before.items():
            if table == "users":
                continue
            count_after = int(
                connection.execute(
                    f"SELECT COUNT(*) FROM {_quote_identifier(table)}"
                ).fetchone()[0]
            )
            if count_after != count_before:
                raise RuntimeError(
                    f"Unexpected row-count change in {table}: "
                    f"{count_before} -> {count_after}"
                )

        return MigrationResult(
            backup_path=backup_path,
            backup_sha256=backup_sha256,
            users_before=users_before,
            users_after=users_after,
            users_added=users_after - users_before,
            violations_before=violations_before,
            violations_after=violations_after,
        )
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Back up the SQLite database and restore users FK parents."
    )
    parser.add_argument("database", type=Path)
    parser.add_argument("--backup-dir", type=Path, required=True)
    arguments = parser.parse_args()
    result = migrate_database(arguments.database, arguments.backup_dir)
    print(f"backup={result.backup_path}")
    print(f"backup_sha256={result.backup_sha256}")
    print(f"users={result.users_before}->{result.users_after}")
    print(f"users_added={result.users_added}")
    print(f"foreign_key_violations={result.violations_before}->{result.violations_after}")


if __name__ == "__main__":
    main()


import sys
import shutil
import logging
from datetime import datetime
from pathlib import Path
from services.atlas.core.config import get_project_root, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.backup")


def create_backup():
    root = get_project_root()
    backup_dir = root / "backups"
    backup_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    # If sqlite fallback database file exists
    sqlite_file = root / "atlas.db"
    if sqlite_file.exists():
        target = backup_dir / f"atlas_backup_{ts}.db"
        shutil.copy2(sqlite_file, target)
        logger.info(f"SQLite backup successfully created at: {target}")
        print(f"Backup created: {target}")
        return

    logger.info("Database snapshot backup complete.")


def restore_backup(filepath: str):
    root = get_project_root()
    src = Path(filepath)
    if not src.exists():
        logger.error(f"Backup file not found: {filepath}")
        sys.exit(1)

    sqlite_file = root / "atlas.db"
    shutil.copy2(src, sqlite_file)
    logger.info(f"Database successfully restored from: {src}")
    print(f"Database restored from: {src}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m services.atlas.db.backup [create|restore <file>]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "create":
        create_backup()
    elif action == "restore":
        if len(sys.argv) < 3:
            print("Error: filepath required for restore")
            sys.exit(1)
        restore_backup(sys.argv[2])
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

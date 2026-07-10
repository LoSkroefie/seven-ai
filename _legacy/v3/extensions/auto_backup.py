"""
Auto-Backup Extension — Seven AI

Backs up Seven's data files (database, knowledge graph, emotions, identity)
on a daily schedule. Keeps the last 7 backups.
"""

import logging
import zipfile
from datetime import datetime
from pathlib import Path
from utils.plugin_loader import SevenExtension

logger = logging.getLogger("AutoBackup")


class AutoBackupExtension(SevenExtension):
    """Automatically backs up Seven's critical data files"""

    name = "Auto-Backup"
    version = "1.0"
    description = "Daily backup of Seven's data (DB, KG, emotions, identity)"
    author = "Seven AI"

    schedule_interval_minutes = 1440  # Once per day
    needs_ollama = False

    MAX_BACKUPS = 7

    def init(self, bot=None):
        self.bot = bot
        self.backup_dir = Path.home() / "Documents" / "Seven" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.last_backup = None
        self.last_backup_size = 0

    def run(self, context: dict = None) -> dict:
        """Create a timestamped zip backup of Seven's data"""
        try:
            import config
            data_dir = Path(getattr(config, 'DATA_DIR', Path.home() / '.chatbot'))
        except ImportError:
            data_dir = Path.home() / '.chatbot'

        if not data_dir.exists():
            return {"message": f"Data directory not found: {data_dir}", "status": "error"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.backup_dir / f"seven_backup_{timestamp}.zip"

        try:
            files_backed_up = 0
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup all files in data directory
                for item in data_dir.rglob('*'):
                    if item.is_file() and not item.name.startswith('.'):
                        # Skip very large files (>50MB)
                        if item.stat().st_size > 50 * 1024 * 1024:
                            continue
                        arcname = item.relative_to(data_dir)
                        zf.write(str(item), str(arcname))
                        files_backed_up += 1

                # Also backup identity files if they exist
                identity_dir = data_dir / "identity"
                scripts_dir = Path.home() / "Documents" / "Seven" / "scripts"
                for extra_dir in [scripts_dir]:
                    if extra_dir.exists():
                        for item in extra_dir.rglob('*'):
                            if item.is_file():
                                arcname = Path("scripts") / item.relative_to(scripts_dir)
                                zf.write(str(item), str(arcname))
                                files_backed_up += 1

            self.last_backup = str(zip_path)
            self.last_backup_size = zip_path.stat().st_size

            # Cleanup old backups
            self._cleanup_old_backups()

            size_mb = round(self.last_backup_size / (1024 * 1024), 1)
            logger.info(f"[AutoBackup] Created backup: {zip_path.name} ({files_backed_up} files, {size_mb}MB)")
            return {
                "message": f"Backup created: {zip_path.name} ({files_backed_up} files, {size_mb}MB)",
                "path": str(zip_path),
                "files": files_backed_up,
                "size_mb": size_mb,
                "status": "ok",
            }

        except Exception as e:
            logger.error(f"[AutoBackup] Backup failed: {e}")
            return {"message": f"Backup failed: {e}", "status": "error"}

    def _cleanup_old_backups(self):
        """Keep only the last MAX_BACKUPS backups"""
        backups = sorted(self.backup_dir.glob("seven_backup_*.zip"), key=lambda p: p.stat().st_mtime)
        while len(backups) > self.MAX_BACKUPS:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                logger.info(f"[AutoBackup] Removed old backup: {oldest.name}")
            except Exception:
                pass

    def get_status(self) -> dict:
        backups = list(self.backup_dir.glob("seven_backup_*.zip"))
        return {
            "name": self.name,
            "version": self.version,
            "last_backup": self.last_backup,
            "last_size_mb": round(self.last_backup_size / (1024 * 1024), 1) if self.last_backup_size else 0,
            "total_backups": len(backups),
            "backup_dir": str(self.backup_dir),
            "running": True,
        }

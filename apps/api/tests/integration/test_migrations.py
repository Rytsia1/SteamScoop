from pathlib import Path

from alembic.config import Config

from alembic import command


def test_alembic_upgrade_downgrade_cycle() -> None:
    """Test full Alembic upgrade, downgrade, and re-upgrade execution."""
    api_dir = Path(__file__).resolve().parent.parent.parent
    alembic_ini_path = api_dir / "alembic.ini"

    alembic_cfg = Config(str(alembic_ini_path))

    # Test downgrade to base
    command.downgrade(alembic_cfg, "base")

    # Test upgrade to head
    command.upgrade(alembic_cfg, "head")

from pathlib import Path
import tomllib

ROOT: Path = Path(__file__).resolve().parent
CONFIG: dict = tomllib.loads((ROOT / "config.toml").read_text(encoding="utf-8"))

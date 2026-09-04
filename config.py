"""BiasEngine configuration."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).parent

class Settings(BaseSettings):
    app_name: str = "PAIR ANALYSIS"
    market_timezone: str = "Africa/Nairobi"
    demo_mode: bool = True
    market_data_api_key: str = ""
    news_api_key: str = ""
    economic_data_api_key: str = ""
    fred_api_key: str = ""
    refresh_seconds: int = 300
    database_path: str = str(ROOT / "data" / "pair_analysis.db")
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore", case_sensitive=False)

settings = Settings()

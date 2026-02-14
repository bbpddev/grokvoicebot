from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    grok_api_key: str = ""
    grok_model: str = "grok-voice"
    grok_realtime_url: str = "wss://api.x.ai/v1/realtime"
    database_url: str = "sqlite:///./itsd.db"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)


settings = Settings()

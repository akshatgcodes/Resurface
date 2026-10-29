from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./resurface.db"
    # Empty → caching is skipped (the app still works, just recomputes)
    redis_url: str = ""
    app_password: str = ""
    session_secret: str = "dev-insecure-secret"
    frontend_url: str = "http://localhost:5173"
    cross_site_cookies: bool = False

    # Daily digest
    digest_size: int = 5
    digest_hour: int = 8
    digest_timezone: str = "Asia/Kolkata"
    digest_to: str = ""  # empty → digest is built and saved, but not emailed
    scheduler_enabled: bool = False

    # SMTP (Mailpit in docker-compose: host=mailpit, port=1025, no auth)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = True
    mail_from: str = "Resurface <digest@resurface.local>"
    public_url: str = "http://localhost:5173"  # used for links in the email


settings = Settings()

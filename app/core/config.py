from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str

    # SMTP settings
    SMTP_HOST: str
    SMTP_PORT: int = 465
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str

    FRONTEND_URL: str

    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env"
    )
    EMAIL_OTP_EXPIRE_MINUTES: int = 10
    EMAIL_OTP_MAX_ATTEMPTS: int = 5
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS: int = 60


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str

    HOSTINGER_API_KEY: str
    HOSTINGER_FROM_EMAIL: str
    HOSTINGER_MAILBOX_RESOURCE_ID: str

    FRONTEND_URL: str

    EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )
    EMAIL_OTP_EXPIRE_MINUTES: int = 10
    EMAIL_OTP_MAX_ATTEMPTS: int = 5
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS: int = 60
    # app/core/config.py
# Add these settings inside your Settings class

    PASSWORD_RESET_OTP_EXPIRE_MINUTES: int = 10
    PASSWORD_RESET_OTP_MAX_ATTEMPTS: int = 5
    PASSWORD_RESET_OTP_RESEND_COOLDOWN_SECONDS: int = 60


settings = Settings()
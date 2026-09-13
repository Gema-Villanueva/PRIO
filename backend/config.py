from pydantic_settings import BaseSettings, SettingsConfigDict


# Definimos la configuración de la aplicación.
class Settings(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"

    external_provider: str = "groq"
    external_base_url: str = "https://api.groq.com/openai/v1"
    external_model: str = "openai/gpt-oss-20b"
    external_api_key: str = ""
    external_input_cost_per_million: float = 0.0
    external_output_cost_per_million: float = 0.0

    database_path: str = "./prio.db"

    # Leemos la configuración local desde el archivo .env.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Creamos la configuración que utilizarán los demás módulos.
settings = Settings()
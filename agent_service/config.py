from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    fara_model_name: str = "hf.co/bartowski/microsoft_Fara-7B-GGUF:IQ4_XS"
    fara_timeout_seconds: int = 120
    planner_model_name: str = "qwen2.5:14b"
    agent_service_port: int = 8000
    screen_capture_monitor: int = 1
    ironclaw_root: str = r"C:\Users\nutty\Documents\workspace\AI\repos\ironclaw"
    ironclaw_agent_project: str = r"C:\Users\nutty\Documents\workspace\AI\ironclaw_tool"


settings = Settings()


import os
from dataclasses import dataclass
from pathlib import Path

# Safe optional import of dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val


@dataclass
class AppConfig:
    ollama_host: str
    director_model: str
    writer_model: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    from_name: str
    wp_post_email: str
    blogger_post_email: str
    default_status: str
    use_jetpack_shortcodes: bool
    wp_site_url: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"


def get_config() -> AppConfig:
    """Retrieve and parse configuration from environment variables."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://192.168.128.59:11434").strip()
    director_model = os.getenv("OLLAMA_DIRECTOR_MODEL", "qwen2.5:14b").strip()
    writer_model = os.getenv("OLLAMA_WRITER_MODEL", "gemma2:9b").strip()

    smtp_user = os.getenv("SMTP_USER", "").strip()
    raw_smtp_host = os.getenv("SMTP_HOST", "").strip()
    if raw_smtp_host:
        smtp_host = raw_smtp_host
    elif any(smtp_user.lower().endswith(d) for d in ("@outlook.com", "@hotmail.com", "@live.com", "@outlook.jp")):
        smtp_host = "smtp-mail.outlook.com"
    else:
        smtp_host = "smtp.gmail.com"
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "yes")
    smtp_use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("true", "1", "yes")
    from_name = os.getenv("MAIL_FROM_NAME", "Rikejo Science Novel Publisher").strip()
    wp_post_email = os.getenv("WP_POST_EMAIL", "").strip()
    blogger_post_email = os.getenv("BLOGGER_POST_EMAIL", "").strip()
    default_status = os.getenv("DEFAULT_POST_STATUS", "publish").strip()
    use_jetpack_shortcodes = os.getenv("USE_JETPACK_SHORTCODES", "false").lower() in ("true", "1", "yes")
    wp_site_url = os.getenv("WP_SITE_URL", "").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash").strip()

    return AppConfig(
        ollama_host=ollama_host,
        director_model=director_model,
        writer_model=writer_model,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        smtp_use_ssl=smtp_use_ssl,
        from_name=from_name,
        wp_post_email=wp_post_email,
        blogger_post_email=blogger_post_email,
        default_status=default_status,
        use_jetpack_shortcodes=use_jetpack_shortcodes,
        wp_site_url=wp_site_url,
        gemini_api_key=gemini_api_key,
        gemini_model=gemini_model,
    )

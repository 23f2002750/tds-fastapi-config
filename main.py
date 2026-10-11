from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
import yaml
from dotenv import dotenv_values

app = FastAPI()

# Allow the TDS grader/browser to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Defaults
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# 2. Environment-specific YAML
yaml_file = "config.development.yaml"
if os.path.exists(yaml_file):
    with open(yaml_file, "r") as f:
        yaml_config = yaml.safe_load(f) or {}
        config.update(yaml_config)

# 3. .env file
if os.path.exists(".env"):
    env_config = dotenv_values(".env")

    for key, value in env_config.items():
        if value is None:
            continue

        if key == "APP_PORT":
            config["port"] = value
        elif key == "NUM_WORKERS":
            config["workers"] = value
        elif key == "APP_WORKERS":
            config["workers"] = value
        elif key == "APP_DEBUG":
            config["debug"] = value
        elif key == "APP_LOG_LEVEL":
            config["log_level"] = value
        elif key == "APP_API_KEY":
            config["api_key"] = value

# 4. OS environment variables — highest config-layer precedence
os_mapping = {
    "APP_PORT": "port",
    "APP_WORKERS": "workers",
    "APP_DEBUG": "debug",
    "APP_LOG_LEVEL": "log_level",
    "APP_API_KEY": "api_key",
}

for env_key, config_key in os_mapping.items():
    if env_key in os.environ:
        config[config_key] = os.environ[env_key]


def to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def coerce(key, value):
    if key in {"port", "workers"}:
        return int(value)
    elif key == "debug":
        return to_bool(value)
    else:
        return str(value)


@app.get("/effective-config")
def effective_config(
    set: list[str] | None = Query(default=None)
):
    # Copy merged configuration
    result = config.copy()

    # CLI/query parameter overrides
    if set:
        for override in set:
            if "=" in override:
                key, value = override.split("=", 1)
                result[key] = value

    # Apply correct types
    for key in list(result.keys()):
        result[key] = coerce(key, result[key])

    # Always mask API key
    result["api_key"] = "****"

    return {
        "port": result["port"],
        "workers": result["workers"],
        "debug": result["debug"],
        "log_level": result["log_level"],
        "api_key": result["api_key"],
    }
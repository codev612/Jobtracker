"""Profile management for Job Tracker - each profile has separate data and settings."""

import json
import shutil
from pathlib import Path
from typing import Optional, List

from .paths import BASE_PATH

PROFILES_DIR = BASE_PATH / "profiles"
PROFILES_CONFIG = BASE_PATH / "profiles.json"


def _ensure_profiles_dir() -> None:
    """Ensure profiles directory exists."""
    PROFILES_DIR.mkdir(exist_ok=True)


def _load_profiles_config() -> dict:
    """Load profiles configuration."""
    if PROFILES_CONFIG.exists():
        try:
            with open(PROFILES_CONFIG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"current": None, "profiles": []}


def _save_profiles_config(config: dict) -> None:
    """Save profiles configuration."""
    try:
        with open(PROFILES_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass


def get_current_profile() -> Optional[str]:
    """Get the currently active profile name."""
    config = _load_profiles_config()
    return config.get("current")


def set_current_profile(profile_name: str) -> None:
    """Set the active profile."""
    config = _load_profiles_config()
    if profile_name in config.get("profiles", []):
        config["current"] = profile_name
        _save_profiles_config(config)


def list_profiles() -> List[str]:
    """List all available profiles."""
    config = _load_profiles_config()
    return config.get("profiles", [])


def create_profile(profile_name: str) -> bool:
    """Create a new profile. Returns True if created, False if exists."""
    _ensure_profiles_dir()
    config = _load_profiles_config()
    profiles = config.get("profiles", [])
    
    if profile_name in profiles:
        return False
    
    profile_dir = PROFILES_DIR / profile_name
    profile_dir.mkdir(exist_ok=True)
    
    profiles.append(profile_name)
    config["profiles"] = profiles
    if not config.get("current"):
        config["current"] = profile_name
    _save_profiles_config(config)
    return True


def rename_profile(old_name: str, new_name: str) -> bool:
    """Rename a profile. Returns True if renamed, False if new_name exists or old_name not found."""
    config = _load_profiles_config()
    profiles = config.get("profiles", [])
    
    if old_name not in profiles:
        return False
    if new_name in profiles:
        return False
    
    # Migrate keyring entry if it exists
    try:
        import keyring
        old_service = f"JobTracker-{old_name}"
        new_service = f"JobTracker-{new_name}"
        api_key = keyring.get_password(old_service, "openai_api_key")
        if api_key:
            keyring.set_password(new_service, "openai_api_key", api_key)
            try:
                keyring.delete_password(old_service, "openai_api_key")
            except Exception:
                pass
    except Exception:
        pass
    
    old_dir = PROFILES_DIR / old_name
    new_dir = PROFILES_DIR / new_name
    
    if old_dir.exists():
        old_dir.rename(new_dir)
    
    # Update profiles list
    idx = profiles.index(old_name)
    profiles[idx] = new_name
    config["profiles"] = profiles
    
    # Update current if it was the renamed profile
    if config.get("current") == old_name:
        config["current"] = new_name
    
    _save_profiles_config(config)
    return True


def delete_profile(profile_name: str) -> bool:
    """Delete a profile and its data. Returns True if deleted."""
    config = _load_profiles_config()
    profiles = config.get("profiles", [])
    
    if profile_name not in profiles:
        return False
    
    profile_dir = PROFILES_DIR / profile_name
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
    
    profiles.remove(profile_name)
    config["profiles"] = profiles
    if config.get("current") == profile_name:
        config["current"] = profiles[0] if profiles else None
    _save_profiles_config(config)
    return True


def get_profile_path(profile_name: Optional[str] = None) -> Path:
    """Get the data directory path for a profile."""
    _ensure_profiles_dir()
    if profile_name is None:
        profile_name = get_current_profile()
    if not profile_name:
        # Default profile for backward compatibility
        return BASE_PATH
    return PROFILES_DIR / profile_name


def get_profile_database_path(profile_name: Optional[str] = None) -> Path:
    """Get the database path for a profile."""
    profile_path = get_profile_path(profile_name)
    return profile_path / "jobs.db"


def get_profile_config_path(profile_name: Optional[str] = None) -> Path:
    """Get the config path for a profile."""
    profile_path = get_profile_path(profile_name)
    return profile_path / "config.json"

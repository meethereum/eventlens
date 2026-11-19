"""
Central configuration loaded from environment variables.
All settings come from .env — never from code.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Literal, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    web_port: int = 8080
    demo_mode: str = "auto"  # auto | 1 | 0

    # Data sources
    fred_api_key: str = ""
    sec_user_agent: str = "EventLens/0.1 user@example.com"
    finnhub_api_key: str = ""

    # LLM — primary
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.2
    llm_max_tokens: int = 2000
    llm_max_input_tokens: int = 4000
    llm_timeout_s: int = 60
    llm_rpm_limit: int = 1
    llm_fallback_model: str = ""
    llm_extra_body: str = ""  # JSON string

    @property
    def llm_extra_body_dict(self) -> dict:
        if not self.llm_extra_body.strip():
            return {}
        try:
            return json.loads(self.llm_extra_body)
        except json.JSONDecodeError:
            return {}

    @property
    def is_demo_mode(self) -> bool:
        if self.demo_mode == "1":
            return True
        if self.demo_mode == "0":
            return False
        # auto: demo if any required key is missing
        return not self.fred_api_key or not self.llm_api_key

    @property
    def missing_keys(self) -> list[str]:
        missing = []
        if not self.fred_api_key:
            missing.append("FRED_API_KEY")
        if not self.llm_api_key:
            missing.append("LLM_API_KEY")
        if self.sec_user_agent == "EventLens/0.1 user@example.com":
            missing.append("SEC_USER_AGENT (using placeholder)")
        return missing


@lru_cache
def get_settings() -> Settings:
    return Settings()

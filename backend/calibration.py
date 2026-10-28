"""Validated immutable price/wage samples. Existing worlds never reread this file."""
import hashlib
import json
import os
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from backend.provider import ProviderNotConfigured


class Calibration(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    calibration_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    geography: str = Field(min_length=1, max_length=128)
    collected_at: str = Field(min_length=1, max_length=64)
    provider: str
    price_cents: list[int] = Field(min_length=1, max_length=1000)
    daily_wage_cents: list[int] = Field(min_length=1, max_length=1000)
    sources: list[dict] = Field(min_length=1, max_length=50)
    rental_context: list[dict] = Field(default_factory=list, max_length=100)


def validate(value):
    result = Calibration.model_validate(value).model_dump()
    if any(type(p) is not int or not 1 <= p <= 100_000 for p in result["price_cents"]):
        raise ValueError("Retail samples must be integer cents between 1 and 100000")
    if any(type(w) is not int or not 1 <= w <= 500_000 for w in result["daily_wage_cents"]):
        raise ValueError("Daily wage samples must be integer cents between 1 and 500000")
    if result["provider"] != "apify":
        raise ValueError("Only explicitly collected Apify calibrations are accepted")
    for source in result["sources"]:
        if not all(isinstance(source.get(k), str) and source[k] for k in ("actor_id", "dataset_id", "run_id", "source_url")):
            raise ValueError("Calibration needs Actor, run, dataset and source provenance")
        if not source["source_url"].startswith("https://"):
            raise ValueError("Calibration source links must be HTTPS")
    return result


def checksum(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(calibration_id):
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", calibration_id):
        raise ProviderNotConfigured("Invalid calibration ID")
    root = Path(os.getenv("APIFY_CALIBRATION_DIR", "data/calibrations"))
    try:
        result = validate(json.loads((root / (calibration_id + ".json")).read_text(encoding="utf-8-sig")))
        if result["calibration_id"] != calibration_id:
            raise ValueError
        return result
    except (OSError, ValueError, TypeError):
        raise ProviderNotConfigured("Selected calibration is missing or invalid; default synthetic inputs were not substituted") from None

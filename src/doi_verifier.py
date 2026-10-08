import re
import os
import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_HOST = "http://rtx5060lp:11434"
SECONDARY_LLM_HOST = "http://sff7020:1234"
FALLBACK_OLLAMA_HOSTS = [
    "http://rtx5060lp:11434",
    "http://192.168.128.62:11434",
    "http://sff7020:1234",
    "http://192.168.128.16:1234",
]
DEFAULT_DIRECTOR_MODEL = "qwen3.5:9b"
DEFAULT_WRITER_MODEL = "shosetsu"
DEFAULT_LM_STUDIO_MODEL = "google/gemma-4-26b-a4b-qat"
DEFAULT_DRAW_THINGS_HOST = "http://kenomac-mini:7860"


def clean_doi_string(raw_doi: str) -> str:
    """Strips URL prefixes, trailing punctuation, and whitespace from a DOI string."""
    if not raw_doi:
        return ""
    doi = raw_doi.strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.rstrip(".,;)]}>'\"")
    return doi.strip()


def check_doi_validity(doi: str, timeout: int = 8) -> bool:
    """
    Verifies whether a DOI actually exists in the official doi.org Handle System API.
    """
    clean_doi = clean_doi_string(doi)
    if not clean_doi or not clean_doi.startswith("10."):
        return False

    api_url = f"https://doi.org/api/handles/{urllib.parse.quote(clean_doi, safe='/')}"
    try:
        req = urllib.request.Request(
            api_url,
            headers={"User-Agent": "RikejoSciNovelBot/1.0 (https://github.com/k518-2026/rikejo-science-novel)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.getcode() == 200:
                data = json.loads(res.read().decode("utf-8", errors="ignore"))
                return data.get("responseCode") == 1
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
    except Exception as e:
        logger.debug(f"DOI check network warning for {clean_doi}: {e}")
    return False

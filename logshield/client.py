from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class LogShieldError(Exception):
    pass


class AuthError(LogShieldError):
    pass


class QuotaError(LogShieldError):
    pass


@dataclass
class SanitizeResult:
    sanitized_text: str
    detections: list[dict[str, Any]]
    processing_ms: float
    quota_pct: float = 0.0


class LogShieldClient:
    def __init__(self, api_url: str, api_host: str, rapidapi_key: str, local: bool = False, timeout: float = 10.0) -> None:
        self.api_url = api_url.rstrip("/")
        self.api_host = api_host
        self.rapidapi_key = rapidapi_key
        self.local = local
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        if self.local:
            return {
                "Content-Type": "application/json",
                "X-RapidAPI-Proxy-Secret": self.rapidapi_key,
                "X-RapidAPI-User": "local-dev-user",
            }
        return {
            "Content-Type": "application/json",
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.api_host,
        }

    def sanitize(self, text: str, confidence_threshold: int = 80) -> SanitizeResult:
        r = httpx.post(
            f"{self.api_url}/v1/sanitize",
            json={"text": text, "options": {"confidence_threshold": confidence_threshold}},
            headers=self._headers(),
            timeout=self.timeout,
        )
        data = self._parse(r)
        return SanitizeResult(
            sanitized_text=data["sanitized_text"],
            detections=data["detections"],
            processing_ms=data["processing_ms"],
            quota_pct=data.get("quota_pct", 0.0),
        )

    def usage(self) -> dict[str, Any]:
        r = httpx.get(
            f"{self.api_url}/v1/usage",
            headers=self._headers(),
            timeout=self.timeout,
        )
        return self._parse(r)

    @staticmethod
    def _parse(r: httpx.Response) -> dict[str, Any]:
        if r.status_code == 401:
            raise AuthError("Invalid or expired RapidAPI key")
        if r.status_code == 429:
            raise QuotaError("Monthly quota exceeded — upgrade plan on RapidAPI")
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise LogShieldError(f"{r.status_code}: {detail}")
        return r.json()

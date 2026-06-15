from dataclasses import dataclass
import logging
from typing import Any

import httpx


logger = logging.getLogger(__name__)


def normalize_mc_number(mc_number: str) -> str:
    cleaned = mc_number.upper().replace("MC", "")
    for token in ("#", "-", " "):
        cleaned = cleaned.replace(token, "")
    return "".join(char for char in cleaned if char.isdigit())


@dataclass
class FmcsaResult:
    verification_status: str
    mc_number: str
    dot_number: str | None
    legal_name: str | None
    dba_name: str | None
    authority_status: str | None
    allowed_to_operate: bool
    out_of_service: bool
    eligible: bool
    reason: str
    recommended_agent_message: str
    raw_response: dict[str, Any]


class FmcsaClient:
    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def verify_mc_number(self, mc_number: str) -> FmcsaResult:
        normalized_mc = normalize_mc_number(mc_number)
        if not self.api_key or self.api_key == "replace-with-real-fmcsa-key":
            return FmcsaResult(
                verification_status="error",
                mc_number=normalized_mc,
                dot_number=None,
                legal_name=None,
                dba_name=None,
                authority_status=None,
                allowed_to_operate=False,
                out_of_service=False,
                eligible=False,
                reason="FMCSA API key is not configured.",
                recommended_agent_message=(
                    "I could not verify your carrier authority right now. Let me take your details and have a rep follow up."
                ),
                raw_response={"error": "missing_fmcsa_api_key"},
            )

        # TODO: Confirm and adjust FMCSA response field mappings for your specific FMCSA API key/docs.
        # The base URL is configurable through FMCSA_BASE_URL to simplify updates without code changes.
        endpoint = f"{self.base_url.rstrip('/')}/carriers/docket-number/{normalized_mc}"
        params = {"webKey": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            logger.warning("FMCSA verification failed for mc_number=%s: %s", normalized_mc, exc)
            return FmcsaResult(
                verification_status="error",
                mc_number=normalized_mc,
                dot_number=None,
                legal_name=None,
                dba_name=None,
                authority_status=None,
                allowed_to_operate=False,
                out_of_service=False,
                eligible=False,
                reason=f"Unable to verify carrier with FMCSA at this time: {exc}",
                recommended_agent_message=(
                    "I could not verify your carrier authority right now. Let me take your details and have a rep follow up."
                ),
                raw_response={"error": str(exc)},
            )

        data = _extract_carrier_data(payload)
        if data is None:
            return FmcsaResult(
                verification_status="not_found",
                mc_number=normalized_mc,
                dot_number=None,
                legal_name=None,
                dba_name=None,
                authority_status=None,
                allowed_to_operate=False,
                out_of_service=False,
                eligible=False,
                reason="No recognizable carrier record was returned by FMCSA.",
                recommended_agent_message=(
                    "I could not find an active FMCSA carrier record for that MC number. "
                    "Please confirm the number or have a representative follow up."
                ),
                raw_response=payload if isinstance(payload, dict) else {"payload": payload},
            )

        authority_status = _as_text(data, ["authority_status", "status", "operating_status", "authorityStatus"])
        allowed_to_operate = _as_bool(data, ["allowed_to_operate", "allowedToOperate", "allowed", "authorized"])
        out_of_service = _as_bool(data, ["out_of_service", "outOfService"])
        legal_name = _as_text(data, ["legal_name", "legalName", "carrier_name", "carrierName"])
        dba_name = _as_text(data, ["dba_name", "dbaName", "dba"])
        dot_number = _as_text(data, ["dot_number", "dotNumber", "usdot", "usdOTNumber"])

        status_upper = (authority_status or "").upper()
        is_active = "ACTIVE" in status_upper or status_upper in {"AUTHORIZED", "A"}
        inferred_allowed = allowed_to_operate or (is_active and _has_any_key(data, ["authority_status", "status", "operating_status", "authorityStatus"]))
        eligible = inferred_allowed and not out_of_service

        if eligible:
            reason = "Carrier is active and eligible for brokerage loads."
            message = f"{legal_name or 'Carrier'} is verified and eligible. Continue with load matching."
        elif out_of_service:
            reason = "Carrier appears to be marked out of service."
            message = "I'm sorry, but I'm unable to continue because your carrier appears out of service."
        else:
            reason = "Carrier authority is not active."
            message = "I'm sorry, but I'm unable to continue because your authority does not appear active."

        return FmcsaResult(
            verification_status="verified",
            mc_number=normalized_mc,
            dot_number=dot_number,
            legal_name=legal_name,
            dba_name=dba_name,
            authority_status=authority_status,
            allowed_to_operate=inferred_allowed,
            out_of_service=out_of_service,
            eligible=eligible,
            reason=reason,
            recommended_agent_message=message,
            raw_response=payload if isinstance(payload, dict) else {"payload": payload},
        )


def _extract_carrier_data(payload: Any) -> dict[str, Any] | None:
    for candidate in _carrier_candidates(payload):
        if _looks_like_carrier(candidate):
            return candidate
    return None


def _carrier_candidates(payload: Any) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            carrier = value.get("carrier")
            if isinstance(carrier, dict):
                candidates.append(carrier)
            candidates.append(value)
            for key in ("content", "data", "result"):
                nested = value.get(key)
                if isinstance(nested, (dict, list)):
                    visit(nested)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return candidates


def _looks_like_carrier(data: dict[str, Any]) -> bool:
    return _has_any_key(
        data,
        [
            "legalName",
            "legal_name",
            "dotNumber",
            "dot_number",
            "allowedToOperate",
            "allowed_to_operate",
            "safetyRating",
            "phyCity",
            "phyState",
            "carrierName",
            "carrier_name",
            "usdot",
            "usdOTNumber",
        ],
    )


def _has_any_key(data: dict[str, Any], keys: list[str]) -> bool:
    return any(key in data and data[key] is not None for key in keys)


def _as_text(data: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return str(value)
    return None


def _as_bool(data: dict[str, Any], keys: list[str]) -> bool:
    for key in keys:
        value = data.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "yes", "y", "1", "active", "authorized", "allowed"}:
            return True
        if text in {"false", "no", "n", "0", "inactive", "unauthorized", "denied"}:
            return False
    return False

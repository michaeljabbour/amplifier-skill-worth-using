"""Small, explicit API transport. Credentials are read from the environment only."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass


class ConfigurationError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    """Messages deliberately omit request headers, keys, and provider response bodies."""


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ProviderError("Provider redirect refused; credentials remain restricted to the configured endpoint")


@dataclass(frozen=True)
class Settings:
    role: str
    model: str | None
    provider: str
    temperature: float
    max_tokens: int
    seed_supported: bool
    input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None

    def public(self):
        value = asdict(self)
        value.pop("seed_supported")
        value["seed_support_status"] = "parameter_requested_pending_live_validation" if self.seed_supported else "provider_has_no_seed_parameter"
        return value


def settings_for(role: str) -> Settings:
    prefix = role.upper()
    model = os.environ.get(prefix + "_MODEL")
    if role == "simulator":
        model = model or os.environ.get("EVAL_MODEL")
    provider = os.environ.get(prefix + "_PROVIDER", "anthropic" if (model or "").startswith("claude") else "openai")
    if provider not in {"openai", "anthropic"}:
        raise ConfigurationError(prefix + "_PROVIDER must be openai or anthropic")
    def rate(suffix):
        value = os.environ.get(prefix + suffix)
        return float(value) if value else None
    return Settings(
        role=role, model=model, provider=provider,
        temperature=float(os.environ.get(prefix + "_TEMPERATURE", "0" if role == "judge" else "0.2")),
        max_tokens=int(os.environ.get(prefix + "_MAX_TOKENS", "6000" if role == "judge" else ("3500" if role == "simulator" else "2400"))),
        seed_supported=provider == "openai",
        input_usd_per_million=rate("_INPUT_USD_PER_MILLION"),
        output_usd_per_million=rate("_OUTPUT_USD_PER_MILLION"),
    )


def preflight(settings: list[Settings]) -> list[str]:
    errors = []
    for cfg in settings:
        if not cfg.model:
            errors.append(cfg.role.upper() + "_MODEL is unset" + (" (defaults to EVAL_MODEL)" if cfg.role == "simulator" else ""))
        if cfg.max_tokens <= 0:
            errors.append(cfg.role + " max_tokens must be positive")
        if not 0 <= cfg.temperature <= (1 if cfg.provider == "anthropic" else 2):
            errors.append(cfg.role + " temperature is outside provider range")
        key_name = "ANTHROPIC_API_KEY" if cfg.provider == "anthropic" else "OPENAI_API_KEY"
        if not os.environ.get(key_name):
            errors.append(key_name + " is unset")
    by_role = {s.role: s for s in settings}
    if by_role["eval"].model and by_role["eval"].model == by_role["judge"].model:
        errors.append("EVAL_MODEL and JUDGE_MODEL must be different exact model IDs")
    return list(dict.fromkeys(errors))


class APIClient:
    def __init__(self, cfg: Settings):
        self.cfg = cfg

    def complete(self, messages: list[dict], seed: int) -> dict:
        cfg = self.cfg
        if not cfg.model:
            raise ConfigurationError(cfg.role.upper() + "_MODEL is unset")
        started = time.monotonic()
        if cfg.provider == "openai":
            base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            payload = {"model": cfg.model, "messages": messages, "temperature": cfg.temperature,
                       "max_completion_tokens": cfg.max_tokens, "seed": seed, "response_format": {"type": "json_object"}, "store": False}
            headers = {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"], "Content-Type": "application/json"}
            url = base + "/chat/completions"
        else:
            base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
            payload = {"model": cfg.model, "system": "\n\n".join(m["content"] for m in messages if m["role"] == "system"),
                       "messages": [m for m in messages if m["role"] != "system"], "temperature": cfg.temperature, "max_tokens": cfg.max_tokens}
            headers = {"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            url = base + "/v1/messages"
        if not url.startswith("https://"):
            raise ConfigurationError("Provider base URL must use HTTPS")
        request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        try:
            with urllib.request.build_opener(NoRedirects()).open(request, timeout=60) as response:
                request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
                result = json.load(response)
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"{cfg.provider} returned HTTP {exc.code}; response body omitted") from None
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
            raise ProviderError(f"{cfg.provider} transport or JSON failure; details omitted to protect credentials") from None
        elapsed = time.monotonic() - started
        if cfg.provider == "openai":
            choice = result.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "") or ""
            usage = result.get("usage", {})
            input_tokens, output_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
            cached = usage.get("prompt_tokens_details", {}).get("cached_tokens")
            finish = choice.get("finish_reason")
        else:
            content = "\n".join(b["text"] for b in result.get("content", []) if b.get("type") == "text")
            usage = result.get("usage", {})
            input_tokens = usage.get("input_tokens")
            if input_tokens is not None:
                input_tokens += usage.get("cache_read_input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
            output_tokens, cached = usage.get("output_tokens"), usage.get("cache_read_input_tokens")
            finish = result.get("stop_reason")
        cost = None
        if cfg.input_usd_per_million is not None and cfg.output_usd_per_million is not None and input_tokens is not None and output_tokens is not None:
            cost = (input_tokens * cfg.input_usd_per_million + output_tokens * cfg.output_usd_per_million) / 1_000_000
        return {"content": content, "model_requested": cfg.model, "model_returned": result.get("model"),
                "provider": cfg.provider, "system_fingerprint": result.get("system_fingerprint"),
                "temperature": cfg.temperature, "max_tokens": cfg.max_tokens,
                "seed_requested": seed, "seed_sent": seed if cfg.seed_supported else None,
                "seed_support_status": "request_accepted_best_effort" if cfg.seed_supported else "provider_has_no_seed_parameter",
                "latency_seconds": elapsed, "request_id": request_id, "response_id": result.get("id"),
                "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens, "cached_input_tokens": cached},
                "usage_missing": input_tokens is None or output_tokens is None,
                "estimated_uncached_cost_usd": cost, "finish_reason": finish}


class OfflineClient:
    """Canned transport probe. Never a subject, judge, or source of empirical scores."""
    def __init__(self, cfg: Settings):
        self.cfg = cfg

    def complete(self, messages: list[dict], seed: int) -> dict:
        # Deliberately identical across all conditions: no staged positive result.
        content = json.dumps({"reply": "Transport check complete. This canned response is not a model evaluation.", "done": True})
        return {"content": content, "model_requested": None, "model_returned": None, "provider": "offline_stub",
                "system_fingerprint": None, "temperature": None, "max_tokens": None,
                "seed_requested": seed, "seed_sent": None, "seed_supported": False,
                "latency_seconds": 0.0, "usage": {"input_tokens": 0, "output_tokens": 0, "cached_input_tokens": 0},
                "estimated_uncached_cost_usd": None, "finish_reason": "offline_stub", "is_empirical": False}

from dataclasses import dataclass

import httpx

from tokyo.packages.contracts.risk import RiskEvent


@dataclass(frozen=True, slots=True)
class WebhookAlertConfig:
    url: str | None
    kind: str | None


class WebhookAlertSender:
    def __init__(self, config: WebhookAlertConfig) -> None:
        self._config = config

    async def send(self, event: RiskEvent) -> None:
        if not self._config.url:
            return
        payload = self._format(event)
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(self._config.url, json=payload)

    def _format(self, event: RiskEvent) -> dict[str, object]:
        text = f"[{event.severity.value}] {event.event_type}: {event.message}"
        if self._config.kind == "discord":
            return {"content": text}
        if self._config.kind == "telegram":
            return {"text": text}
        return {"text": text}


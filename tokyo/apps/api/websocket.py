from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from tokyo.apps.api.runtime import TokyoRuntime
from tokyo.apps.api.utils.dependencies import validate_api_key
from tokyo.packages.common.errors import TokyoError, ValidationFailure
from tokyo.packages.contracts.api import ApiError
from tokyo.packages.contracts.enums import ErrorCode
from tokyo.packages.contracts.orders import OrderIntent
from tokyo.packages.contracts.websocket import (
    SubscribePayload,
    SubscriptionAckPayload,
    WebSocketEnvelope,
)

websocket_router = APIRouter(tags=["websocket"])


class WebSocketSession:
    def __init__(self, websocket: WebSocket, runtime: TokyoRuntime) -> None:
        self.websocket = websocket
        self.runtime = runtime
        self.sequence = 0
        self.channels: set[str] = set()

    async def send(
        self,
        message_type: str,
        payload: dict[str, object],
        request_id: object | None = None,
    ) -> None:
        self.sequence += 1
        envelope = WebSocketEnvelope(
            type=message_type,
            request_id=request_id,
            correlation_id=uuid4(),
            sequence=self.sequence,
            timestamp=datetime.now(UTC),
            source="tokyo-api",
            payload=payload,
        )
        await self.websocket.send_json(envelope.model_dump(mode="json"))

    async def send_error(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        await self.send(
            "error",
            {
                "error": ApiError(
                    code=code,
                    message=message,
                    details=details or {},
                ).model_dump(mode="json")
            },
        )


@websocket_router.websocket("/ws/v1/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    runtime: TokyoRuntime = websocket.app.state.runtime
    try:
        validate_api_key(
            runtime.settings,
            websocket.headers.get("x-api-key"),
            websocket.headers.get("authorization"),
        )
    except TokyoError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await websocket.accept()
    session = WebSocketSession(websocket, runtime)
    try:
        while True:
            raw = await websocket.receive_json()
            envelope = WebSocketEnvelope.model_validate(raw)
            await handle_message(session, envelope)
    except WebSocketDisconnect:
        return
    except ValidationError as exc:
        await session.send_error(
            ErrorCode.validation_error,
            "Invalid WebSocket message.",
            {"errors": exc.errors()},
        )
    except TokyoError as exc:
        await session.send_error(exc.code, exc.message, exc.details)


async def handle_message(session: WebSocketSession, envelope: WebSocketEnvelope) -> None:
    if envelope.type == "subscribe":
        payload = SubscribePayload.model_validate(envelope.payload)
        session.channels.update(payload.channels)
        await session.send(
            "subscription.ack",
            SubscriptionAckPayload(channels=payload.channels).model_dump(mode="json"),
            envelope.request_id,
        )
        return
    if envelope.type == "unsubscribe":
        payload = SubscribePayload.model_validate(envelope.payload)
        for channel in payload.channels:
            session.channels.discard(channel)
        await session.send("subscription.ack", {"channels": payload.channels}, envelope.request_id)
        return
    if envelope.type == "system.heartbeat":
        await session.send(
            "system.heartbeat",
            {"sent_at": datetime.now(UTC).isoformat()},
            envelope.request_id,
        )
        return
    if envelope.type == "order.intent":
        intent = OrderIntent.model_validate(envelope.payload)
        result = await session.runtime.execution.submit_order_intent(
            intent,
            envelope.correlation_id,
        )
        if result.accepted:
            await session.send(
                "order.accepted",
                {"order": result.order.model_dump(mode="json")},
                envelope.request_id,
            )
            await session.send("order.state", {"order": result.order.model_dump(mode="json")})
            for execution in result.executions:
                await session.send(
                    "execution.report",
                    {"execution": execution.model_dump(mode="json")},
                )
            if result.position:
                await session.send(
                    "position.snapshot",
                    {"position": result.position.model_dump(mode="json")},
                )
        else:
            await session.send(
                "order.rejected",
                {
                    "order": result.order.model_dump(mode="json"),
                    "reason_code": result.reason_code,
                },
                envelope.request_id,
            )
        return
    raise ValidationFailure(
        ErrorCode.validation_error,
        "Unsupported WebSocket message type.",
        {"type": envelope.type},
    )

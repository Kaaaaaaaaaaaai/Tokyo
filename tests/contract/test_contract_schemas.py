from tokyo.packages.contracts.market_data import MarketBar, MarketTick
from tokyo.packages.contracts.orders import OrderIntent
from tokyo.packages.contracts.symbol import Symbol
from tokyo.packages.contracts.websocket import WebSocketEnvelope


def test_core_contracts_generate_json_schema() -> None:
    for model in (Symbol, MarketTick, MarketBar, OrderIntent, WebSocketEnvelope):
        schema = model.model_json_schema()
        assert schema["type"] == "object"
        assert "properties" in schema


def test_decimal_fields_are_json_schema_strings() -> None:
    schema = OrderIntent.model_json_schema()
    quantity_schema = schema["properties"]["quantity"]
    assert quantity_schema["type"] == "string"


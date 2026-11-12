import json
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator
import yaml


CONTRACTS = Path(__file__).parents[1]
EVENTS = CONTRACTS / "events"
EVENT_TYPES = {
    "ServiceOrderOpenedV1",
    "DiagnosisStartedV1",
    "DiagnosisRequestedV1",
    "DiagnosisCompletedV1",
    "QuoteGenerationRequestedV1",
    "QuoteGeneratedV1",
    "QuoteApprovedV1",
    "QuoteRejectedV1",
    "ExecutionRequestedV1",
    "ExecutionQueuedV1",
    "ExecutionStartedV1",
    "ExecutionCompletedV1",
    "ExecutionFailedV1",
    "ExecutionCancelledV1",
    "PaymentCreationRequestedV1",
    "PaymentPendingV1",
    "PaymentConfirmedV1",
    "PaymentRejectedV1",
    "PaymentRefundedV1",
}


def test_every_json_schema_is_valid():
    schemas = list(EVENTS.glob("*.schema.json"))
    assert {path.name for path in schemas} >= {
        "envelope.schema.json",
        "integration-event.schema.json",
    }
    for path in schemas:
        Draft202012Validator.check_schema(json.loads(path.read_text()))


def test_integration_schema_accepts_every_documented_event_type():
    schema = json.loads((EVENTS / "integration-event.schema.json").read_text())
    validator = Draft202012Validator(schema)
    for event_type in EVENT_TYPES:
        identifier = str(uuid4())
        event = {
            "event_id": identifier,
            "event_type": event_type,
            "event_version": 1,
            "occurred_at": "2026-11-12T12:00:00Z",
            "correlation_id": str(uuid4()),
            "causation_id": str(uuid4()),
            "saga_id": str(uuid4()),
            "order_id": str(uuid4()),
            "payload": {},
        }
        validator.validate(event)


def test_asyncapi_documents_queues_dlqs_and_all_event_types():
    document = yaml.safe_load((CONTRACTS / "asyncapi.yaml").read_text())
    assert document["asyncapi"] == "2.6.0"
    channels = document["channels"]
    assert {
        "service-order-commands",
        "billing-commands",
        "execution-commands",
        "domain-events",
        "service-order-dlq",
        "billing-dlq",
        "execution-dlq",
    } <= set(channels)
    documented = set(
        document["components"]["schemas"]["IntegrationEvent"]["properties"][
            "event_type"
        ]["enum"]
    )
    assert documented == EVENT_TYPES

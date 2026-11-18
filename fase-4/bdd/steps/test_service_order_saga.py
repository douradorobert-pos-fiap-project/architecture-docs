from __future__ import annotations

import importlib
import os
import sys
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from pytest_bdd import given, scenarios, then, when
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[3]
REPOS = Path(os.getenv("FASE4_REPOS_ROOT", "/home/robertd/repositorios"))
scenarios("../features/service_order_saga.feature")


def purge_src() -> None:
    for name in [
        name for name in sys.modules if name == "src" or name.startswith("src.")
    ]:
        del sys.modules[name]


def import_from(repo: Path, *modules: str):
    purge_src()
    sys.path.insert(0, str(repo))
    try:
        return [importlib.import_module(module) for module in modules]
    finally:
        sys.path.remove(str(repo))


@pytest.fixture
def world():
    stack = ExitStack()
    os_main, os_models, os_domain, os_status, os_saga, os_envelope = import_from(
        REPOS / "tech-challenge-fiap-os-service",
        "src.api.main",
        "src.infrastructure.database.models",
        "src.domain.service_order",
        "src.domain.service_order_status",
        "src.application.process_saga_event",
        "src.infrastructure.messaging.envelope",
    )
    os_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    os_models.Base.metadata.create_all(os_engine)
    os_client = stack.enter_context(
        TestClient(os_main.create_app(sessionmaker(os_engine, expire_on_commit=False)))
    )

    billing_main, billing_models = import_from(
        REPOS / "tech-challenge-fiap-billing-service",
        "src.api.main",
        "src.infrastructure.database.models",
    )
    billing_engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    billing_models.Base.metadata.create_all(billing_engine)
    billing_client = stack.enter_context(
        TestClient(
            billing_main.create_app(
                sessionmaker(billing_engine, expire_on_commit=False),
                environment="test",
            )
        )
    )

    moto = stack.enter_context(mock_aws())
    del moto
    execution_main, execution_bootstrap, execution_repo = import_from(
        REPOS / "tech-challenge-fiap-execution-service",
        "src.api.main",
        "src.infrastructure.database.bootstrap",
        "src.infrastructure.database.dynamodb_repository",
    )
    dynamodb = boto3.client("dynamodb", region_name="us-east-1")
    execution_bootstrap.create_execution_table(dynamodb, "bdd-executions")
    execution_client = stack.enter_context(
        TestClient(
            execution_main.create_app(
                execution_repo.DynamoDBExecutionRepository(dynamodb, "bdd-executions")
            )
        )
    )
    fake_path = ROOT / "fase-4" / "bdd" / "fakes"
    sys.path.insert(0, str(fake_path))
    try:
        fake_module = importlib.import_module("mercado_pago")
    finally:
        sys.path.remove(str(fake_path))
    yield SimpleNamespace(
        stack=stack,
        os=os_client,
        billing=billing_client,
        execution=execution_client,
        ServiceOrder=os_domain.ServiceOrder,
        ServiceOrderStatus=os_status.ServiceOrderStatus,
        SagaProcessManager=os_saga.SagaProcessManager,
        Envelope=os_envelope.EventEnvelopeV1,
        payment=fake_module.FakeMercadoPago(),
        deliveries=0,
    )
    stack.close()


def event(world, event_type: str, event_id: UUID | None = None):
    return world.Envelope(
        event_id=event_id or uuid4(),
        event_type=event_type,
        occurred_at=datetime.now(UTC),
        correlation_id=world.correlation_id,
        causation_id=uuid4(),
        saga_id=world.saga_id,
        order_id=world.order_id,
        payload={},
    )


def apply(world, event_type: str, event_id: UUID | None = None):
    before = world.manager.order.status
    commands = world.manager.handle_event(event(world, event_type, event_id))
    if (
        before != world.ServiceOrderStatus.DELIVERED
        and world.manager.order.status == world.ServiceOrderStatus.DELIVERED
    ):
        world.deliveries += 1
    return commands


@given("uma ordem de serviço aberta com rastreabilidade")
def opened_order(world):
    world.correlation_id = uuid4()
    headers = {"X-Correlation-ID": str(world.correlation_id)}
    customer = world.os.post(
        "/api/v1/customers",
        json={"name": "BDD", "document": "12345678901"},
        headers=headers,
    ).json()
    vehicle = world.os.post(
        "/api/v1/vehicles",
        json={
            "customer_id": customer["id"],
            "license_plate": "BDD4A01",
            "make": "FIAP",
            "model": "Test",
            "year": 2026,
        },
        headers=headers,
    ).json()
    response = world.os.post(
        "/api/v1/service-orders",
        json={"customer_id": customer["id"], "vehicle_id": vehicle["id"]},
        headers=headers,
    )
    assert response.status_code == 201
    order = response.json()
    world.order_id, world.saga_id = UUID(order["id"]), UUID(order["saga_id"])
    aggregate = world.ServiceOrder(
        id=world.order_id,
        customer_id=UUID(customer["id"]),
        vehicle_id=UUID(vehicle["id"]),
        saga_id=world.saga_id,
        correlation_id=world.correlation_id,
    )
    world.manager = world.SagaProcessManager(aggregate)
    apply(world, "ServiceOrderOpenedV1")


def complete_until_execution(world, *, start_repair: bool):
    headers = {
        "X-Correlation-ID": str(world.correlation_id),
        "X-Event-ID": str(uuid4()),
    }
    execution = world.execution.post(
        "/api/v1/executions/diagnosis",
        json={"order_id": str(world.order_id), "saga_id": str(world.saga_id)},
        headers=headers,
    ).json()
    execution_id = execution["id"]
    response = world.execution.post(
        f"/api/v1/executions/{execution_id}/diagnosis/complete",
        json={"diagnosis": "freios", "recommended_service_ids": [str(uuid4())]},
        headers={"X-Event-ID": str(uuid4())},
    )
    assert response.status_code == 200
    apply(world, "DiagnosisCompletedV1")
    catalog = world.billing.post(
        "/api/v1/catalog-items",
        json={"name": "Reparo", "item_type": "SERVICE", "unit_price": "150.00"},
        headers={"X-Correlation-ID": str(world.correlation_id)},
    ).json()
    quote = world.billing.post(
        "/api/v1/quotes",
        json={
            "order_id": str(world.order_id),
            "saga_id": str(world.saga_id),
            "items": [{"catalog_item_id": catalog["id"], "quantity": 1}],
        },
        headers={"X-Correlation-ID": str(world.correlation_id)},
    ).json()
    apply(world, "QuoteGeneratedV1")
    approved = world.billing.post(
        f"/api/v1/quotes/{quote['id']}/approval", json={"action": "approve"}
    )
    assert approved.status_code == 200
    apply(world, "QuoteApprovedV1")
    queued = world.execution.post(
        f"/api/v1/executions/{execution_id}/queue", headers={"X-Event-ID": str(uuid4())}
    )
    assert queued.status_code == 200
    world.execution_id = execution_id
    if start_repair:
        started = world.execution.post(
            f"/api/v1/executions/{execution_id}/repair/start",
            headers={"X-Event-ID": str(uuid4())},
        )
        assert started.status_code == 200
        apply(world, "ExecutionStartedV1")


@when("o diagnóstico, orçamento aprovado, reparo e pagamento forem concluídos")
def happy_flow(world):
    complete_until_execution(world, start_repair=True)
    repaired = world.execution.post(
        f"/api/v1/executions/{world.execution_id}/repair/complete",
        json={"notes": "concluído"},
        headers={"X-Event-ID": str(uuid4())},
    )
    assert repaired.status_code == 200
    apply(world, "ExecutionCompletedV1")
    world.payment.confirm_once(str(world.order_id))
    apply(world, "PaymentConfirmedV1")


@when("a execução falhar antes do início do reparo")
def failure_before_repair(world):
    complete_until_execution(world, start_repair=False)
    failed = world.execution.post(
        f"/api/v1/executions/{world.execution_id}/cancel",
        json={"reason": "elevador indisponível"},
        headers={"X-Event-ID": str(uuid4())},
    )
    assert failed.status_code == 200
    apply(world, "ExecutionCancelledV1")


@given("uma ordem de serviço pronta para receber o pagamento")
def ready_for_payment(world):
    opened_order(world)
    complete_until_execution(world, start_repair=True)
    repaired = world.execution.post(
        f"/api/v1/executions/{world.execution_id}/repair/complete",
        json={"notes": "concluído"},
        headers={"X-Event-ID": str(uuid4())},
    )
    assert repaired.status_code == 200
    apply(world, "ExecutionCompletedV1")


@when("a mesma confirmação de pagamento for recebida duas vezes")
def duplicate_payment(world):
    payment_event_id = uuid4()
    world.payment.confirm_once(str(world.order_id))
    apply(world, "PaymentConfirmedV1", payment_event_id)
    apply(world, "PaymentConfirmedV1", payment_event_id)


@then("a ordem deve ser entregue uma única vez")
def delivered_once(world):
    assert world.manager.order.status == world.ServiceOrderStatus.DELIVERED
    assert world.deliveries == 1


@then("todos os participantes devem preservar o mesmo identificador de correlação")
def correlated(world):
    assert world.manager.order.correlation_id == world.correlation_id


@then("a saga deve cancelar a ordem sem exigir intervenção manual")
def compensated(world):
    assert world.manager.order.status == world.ServiceOrderStatus.CANCELLED


@then("o provedor de pagamento deve registrar uma única confirmação")
def payment_once(world):
    assert world.payment.confirmation_count == 1

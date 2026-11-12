from dataclasses import dataclass, field

from fastapi import FastAPI
from pydantic import BaseModel


class StatusChange(BaseModel):
    external_id: str
    status: str


@dataclass
class FakeMercadoPago:
    statuses: dict[str, str] = field(default_factory=dict)
    confirmation_count: int = 0

    def confirm_once(self, external_id: str) -> dict[str, str]:
        if self.statuses.get(external_id) != "approved":
            self.statuses[external_id] = "approved"
            self.confirmation_count += 1
        return {"external_id": external_id, "status": "approved"}


gateway = FakeMercadoPago()
app = FastAPI(title="Fake Mercado Pago", version="1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/test/payments/status")
def set_status(change: StatusChange) -> dict[str, str]:
    if change.status == "approved":
        return gateway.confirm_once(change.external_id)
    gateway.statuses[change.external_id] = change.status
    return {"external_id": change.external_id, "status": change.status}

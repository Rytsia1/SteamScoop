from fastapi.testclient import TestClient

from app.main import app
from app.schemas.common import HealthData, ResponseEnvelope

client = TestClient(app)


def test_health_contract_schema_validation() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    raw_json = response.json()
    validated = ResponseEnvelope[HealthData].model_validate(raw_json)

    assert validated.error is None
    assert validated.data is not None
    assert validated.data.status in ("healthy", "degraded")
    assert validated.data.dependencies is not None
    assert validated.meta.request_id.startswith("req_")

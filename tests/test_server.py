"""Tests for the local HTTP service wrapper (shyftr.server)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from shyftr.server import _get_app, main, service_dependencies_available


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    """TestClient backed by the FastAPI app (no server process needed)."""
    app = _get_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["status"] == "ok"
        assert payload["service"] == "shyftr-local-http"

    def test_service_dependencies_available(self) -> None:
        assert service_dependencies_available() is True

    def test_module_main_parses_bind_options(self) -> None:
        with patch("shyftr.server.run") as mock_run:
            main(["--host", "127.0.0.1", "--port", "8123", "--log-level", "debug"])
        mock_run.assert_called_once_with(host="127.0.0.1", port=8123, log_level="debug")


# ---------------------------------------------------------------------------
# POST /validate
# ---------------------------------------------------------------------------


class TestValidate:
    VALID_CONFIG_RESPONSE = {
        "adapter_id": "my-adapter",
        "cell_id": "cell-01",
        "external_system": "jira",
        "external_scope": "PROJ-1",
        "source_root": "/tmp/sources",
        "inputs": [
            {"kind": "epic", "path": "epics.csv", "source_kind": "csv"},
        ],
    }

    def test_validate_ok(self, client: TestClient) -> None:
        with patch("shyftr.integrations.config.load_config") as mock_load, \
             patch("shyftr.integrations.config.validate_config") as mock_validate:
            mock_load.return_value = _make_config_stub(**self.VALID_CONFIG_RESPONSE)
            mock_validate.return_value = None

            resp = client.post("/validate", json={"config_path": "/tmp/test.yaml"})
            assert resp.status_code == 200
            payload = resp.json()
            assert payload["status"] == "ok"
            assert payload["adapter_id"] == "my-adapter"

    def test_validate_missing_config_path(self, client: TestClient) -> None:
        resp = client.post("/validate", json={})
        assert resp.status_code == 422
        assert "config_path is required" in resp.json()["message"]

    def test_validate_error(self, client: TestClient) -> None:
        with patch("shyftr.integrations.config.load_config") as mock_load:
            mock_load.side_effect = ValueError("invalid config")

            resp = client.post("/validate", json={"config_path": "/tmp/bad.yaml"})
            assert resp.status_code == 400
            assert "invalid config" in resp.json()["message"]


# ---------------------------------------------------------------------------
# POST /ingest
# ---------------------------------------------------------------------------


class TestIngest:
    def test_ingest_ok(self, client: TestClient) -> None:
        with patch("shyftr.ingest.ingest_from_adapter") as mock_ingest:
            mock_ingest.return_value = {"sources_created": 3, "pulse_id": "pulse-abc"}

            resp = client.post(
                "/ingest",
                json={
                    "config_path": "/tmp/test.yaml",
                    "cell_path": "/tmp/cell",
                    "dry_run": False,
                },
            )
            assert resp.status_code == 200
            payload = resp.json()
            assert payload["status"] == "ok"
            assert payload["sources_created"] == 3

    def test_ingest_dry_run(self, client: TestClient) -> None:
        with patch("shyftr.ingest.ingest_from_adapter") as mock_ingest:
            mock_ingest.return_value = {"sources_created": 0, "pulse_id": None}

            resp = client.post(
                "/ingest",
                json={
                    "config_path": "/tmp/test.yaml",
                    "cell_path": "/tmp/cell",
                    "dry_run": True,
                },
            )
            assert resp.status_code == 200
            # Verify ingest_from_adapter was called with dry_run=True
            _args, kwargs = mock_ingest.call_args
            assert kwargs.get("dry_run") is True

    def test_ingest_missing_config_path(self, client: TestClient) -> None:
        resp = client.post("/ingest", json={"cell_path": "/tmp/cell"})
        assert resp.status_code == 422
        assert "config_path is required" in resp.json()["message"]

    def test_ingest_missing_cell_path(self, client: TestClient) -> None:
        resp = client.post("/ingest", json={"config_path": "/tmp/test.yaml"})
        assert resp.status_code == 422
        assert "cell_path is required" in resp.json()["message"]

    def test_ingest_error(self, client: TestClient) -> None:
        with patch("shyftr.ingest.ingest_from_adapter") as mock_ingest:
            mock_ingest.side_effect = RuntimeError("ingest failure")

            resp = client.post(
                "/ingest",
                json={"config_path": "/tmp/test.yaml", "cell_path": "/tmp/cell"},
            )
            assert resp.status_code == 400
            assert "ingest failure" in resp.json()["message"]


# ---------------------------------------------------------------------------
# POST /pack
# ---------------------------------------------------------------------------


class TestPack:
    def test_pack_ok(self, client: TestClient) -> None:
        mock_response = {"pack_id": "pack-42", "status": "accepted", "items": []}

        with patch(
            "shyftr.integrations.loadout_api.process_runtime_loadout_request"
        ) as mock_process, patch(
            "shyftr.integrations.loadout_api.RuntimeLoadoutRequest"
        ) as mock_req:
            mock_req.from_dict.return_value = "request-stub"
            mock_process.return_value.to_dict.return_value = mock_response

            resp = client.post(
                "/pack",
                json={"cell_id": "cell-01", "scope": "test"},
            )
            assert resp.status_code == 200
            assert resp.json() == mock_response

    def test_pack_error(self, client: TestClient) -> None:
        with patch(
            "shyftr.integrations.loadout_api.process_runtime_loadout_request"
        ) as mock_process, patch(
            "shyftr.integrations.loadout_api.RuntimeLoadoutRequest"
        ) as mock_req:
            mock_req.from_dict.return_value = "request-stub"
            mock_process.side_effect = ValueError("bad loadout")

            resp = client.post(
                "/pack",
                json={"cell_id": "cell-01"},
            )
            assert resp.status_code == 400
            assert "bad loadout" in resp.json()["message"]


# ---------------------------------------------------------------------------
# POST /signal
# ---------------------------------------------------------------------------


class TestSignal:
    def test_signal_ok(self, client: TestClient) -> None:
        mock_response = {"signal_id": "sig-99", "status": "recorded"}

        with patch(
            "shyftr.integrations.outcome_api.process_runtime_outcome_report"
        ) as mock_process, patch(
            "shyftr.integrations.outcome_api.RuntimeOutcomeReport"
        ) as mock_req:
            mock_req.from_dict.return_value = "report-stub"
            mock_process.return_value.to_dict.return_value = mock_response

            resp = client.post(
                "/signal",
                json={"cell_id": "cell-01", "outcome": "success"},
            )
            assert resp.status_code == 200
            assert resp.json() == mock_response

    def test_signal_error(self, client: TestClient) -> None:
        with patch(
            "shyftr.integrations.outcome_api.process_runtime_outcome_report"
        ) as mock_process, patch(
            "shyftr.integrations.outcome_api.RuntimeOutcomeReport"
        ) as mock_req:
            mock_req.from_dict.return_value = "report-stub"
            mock_process.side_effect = ValueError("bad signal")

            resp = client.post(
                "/signal",
                json={"cell_id": "cell-01"},
            )
            assert resp.status_code == 400
            assert "bad signal" in resp.json()["message"]


# ---------------------------------------------------------------------------
# POST /proposals/export
# ---------------------------------------------------------------------------


class TestProposalsExport:
    def test_export_ok(self, client: TestClient) -> None:
        mock_payload = {"proposals": [], "stale_accepted": []}

        with patch(
            "shyftr.integrations.proposals.export_runtime_proposals"
        ) as mock_export:
            mock_export.return_value = mock_payload

            resp = client.post(
                "/proposals/export",
                json={
                    "cell_path": "/tmp/cell",
                    "external_system": "jira",
                    "include_accepted": True,
                },
            )
            assert resp.status_code == 200
            assert resp.json() == mock_payload

    def test_export_missing_cell_path(self, client: TestClient) -> None:
        resp = client.post("/proposals/export", json={})
        assert resp.status_code == 422
        assert "cell_path is required" in resp.json()["message"]

    def test_export_error(self, client: TestClient) -> None:
        with patch(
            "shyftr.integrations.proposals.export_runtime_proposals"
        ) as mock_export:
            mock_export.side_effect = RuntimeError("export failed")

            resp = client.post(
                "/proposals/export",
                json={"cell_path": "/tmp/cell"},
            )
            assert resp.status_code == 400
            assert "export failed" in resp.json()["message"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_invalid_json_body(self, client: TestClient) -> None:
        """Sending non-JSON body returns 422."""
        resp = client.post(
            "/validate",
            content=b"not-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422

    def test_missing_route_returns_404(self, client: TestClient) -> None:
        resp = client.get("/nonexistent")
        assert resp.status_code == 404

    def test_method_not_allowed(self, client: TestClient) -> None:
        """GET on a POST-only endpoint returns 405."""
        resp = client.get("/validate")
        assert resp.status_code == 405


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config_stub(**kwargs: object):
    """Return a simple stub object with attribute access."""

    class _Stub:
        pass

    stub = _Stub()
    for key, val in kwargs.items():
        if key == "inputs":
            stub.inputs = [_make_input_stub(**i) if isinstance(i, dict) else i for i in val]
        else:
            setattr(stub, key, val)
    return stub


def _make_input_stub(**kwargs: object):
    class _InputStub:
        pass
    stub = _InputStub()
    for key, val in kwargs.items():
        setattr(stub, key, val)
    return stub

"""reporting_support — search hit shape and export/search schemas."""

from datetime import datetime, timezone

from app.modules.reporting_support.domain.schemas import AskRequest, ExportCreateRequest, SearchHit
from app.modules.reporting_support.services.search import build_search_hit


def test_build_search_hit_shape():
    hit = build_search_hit(
        resource="documents",
        entity_id="abc",
        title="Title",
        description="Desc",
        updated_at=datetime.now(timezone.utc),
    )
    assert hit["id"] == "abc"
    assert hit["title"] == "Title"
    assert hit["url"]
    assert hit["permission"]
    assert "snippet" in hit


def test_ask_and_export_schemas():
    assert AskRequest(q="hello").q == "hello"
    body = ExportCreateRequest(resource="records.documents", format="csv")
    assert body.format == "csv"


def test_search_hit_schema():
    hit = SearchHit(id="1", title="t", entityType="document")
    assert hit.id == "1"

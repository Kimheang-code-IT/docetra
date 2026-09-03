from app.modules.record.services.kind import CollectionSpec


def test_collection_spec_maps_typed_resources():
    assert CollectionSpec(type_code="meeting_history").kind() == "record"
    assert CollectionSpec("export-jobs").kind() == "entity"

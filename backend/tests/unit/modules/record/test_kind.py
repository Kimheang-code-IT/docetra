from app.modules.record.services.kind import CollectionSpec


def test_collection_spec_maps_typed_resources():
    assert CollectionSpec(type_code="meeting_history").kind() == "record"
    assert CollectionSpec(org_type="company").kind() == "organization"
    assert CollectionSpec("roles").kind() == "role"
    assert CollectionSpec("users").kind() == "user"
    assert CollectionSpec("file-uploads").kind() == "file"
    assert CollectionSpec("export-jobs").kind() == "entity"

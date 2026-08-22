from app.core.permissions import catalog_rows


def permission_catalog() -> list[dict]:
    return catalog_rows()

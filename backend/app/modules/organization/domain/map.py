"""Organization type map.

API org types:
- ``department`` — government structures (DB ``organization_type=government``)
- ``company`` — external companies

Classification lookups are top-level: ``/api/v2/sector``, ``/api/v2/purpose``.
Officers are owned by people_access at ``/api/v2/officers``.
"""

from __future__ import annotations

# API orgType → DB organization.organization_type
ORG_TYPES: dict[str, str] = {
    "department": "government",
    "company": "company",
}

# Legacy plural collection resource → API orgType
LEGACY_ORG_RESOURCES: dict[str, str] = {
    "departments": "department",
    "companies": "company",
}

# Legacy plural collection → DB organization_type (compat)
ORG_RESOURCES: dict[str, str] = {
    "departments": "government",
    "companies": "company",
}

ORG_TYPE_TO_RESOURCE: dict[str, str] = {org_type: resource for resource, org_type in LEGACY_ORG_RESOURCES.items()}
RESOURCE_FOR_DB_ORG_TYPE: dict[str, str] = {db_type: resource for resource, db_type in ORG_RESOURCES.items()}

RESERVED_ORG_SEGMENTS = frozenset({"_meta", "sectors", "purposes", "officers"})

ORG_LOOKUP_RESOURCES = {
    "sectors": "organization_sector",
    "purposes": "organization_purpose",
}

ORG_TYPE_META: dict[str, dict] = {
    "department": {
        "name": "Department",
        "kind": "government_structure",
        "slug": "departments",
        "icon": "i-lucide-building-2",
        "menuOrder": 10,
        "supportsHierarchy": True,
        "supportsSectorPurpose": False,
        "routeBase": "/organizations/departments",
        "apiBase": "/api/v2/organizations/department",
    },
    "company": {
        "name": "Company",
        "kind": "company",
        "slug": "companies",
        "icon": "i-lucide-briefcase",
        "menuOrder": 20,
        "supportsHierarchy": False,
        "supportsSectorPurpose": True,
        "routeBase": "/organizations/companies",
        "apiBase": "/api/v2/organizations/company",
    },
}


def is_valid_org_type(org_type: str) -> bool:
    return org_type in ORG_TYPES and org_type not in RESERVED_ORG_SEGMENTS


def db_org_type_for(org_type: str) -> str:
    if not is_valid_org_type(org_type):
        raise KeyError(org_type)
    return ORG_TYPES[org_type]


def permission_prefix_for_org_type(org_type: str) -> str:
    resource = ORG_TYPE_TO_RESOURCE.get(org_type)
    if resource == "departments":
        return "organizations.departments"
    if resource == "companies":
        return "organizations.companies"
    return f"organizations.{org_type}"

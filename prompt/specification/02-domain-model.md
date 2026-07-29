# Docetra v2 Domain Model

## Purpose

This document defines the business domains and core concepts used by Docetra v2. It explains what the system considers important business objects, how they relate to each other, and how the unified record model should be understood by the engineering team.

## Domain summary

Docetra is built around a unified record-centered domain model. Instead of treating every business item as a separate product, the system represents many operational items through a common record structure and differentiates behavior by record type.

The main domains are:
- Record.
- Organization.
- People and access.
- Storage.
- Configuration.
- Reporting support.

## Core domain principle

The central principle of Docetra v2 is that many different operational items can be represented as records, while still allowing type-specific behavior, attributes, workflow stages, and visibility rules.

This keeps the operational model consistent while still supporting different business needs across documents, meetings, logs, files, and other record categories.

## Record domain

The record domain is the heart of the system. It covers the lifecycle, history, type, attachments, and visibility of all record-based business items.

### Record
A record is the primary business object in the system. It represents an operational item that can be tracked, updated, viewed, shared, and preserved over time.

A record should usually contain:
- a record type.
- a title.
- status information.
- current stage information.
- timestamps.
- history context.
- links to related organizations.
- dynamic attributes.
- attachments or file references when applicable.

### Record type
A record type defines the category and behavior of a record. Different record types may have different fields, workflow stages, labels, and UI rendering rules.

Examples include:
- document.
- meeting.
- meeting-topic.
- approved-master-list.
- master-list-request.
- extension-of-validity.
- physical-inspection.
- tax-incentive.
- file.
- url.

### Record attribute
A record attribute defines a field that can be used by one or more record types. Attributes allow the system to support dynamic or configurable record data without changing the core record table structure each time.

### Record template
A record template defines which attributes belong to a record type and whether those attributes are required or optional.

### Record stage
A record stage represents the current step or phase of a record in its workflow. Different record types may have different stage templates.

### Record history
Record history preserves changes over time. It is required for timeline views, auditability, and operational traceability.

### Record attachment
A record attachment represents a link between a record and stored file metadata or another related record.

### Record detail
Record detail stores flexible field values for a record using typed value columns. It supports dynamic record behavior while keeping structured data available.

### Record organization link
A record may be associated with one or more organizations. This relationship captures ownership, participation, collaboration, or visibility context.

## Organization domain

The organization domain models departments, companies, government structures, and supporting classification data.

### Organization
An organization represents a business or administrative entity in the system. It may be a government unit, department, company, or other related structure.

### Organization hierarchy
Organizations may be nested or related through parent-child relationships. This allows the system to represent structured administrative or corporate trees.

### Organization sector
A sector is a classification layer used to group organizations by type or functional category.

### Organization purpose
A purpose is a classification that describes the business role or reason for an organization in the system.

### Organization history
Organizations should maintain history so that changes can be tracked over time and displayed in timeline-style views where needed.

## People and access domain

The people and access domain covers officers, users, roles, permissions, and account identity.

### Officer
An officer is a business-side person entity. Officers represent internal people who operate in the system or belong to an organization.

### User account
A user account is the authentication entity used to sign in. Not every officer must have a user account.

### Identity mapping
An officer may be linked to a user account. This mapping should be explicit and stable, but not assumed to be one-to-one in every case.

### Role
A role defines a permission set or access category for a user or officer.

### Permission
A permission controls whether a role can perform a specific action or access a specific menu, feature, or operation.

### Menu or action code
A menu or action code is a system-facing identifier used to enable or disable access to navigation items or actions.

## Storage domain

The storage domain manages uploaded files, object storage references, and external storage synchronization.

### File
A file represents stored binary content metadata. It is the business-facing record of a stored asset rather than the binary object itself.

### Storage reference
Storage references connect file metadata to the actual object storage location and any additional delivery details.

### Google Drive sync
Google Drive sync is a supporting storage process used to import, organize, or synchronize files and related records.

## Configuration domain

The configuration domain stores system settings, record definitions, document types, and other reusable configuration data.

### Setting
A setting is a configurable system value used by modules or runtime logic.

### Document type
A document type classifies a document record more specifically than the generic record type when needed.

### Enum-style reference data
Some reference data may be represented as configurable enum-style data where that improves maintainability without harming data quality.

## Reporting support domain

The reporting support domain prepares operational data for exports, dashboards, and future BI use cases.

### Reporting dataset
A reporting dataset is a read-oriented representation of business data optimized for filtering, export, and analysis.

### Export-ready data
Export-ready data is data shaped for spreadsheet exports or downloadable reports.

## Domain relationships

The main relationship pattern is:

- A record belongs to a record type.
- A record may have many dynamic details.
- A record may have many attachments.
- A record may relate to many organizations.
- A record may have many history entries.
- An officer may belong to one organization.
- An officer may optionally map to one user account.
- A role may have many permissions.
- A file may be linked to records or storage records.
- A setting may influence module behavior.

## Domain rules

- Every record must have a record type.
- Every record must have a clear owning or related organizational context.
- Record history must be preserved.
- Access rules must be enforced by role and organizational context.
- Dynamic attributes must be defined through record type configuration, not ad hoc UI logic.
- Files must be tracked as metadata entities, not only as raw storage objects.

## Domain boundaries

The engineering team should treat the following as separate domains, even if they share related data:
- Record operations.
- Organization structure.
- Identity and access.
- Storage handling.
- Configuration management.
- Reporting preparation.

This separation is important for maintainability and for keeping the rewrite clean.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/record.md`
- `modules/organization.md`
- `modules/people-access.md`

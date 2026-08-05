/**
 * Seed the Phase 2 search index from mock entity datasets (once per browser).
 */
import {
  mockCompanies,
  mockDepartments,
  mockDocuments,
  mockFileUploads,
  mockIncomingDocuments,
  mockMeetingHistory,
  mockMeetingTopics,
  mockOfficers,
  mockOutgoingDocuments,
  mockUsers,
} from '~/mocks/datasets'
import { seedAttachments } from '~/mocks/seed'
import type { IndexedDocument, SearchEntityType } from '~/types/docetra/search'
import {
  isSearchIndexSeeded,
  markSearchIndexSeeded,
  upsertIndexedDocuments,
} from '~/utils/search/search-index'
import { extractText } from '~/utils/search/text-extract'

function doc(partial: IndexedDocument): IndexedDocument {
  return partial
}

function buildSeedDocuments(): IndexedDocument[] {
  const out: IndexedDocument[] = []

  for (const row of mockIncomingDocuments.slice(0, 20)) {
    out.push(doc({
      id: `idx:incoming:${row.id}`,
      entityType: 'incomingDocument',
      entityId: row.id,
      title: row.title,
      text: [row.title, row.referenceNumber, row.status, row.stage].filter(Boolean).join('\n'),
      url: `/records/incoming-documents/${row.id}`,
      permission: 'records.incoming_documents.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockOutgoingDocuments.slice(0, 20)) {
    out.push(doc({
      id: `idx:outgoing:${row.id}`,
      entityType: 'outgoingDocument',
      entityId: row.id,
      title: row.title,
      text: [row.title, row.referenceNumber, row.status, row.stage].filter(Boolean).join('\n'),
      url: `/records/outgoing-documents/${row.id}`,
      permission: 'records.outgoing_documents.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockDocuments.slice(0, 20)) {
    out.push(doc({
      id: `idx:document:${row.id}`,
      entityType: 'document',
      entityId: row.id,
      title: row.title,
      text: [row.title, row.referenceNumber, row.status, row.stage].filter(Boolean).join('\n'),
      url: `/records/documents/${row.id}`,
      permission: 'records.documents.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockMeetingHistory.slice(0, 20)) {
    const notes = (row as { notes?: string }).notes || ''
    out.push(doc({
      id: `idx:meeting:${row.id}`,
      entityType: 'meeting',
      entityId: row.id,
      title: row.title,
      text: [row.title, row.location, row.topicTitle, notes, row.status].filter(Boolean).join('\n'),
      url: `/meetings/history/${row.id}`,
      permission: 'meetings.history.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockMeetingTopics.slice(0, 15)) {
    out.push(doc({
      id: `idx:topic:${row.id}`,
      entityType: 'meetingTopic',
      entityId: row.id,
      title: row.title,
      text: [row.title, row.status, row.stage, row.description].filter(Boolean).join('\n'),
      url: `/meetings/topics/${row.id}`,
      permission: 'meetings.topics.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockFileUploads) {
    const text = extractText({
      fileName: row.fileName,
      mimeType: row.mimeType,
      contextTitle: row.linkedRecordTitle || row.name,
    })
    out.push(doc({
      id: `idx:file:${row.id}`,
      entityType: 'file',
      entityId: row.id,
      title: row.fileName,
      text,
      url: `/portal/file-upload/${row.id}`,
      permission: 'portal.file_upload.view',
      mimeType: row.mimeType,
      updatedAt: row.updatedAt,
    }))
  }

  // Sample attachments linked to first incoming docs
  for (const row of mockIncomingDocuments.slice(0, 8)) {
    const atts = seedAttachments(2)
    for (const att of atts) {
      const text = extractText({
        fileName: att.name,
        mimeType: att.mimeType,
        contextTitle: row.title,
      })
      out.push(doc({
        id: `idx:att:${row.id}:${att.name}`,
        entityType: 'attachment',
        entityId: row.id,
        title: att.name,
        text,
        url: `/records/incoming-documents/${row.id}`,
        permission: 'records.incoming_documents.view',
        mimeType: att.mimeType,
        updatedAt: att.uploadedAt,
      }))
    }
  }

  for (const row of mockDepartments.slice(0, 12)) {
    out.push(doc({
      id: `idx:dept:${row.id}`,
      entityType: 'department',
      entityId: row.id,
      title: row.name,
      text: [row.name, row.code, row.status].filter(Boolean).join('\n'),
      url: `/organizations/departments/${row.id}`,
      permission: 'organizations.departments.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockCompanies.slice(0, 12)) {
    out.push(doc({
      id: `idx:company:${row.id}`,
      entityType: 'company',
      entityId: row.id,
      title: row.name,
      text: [row.name, row.code, row.registrationNumber, row.status].filter(Boolean).join('\n'),
      url: `/organizations/companies/${row.id}`,
      permission: 'organizations.companies.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockOfficers.slice(0, 12)) {
    out.push(doc({
      id: `idx:officer:${row.id}`,
      entityType: 'officer',
      entityId: row.id,
      title: row.name,
      text: [row.name, row.code, row.email, row.status].filter(Boolean).join('\n'),
      url: `/organizations/officers/${row.id}`,
      permission: 'organizations.officers.view',
      updatedAt: row.updatedAt,
    }))
  }

  for (const row of mockUsers.slice(0, 10)) {
    out.push(doc({
      id: `idx:user:${row.id}`,
      entityType: 'user',
      entityId: row.id,
      title: row.name,
      text: [row.name, row.email, row.status].filter(Boolean).join('\n'),
      url: `/user-management/users/${row.id}`,
      permission: 'users.users.view',
      updatedAt: row.updatedAt,
    }))
  }

  return out
}

export function ensureSearchIndexSeeded() {
  if (!import.meta.client) return
  if (isSearchIndexSeeded()) return
  upsertIndexedDocuments(buildSeedDocuments())
  markSearchIndexSeeded()
}

export function sourceLabelFor(entityType: SearchEntityType): string {
  const map: Record<SearchEntityType, string> = {
    navigation: 'Navigation',
    document: 'Document',
    incomingDocument: 'Incoming',
    outgoingDocument: 'Outgoing',
    meeting: 'Meeting',
    meetingTopic: 'Topic',
    file: 'File',
    attachment: 'Attachment',
    company: 'Company',
    department: 'Department',
    officer: 'Officer',
    user: 'User',
    other: 'Record',
  }
  return map[entityType] || 'Record'
}

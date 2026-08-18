/**
 * Helpers to upsert search-index rows after upload / notes save.
 */
import type { SearchEntityType } from '~/types/docetra/search'
import { upsertIndexedDocument } from '~/utils/search/search-index'
import { extractText } from '~/utils/search/text-extract'
function nowIso() {
  return new Date().toISOString()
}

export function indexFileForSearch(input: {
  entityId: string
  fileName: string
  mimeType?: string
  url: string
  permission?: string
  contextTitle?: string
  rawText?: string
  entityType?: SearchEntityType
  indexId?: string
}) {
  const text = extractText({
    fileName: input.fileName,
    mimeType: input.mimeType,
    contextTitle: input.contextTitle,
    rawText: input.rawText,
  })
  upsertIndexedDocument({
    id: input.indexId || `idx:file:${input.entityId}`,
    entityType: input.entityType || 'file',
    entityId: input.entityId,
    title: input.fileName,
    text,
    url: input.url,
    permission: input.permission || 'portal.file_upload.view',
    mimeType: input.mimeType,
    updatedAt: nowIso(),
  })
}

export function indexMeetingNotesForSearch(input: {
  meetingId: string
  title: string
  notes: string
}) {
  const body = String(input.notes || '').replace(/<[^>]+>/g, ' ').trim()
  upsertIndexedDocument({
    id: `idx:meeting:${input.meetingId}`,
    entityType: 'meeting',
    entityId: input.meetingId,
    title: input.title || 'Meeting',
    text: [input.title, body].filter(Boolean).join('\n'),
    url: `/meetings/history/${input.meetingId}`,
    permission: 'meetings.history.view',
    updatedAt: nowIso(),
  })
}

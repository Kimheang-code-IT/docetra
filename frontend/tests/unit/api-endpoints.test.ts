import { describe, expect, it } from 'vitest'
import { ApiEndpoints } from '../../app/utils/constants/api-endpoints'
import { unwrapApiData } from '../../app/repositories/http/response'
import { ROLE_DOCUMENT_TYPES } from '../../app/utils/role/permissions'
import { sameOriginApiUrl } from '../../app/utils/security/url'

function catalogPaths(): string[] {
  return Object.values(ApiEndpoints).flatMap((value) => {
    if (typeof value === 'string') return [value]
    if (typeof value === 'function') return [value('document', 'entity-1')]
    return []
  })
}

describe('ApiEndpoints catalog', () => {
  it('uses snake_case record type codes and singular org types', () => {
    expect(ApiEndpoints.MEETING_TOPICS).toBe('/api/v2/records/meeting_topic')
    expect(ApiEndpoints.MEETING_HISTORY).toBe('/api/v2/records/meeting_history')
    expect(ApiEndpoints.INCOMING_DOCUMENTS).toBe('/api/v2/records/incoming_document')
    expect(ApiEndpoints.OUTGOING_DOCUMENTS).toBe('/api/v2/records/outgoing_document')
    expect(ApiEndpoints.DOCUMENTS).toBe('/api/v2/records/document')
    expect(ApiEndpoints.MASTER_LIST_REQUESTS).toBe('/api/v2/records/master_list_request')
    expect(ApiEndpoints.DEPARTMENTS).toBe('/api/v2/organizations/department')
    expect(ApiEndpoints.COMPANIES).toBe('/api/v2/organizations/company')
    expect(ApiEndpoints.OFFICERS).toBe('/api/v2/officers')
    expect(ApiEndpoints.SECTOR).toBe('/api/v2/sector')
    expect(ApiEndpoints.PURPOSE).toBe('/api/v2/purpose')
    expect(ApiEndpoints.MENTIONS).toBe('/api/v2/mentions')
    expect(ApiEndpoints.FILES('file-1')).toBe('/api/v2/files/file-1')
  })

  it('does not nest officer/sector/purpose collections under /organizations', () => {
    const paths = catalogPaths().join('\n')
    expect(paths).not.toContain('/api/v2/organizations/officers')
    expect(paths).not.toContain('/api/v2/organizations/sectors')
    expect(paths).not.toContain('/api/v2/organizations/purposes')
  })

  it('builds adapter collection URLs from type codes', () => {
    expect(ApiEndpoints.RECORDS('document')).toBe('/api/v2/records/document')
    expect(ApiEndpoints.RECORDS('meeting_topic')).toBe('/api/v2/records/meeting_topic')
    expect(ApiEndpoints.ORGANIZATIONS('department')).toBe('/api/v2/organizations/department')
    expect(ApiEndpoints.RECORD_COMMENTS('document', 'abc')).toBe('/api/v2/records/document/abc/comments')
    expect(ApiEndpoints.RECORD_ATTACHMENTS('document', 'abc')).toBe('/api/v2/records/document/abc/attachments')
  })

  it('never exposes a /meetings HTTP family or hyphenated record collections', () => {
    const paths = catalogPaths().join('\n')
    expect(paths).not.toContain('/api/v2/meetings/')
    expect(paths).not.toContain('/records/incoming-documents')
    expect(paths).not.toContain('/records/outgoing-documents')
    expect(paths).not.toContain('/records/master-list-requests')
    expect(paths).not.toContain('/entities/')
  })
})

describe('unwrapApiData', () => {
  it('unwraps { data } envelopes and passes through raw payloads', () => {
    expect(unwrapApiData({ data: { id: '1' } })).toEqual({ id: '1' })
    expect(unwrapApiData({ id: '1' })).toEqual({ id: '1' })
  })
})

describe('permission prefixes', () => {
  it('maps meeting types under records.*, not meetings.*', () => {
    const prefixes = Object.fromEntries(
      ROLE_DOCUMENT_TYPES.map(row => [row.value, row.permissionPrefix]),
    )
    expect(prefixes.meeting_topic).toBe('records.meeting_topic')
    expect(prefixes.meeting_history).toBe('records.meeting_history')
    expect(prefixes.incoming_document).toBe('records.incoming_documents')
    expect(prefixes.department).toBe('organizations.departments')
    for (const row of ROLE_DOCUMENT_TYPES) {
      expect(row.permissionPrefix.startsWith('meetings.')).toBe(false)
    }
  })
})

describe('sameOriginApiUrl', () => {
  it('keeps relative /api paths when apiBase is empty (same-origin proxy)', () => {
    expect(sameOriginApiUrl('/api/v2/auth/me', '')).toBe('/api/v2/auth/me')
  })

  it('resolves against an explicit API origin of the same host', () => {
    expect(sameOriginApiUrl('/api/v2/auth/me', 'http://localhost:8000'))
      .toBe('http://localhost:8000/api/v2/auth/me')
  })
})

import { afterEach, describe, expect, it, vi } from 'vitest'
import { createEntityApi } from '../../app/composables/api/useEntityApi'
import { usePathModel } from '../../app/composables/common/usePathModel'
import { resolveRecordSurfaceByParam } from '../../app/utils/record/surfaces'
import {
  AUTH_USER_STORAGE_KEY,
  readStoredUser,
  writeStoredUser,
} from '../../app/utils/auth/session-user'
import {
  AUTH_SESSION_EVENT_KEY,
  publishAuthSessionEvent,
} from '../../app/utils/auth/session-sync'
import {
  clearPasswordResetSession,
  getPasswordResetSession,
  markPasswordResetVerified,
  startPasswordReset,
} from '../../app/utils/auth/password-reset'
import { defaultUserAvatarUrl, resolveUserAvatar } from '../../app/utils/auth/user-avatar'
import { serializePageLimit, paginationItemsPerPage } from '../../app/utils/pagination'
import { compactQuery } from '../../app/utils/api/query'
import { requestCacheKey } from '../../app/utils/api/request-cache'
import { csrfRequestHeaders } from '../../app/utils/security/csrf'
import {
  extensionsToUppyTypes,
  fileMatchesAllowedTypes,
  isSafeRasterImage,
} from '../../app/utils/security/files'
import { safeInternalPath, safeExternalUrl } from '../../app/utils/security/url'
import { splitCardSlots, resolveVisibleSlots, isTitleChromeSlot, catalogForEntity, blocksForEntity, isCardFooterSlot, defaultFooterAlign, resolveFooterAlign } from '../../app/utils/card-fields'
import {
  attributeDataTypeToFieldType,
  detailFieldKey,
  mapTypeAttributeToField,
  mapTypeAttributesToSections,
  pruneDetailsForType,
  stageOptionsFromType,
} from '../../app/utils/record-type-fields'
import { computeMeetingTiming, getImminentMinutesBefore, isJoinableMeeting, mergeMeetingTiming, sortMeetingsForBoard } from '../../app/utils/meeting/board'
import {
  MEETING_TOPICS_PATH,
  hydrateMeetingHistoryModel,
  isCompletedMeeting,
  meetingDetailOpenedFromTopics,
  meetingHistoryDetailPath,
} from '../../app/utils/meeting/detail-route'
import {
  consumeListStale,
  markListStale,
  resolveCreateReturnTo,
  returnsToListAfterCreate,
  shouldReturnToListAfterCreate,
} from '../../app/utils/workspace-list-stale'
import { toConfigCode } from '../../app/utils/config-code'
import { getFilterDateUi, getFilterSearchInputConfig, getFilterSearchUi, getFilterSelectUi, isFilterValueActive } from '../../app/utils/filter/select-ui'
import { normalizeFontSize, DEFAULT_FONT_SIZE } from '../../app/utils/preferences/font-size'
import {
  normalizePermissionActions,
  permissionRowsToFlatKeys,
  setPermissionAction,
} from '../../app/utils/role/permissions'
import {
  clearPendingTypeAttributeIds,
  pushPendingTypeAttributeId,
  readPendingTypeAttributeIds,
} from '../../app/utils/pending-type-attributes'
import { defaultRecordTypeFeatures, previewRecordNumber } from '../../app/types/docetra/configuration'
import type { RecordTypeAttribute } from '../../app/types/docetra/configuration'

function mockBrowserStorage() {
  const local = new Map<string, string>()
  const session = new Map<string, string>()
  const asStorage = (store: Map<string, string>): Storage => ({
    getItem: key => store.get(key) ?? null,
    setItem: (key, value) => { store.set(key, String(value)) },
    removeItem: key => { store.delete(key) },
    clear: () => store.clear(),
    key: index => [...store.keys()][index] ?? null,
    get length() { return store.size },
  }) as Storage
  Object.defineProperty(globalThis, 'localStorage', { value: asStorage(local), configurable: true })
  Object.defineProperty(globalThis, 'sessionStorage', { value: asStorage(session), configurable: true })
  Object.defineProperty(globalThis, 'window', { value: globalThis, configurable: true })
  return { local, session }
}

function assigned(partial: Partial<RecordTypeAttribute> & Pick<RecordTypeAttribute, 'attributeCode'>): RecordTypeAttribute {
  return {
    attributeId: partial.attributeId || 'attr-1',
    attributeLabel: partial.attributeLabel || partial.attributeCode,
    dataType: partial.dataType || 'short_text',
    required: partial.required ?? false,
    readOnly: partial.readOnly ?? false,
    visible: partial.visible ?? true,
    searchable: false,
    filterable: false,
    showInList: false,
    order: partial.order ?? 0,
    section: partial.section,
    ...partial,
  }
}

describe('auth store persistence', () => {
  it('round-trips the signed-in user snapshot', () => {
    mockBrowserStorage()
    writeStoredUser({ name: 'Ada', email: 'ada@example.com' })
    expect(readStoredUser()?.email).toBe('ada@example.com')
    writeStoredUser(null)
    expect(readStoredUser()).toBeNull()
    expect(localStorage.getItem(AUTH_USER_STORAGE_KEY)).toBeNull()
  })

  it('ignores malformed stored users', () => {
    mockBrowserStorage()
    localStorage.setItem(AUTH_USER_STORAGE_KEY, '{not-json')
    expect(readStoredUser()).toBeNull()
  })
})

describe('preferences store helpers', () => {
  it('normalizes font sizes used by the preferences store', () => {
    expect(normalizeFontSize('lg')).toBe('lg')
    expect(normalizeFontSize('huge')).toBe(DEFAULT_FONT_SIZE)
    expect(normalizeFontSize(undefined)).toBe('md')
  })
})

describe('password reset form session', () => {
  it('stores verify state for the reset-password form', () => {
    mockBrowserStorage()
    startPasswordReset('Ada@Example.com')
    expect(getPasswordResetSession()?.email).toBe('ada@example.com')
    expect(getPasswordResetSession()?.verified).toBe(false)
    markPasswordResetVerified('123456')
    expect(getPasswordResetSession()).toMatchObject({ verified: true, code: '123456' })
    clearPasswordResetSession()
    expect(getPasswordResetSession()).toBeNull()
  })
})

describe('session sync and avatars', () => {
  it('publishes login events for other tabs', () => {
    mockBrowserStorage()
    publishAuthSessionEvent('login')
    const raw = localStorage.getItem(AUTH_SESSION_EVENT_KEY)
    expect(raw).toBeTruthy()
    expect(JSON.parse(String(raw)).kind).toBe('login')
  })

  it('falls back to generated avatars', () => {
    expect(resolveUserAvatar({ name: 'Ada' })).toBe(defaultUserAvatarUrl('Ada'))
    expect(resolveUserAvatar({ name: 'Ada', avatar: '/me.png' })).toBe('/me.png')
    expect(defaultUserAvatarUrl('Ada')).toMatch(/^data:image\/svg\+xml/)
    expect(defaultUserAvatarUrl('Ada')).not.toContain('ui-avatars.com')
  })
})

describe('usePathModel composable', () => {
  it('reads and writes nested form paths', () => {
    const model = { value: { details: { title: 'A' } } }
    const { fieldValue, setFieldValue } = usePathModel(model)
    expect(fieldValue('details.title')).toBe('A')
    setFieldValue('details.title', 'B')
    expect(model.value.details.title).toBe('B')
  })
})

describe('record surface routing composable helper', () => {
  it('resolves types by code, slug, or route suffix', () => {
    const types = [{
      id: '1',
      code: 'incoming_document',
      name: 'Incoming',
      uiSurface: 'document',
      slug: 'incoming-documents',
      apiBase: '/api/v2/records/incoming_document',
      routeBase: '/records/incoming-documents',
    }]
    expect(resolveRecordSurfaceByParam(types, 'incoming_document')?.id).toBe('1')
    expect(resolveRecordSurfaceByParam(types, 'incoming-documents')?.id).toBe('1')
    expect(resolveRecordSurfaceByParam(types, '')).toBeNull()
  })

  it('keeps meeting topic and history as distinct live route params', () => {
    const types = [
      {
        id: 'topic',
        code: 'meeting_topic',
        name: 'Topics',
        uiSurface: 'meeting',
        slug: 'topics',
        apiBase: '/api/v2/records/meeting_topic',
        routeBase: '/meetings/topics',
      },
      {
        id: 'history',
        code: 'meeting_history',
        name: 'History',
        uiSurface: 'meeting',
        slug: 'history',
        apiBase: '/api/v2/records/meeting_history',
        routeBase: '/meetings/history',
      },
    ]
    expect(resolveRecordSurfaceByParam(types, 'topics')?.id).toBe('topic')
    expect(resolveRecordSurfaceByParam(types, 'history')?.id).toBe('history')
    expect(resolveRecordSurfaceByParam(types, 'topics')?.id).not.toBe(
      resolveRecordSurfaceByParam(types, 'history')?.id,
    )
  })
})

describe('organization type route helpers', () => {
  it('maps live orgType params to entity keys and canonical paths', async () => {
    const {
      organizationCanonicalPath,
      organizationEntityKeyFromParam,
    } = await import('../../app/utils/organization/org-type-route')
    expect(organizationEntityKeyFromParam('departments')).toBe('departments')
    expect(organizationEntityKeyFromParam('company')).toBe('companies')
    expect(organizationEntityKeyFromParam('unknown')).toBeNull()
    expect(organizationCanonicalPath('department')).toBe('/organizations/departments')
    expect(organizationCanonicalPath('company', 'abc')).toBe('/organizations/companies/abc')
    expect(organizationCanonicalPath('departments')).toBeNull()
  })
})

describe('entity API concurrency', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends If-Match and version on mutations', async () => {
    const calls: Array<{ method: string, url: string, body?: unknown, options?: unknown }> = []
    vi.stubGlobal('useApi', () => ({
      get: (url: string, options?: unknown) => {
        calls.push({ method: 'GET', url, options })
        return Promise.resolve({ data: {} })
      },
      post: (url: string, body?: unknown, options?: unknown) => {
        calls.push({ method: 'POST', url, body, options })
        return Promise.resolve({ data: {} })
      },
      patch: (url: string, body?: unknown, options?: unknown) => {
        calls.push({ method: 'PATCH', url, body, options })
        return Promise.resolve({ data: {} })
      },
      put: (url: string, body?: unknown, options?: unknown) => {
        calls.push({ method: 'PUT', url, body, options })
        return Promise.resolve({ data: {} })
      },
      delete: (url: string, options?: unknown) => {
        calls.push({ method: 'DELETE', url, options })
        return Promise.resolve({ data: {} })
      },
    }))
    const api = createEntityApi({ endpoint: '/api/v2/records/document' })
    await api.update('doc-1', { title: 'X', version: 4 })
    await api.list({ view: 'list' })
    await api.get('doc-1')
    await api.create({ title: 'N' })
    await api.archive('doc-1', { version: 4 })
    await api.restore?.('doc-1', { version: 4 })
    await api.delete('doc-1', { version: 4 })
    await api.deleteMany(['doc-1'], { 'doc-1': 4 })
    await api.purge?.('doc-1', { version: 4 })
    await api.transitionStage('doc-1', 'review', { version: 4 })
    await api.listByStage?.('review')
    await api.getGroupCounts?.('stage')
    await api.listComments?.('doc-1')
    await api.addComment?.('doc-1', 'hi')
    await api.updateComment?.('doc-1', 'c1', 'bye')
    await api.deleteComment?.('doc-1', 'c1')
    await api.getNeighbors?.('doc-1')
    await api.listActivity?.('doc-1')
    await api.listAttachments?.('doc-1')
    await api.replaceAttachments('doc-1', [], { version: 5 })
    expect(calls.find(call => call.method === 'PATCH' && (call.body as { title?: string })?.title === 'X')).toMatchObject({
      body: { title: 'X', version: 4 },
      options: { headers: { 'If-Match': '4' } },
    })
    expect(calls.find(call => call.url.endsWith('/archive'))).toMatchObject({
      method: 'POST',
      body: { version: 4 },
    })
    expect(calls.find(call => call.method === 'DELETE' && !String(call.url).includes('/purge'))).toMatchObject({
      options: { query: { version: 4 }, headers: { 'If-Match': '4' } },
    })
    expect(calls.find(call => String(call.url).endsWith('/bulk-delete'))).toMatchObject({
      body: { ids: ['doc-1'], versions: { 'doc-1': 4 } },
    })
    expect(calls.find(call => String(call.url).endsWith('/stage'))).toMatchObject({
      body: { stage: 'review', version: 4 },
    })
    expect(calls.find(call => String(call.url).endsWith('/attachments') && call.method === 'PUT')).toMatchObject({
      body: { files: [], version: 5 },
    })
  })
})

describe('forms and configuration helpers', () => {
  it('maps type attributes onto document form sections', () => {
    const field = mapTypeAttributeToField(assigned({
      attributeCode: 'letter_number',
      dataType: 'short_text',
      required: true,
    }))
    expect(field?.key).toBe(detailFieldKey('letter_number'))
    expect(attributeDataTypeToFieldType('datetime')).toBe('datetime')
    expect(mapTypeAttributesToSections([
      assigned({ attributeCode: 'letter_number', section: 'Identity' }),
    ])[0]?.title).toBe('Identity')
    expect(pruneDetailsForType({ letter_number: '1', gone: 'x' }, [
      assigned({ attributeCode: 'letter_number' }),
    ])).toEqual({ letter_number: '1' })
    expect(stageOptionsFromType({
      features: { ...defaultRecordTypeFeatures(), enableWorkflow: true },
      stages: [
        { code: 'draft', name: 'Draft', order: 1 },
        { code: 'done', name: 'Done', order: 0 },
      ],
    } as never)).toEqual([
      { label: 'Done', value: 'done', labelKey: 'docetra.stages.done' },
      { label: 'Draft', value: 'draft', labelKey: 'docetra.stages.draft' },
    ])
  })

  it('normalizes role permission form rows', () => {
    expect(normalizePermissionActions(['write', 'email'])).toEqual(['view', 'edit', 'comment'])
    const row = setPermissionAction({
      id: 'perm_document',
      documentType: 'document',
      actions: ['view'],
      onlyIfCreator: false,
      level: 0,
    }, 'edit', true)
    expect(row.actions).toContain('edit')
    expect(permissionRowsToFlatKeys([row]).some(key => key === 'records.documents.edit')).toBe(true)
  })

  it('builds config codes and numbering previews', () => {
    expect(toConfigCode('Letter Number')).toBe('letter_number')
    expect(previewRecordNumber({ prefix: 'DOC', includeYear: false, sequenceLength: 3, resetYearly: true }, 7)).toBe('DOC-007')
  })
})

describe('major component helpers', () => {
  it('splits board card slots for title, body, and footer', () => {
    expect(isTitleChromeSlot('sortOrder')).toBe(true)
    expect(isTitleChromeSlot('status')).toBe(false)
    const split = splitCardSlots('meetingHistory', ['sortOrder', 'letterNumber', 'location'])
    expect(split.titleChrome).toEqual(['sortOrder'])
    expect(split.body).toContain('letterNumber')
    expect(split.footer).toContain('location')
    expect(resolveVisibleSlots('meetingTopics', ['status', 'unknown'])).toEqual([])
    expect(catalogForEntity('meetingTopics')).toContain('tags')
    expect(catalogForEntity('documents')).not.toContain('status')
    expect(catalogForEntity('documents')).not.toContain('stage')
    expect(catalogForEntity('meetingHistory')).not.toContain('status')
    expect(catalogForEntity('meetingHistory')).not.toContain('stage')
    expect(blocksForEntity('documents').length).toBeGreaterThan(0)
    expect(isCardFooterSlot('documents', 'recordTime')).toBe(true)
    expect(defaultFooterAlign('location')).toBe('right')
    expect(resolveFooterAlign('documents', 'location', { documents: { location: 'left' } })).toBe('left')
  })

  it('times and sorts meeting board cards', () => {
    const now = new Date('2026-08-23T10:00:00Z')
    const timing = computeMeetingTiming('2026-08-23T10:10:00Z', 30, now, 15)
    expect(timing.imminent).toBe(true)
    expect(getImminentMinutesBefore()).toBe(15)
    expect(mergeMeetingTiming({ meetingDate: '2026-08-23T10:10:00Z', durationMinutes: 30 }).minutesUntilStart).toBeTypeOf('number')
    expect(isJoinableMeeting('online', 'https://meet.example/abc')).toBe(true)
    expect(isJoinableMeeting('online', 'javascript:alert(1)')).toBe(false)
    const sorted = sortMeetingsForBoard([
      { meetingDate: '2026-08-23T12:00:00Z', imminent: false, sortOrder: 2 },
      { meetingDate: '2026-08-23T11:00:00Z', imminent: true, sortOrder: 9 },
    ], { topicScoped: true })
    expect(sorted[0]?.imminent).toBe(true)
  })

  it('opens meeting card detail from the topic board, not as a history-list entry', () => {
    expect(meetingHistoryDetailPath('abc-1', MEETING_TOPICS_PATH)).toBe(
      '/meetings/history/abc-1?returnTo=%2Fmeetings%2Ftopics',
    )
    expect(meetingDetailOpenedFromTopics('/meetings/topics')).toBe(true)
    expect(meetingDetailOpenedFromTopics('/meetings/history')).toBe(false)
    expect(isCompletedMeeting('completed')).toBe(true)
    expect(isCompletedMeeting('intake')).toBe(false)
    const hydrated = hydrateMeetingHistoryModel({
      title: 'Meeting 11bd304b',
      recordTime: '2026-08-28T10:54:00Z',
      parentId: 'topic-1',
      letterNumber: 'LTR-9',
    })
    expect(hydrated.meetingDate).toBe('2026-08-28T10:54:00Z')
    expect(hydrated.topicId).toBe('topic-1')
    expect(hydrated.letterNumber).toBe('LTR-9')
    expect((hydrated.details as Record<string, unknown>).topicId).toBe('topic-1')
  })
})

describe('workspace and filter composable helpers', () => {
  it('tracks stale lists and safe create return paths', () => {
    markListStale('documents')
    expect(consumeListStale('documents')).toBe(true)
    expect(consumeListStale('documents')).toBe(false)
    expect(returnsToListAfterCreate('documents')).toBe(true)
    expect(returnsToListAfterCreate('users')).toBe(true)
    expect(returnsToListAfterCreate('recordTypes')).toBe(true)
    expect(shouldReturnToListAfterCreate('users', '/user-management/users')).toBe(true)
    expect(shouldReturnToListAfterCreate('recordTypes', '/configuration/record-types')).toBe(true)
    expect(shouldReturnToListAfterCreate('recordTypes', 'https://evil.example')).toBe(true)
    expect(resolveCreateReturnTo('/records/documents', '/')).toBe('/records/documents')
    expect(resolveCreateReturnTo('https://evil.example', '/fallback')).toBe('/fallback')
    expect(resolveCreateReturnTo(undefined, '/officers')).toBe('/officers')
  })

  it('detects active filter values and compact query params', () => {
    expect(isFilterValueActive(['a'])).toBe(true)
    expect(isFilterValueActive('  ')).toBe(false)
    expect(getFilterSelectUi(true).base).toContain('ring-1')
    expect(getFilterSearchUi(false).base).toContain('rounded-md')
    expect(getFilterDateUi(true, { isDateTime: true, isRange: true, fitContent: true }).base).toContain('ring-1')
    expect(getFilterSearchInputConfig(key => key).placeholder).toBe('components.filterSearch')
    expect(compactQuery({ q: 'x', empty: '', none: null })).toEqual({ q: 'x' })
    expect(serializePageLimit(20)).toBeUndefined()
    expect(serializePageLimit(50)).toBe('50')
    expect(paginationItemsPerPage(0)).toBe(1)
  })

  it('builds one stable identity for equivalent shared GETs', () => {
    expect(requestCacheKey('GET', '/api/v2/options', { status: 'active', limit: 50 }))
      .toBe(requestCacheKey('GET', '/api/v2/options', { limit: 50, status: 'active' }))
    expect(requestCacheKey('GET', '/api/v2/options', { q: 'a' }))
      .not.toBe(requestCacheKey('GET', '/api/v2/options', { q: 'b' }))
    expect(requestCacheKey('GET', '/ignored', { q: 'a' }, 'record-surfaces')).toBe('record-surfaces')
  })
})

describe('upload and CSRF helpers', () => {
  it('validates raster images and allowed upload types', () => {
    expect(isSafeRasterImage({ type: 'image/png', size: 100 }, 1)).toBe(true)
    expect(isSafeRasterImage({ type: 'application/pdf', size: 100 }, 1)).toBe(false)
    expect(fileMatchesAllowedTypes({ name: 'a.docx', type: '' }, ['.docx'])).toBe(true)
    expect(extensionsToUppyTypes(['PDF', '.png'])).toEqual(['.pdf', '.png'])
    expect(extensionsToUppyTypes([])[0]).toBe('application/pdf')
  })

  it('attaches CSRF headers from the double-submit cookie', () => {
    Object.defineProperty(globalThis, 'document', {
      value: { cookie: 'XSRF-TOKEN=abc%2Fdef' },
      configurable: true,
    })
    expect(csrfRequestHeaders('POST', 'XSRF-TOKEN', 'X-CSRF-Token')).toEqual({
      'X-CSRF-Token': 'abc/def',
    })
    expect(csrfRequestHeaders('GET', 'XSRF-TOKEN', 'X-CSRF-Token')).toEqual({})
  })

  it('rejects control characters in in-app paths', () => {
    expect(safeInternalPath('/records/documents')).toBe('/records/documents')
    expect(safeInternalPath('/\u0000evil')).toBeNull()
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
  })
})

describe('pending type-attribute form handoff', () => {
  it('queues ids created from the type editor', () => {
    mockBrowserStorage()
    pushPendingTypeAttributeId('a1')
    pushPendingTypeAttributeId('a1')
    expect(readPendingTypeAttributeIds()).toEqual(['a1'])
    clearPendingTypeAttributeIds()
    expect(readPendingTypeAttributeIds()).toEqual([])
  })
})

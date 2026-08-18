import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import type { ActivityEvent, AttachmentMeta, DocumentTabSchema, EntityComment } from '~/types/docetra/common'
import type { AppRolePermissionRow } from '~/types/docetra/entities'
import { normalizePermissionRows, permissionRowsToFlatKeys } from '~/utils/role/permissions'
import { getByPath, setByPath } from '~/utils/object-path'
import { loadReferenceOptions } from '~/adapters/reference-options'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import {
  markListStale,
  resolveCreateReturnTo,
  returnsToListAfterCreate,
} from '~/utils/workspace-list-stale'

export function useDocumentPage(config: EntityConfig, idParam?: string) {
  const route = useRoute()
  const router = useRouter()
  const { t, te } = useI18n()
  const toast = useToast()
  const { confirm } = useConfirm()
  const adapter = getEntityAdapter(config.key)

  const id = computed(() => idParam || String(route.params.id || ''))
  const isCreate = computed(() => !id.value || id.value === 'new' || route.path.endsWith('/new'))

  const model = ref<Record<string, unknown>>({})
  const dirty = ref(false)
  const trackingChanges = ref(false)
  const pending = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const notFound = ref(false)
  const activeTab = ref(config.tabs[0]?.id || 'details')
  const comments = ref<EntityComment[]>([])
  const activity = ref<ActivityEvent[]>([])
  const attachments = ref<AttachmentMeta[]>([])
  const feedPage = ref(1)
  const commentsTotal = ref(0)
  const activityTotal = ref(0)
  const loadingMoreFeed = ref(false)
  const commentBody = ref('')
  const submittingComment = ref(false)
  const updatingCommentId = ref<string | null>(null)
  const deletingCommentId = ref<string | null>(null)
  const auth = useAuthStore()
  const previousRecordId = ref<string | null>(null)
  const nextRecordId = ref<string | null>(null)
  const loadingRecordNavigation = ref(false)
  const recordNavigationDirection = ref<'previous' | 'next' | null>(null)
  const isFavorite = ref(false)
  const togglingFavorite = ref(false)
  let neighborRequestToken = 0
  let favoriteRequestToken = 0
  let loadRequestToken = 0
  let approvedRecordNavigation = false

  const hasMoreFeed = computed(() =>
    comments.value.length < commentsTotal.value || activity.value.length < activityTotal.value,
  )

  const title = computed(() => {
    if (isCreate.value) {
      if (config.createLabelKey) return t(config.createLabelKey)
      return t('docetra.document.new', { entity: t(config.titleKey) })
    }
    const value = model.value[config.titleField]
    return value ? String(value) : t(config.titleKey)
  })

  function fieldValue(key: string) {
    return getByPath(model.value, key)
  }

  function setFieldValue(key: string, value: unknown) {
    const next = { ...model.value }
    setByPath(next, key, value)
    model.value = next
    if (trackingChanges.value) dirty.value = true
  }

  async function loadRecordNeighbors() {
    const token = ++neighborRequestToken
    const currentId = id.value
    previousRecordId.value = null
    nextRecordId.value = null
    if (isCreate.value || !currentId || !adapter.getNeighbors) return

    loadingRecordNavigation.value = true
    try {
      const response = await adapter.getNeighbors(currentId, { sort: '-updatedAt' })
      if (token !== neighborRequestToken || currentId !== id.value) return
      previousRecordId.value = response.data.previousId
      nextRecordId.value = response.data.nextId
    }
    catch {
      previousRecordId.value = null
      nextRecordId.value = null
    }
    finally {
      if (token === neighborRequestToken) loadingRecordNavigation.value = false
    }
  }

  async function loadFavorite() {
    const token = ++favoriteRequestToken
    const currentId = id.value
    isFavorite.value = false
    togglingFavorite.value = false
    if (isCreate.value || !currentId || !adapter.getFavorite) return

    try {
      const response = await adapter.getFavorite(
        currentId,
        String(auth.user?.id || auth.user?.email || 'current'),
      )
      if (token !== favoriteRequestToken || currentId !== id.value) return
      isFavorite.value = response.data.isFavorite
    }
    catch {
      isFavorite.value = false
    }
  }

  async function toggleFavorite() {
    if (isCreate.value || !adapter.setFavorite || togglingFavorite.value) return
    const currentId = id.value
    const previous = isFavorite.value
    isFavorite.value = !previous
    togglingFavorite.value = true
    try {
      const response = await adapter.setFavorite(
        currentId,
        isFavorite.value,
        String(auth.user?.id || auth.user?.email || 'current'),
      )
      if (currentId !== id.value) return
      isFavorite.value = response.data.isFavorite
    }
    catch (e: any) {
      if (currentId === id.value) {
        isFavorite.value = previous
        toast.add({ title: e?.message || t('docetra.document.favoriteUpdateFailed'), color: 'error' })
      }
    }
    finally {
      if (currentId === id.value) togglingFavorite.value = false
    }
  }

  async function load() {
    const token = ++loadRequestToken
    const requestedId = id.value
    // A create page only initializes a local draft; it does not load a record.
    // Keep its form interactive while optional Record Type fields resolve.
    pending.value = !isCreate.value
    trackingChanges.value = false
    error.value = null
    notFound.value = false
    try {
      if (isCreate.value) {
        const recordKinds: Partial<Record<EntityConfig['key'], string>> = {
          incomingDocuments: 'incoming',
          outgoingDocuments: 'outgoing',
          documents: 'document',
          masterListRequests: 'master_list_request',
        }
        const recordTypeNames: Partial<Record<EntityConfig['key'], string>> = {
          incomingDocuments: 'Incoming Document',
          outgoingDocuments: 'Outgoing Document',
          documents: 'Document',
          masterListRequests: 'Master List Request',
        }
        const recordKind = recordKinds[config.key]
        const now = new Date().toISOString()
        model.value = {
          status: 'active',
          stage: config.stages?.[0]?.code || undefined,
          details: {},
          tags: [],
          ...(['departments', 'companies', 'companyPurposes', 'companySectors', 'officers'].includes(config.key) ? { status: 'active', isActive: true } : {}),
          ...(recordKind
            ? {
                recordKind,
                recordTypeName: recordTypeNames[config.key],
                recordTime: now.slice(0, 10),
                attachmentCount: 0,
                commentCount: 0,
              }
            : {}),
          ...(config.key === 'incomingDocuments' ? { receivedDate: now.slice(0, 10), involvedOfficers: [], externalUnits: [] } : {}),
          ...(config.key === 'outgoingDocuments' ? { sentDate: now.slice(0, 10), involvedOfficers: [], externalUnits: [] } : {}),
          ...(config.key === 'documents' ? { documentDate: now.slice(0, 10), involvedOfficers: [], externalUnits: [] } : {}),
          ...(config.key === 'masterListRequests' ? { letterDate: now.slice(0, 10) } : {}),
          ...(config.key === 'meetingTopics'
            ? {
                childMeetingCount: 0,
                childMeetings: [],
                recordTime: now,
                attachmentCount: 0,
                commentCount: 0,
              }
            : {}),
          ...(config.key === 'roles' ? { permissionRows: [] as AppRolePermissionRow[] } : {}),
          ...(config.key === 'meetingHistory'
            ? {
                meetingMode: 'in_person',
                participants: [],
                internalUnits: [],
                externalUnits: [],
                attendeesCount: 0,
                attachmentCount: 0,
                ...(typeof route.query.topicId === 'string' && route.query.topicId
                  ? { topicId: route.query.topicId }
                  : {}),
              }
            : {}),
        }
        dirty.value = false
        comments.value = []
        activity.value = []
        attachments.value = []
        void loadRecordNeighbors()
        void loadFavorite()
        return
      }
      const res = await adapter.get(requestedId)
      if (token !== loadRequestToken || requestedId !== id.value) return
      model.value = {
        details: {},
        ...(res.data as Record<string, unknown>),
      }
      if (!model.value.details || typeof model.value.details !== 'object') {
        model.value.details = {}
      }
      if (['departments', 'companies', 'companyPurposes', 'companySectors', 'officers'].includes(config.key) && typeof model.value.isActive !== 'boolean') {
        model.value.isActive = model.value.status !== 'disabled'
      }
      if (config.key === 'officers' && typeof model.value.authenticationEnabled !== 'boolean') {
        model.value.authenticationEnabled = Boolean(model.value.userId)
      }
      if (config.key === 'roles') {
        model.value.permissionRows = normalizePermissionRows(
          Array.isArray(model.value.permissionRows)
            ? model.value.permissionRows as AppRolePermissionRow[]
            : [],
        )
      }
      dirty.value = false
      const related = await Promise.allSettled([
        adapter.listComments?.(requestedId, { page: 1, limit: 20 }),
        adapter.listActivity?.(requestedId, { page: 1, limit: 20 }),
        adapter.listAttachments?.(requestedId, { page: 1, limit: 50 }),
      ])
      if (token !== loadRequestToken || requestedId !== id.value) return
      const c = related[0].status === 'fulfilled' ? related[0].value : undefined
      const a = related[1].status === 'fulfilled' ? related[1].value : undefined
      const f = related[2].status === 'fulfilled' ? related[2].value : undefined
      comments.value = (c?.data || []) as EntityComment[]
      activity.value = (a?.data || []) as ActivityEvent[]
      attachments.value = (f?.data || []) as AttachmentMeta[]
      commentsTotal.value = c?.meta?.total || comments.value.length
      activityTotal.value = a?.meta?.total || activity.value.length
      feedPage.value = 1
      void loadRecordNeighbors()
      void loadFavorite()
    }
    catch (e: any) {
      if (token !== loadRequestToken) return
      if (e?.statusCode === 404) notFound.value = true
      error.value = e?.message || 'Failed to load document'
    }
    finally {
      if (token === loadRequestToken) {
        pending.value = false
        trackingChanges.value = true
      }
    }
  }

  function prepareModelForSave() {
    const payload = { ...model.value }
    const isRecordDocument = [
      'incomingDocuments',
      'outgoingDocuments',
      'documents',
      'masterListRequests',
    ].includes(config.key)
    if (config.key === 'meetingTopics' || config.key === 'meetingHistory' || isRecordDocument) {
      const tags = Array.isArray(payload.tags)
        ? payload.tags.map(String).map(tag => tag.trim()).filter(Boolean)
        : []
      payload.tags = tags
      payload.recordTag = tags.join(', ')
    }
    if (config.key === 'meetingTopics') {
      if (typeof payload.childMeetingCount !== 'number') payload.childMeetingCount = 0
      if (!Array.isArray(payload.childMeetings)) payload.childMeetings = []
    }
    if (isRecordDocument) {
      for (const key of ['involvedOfficers', 'externalUnits', 'officeInCharge']) {
        payload[key] = Array.isArray(payload[key])
          ? payload[key].map(String).map(value => value.trim()).filter(Boolean)
          : []
      }
      const recordTime = payload.recordTime ? String(payload.recordTime).slice(0, 10) : undefined
      if (config.key === 'incomingDocuments' && !payload.receivedDate && recordTime) {
        payload.receivedDate = recordTime
      }
      if (config.key === 'outgoingDocuments' && !payload.sentDate && recordTime) {
        payload.sentDate = recordTime
      }
      if (config.key === 'documents' && !payload.documentDate && recordTime) {
        payload.documentDate = recordTime
      }
      if (typeof payload.attachmentCount !== 'number') payload.attachmentCount = attachments.value.length
      if (typeof payload.commentCount !== 'number') payload.commentCount = 0
    }
    if (['departments', 'companies', 'companyPurposes', 'companySectors', 'officers'].includes(config.key)) {
      payload.isActive = payload.isActive !== false
      payload.status = payload.isActive ? 'active' : 'disabled'
    }
    if (config.key === 'meetingHistory') {
      for (const key of ['participants', 'internalUnits', 'externalUnits']) {
        payload[key] = Array.isArray(payload[key])
          ? payload[key].map(String).map(value => value.trim()).filter(Boolean)
          : []
      }
      payload.attendeesCount = (payload.participants as string[]).length
      if (payload.meetingDate && !payload.recordTime) payload.recordTime = payload.meetingDate
    }
    if (config.key === 'roles') {
      const rows = normalizePermissionRows((Array.isArray(payload.permissionRows)
        ? payload.permissionRows
        : []) as AppRolePermissionRow[], false)
      payload.permissionRows = rows
      payload.permissions = permissionRowsToFlatKeys(rows)
      payload.permissionCount = rows.reduce((sum, row) => sum + row.actions.length, 0)
      payload.permissionSchemaVersion = 1
    }
    return payload
  }

  function validateRequiredFields(documentTabs: DocumentTabSchema[] = config.tabs) {
    const missing = documentTabs.flatMap(tab =>
      tab.sections.flatMap(section =>
        section.fields
          .filter(field => field.required && !field.readOnly)
          .filter((field) => {
            const value = getByPath(model.value, field.key)
            if (value == null) return true
            if (typeof value === 'string') return !value.trim()
            if (Array.isArray(value)) return value.length === 0
            return false
          })
          .map(field => ({ field, tabId: tab.id })),
      ),
    )

    if (!missing.length) return true
    activeTab.value = missing[0]!.tabId
    const labels = missing.map(({ field }) => {
      if (field.label) return field.label
      return te(field.labelKey) ? t(field.labelKey) : field.labelKey
    })
    toast.add({
      title: t('docetra.document.requiredFieldsMissing'),
      description: labels.join(', '),
      color: 'error',
    })
    return false
  }

  async function save(documentTabs: DocumentTabSchema[] = config.tabs) {
    if (config.readOnly) return
    if (!validateRequiredFields(documentTabs)) return
    if (config.key === 'meetingHistory') {
      const mode = String(model.value.meetingMode || '')
      const url = String(model.value.meetingUrl || '').trim()
      if ((mode === 'online' || mode === 'hybrid') && !url) {
        toast.add({ title: t('docetra.meetingBoard.meetingUrlRequired'), color: 'error' })
        return
      }
    }
    if (config.key === 'departments' && !isCreate.value && model.value.parentId === id.value) {
      toast.add({ title: t('docetra.department.cannotBeOwnAncestor'), color: 'error' })
      return
    }
    if (config.key === 'companySectors' && !isCreate.value && model.value.parentId === id.value) {
      toast.add({ title: t('docetra.companySector.cannotBeOwnParent'), color: 'error' })
      return
    }
    saving.value = true
    try {
      const payload = prepareModelForSave()
      const useMockData = useRuntimeConfig().public.useMockData !== false
      if (config.key === 'meetingHistory' && payload.topicId && !payload.topicTitle) {
        try {
          const topicRes = await getEntityAdapter('meetingTopics').get(String(payload.topicId))
          const title = (topicRes.data as { title?: string } | undefined)?.title
          if (title) payload.topicTitle = title
        }
        catch {
          // Topic title is optional for save; board can still show the meeting.
        }
      }
      if (config.key === 'departments' && useMockData) {
        const parentId = String(payload.parentId || '')
        const exclude = !isCreate.value && id.value
          ? `&excludeId=${encodeURIComponent(id.value)}`
          : ''
        const departmentOptions = await loadReferenceOptions(
          `${ApiEndpoints.DEPARTMENTS}/options?hierarchy=true${exclude}`,
        )
        const parentOption = departmentOptions.find(option => option.value === parentId)
        if (parentId && !parentOption) {
          toast.add({ title: t('docetra.department.cannotBeDescendant'), color: 'error' })
          return
        }
        payload.parentName = String(parentOption?.meta?.name || parentOption?.label || '')
          .replace(/^(?:(?:—|-)\s*)+/, '')
      }
      if (config.key === 'companies' && useMockData) {
        const [sectorOptions, purposeOptions] = await Promise.all([
          loadReferenceOptions(`${ApiEndpoints.COMPANY_SECTORS}/options`),
          loadReferenceOptions(`${ApiEndpoints.COMPANY_PURPOSES}/options`),
        ])
        payload.sectorName = sectorOptions.find(option => option.value === String(payload.sectorId || ''))?.label || ''
        payload.purposeName = purposeOptions.find(option => option.value === String(payload.purposeId || ''))?.label || ''
      }
      if (config.key === 'companySectors' && useMockData) {
        const sectorOptions = await loadReferenceOptions(`${ApiEndpoints.COMPANY_SECTORS}/options`)
        payload.parentName = sectorOptions.find(option => option.value === String(payload.parentId || ''))?.label || ''
      }
      if (config.key === 'officers' && useMockData) {
        const [organizationOptions, roleOptions] = await Promise.all([
          loadReferenceOptions(`${ApiEndpoints.DEPARTMENTS}/options`),
          loadReferenceOptions(`${ApiEndpoints.ROLES}/options`),
        ])
        payload.organizationName = organizationOptions.find(option => option.value === String(payload.organizationId || ''))?.label || ''
        payload.roleName = roleOptions.find(option => option.value === String(payload.roleId || ''))?.label || ''
        payload.departmentId = payload.organizationId
        payload.departmentName = payload.organizationName
        if (typeof payload.authenticationEnabled !== 'boolean') {
          payload.authenticationEnabled = Boolean(payload.userId)
        }
      }
      else if (config.key === 'officers' && typeof payload.authenticationEnabled !== 'boolean') {
        payload.authenticationEnabled = Boolean(payload.userId)
      }
      if (isCreate.value) {
        const res = await adapter.create(payload as any)
        const created = res.data as { id: string }
        toast.add({ title: t('docetra.document.created'), color: 'success' })
        // Board/list creates: return to the list instead of remounting the full
        // detail document (get + comments + activity + attachments + schema).
        if (returnsToListAfterCreate(config.key)) {
          markListStale(config.key)
          if (config.key === 'meetingHistory' || config.key === 'meetingTopics') {
            markListStale('meetingTopics', 'meetingHistory')
          }
          await router.replace(resolveCreateReturnTo(route.query.returnTo, config.routeBase))
          return
        }
        await router.replace(`${config.routeBase}/${created.id}`)
        return
      }
      const res = await adapter.update(id.value, payload as any)
      model.value = { ...(res.data as Record<string, unknown>) }
      dirty.value = false
      if (adapter.replaceAttachments) {
        await adapter.replaceAttachments(id.value, attachments.value)
        const { indexFileForSearch } = await import('~/utils/search/index-hooks')
        const title = String(model.value[config.titleField] || '')
        for (const file of attachments.value) {
          indexFileForSearch({
            entityId: id.value,
            indexId: `idx:att:${config.key}:${id.value}:${file.id}`,
            fileName: file.name,
            mimeType: file.mimeType,
            url: `${config.routeBase}/${id.value}`,
            permission: config.permission,
            contextTitle: title,
            entityType: 'attachment',
          })
        }
      }
      toast.add({ title: t('docetra.document.saved'), color: 'success' })
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.document.saveFailed'), color: 'error' })
    }
    finally {
      saving.value = false
    }
  }

  async function loadMoreFeed() {
    if (!hasMoreFeed.value || loadingMoreFeed.value || isCreate.value) return
    const currentId = id.value
    const nextPage = feedPage.value + 1
    loadingMoreFeed.value = true
    try {
      const related = await Promise.allSettled([
        comments.value.length < commentsTotal.value
          ? adapter.listComments?.(currentId, { page: nextPage, limit: 20 })
          : undefined,
        activity.value.length < activityTotal.value
          ? adapter.listActivity?.(currentId, { page: nextPage, limit: 20 })
          : undefined,
      ])
      if (currentId !== id.value) return
      const commentsResponse = related[0].status === 'fulfilled' ? related[0].value : undefined
      const activityResponse = related[1].status === 'fulfilled' ? related[1].value : undefined
      const commentIds = new Set(comments.value.map(item => item.id))
      const activityIds = new Set(activity.value.map(item => item.id))
      comments.value.push(...(commentsResponse?.data || []).filter(item => !commentIds.has(item.id)))
      activity.value.push(...(activityResponse?.data || []).filter(item => !activityIds.has(item.id)))
      feedPage.value = nextPage
    }
    finally { loadingMoreFeed.value = false }
  }

  async function submitComment() {
    if (!commentBody.value.trim() || !adapter.addComment || isCreate.value) return
    const currentId = id.value
    submittingComment.value = true
    try {
      const res = await adapter.addComment(currentId, commentBody.value.trim(), {
        id: String(auth.user?.id || auth.user?.email || 'current'),
        name: auth.user?.name || 'You',
        email: auth.user?.email,
      })
      if (currentId !== id.value) return
      comments.value = [res.data as EntityComment, ...comments.value]
      activity.value = [{
        id: `act-comment-${(res.data as EntityComment).id}`,
        entityType: (res.data as EntityComment).entityType,
        entityId: (res.data as EntityComment).entityId,
        action: 'commented',
        actor: (res.data as EntityComment).author,
        summary: `${(res.data as EntityComment).author.name} commented`,
        occurredAt: (res.data as EntityComment).createdAt,
      }, ...activity.value]
      commentBody.value = ''
      toast.add({ title: t('docetra.document.commentAdded'), color: 'success' })
    }
    catch (e: any) {
      if (currentId === id.value) toast.add({ title: e?.message || 'Failed', color: 'error' })
    }
    finally {
      submittingComment.value = false
    }
  }

  async function updateComment(commentId: string, body: string) {
    const trimmed = body.trim()
    if (!trimmed || !adapter.updateComment || updatingCommentId.value) return
    const currentId = id.value
    updatingCommentId.value = commentId
    try {
      const res = await adapter.updateComment(currentId, commentId, trimmed)
      if (currentId !== id.value) return
      const updated = res.data as EntityComment
      comments.value = comments.value.map(comment => comment.id === commentId ? updated : comment)
      toast.add({ title: t('docetra.document.commentUpdated'), color: 'success' })
    }
    catch (e: any) {
      if (currentId === id.value) {
        toast.add({ title: e?.message || t('docetra.document.commentUpdateFailed'), color: 'error' })
      }
    }
    finally {
      updatingCommentId.value = null
    }
  }

  async function deleteComment(commentId: string) {
    if (!adapter.deleteComment || deletingCommentId.value) return
    const ok = await confirm({
      kind: 'delete',
      titleKey: 'docetra.comments.deleteTitle',
      descriptionKey: 'docetra.comments.deleteDescription',
      confirmLabelKey: 'actions.delete',
    })
    if (!ok) return

    const currentId = id.value
    deletingCommentId.value = commentId
    try {
      await adapter.deleteComment(currentId, commentId)
      if (currentId !== id.value) return
      comments.value = comments.value.filter(comment => comment.id !== commentId)
      activity.value = activity.value.filter(event => event.id !== `act-comment-${commentId}`)
      toast.add({ title: t('docetra.document.commentDeleted'), color: 'success' })
    }
    catch (e: any) {
      if (currentId === id.value) {
        toast.add({ title: e?.message || t('docetra.document.commentDeleteFailed'), color: 'error' })
      }
    }
    finally {
      deletingCommentId.value = null
    }
  }

  async function confirmLeave() {
    if (!dirty.value) return true
    return confirm({ kind: 'unsaved' })
  }

  async function navigateRecord(direction: 'previous' | 'next') {
    const targetId = direction === 'previous' ? previousRecordId.value : nextRecordId.value
    if (!targetId || recordNavigationDirection.value) return
    if (!await confirmLeave()) return

    recordNavigationDirection.value = direction
    approvedRecordNavigation = true
    try {
      await router.push(`${config.routeBase}/${targetId}`)
    }
    finally {
      approvedRecordNavigation = false
      recordNavigationDirection.value = null
    }
  }

  onBeforeRouteLeave(async () => approvedRecordNavigation || confirmLeave())

  if (import.meta.client) {
    useEventListener(window, 'beforeunload', (event) => {
      if (!dirty.value) return
      event.preventDefault()
      event.returnValue = ''
    })
  }

  watch(id, (currentId, previousId) => {
    if (previousId !== undefined && currentId !== previousId) commentBody.value = ''
    load()
  }, { immediate: true })

  return {
    isCreate,
    model,
    pending,
    saving,
    error,
    notFound,
    dirty,
    title,
    activeTab,
    comments,
    activity,
    attachments,
    hasMoreFeed,
    loadingMoreFeed,
    commentBody,
    submittingComment,
    updatingCommentId,
    deletingCommentId,
    previousRecordId,
    nextRecordId,
    loadingRecordNavigation,
    recordNavigationDirection,
    isFavorite,
    togglingFavorite,
    fieldValue,
    setFieldValue,
    load,
    save,
    submitComment,
    updateComment,
    deleteComment,
    loadMoreFeed,
    navigatePreviousRecord: () => navigateRecord('previous'),
    navigateNextRecord: () => navigateRecord('next'),
    toggleFavorite,
    confirmLeave,
  }
}

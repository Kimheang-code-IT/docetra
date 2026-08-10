import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import { useConfirm } from '~/composables/common/useConfirm'
import type { ActivityEvent, AttachmentMeta, EntityComment } from '~/types/docetra/common'
import type { AppRolePermissionRow } from '~/types/docetra/entities'
import { permissionRowsToFlatKeys } from '~/utils/role/permissions'
import { getByPath, setByPath } from '~/utils/object-path'
import { loadReferenceOptions } from '~/adapters/reference-options'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

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
  const initialSnapshot = ref('')
  const pending = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)
  const notFound = ref(false)
  const activeTab = ref(config.tabs[0]?.id || 'details')
  const comments = ref<EntityComment[]>([])
  const activity = ref<ActivityEvent[]>([])
  const attachments = ref<AttachmentMeta[]>([])
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

  const dirty = computed(() => JSON.stringify(model.value) !== initialSnapshot.value)

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
    pending.value = true
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
        const recordKind = recordKinds[config.key]
        model.value = {
          status: 'draft',
          stage: config.stages?.[0]?.code || undefined,
          details: {},
          ...(['departments', 'companies', 'companyPurposes', 'companySectors', 'officers'].includes(config.key) ? { status: 'active', isActive: true } : {}),
          ...(recordKind ? { recordKind } : {}),
          ...(recordKind && recordKind !== 'master_list_request' ? { recordFlowCode: 'normal' } : {}),
          ...(config.key === 'roles' ? { permissionRows: [] as AppRolePermissionRow[] } : {}),
        }
        initialSnapshot.value = JSON.stringify(model.value)
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
      initialSnapshot.value = JSON.stringify(model.value)
      const [c, a, f] = await Promise.all([
        adapter.listComments?.(requestedId, { page: 1, limit: 20 }),
        adapter.listActivity?.(requestedId, { page: 1, limit: 20 }),
        adapter.listAttachments?.(requestedId),
      ])
      if (token !== loadRequestToken || requestedId !== id.value) return
      comments.value = (c?.data || []) as EntityComment[]
      activity.value = (a?.data || []) as ActivityEvent[]
      attachments.value = (f?.data || []) as AttachmentMeta[]
      void loadRecordNeighbors()
      void loadFavorite()
    }
    catch (e: any) {
      if (token !== loadRequestToken) return
      if (e?.statusCode === 404) notFound.value = true
      error.value = e?.message || 'Failed to load document'
    }
    finally {
      if (token === loadRequestToken) pending.value = false
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
    if (isRecordDocument) {
      for (const key of ['involvedOfficers', 'externalUnits']) {
        payload[key] = Array.isArray(payload[key])
          ? payload[key].map(String).map(value => value.trim()).filter(Boolean)
          : []
      }
    }
    if (['departments', 'companies', 'companyPurposes', 'companySectors', 'officers'].includes(config.key)) {
      payload.isActive = payload.isActive !== false
      payload.status = payload.isActive ? 'active' : 'disabled'
    }
    if (config.key === 'meetingHistory') {
      const participants = Array.isArray(payload.participants)
        ? payload.participants.map(String).map(name => name.trim()).filter(Boolean)
        : []
      payload.participants = participants
      payload.attendeesCount = participants.length
    }
    if (config.key === 'roles') {
      const rows = (Array.isArray(payload.permissionRows)
        ? payload.permissionRows
        : []) as AppRolePermissionRow[]
      payload.permissionRows = rows
      payload.permissions = permissionRowsToFlatKeys(rows)
      payload.permissionCount = rows.reduce((sum, row) => sum + row.actions.length, 0)
    }
    return payload
  }

  function validateRequiredFields() {
    const missing = config.tabs.flatMap(tab =>
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

  async function save() {
    if (config.readOnly) return
    if (!validateRequiredFields()) return
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
      if (config.key === 'departments') {
        const parentId = String(payload.parentId || '')
        const departmentOptions = await loadReferenceOptions(`${ApiEndpoints.DEPARTMENTS}/options`)
        payload.parentName = departmentOptions.find(option => option.value === parentId)?.label || ''
      }
      if (config.key === 'companies') {
        const [sectorOptions, purposeOptions] = await Promise.all([
          loadReferenceOptions(`${ApiEndpoints.COMPANY_SECTORS}/options`),
          loadReferenceOptions(`${ApiEndpoints.COMPANY_PURPOSES}/options`),
        ])
        payload.sectorName = sectorOptions.find(option => option.value === String(payload.sectorId || ''))?.label || ''
        payload.purposeName = purposeOptions.find(option => option.value === String(payload.purposeId || ''))?.label || ''
      }
      if (config.key === 'companySectors') {
        const sectorOptions = await loadReferenceOptions(`${ApiEndpoints.COMPANY_SECTORS}/options`)
        payload.parentName = sectorOptions.find(option => option.value === String(payload.parentId || ''))?.label || ''
      }
      if (config.key === 'officers') {
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
      if (isCreate.value) {
        const res = await adapter.create(payload as any)
        const created = res.data as { id: string }
        toast.add({ title: t('docetra.document.created'), color: 'success' })
        await router.replace(`${config.routeBase}/${created.id}`)
        return
      }
      const res = await adapter.update(id.value, payload as any)
      model.value = { ...(res.data as Record<string, unknown>) }
      initialSnapshot.value = JSON.stringify(model.value)
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
    navigatePreviousRecord: () => navigateRecord('previous'),
    navigateNextRecord: () => navigateRecord('next'),
    toggleFavorite,
    confirmLeave,
  }
}

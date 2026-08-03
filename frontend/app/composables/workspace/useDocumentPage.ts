import type { EntityConfig } from '~/config/entities'
import { getEntityAdapter } from '~/config/entities'
import type { ActivityEvent, AttachmentMeta, EntityComment } from '~/types/docetra/common'
import type { AppRolePermissionRow } from '~/types/docetra/entities'
import { permissionRowsToFlatKeys } from '~/utils/role/permissions'
import { getByPath, setByPath } from '~/utils/object-path'

export function useDocumentPage(config: EntityConfig, idParam?: string) {
  const route = useRoute()
  const router = useRouter()
  const { t } = useI18n()
  const toast = useToast()
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

  const dirty = computed(() => JSON.stringify(model.value) !== initialSnapshot.value)

  const title = computed(() => {
    if (isCreate.value) return t('docetra.document.new', { entity: t(config.titleKey) })
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

  async function load() {
    pending.value = true
    error.value = null
    notFound.value = false
    try {
      if (isCreate.value) {
        model.value = {
          status: 'draft',
          stage: config.stages?.[0]?.code || undefined,
          ...(config.key === 'roles' ? { permissionRows: [] as AppRolePermissionRow[] } : {}),
        }
        initialSnapshot.value = JSON.stringify(model.value)
        comments.value = []
        activity.value = []
        attachments.value = []
        return
      }
      const res = await adapter.get(id.value)
      model.value = { ...(res.data as Record<string, unknown>) }
      initialSnapshot.value = JSON.stringify(model.value)
      const [c, a, f] = await Promise.all([
        adapter.listComments?.(id.value, { page: 1, limit: 20 }),
        adapter.listActivity?.(id.value, { page: 1, limit: 20 }),
        adapter.listAttachments?.(id.value),
      ])
      comments.value = (c?.data || []) as EntityComment[]
      activity.value = (a?.data || []) as ActivityEvent[]
      attachments.value = (f?.data || []) as AttachmentMeta[]
    }
    catch (e: any) {
      if (e?.statusCode === 404) notFound.value = true
      error.value = e?.message || 'Failed to load document'
    }
    finally {
      pending.value = false
    }
  }

  function prepareModelForSave() {
    const payload = { ...model.value }
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

  async function save() {
    if (config.readOnly) return
    saving.value = true
    try {
      const payload = prepareModelForSave()
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
    submittingComment.value = true
    try {
      const res = await adapter.addComment(id.value, commentBody.value.trim())
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
      toast.add({ title: e?.message || 'Failed', color: 'error' })
    }
    finally {
      submittingComment.value = false
    }
  }

  function confirmLeave() {
    if (!dirty.value) return true
    return window.confirm(t('docetra.document.unsavedConfirm'))
  }

  onBeforeRouteLeave(() => confirmLeave())

  if (import.meta.client) {
    useEventListener(window, 'beforeunload', (event) => {
      if (!dirty.value) return
      event.preventDefault()
      event.returnValue = ''
    })
  }

  watch(() => route.fullPath, () => {
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
    fieldValue,
    setFieldValue,
    load,
    save,
    submitComment,
    confirmLeave,
  }
}

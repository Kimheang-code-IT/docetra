import type { MaybeRefOrGetter } from 'vue'
import type { ConfigurationDiscussionRepository } from '~/repositories/contracts/configuration'
import type { ActivityEvent, EntityComment } from '~/types/docetra/common'
import { useConfirm } from '~/composables/common/useConfirm'

export function useConfigurationDiscussion(options: {
  repository: ConfigurationDiscussionRepository
  id: MaybeRefOrGetter<string | undefined>
  isCreate: MaybeRefOrGetter<boolean>
}) {
  const { t } = useI18n()
  const toast = useToast()
  const auth = useAuthStore()
  const { confirm } = useConfirm()

  const comments = ref<EntityComment[]>([])
  const activity = ref<ActivityEvent[]>([])
  const commentBody = ref('')
  const submittingComment = ref(false)
  const updatingCommentId = ref<string | null>(null)
  const deletingCommentId = ref<string | null>(null)
  const commentsTotal = ref(0)
  const activityTotal = ref(0)
  const feedPage = ref(1)
  const loadingMoreFeed = ref(false)
  const hasMoreFeed = computed(() =>
    comments.value.length < commentsTotal.value || activity.value.length < activityTotal.value,
  )

  const currentUser = computed(() => ({
    id: String(auth.user?.id || auth.user?.email || 'current'),
    name: auth.user?.name || 'You',
    email: auth.user?.email,
  }))

  async function loadDiscussion() {
    const id = toValue(options.id)
    if (toValue(options.isCreate) || !id) {
      comments.value = []
      activity.value = []
      return
    }
    const [commentsResponse, activityResponse] = await Promise.all([
      options.repository.listComments(id, { page: 1, limit: 20, sort: '-createdAt' }),
      options.repository.listActivity(id, { page: 1, limit: 20, sort: '-occurredAt' }),
    ])
    comments.value = commentsResponse.data || []
    activity.value = activityResponse.data || []
    commentsTotal.value = commentsResponse.meta?.total || comments.value.length
    activityTotal.value = activityResponse.meta?.total || activity.value.length
    feedPage.value = 1
  }

  async function loadMoreFeed() {
    const id = toValue(options.id)
    if (!id || !hasMoreFeed.value || loadingMoreFeed.value) return
    const page = feedPage.value + 1
    loadingMoreFeed.value = true
    try {
      const [commentResponse, activityResponse] = await Promise.all([
        comments.value.length < commentsTotal.value
          ? options.repository.listComments(id, { page, limit: 20, sort: '-createdAt' })
          : undefined,
        activity.value.length < activityTotal.value
          ? options.repository.listActivity(id, { page, limit: 20, sort: '-occurredAt' })
          : undefined,
      ])
      comments.value.push(...(commentResponse?.data || []))
      activity.value.push(...(activityResponse?.data || []))
      feedPage.value = page
    }
    finally { loadingMoreFeed.value = false }
  }

  async function submitComment() {
    const id = toValue(options.id)
    const body = commentBody.value.trim()
    if (!id || !body || toValue(options.isCreate) || submittingComment.value) return
    submittingComment.value = true
    try {
      await options.repository.addComment(id, body, currentUser.value)
      commentBody.value = ''
      await loadDiscussion()
      toast.add({ title: t('docetra.document.commentAdded'), color: 'success' })
    }
    catch (cause: any) {
      toast.add({ title: cause?.message || t('docetra.document.commentAddFailed'), color: 'error' })
    }
    finally {
      submittingComment.value = false
    }
  }

  async function updateComment(commentId: string, body: string) {
    const id = toValue(options.id)
    const nextBody = body.trim()
    if (!id || !nextBody || updatingCommentId.value) return
    updatingCommentId.value = commentId
    try {
      await options.repository.updateComment(id, commentId, nextBody)
      await loadDiscussion()
      toast.add({ title: t('docetra.document.commentUpdated'), color: 'success' })
    }
    catch (cause: any) {
      toast.add({ title: cause?.message || t('docetra.document.commentUpdateFailed'), color: 'error' })
    }
    finally {
      updatingCommentId.value = null
    }
  }

  async function deleteComment(commentId: string) {
    const id = toValue(options.id)
    if (!id || deletingCommentId.value) return
    const approved = await confirm({
      kind: 'delete',
      titleKey: 'docetra.comments.deleteTitle',
      descriptionKey: 'docetra.comments.deleteDescription',
      confirmLabelKey: 'actions.delete',
    })
    if (!approved) return
    deletingCommentId.value = commentId
    try {
      await options.repository.deleteComment(id, commentId)
      await loadDiscussion()
      toast.add({ title: t('docetra.document.commentDeleted'), color: 'success' })
    }
    catch (cause: any) {
      toast.add({ title: cause?.message || t('docetra.document.commentDeleteFailed'), color: 'error' })
    }
    finally {
      deletingCommentId.value = null
    }
  }

  return {
    comments,
    activity,
    commentBody,
    submittingComment,
    updatingCommentId,
    deletingCommentId,
    hasMoreFeed,
    loadingMoreFeed,
    currentUser,
    loadDiscussion,
    submitComment,
    updateComment,
    deleteComment,
    loadMoreFeed,
  }
}

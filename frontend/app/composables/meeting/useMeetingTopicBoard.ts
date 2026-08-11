import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'
import { getEntityAdapter } from '~/config/entities'
import {
  assignMeetingToTopic as assignMeetingToTopicApi,
  reorderMeetingsInTopic,
} from '~/adapters/meeting-board'
import { mergeMeetingTiming, sortMeetingsForBoard } from '~/utils/meeting/board'

/** Sentinel for the Unassigned row on the topic rail (not a real topic id). */
export const MEETING_BOARD_UNASSIGNED = '__unassigned__'

export function useMeetingTopicBoard() {
  const { t } = useI18n()
  const toast = useToast()
  const topicsAdapter = getEntityAdapter('meetingTopics')
  const meetingsAdapter = getEntityAdapter('meetingHistory')

  const pending = ref(false)
  const error = ref<string | null>(null)
  const topics = ref<MeetingTopic[]>([])
  const meetings = ref<MeetingHistory[]>([])
  /**
   * null = All meetings (full card list + search/date)
   * MEETING_BOARD_UNASSIGNED = meetings with no topicId
   * otherwise = topic id
   */
  const selectedTopicId = ref<string | null>(null)
  const draggingMeetingId = ref<string | null>(null)
  const dropTopicId = ref<string | null>(null)
  const topicSearch = ref('')
  const meetingSearch = ref('')
  /** YYYY-MM-DDTHH:mm — empty = open-ended */
  const meetingDateStart = ref('')
  const meetingDateEnd = ref('')
  const topicPage = ref(1)
  const topicTotal = ref(0)
  const meetingPage = ref(1)
  const meetingTotal = ref(0)
  const loadingMoreTopics = ref(false)
  const loadingMoreMeetings = ref(false)
  const countSummary = ref({ total: 0, unassigned: 0, groups: {} as Record<string, number> })
  const topicPageSize = 30
  const meetingPageSize = 24
  let requestToken = 0

  const isAllMeetings = computed(() => selectedTopicId.value == null)
  const isUnassigned = computed(() => selectedTopicId.value === MEETING_BOARD_UNASSIGNED)
  /** True when viewing All or Unassigned (not a specific topic). */
  const isPoolView = computed(() => isAllMeetings.value || isUnassigned.value)

  const selectedTopic = computed(() => {
    const id = selectedTopicId.value
    if (!id || id === MEETING_BOARD_UNASSIGNED) return null
    return topics.value.find(t => t.id === id) || null
  })

  const filteredTopics = computed(() => topics.value)

  const unassignedMeetingCount = computed(() => countSummary.value.unassigned)
  const allMeetingCount = computed(() => countSummary.value.total)

  const filteredMeetings = computed(() => {
    const withTiming = meetings.value.map(m => mergeMeetingTiming(m))
    return sortMeetingsForBoard(withTiming, { topicScoped: !isPoolView.value })
  })

  const topicMeetingCounts = computed(() => {
    return new Map(Object.entries(countSummary.value.groups))
  })

  const hasMoreTopics = computed(() => topics.value.length < topicTotal.value)
  const hasMoreMeetings = computed(() => meetings.value.length < meetingTotal.value)

  function meetingQuery(page = 1) {
    return {
      q: meetingSearch.value || undefined,
      topicId: isUnassigned.value ? '__empty__' : (selectedTopicId.value || undefined),
      startDate: meetingDateStart.value || undefined,
      endDate: meetingDateEnd.value || undefined,
      page,
      limit: meetingPageSize,
      sort: isPoolView.value ? 'meetingDate' : 'sortOrder',
    }
  }

  async function refreshCounts() {
    if (!meetingsAdapter.getGroupCounts) return
    const response = await meetingsAdapter.getGroupCounts('topicId', {
      q: meetingSearch.value || undefined,
      startDate: meetingDateStart.value || undefined,
      endDate: meetingDateEnd.value || undefined,
    })
    countSummary.value = response.data
  }

  async function refresh() {
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      const [topicsRes, meetingsRes] = await Promise.all([
        topicsAdapter.list({ q: topicSearch.value || undefined, page: 1, limit: topicPageSize, sort: '-updatedAt' }),
        meetingsAdapter.list(meetingQuery(1)),
        refreshCounts(),
      ])
      if (token !== requestToken) return
      topics.value = (topicsRes.data || []) as MeetingTopic[]
      meetings.value = (meetingsRes.data || []) as MeetingHistory[]
      topicPage.value = 1
      meetingPage.value = 1
      topicTotal.value = topicsRes.meta?.total || topics.value.length
      meetingTotal.value = meetingsRes.meta?.total || meetings.value.length
    }
    catch (e: any) {
      if (token === requestToken) error.value = e?.message || 'Failed to load meetings'
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  async function refreshMeetings() {
    const token = ++requestToken
    pending.value = true
    error.value = null
    try {
      const [response] = await Promise.all([meetingsAdapter.list(meetingQuery(1)), refreshCounts()])
      if (token !== requestToken) return
      meetings.value = (response.data || []) as MeetingHistory[]
      meetingPage.value = 1
      meetingTotal.value = response.meta?.total || meetings.value.length
    }
    catch (e: any) {
      if (token === requestToken) error.value = e?.message || 'Failed to load meetings'
    }
    finally {
      if (token === requestToken) pending.value = false
    }
  }

  async function loadMoreTopics() {
    if (!hasMoreTopics.value || loadingMoreTopics.value) return
    loadingMoreTopics.value = true
    const nextPage = topicPage.value + 1
    try {
      const response = await topicsAdapter.list({ q: topicSearch.value || undefined, page: nextPage, limit: topicPageSize, sort: '-updatedAt' })
      topics.value.push(...((response.data || []) as MeetingTopic[]))
      topicPage.value = nextPage
      topicTotal.value = response.meta?.total || topicTotal.value
    }
    finally { loadingMoreTopics.value = false }
  }

  async function loadMoreMeetings() {
    if (!hasMoreMeetings.value || loadingMoreMeetings.value) return
    loadingMoreMeetings.value = true
    const nextPage = meetingPage.value + 1
    try {
      const response = await meetingsAdapter.list(meetingQuery(nextPage))
      const seen = new Set(meetings.value.map(item => item.id))
      meetings.value.push(...((response.data || []) as MeetingHistory[]).filter(item => !seen.has(item.id)))
      meetingPage.value = nextPage
      meetingTotal.value = response.meta?.total || meetingTotal.value
    }
    finally { loadingMoreMeetings.value = false }
  }

  function selectTopic(id: string | null) {
    selectedTopicId.value = id
    void refreshMeetings()
  }

  async function assignMeetingToTopic(meetingId: string, topicId: string | null) {
    const meeting = meetings.value.find(m => m.id === meetingId)
    if (!meeting) return
    if ((meeting.topicId || null) === topicId) return

    const topic = topicId ? topics.value.find(t => t.id === topicId) : null
    if (topicId && !topic) {
      toast.add({ title: t('docetra.meetingBoard.invalidTopicDrop'), color: 'error' })
      return
    }
    const siblings = topicId
      ? meetings.value.filter(m => m.topicId === topicId && m.id !== meetingId)
      : []
    const nextOrder = siblings.length
      ? Math.max(...siblings.map(m => m.sortOrder ?? 0)) + 1
      : 0

    const snapshot = { ...meeting }
    meeting.topicId = topicId || undefined
    meeting.topicTitle = topic?.title
    meeting.sortOrder = topicId ? nextOrder : undefined

    try {
      await assignMeetingToTopicApi(meetingId, {
        topicId: meeting.topicId || null,
        topicTitle: meeting.topicTitle,
        sortOrder: meeting.sortOrder,
      })
      // The API owns aggregate counts and topic children; the browser only
      // refreshes its bounded page after the atomic assignment succeeds.
      await refresh()
      toast.add({
        title: topicId
          ? t('docetra.meetingBoard.assigned', { topic: topic?.title || '' })
          : t('docetra.meetingBoard.unassignedToast'),
        color: 'success',
      })
    }
    catch (e: any) {
      Object.assign(meeting, snapshot)
      toast.add({ title: e?.message || t('docetra.meetingBoard.assignFailed'), color: 'error' })
    }
  }

  async function reorderMeeting(meetingId: string, beforeId: string | null) {
    if (!selectedTopicId.value || selectedTopicId.value === MEETING_BOARD_UNASSIGNED) return
    const topicId = selectedTopicId.value
    const list = filteredMeetings.value.filter(m => m.topicId === topicId)
    const fromIndex = list.findIndex(m => m.id === meetingId)
    if (fromIndex < 0) return

    const next = [...list]
    const [item] = next.splice(fromIndex, 1)
    if (!item) return
    let toIndex = beforeId ? next.findIndex(m => m.id === beforeId) : next.length
    if (toIndex < 0) toIndex = next.length
    next.splice(toIndex, 0, item)

    try {
      await reorderMeetingsInTopic({
        topicId,
        orderedMeetingIds: next.map(m => m.id),
      })
      await refresh()
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.meetingBoard.reorderFailed'), color: 'error' })
      await refresh()
    }
  }

  const debouncedTopicSearch = useDebounceFn(() => refresh(), 300)
  const debouncedMeetingFilter = useDebounceFn(() => refreshMeetings(), 300)
  watch(topicSearch, () => debouncedTopicSearch())
  watch([meetingSearch, meetingDateStart, meetingDateEnd], () => debouncedMeetingFilter())

  function openTopic(id: string) {
    navigateTo(`/meetings/topics/${id}`)
  }

  function openMeeting(id: string) {
    navigateTo(`/meetings/history/${id}`)
  }

  function openCreateTopic() {
    return navigateTo(`/meetings/topics/new?returnTo=${encodeURIComponent('/meetings/topics')}`)
  }

  function openCreateMeeting() {
    const params = new URLSearchParams()
    params.set('returnTo', '/meetings/topics')
    const tid = selectedTopicId.value
    if (tid && tid !== MEETING_BOARD_UNASSIGNED) params.set('topicId', tid)
    return navigateTo(`/meetings/history/new?${params.toString()}`)
  }

  return {
    pending,
    error,
    topics,
    meetings,
    topicSearch,
    meetingSearch,
    meetingDateStart,
    meetingDateEnd,
    selectedTopicId,
    selectedTopic,
    isAllMeetings,
    isUnassigned,
    isPoolView,
    filteredTopics,
    filteredMeetings,
    allMeetingCount,
    unassignedMeetingCount,
    topicMeetingCounts,
    hasMoreTopics,
    hasMoreMeetings,
    loadingMoreTopics,
    loadingMoreMeetings,
    draggingMeetingId,
    dropTopicId,
    refresh,
    loadMoreTopics,
    loadMoreMeetings,
    selectTopic,
    assignMeetingToTopic,
    reorderMeeting,
    openTopic,
    openMeeting,
    openCreateTopic,
    openCreateMeeting,
  }
}

import type { MeetingHistory, MeetingTopic } from '~/types/docetra/entities'
import { getEntityAdapter } from '~/config/entities'
import { isWithinDateTimeRange } from '~/utils/date-time-range'

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

  const isAllMeetings = computed(() => selectedTopicId.value == null)
  const isUnassigned = computed(() => selectedTopicId.value === MEETING_BOARD_UNASSIGNED)
  /** True when viewing All or Unassigned (not a specific topic). */
  const isPoolView = computed(() => isAllMeetings.value || isUnassigned.value)

  const selectedTopic = computed(() => {
    const id = selectedTopicId.value
    if (!id || id === MEETING_BOARD_UNASSIGNED) return null
    return topics.value.find(t => t.id === id) || null
  })

  const filteredTopics = computed(() => {
    const q = topicSearch.value.trim().toLowerCase()
    if (!q) return topics.value
    return topics.value.filter(topic =>
      topic.title.toLowerCase().includes(q)
      || String((topic as any).owner?.name || '').toLowerCase().includes(q),
    )
  })

  const unassignedMeetings = computed(() =>
    meetings.value.filter(m => !m.topicId),
  )

  const unassignedMeetingCount = computed(() => unassignedMeetings.value.length)
  const allMeetingCount = computed(() => meetings.value.length)

  const filteredMeetings = computed(() => {
    const q = meetingSearch.value.trim().toLowerCase()
    let list: MeetingHistory[]
    if (isAllMeetings.value) {
      list = meetings.value
    }
    else if (isUnassigned.value) {
      list = unassignedMeetings.value
    }
    else {
      list = meetings.value.filter(m => m.topicId === selectedTopicId.value)
    }
    if (meetingDateStart.value || meetingDateEnd.value) {
      list = list.filter(m =>
        isWithinDateTimeRange(m.meetingDate, meetingDateStart.value, meetingDateEnd.value),
      )
    }
    if (q) {
      list = list.filter(m =>
        m.title.toLowerCase().includes(q)
        || (m.topicTitle || '').toLowerCase().includes(q)
        || (m.location || '').toLowerCase().includes(q),
      )
    }
    return [...list].sort((a, b) => {
      const ao = a.sortOrder ?? Number.MAX_SAFE_INTEGER
      const bo = b.sortOrder ?? Number.MAX_SAFE_INTEGER
      if (ao !== bo) return ao - bo
      return String(a.meetingDate).localeCompare(String(b.meetingDate))
    })
  })

  const topicMeetingCounts = computed(() => {
    const map = new Map<string, number>()
    for (const meeting of meetings.value) {
      if (!meeting.topicId) continue
      map.set(meeting.topicId, (map.get(meeting.topicId) || 0) + 1)
    }
    return map
  })

  async function refresh() {
    pending.value = true
    error.value = null
    try {
      const [topicsRes, meetingsRes] = await Promise.all([
        topicsAdapter.list({ limit: 100, sort: '-updatedAt' }),
        meetingsAdapter.list({ limit: 200, sort: 'meetingDate' }),
      ])
      topics.value = (topicsRes.data || []) as MeetingTopic[]
      meetings.value = (meetingsRes.data || []) as MeetingHistory[]
    }
    catch (e: any) {
      error.value = e?.message || 'Failed to load meetings'
    }
    finally {
      pending.value = false
    }
  }

  function selectTopic(id: string | null) {
    selectedTopicId.value = id
  }

  async function syncTopicChildren(topicId: string) {
    const linked = meetings.value
      .filter(m => m.topicId === topicId)
      .sort((a, b) => (a.sortOrder ?? 9999) - (b.sortOrder ?? 9999))
    await topicsAdapter.update(topicId, {
      childMeetingCount: linked.length,
      childMeetings: linked.map((m, index) => ({
        id: m.id,
        title: m.title,
        meetingDate: m.meetingDate,
        sortOrder: m.sortOrder ?? index,
      })),
    } as any)
  }

  async function assignMeetingToTopic(meetingId: string, topicId: string | null) {
    const meeting = meetings.value.find(m => m.id === meetingId)
    if (!meeting) return
    if ((meeting.topicId || null) === topicId) return

    const previousTopicId = meeting.topicId
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
      await meetingsAdapter.update(meetingId, {
        topicId: meeting.topicId,
        topicTitle: meeting.topicTitle,
        sortOrder: meeting.sortOrder,
      } as any)
      if (previousTopicId) await syncTopicChildren(previousTopicId)
      if (topicId) await syncTopicChildren(topicId)
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
      await Promise.all(next.map((meeting, index) => {
        meeting.sortOrder = index
        return meetingsAdapter.update(meeting.id, { sortOrder: index } as any)
      }))
      await syncTopicChildren(topicId)
      await refresh()
    }
    catch (e: any) {
      toast.add({ title: e?.message || t('docetra.meetingBoard.reorderFailed'), color: 'error' })
      await refresh()
    }
  }

  function openTopic(id: string) {
    navigateTo(`/meetings/topics/${id}`)
  }

  function openMeeting(id: string) {
    navigateTo(`/meetings/history/${id}`)
  }

  function openCreateTopic() {
    navigateTo('/meetings/topics/new')
  }

  function openCreateMeeting() {
    navigateTo('/meetings/history/new')
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
    draggingMeetingId,
    dropTopicId,
    refresh,
    selectTopic,
    assignMeetingToTopic,
    reorderMeeting,
    openTopic,
    openMeeting,
    openCreateTopic,
    openCreateMeeting,
  }
}

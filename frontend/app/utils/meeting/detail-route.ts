/** Canonical meeting-history document route, opened from the topic board or history list. */

export const MEETING_TOPICS_PATH = '/meetings/topics'
export const MEETING_HISTORY_PATH = '/meetings/history'
export const MEETING_COMPLETED_STAGE = 'completed'

export function isCompletedMeeting(stage: unknown): boolean {
  return String(stage || '') === MEETING_COMPLETED_STAGE
}

export function meetingHistoryDetailPath(id: string, returnTo?: string): string {
  const path = `${MEETING_HISTORY_PATH}/${encodeURIComponent(id)}`
  if (!returnTo) return path
  return `${path}?returnTo=${encodeURIComponent(returnTo)}`
}

export function meetingDetailOpenedFromTopics(returnTo: unknown): boolean {
  if (typeof returnTo !== 'string') return false
  return returnTo === MEETING_TOPICS_PATH || returnTo.startsWith(`${MEETING_TOPICS_PATH}/`)
}

/** Fill history-form aliases so a topic-board card opens with the same fields as the card. */
export function hydrateMeetingHistoryModel(
  model: Record<string, unknown>,
): Record<string, unknown> {
  const nested = model.details
  const details = nested && typeof nested === 'object' && !Array.isArray(nested)
    ? { ...(nested as Record<string, unknown>) }
    : {}
  const next: Record<string, unknown> = { ...model, details }

  const meetingDate = next.meetingDate || details.meetingDate || next.recordTime
  if (meetingDate && !next.meetingDate) next.meetingDate = meetingDate
  if (meetingDate && details.meetingDate == null) details.meetingDate = meetingDate

  const topicId = next.topicId || details.topicId || next.parentId || next.parentRecord
  if (topicId && !next.topicId) next.topicId = topicId
  if (topicId && details.topicId == null) details.topicId = topicId

  const copyKeys = [
    'topicTitle',
    'letterNumber',
    'letterDate',
    'durationMinutes',
    'meetingMode',
    'meetingUrl',
    'location',
    'participants',
    'internalUnits',
    'externalUnits',
    'sortOrder',
  ] as const
  for (const key of copyKeys) {
    const value = next[key] ?? details[key]
    if (value == null || value === '') continue
    if (next[key] == null) next[key] = value
    if (details[key] == null) details[key] = value
  }

  next.details = details
  return next
}

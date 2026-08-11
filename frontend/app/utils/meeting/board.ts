import type { MeetingBoardTiming } from '~/types/docetra/meeting-api'

export const DEFAULT_IMMINENT_MINUTES = 15

export function getImminentMinutesBefore(): number {
  return DEFAULT_IMMINENT_MINUTES
}

export function computeMeetingTiming(
  meetingDate: string | undefined,
  durationMinutes?: number,
  now = new Date(),
  thresholdMinutes = getImminentMinutesBefore(),
): MeetingBoardTiming {
  if (!meetingDate) return {}
  const start = new Date(meetingDate)
  if (Number.isNaN(start.getTime())) return {}

  const end = durationMinutes != null && durationMinutes > 0
    ? new Date(start.getTime() + durationMinutes * 60_000)
    : null

  const minutesUntilStart = Math.round((start.getTime() - now.getTime()) / 60_000)
  const inProgress = end
    ? now >= start && now <= end
    : false
  const imminent = minutesUntilStart >= 0
    && minutesUntilStart <= thresholdMinutes
    && !inProgress
    || inProgress

  return {
    imminent,
    minutesUntilStart,
    inProgress,
  }
}

export function mergeMeetingTiming<T extends { meetingDate?: string; durationMinutes?: number }>(
  meeting: T,
  thresholdMinutes = getImminentMinutesBefore(),
): T & MeetingBoardTiming {
  const timing = computeMeetingTiming(
    meeting.meetingDate,
    meeting.durationMinutes,
    new Date(),
    thresholdMinutes,
  )
  return { ...meeting, ...timing }
}

export function sortMeetingsForBoard<
  T extends {
    meetingDate: string
    sortOrder?: number
    imminent?: boolean
    minutesUntilStart?: number
  },
>(
  list: T[],
  options: { topicScoped: boolean },
): T[] {
  const copy = [...list]
  copy.sort((a, b) => {
    const ai = a.imminent ? 1 : 0
    const bi = b.imminent ? 1 : 0
    if (ai !== bi) return bi - ai

    if (options.topicScoped) {
      const ao = a.sortOrder ?? Number.MAX_SAFE_INTEGER
      const bo = b.sortOrder ?? Number.MAX_SAFE_INTEGER
      if (ao !== bo) return ao - bo
    }

    const ad = a.meetingDate ? new Date(a.meetingDate).getTime() : 0
    const bd = b.meetingDate ? new Date(b.meetingDate).getTime() : 0
    if (ad !== bd) return ad - bd

    return String(a.meetingDate).localeCompare(String(b.meetingDate))
  })
  return copy
}

export function formatMeetingDateTime(value: unknown): string {
  if (value == null || value === '') return ''
  const s = String(value)
  if (s.includes('T')) return s.slice(0, 16).replace('T', ' ')
  return s.slice(0, 10)
}

export function isJoinableMeeting(mode?: string, url?: string): boolean {
  if (!safeExternalUrl(url)) return false
  return mode === 'online' || mode === 'hybrid'
}

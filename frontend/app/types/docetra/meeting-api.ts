/**
 * Meeting Topic board API contracts used by the HTTP meeting-board adapter.
 * Spec: prompt/backend/modules/meeting-topic-board.md
 */

export type MeetingMode = 'in_person' | 'online' | 'hybrid'

export type MeetingRecurrenceFrequency = 'daily' | 'weekly' | 'monthly'

export interface MeetingRecurrenceRule {
  frequency: MeetingRecurrenceFrequency
  interval?: number
  byWeekday?: string[]
  until?: string
  count?: number
}

/** PATCH assign or POST /meetings/{id}/assign-topic */
export interface AssignMeetingTopicBody {
  topicId: string | null
  sortOrder?: number
  /** Mock / optional denormalized title; API should resolve from topic id */
  topicTitle?: string
}

/** POST /meetings/reorder */
export interface ReorderMeetingsBody {
  topicId: string
  orderedMeetingIds: string[]
}

/** POST /meetings/{id}/attachments/link */
export interface LinkMeetingDriveFileBody {
  source: 'google_drive'
  driveFileId: string
  driveSyncJobId?: string
  displayName?: string
}

/** GET /portal/drive-files catalog row */
export interface DriveFileCatalogItem {
  id: string
  driveFileId: string
  name: string
  mimeType?: string
  sizeBytes?: number
  syncedAt?: string
  webViewLink?: string
}

/** Optional server-computed fields on list/detail meeting payloads */
export interface MeetingBoardTiming {
  imminent?: boolean
  minutesUntilStart?: number
  inProgress?: boolean
}

export interface MeetingListQuery {
  topicId?: string
  unassignedOnly?: boolean
  dateFrom?: string
  dateTo?: string
  search?: string
  sort?: string
  page?: number
  limit?: number
}

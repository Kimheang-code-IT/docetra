import { dateOnly } from './seed'

const PRIORITIES = ['low', 'medium', 'high'] as const
const TAG_OPTIONS = ['internal', 'external', 'legal', 'finance'] as const
const MEETING_FORMATS = ['in_person', 'online', 'hybrid'] as const

export type DynamicFieldMockProfile =
  | 'incoming'
  | 'outgoing'
  | 'document'
  | 'master_list'
  | 'meeting'
  | 'meeting_topic'

/** Sample `record_detail` values aligned with mock Record Type attribute assignments. */
export function mockDynamicDetails(i: number, profile: DynamicFieldMockProfile): Record<string, unknown> {
  const priority = PRIORITIES[i % PRIORITIES.length]!
  const notes = i % 3 === 0
    ? `Sample notes for record ${i + 1}. Review before approval.`
    : ''
  const dueDate = dateOnly((i + 5) % 30)
  const confidential = i % 4 === 0

  switch (profile) {
    case 'incoming':
      return {
        external_ref: `EXT-IN-${1000 + i}`,
        priority,
        due_date: dueDate,
        confidential,
        notes,
        contact_email: `sender${i + 1}@example.gov.kh`,
      }
    case 'outgoing':
      return {
        external_ref: `EXT-OUT-${2000 + i}`,
        priority,
        due_date: dueDate,
        notes,
        source_url: i % 2 === 0 ? `https://docs.example.gov.kh/out/${i + 1}` : '',
      }
    case 'document':
      return {
        amount: 1000 + i * 25,
        budget: 5000 + i * 100,
        priority,
        notes,
        page_count: 3 + (i % 12),
        tags: [TAG_OPTIONS[i % TAG_OPTIONS.length]!, TAG_OPTIONS[(i + 1) % TAG_OPTIONS.length]!]
          .filter((value, index, array) => array.indexOf(value) === index),
      }
    case 'master_list':
      return {
        external_ref: `EXT-MLR-${3000 + i}`,
        amount: 750 + i * 15,
        priority,
        due_date: dueDate,
        confidential,
        notes,
      }
    case 'meeting':
      return {
        meeting_format: MEETING_FORMATS[i % MEETING_FORMATS.length]!,
        priority,
        notes: notes || `Meeting agenda notes ${i + 1}`,
        review_time: `${dateOnly(i % 20)}T14:30:00+07:00`,
      }
    case 'meeting_topic':
      return {
        priority,
        notes: `Topic briefing ${i + 1}`,
        due_date: dueDate,
        tags: [TAG_OPTIONS[i % TAG_OPTIONS.length]!],
      }
  }
}

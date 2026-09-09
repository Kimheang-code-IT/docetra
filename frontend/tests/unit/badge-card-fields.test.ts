import { describe, expect, it } from 'vitest'
import { normalizeBadgeColor } from '../../app/utils/badge'
import {
  cardEntityKeyForRecordType,
  readableCardText,
  resolveFooterAlign,
  resolveTypeAwareCardFields,
  resolveTypeAwareFooterAlign,
} from '../../app/utils/card-fields'

const fallback = [
  { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
  { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
]

describe('normalizeBadgeColor', () => {
  it('accepts only the Nuxt UI badge union', () => {
    expect(normalizeBadgeColor('warning')).toBe('warning')
    expect(normalizeBadgeColor('secondary')).toBe('secondary')
    expect(normalizeBadgeColor(null)).toBeNull()
    expect(normalizeBadgeColor('#ff0000')).toBeNull()
    expect(normalizeBadgeColor('neon')).toBeNull()
  })
})

describe('resolveTypeAwareCardFields', () => {
  it('record-type payload wins over app config and defaults', () => {
    const slots = resolveTypeAwareCardFields('documents', {
      typeOverride: { documents: ['tags', 'made_up_slot', 'referenceNumber'] },
      appConfig: { documents: ['attachmentCount'] },
    })
    expect(slots).toEqual(['tags', 'referenceNumber'])
  })

  it('falls back to app config when the type has no selection', () => {
    const slots = resolveTypeAwareCardFields('meetingTopics', {
      typeOverride: {},
      appConfig: { meetingTopics: ['tags'] },
    })
    expect(slots).toEqual(['tags'])
  })

  it('falls back to defaults when neither source defines slots', () => {
    expect(resolveTypeAwareCardFields('meetingTopics', {})).toEqual(
      resolveVisibleDefaultsForTopic(),
    )
  })

  function resolveVisibleDefaultsForTopic() {
    // card-fields.ts default for topic cards: description + optional tags.
    return ['description', 'tags']
  }
})

describe('resolveTypeAwareFooterAlign', () => {
  it('per-slot precedence: type override, app config, then default', () => {
    const sources = {
      typeOverride: { documents: { recordTime: 'right' as const } },
      appConfig: { documents: { recordTime: 'left' as const, location: 'left' as const } },
    }
    expect(resolveTypeAwareFooterAlign('documents', 'recordTime', sources)).toBe('right')
    expect(resolveTypeAwareFooterAlign('meetingHistory', 'location', sources)).toBe('right')
    expect(resolveTypeAwareFooterAlign('meetingHistory', 'letterDate', sources)).toBe('left')
  })

  it('matches legacy resolveFooterAlign without overrides', () => {
    const map = { meetingHistory: { meetingDate: 'right' as const } }
    expect(resolveFooterAlign('meetingHistory', 'meetingDate', map)).toBe(
      resolveTypeAwareFooterAlign('meetingHistory', 'meetingDate', { appConfig: map }),
    )
  })
})

describe('cardEntityKeyForRecordType', () => {
  it('maps built-in codes and buckets custom types with generic records', () => {
    expect(cardEntityKeyForRecordType('meeting_topic')).toBe('meetingTopics')
    expect(cardEntityKeyForRecordType('incoming_document')).toBe('incomingDocuments')
    expect(cardEntityKeyForRecordType('master_list_request')).toBe('masterListRequests')
    expect(cardEntityKeyForRecordType('annual_report')).toBe('documents')
    expect(cardEntityKeyForRecordType(null)).toBe('documents')
  })
})

describe('readableCardText', () => {
  it('hides UUID-shaped values and keeps human labels', () => {
    expect(readableCardText('17f2dbc1-5e61-4db9-8219-9bb239e1008c')).toBe('')
    expect(readableCardText('Incoming document')).toBe('Incoming document')
    expect(readableCardText({ name: 'Cabinet Office' })).toBe('Cabinet Office')
    expect(readableCardText({ name: '17f2dbc1-5e61-4db9-8219-9bb239e1008c' })).toBe('')
  })
})

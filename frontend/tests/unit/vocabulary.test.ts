import { describe, expect, it } from 'vitest'
import {
  cardEntityKeyForRecordType,
  enumValueLabel,
  mergeVocabularyOptions,
  normalizeBadgeColor,
  vocabularyBadgeColor,
} from '../../app/utils/vocabulary'
import type { EnumValueOption } from '../../app/types/docetra/vocabulary'
import {
  resolveFooterAlign,
  resolveTypeAwareCardFields,
  resolveTypeAwareFooterAlign,
} from '../../app/utils/card-fields'

const fallback = [
  { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
  { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
]

function enumValue(overrides: Partial<EnumValueOption>): EnumValueOption {
  return {
    code: 'x',
    isActive: true,
    ...overrides,
  }
}

describe('normalizeBadgeColor', () => {
  it('accepts only the Nuxt UI badge union', () => {
    expect(normalizeBadgeColor('warning')).toBe('warning')
    expect(normalizeBadgeColor('secondary')).toBe('secondary')
    expect(normalizeBadgeColor(null)).toBeNull()
    expect(normalizeBadgeColor('#ff0000')).toBeNull()
    expect(normalizeBadgeColor('neon')).toBeNull()
  })
})

describe('mergeVocabularyOptions', () => {
  const resolveLabel = (value: EnumValueOption) =>
    value.labelEn || value.labelKm || value.code

  it('passes fallback through when no server values exist', () => {
    expect(mergeVocabularyOptions(fallback, null, resolveLabel)).toEqual([
      { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
      { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
    ])
  })

  it('server wins for label and color, keeping code identity', () => {
    const server = [enumValue({ code: 'active', labelEn: 'Enabled', color: 'success' })]
    const merged = mergeVocabularyOptions(fallback, server, resolveLabel)
    expect(merged[0]).toMatchObject({ value: 'active', label: 'Enabled', color: 'success' })
    expect(merged[0].labelKey).toBeUndefined()
  })

  it('unions by code and appends custom server entries', () => {
    const server = [
      enumValue({ code: 'custom_state', labelEn: 'Custom' }),
      enumValue({ code: 'archived', labelEn: 'Archived' }),
    ]
    const merged = mergeVocabularyOptions(fallback, server, resolveLabel)
    expect(merged.map(option => option.value)).toEqual(['active', 'archived', 'custom_state'])
  })

  it('drops inactive server entries but keeps their fallback twin', () => {
    const server = [
      enumValue({ code: 'active', isActive: false }),
      enumValue({ code: 'brand_new', labelEn: 'New' }),
    ]
    const merged = mergeVocabularyOptions(fallback, server, resolveLabel)
    expect(merged.map(option => option.value)).toEqual(['active', 'archived', 'brand_new'])
  })

  it('orders by server order with fallbacks keeping relative position', () => {
    const server = [
      enumValue({ code: 'z_last', labelEn: 'Z', order: 1 }),
      enumValue({ code: 'archived', order: 5 }),
      enumValue({ code: 'active', order: 50 }),
    ]
    const merged = mergeVocabularyOptions(fallback, server, resolveLabel)
    expect(merged.map(option => option.value)).toEqual(['z_last', 'archived', 'active'])
  })
})

describe('enumValueLabel', () => {
  it('prefers the locale label then falls back across languages and code', () => {
    const value = { code: 'stage_new', labelEn: 'New stage', labelKm: 'ដំណាក់កាលថ្មី' }
    expect(enumValueLabel(value, 'km')).toBe('ដំណាក់កាលថ្មី')
    expect(enumValueLabel(value, 'en')).toBe('New stage')
    expect(enumValueLabel({ code: 'only_code', labelEn: '', labelKm: '' }, 'km')).toBe('only_code')
  })
})

describe('vocabularyBadgeColor', () => {
  const catalog = {
    status: [enumValue({ code: 'active', color: 'success' }), enumValue({ code: 'hexed', color: '#123456' })],
  }

  it('returns constrained colors only', () => {
    expect(vocabularyBadgeColor(catalog, 'status', 'active')).toBe('success')
    expect(vocabularyBadgeColor(catalog, 'status', 'hexed')).toBeNull()
    expect(vocabularyBadgeColor(catalog, 'status', 'missing')).toBeNull()
    expect(vocabularyBadgeColor(null, 'status', 'active')).toBeNull()
  })
})

describe('resolveTypeAwareCardFields', () => {
  it('record-type payload wins over app config and defaults', () => {
    const slots = resolveTypeAwareCardFields('documents', {
      typeOverride: { documents: ['status', 'tags', 'made_up_slot'] },
      appConfig: { documents: ['attachmentCount'] },
    })
    expect(slots).toEqual(['status', 'tags'])
  })

  it('falls back to app config when the type has no selection', () => {
    const slots = resolveTypeAwareCardFields('meetingTopics', {
      typeOverride: {},
      appConfig: { meetingTopics: ['stage'] },
    })
    expect(slots).toEqual(['stage'])
  })

  it('falls back to defaults when neither source defines slots', () => {
    expect(resolveTypeAwareCardFields('meetingTopics', {})).toEqual(
      resolveVisibleDefaultsForTopic(),
    )
  })

  function resolveVisibleDefaultsForTopic() {
    return ['status', 'stage', 'tags']
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

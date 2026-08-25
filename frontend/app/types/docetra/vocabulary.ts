import type { AppConfigDisplay } from './settings'

/** Nuxt UI badge color union — vocabulary colors must stay inside this set. */
export type BadgeColor =
  | 'primary'
  | 'secondary'
  | 'success'
  | 'info'
  | 'warning'
  | 'error'
  | 'neutral'

export const BADGE_COLORS: BadgeColor[] = [
  'primary',
  'secondary',
  'success',
  'info',
  'warning',
  'error',
  'neutral',
]

/** One DB-driven enum value from GET /api/v2/configuration/enums. */
export interface EnumValueOption {
  id?: string
  /** Optimistic-concurrency version when the API provides one. */
  version?: number
  code: string
  labelEn?: string | null
  labelKm?: string | null
  color?: string | null
  order?: number | null
  isActive: boolean
}

/** Grouped catalog payload: `{ groups: { [group]: EnumValueOption[] } }`. */
export type VocabularyCatalog = Record<string, EnumValueOption[]>

export interface CreateEnumValueInput {
  code: string
  labelEn: string
  labelKm?: string
  color?: BadgeColor | string
  order?: number
  isActive?: boolean
}

export type UpdateEnumValueInput = Partial<CreateEnumValueInput> & {
  version?: number
}

/**
 * Per-record-type card display override stored in `record_type.payload`.
 * Same shape as `AppConfigDisplay` so both sources merge with one resolver.
 */
export interface RecordTypePayload extends Record<string, unknown> {
  cardFields?: AppConfigDisplay['cardFields']
  cardFooterAlign?: AppConfigDisplay['cardFooterAlign']
}

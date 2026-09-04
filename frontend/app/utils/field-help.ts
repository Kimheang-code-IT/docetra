import type { DocumentFieldSchema } from '~/types/docetra/common'

type Translate = (key: string, values?: Record<string, unknown>) => string
type TranslateExists = (key: string) => boolean

/**
 * Remove redundant "Optional." prefix — optional fields already omit the required asterisk.
 */
export function stripOptionalHelpPrefix(text: string): string {
  return text
    .replace(/^Optional\.\s*/i, '')
    .replace(/^ស្រេចចិត្ត\s*[\.។]?\s*/u, '')
    .trim()
}

export function resolveFieldHelp(
  field: Pick<DocumentFieldSchema, 'key' | 'helpKey' | 'labelKey'>,
  label: string,
  t: Translate,
  te: TranslateExists,
  options?: { required?: boolean },
): string {
  let text: string

  if (field.helpKey && te(field.helpKey)) {
    text = t(field.helpKey)
  }
    else {
      const fullKey = `docetra.fieldHelp.${field.key}`
      if (te(fullKey)) text = t(fullKey)
      else {
        const leaf = field.key.includes('.') ? field.key.slice(field.key.lastIndexOf('.') + 1) : field.key
        const leafKey = `docetra.fieldHelp.${leaf}`
        if (leaf && te(leafKey)) text = t(leafKey)
        else return ''
      }
    }

  if (options?.required === false && text) {
    return stripOptionalHelpPrefix(text)
  }

  return text
}

const SELECT_PLACEHOLDER_TYPES = new Set([
  'select',
  'multiselect',
  'organization',
  'officer',
  'relation',
  'date',
  'datetime',
  'icon',
])

/**
 * Every form control shows a placeholder when empty.
 * Order: explicit placeholder → placeholderKey → type-aware Enter/Select {label}.
 */
export function resolveFieldPlaceholder(
  field: Pick<DocumentFieldSchema, 'type' | 'placeholder' | 'placeholderKey'>,
  label: string,
  t: Translate,
  te?: TranslateExists,
): string {
  if (field.placeholder?.trim()) return field.placeholder.trim()
  if (field.placeholderKey && (!te || te(field.placeholderKey))) {
    return t(field.placeholderKey)
  }
  const name = label.trim() || t('docetra.fields.value')
  if (field.type === 'url') return t('docetra.fields.placeholderUrl')
  if (field.type === 'number') return t('docetra.fields.placeholderNumber')
  if (field.type === 'color') return '#2563eb'
  if (SELECT_PLACEHOLDER_TYPES.has(field.type)) {
    return t('docetra.fields.placeholderSelect', { label: name })
  }
  return t('docetra.fields.placeholderEnter', { label: name })
}


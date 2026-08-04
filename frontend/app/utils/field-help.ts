import type { DocumentFieldSchema } from '~/types/docetra/common'

type Translate = (key: string, values?: Record<string, unknown>) => string
type TranslateExists = (key: string) => boolean

/**
 * Resolve ERPNext-style helper text for a document field.
 * Order: explicit helpKey → fieldHelp.<fullKey> → fieldHelp.<leaf> → default.
 */
export function resolveFieldHelp(
  field: Pick<DocumentFieldSchema, 'key' | 'helpKey' | 'labelKey'>,
  label: string,
  t: Translate,
  te: TranslateExists,
): string {
  if (field.helpKey && te(field.helpKey)) {
    return t(field.helpKey)
  }

  const fullKey = `docetra.fieldHelp.${field.key}`
  if (te(fullKey)) return t(fullKey)

  const leaf = field.key.includes('.') ? field.key.slice(field.key.lastIndexOf('.') + 1) : field.key
  const leafKey = `docetra.fieldHelp.${leaf}`
  if (leaf && te(leafKey)) return t(leafKey)

  return t('docetra.fieldHelp.default', { field: label })
}

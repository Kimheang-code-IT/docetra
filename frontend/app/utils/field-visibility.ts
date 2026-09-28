import type { DocumentFieldSchema } from '~/types/docetra/common'

type VisibilityField = Pick<DocumentFieldSchema, 'visibleWhen'>

/**
 * Whether a form field should render/validate given the current model values.
 * Fields without a `visibleWhen` condition are always visible.
 */
export function isFieldVisible(
  field: VisibilityField,
  getValue: (key: string) => unknown,
): boolean {
  const condition = field.visibleWhen
  if (!condition) return true
  const value = getValue(condition.key)
  if ('equals' in condition && value !== condition.equals) return false
  if ('notEquals' in condition && value === condition.notEquals) return false
  return true
}

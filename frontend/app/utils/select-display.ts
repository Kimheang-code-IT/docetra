import type { FieldOption } from '~/types/docetra/common'

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

/** Map FK field keys → companion display-name keys returned by the API. */
const COMPANION_NAME_KEYS: Record<string, string> = {
  roleId: 'roleName',
  organizationId: 'organizationName',
  departmentId: 'departmentName',
  officerId: 'officerName',
  parentId: 'parentName',
  topicId: 'topicName',
  sectorId: 'sectorName',
  purposeId: 'purposeName',
  documentType: 'documentTypeName',
  userId: 'userName',
  companyId: 'companyName',
}

export function companionNameKey(fieldKey: string): string | undefined {
  if (COMPANION_NAME_KEYS[fieldKey]) return COMPANION_NAME_KEYS[fieldKey]
  if (fieldKey.endsWith('Id')) return `${fieldKey.slice(0, -2)}Name`
  return undefined
}

export function looksLikeOpaqueId(value: unknown): boolean {
  const text = String(value ?? '').trim()
  if (!text) return false
  return UUID_RE.test(text) || (/^\d+$/.test(text) && text.length >= 10)
}

/**
 * Ensure select items always include a human label for the current value.
 * Prevents UInputMenu/USelect from rendering raw UUIDs/codes when options
 * have not loaded yet or the selected row is outside the active option page.
 */
export function ensureSelectItemsHaveLabel(
  items: Array<{ label: string; value: string }>,
  value: unknown,
  selectedLabel?: string | null,
): Array<{ label: string; value: string }> {
  const current = value == null || value === '' ? '' : String(value)
  if (!current) return items

  const existing = items.find(item => String(item.value) === current)
  const friendly = String(selectedLabel || '').trim()
  if (existing) {
    if (friendly && looksLikeOpaqueId(existing.label)) {
      return items.map(item => (
        String(item.value) === current
          ? { ...item, label: friendly }
          : item
      ))
    }
    return items
  }

  if (friendly && !looksLikeOpaqueId(friendly)) {
    return [{ label: friendly, value: current }, ...items]
  }

  // Last resort: keep value selectable but do not invent a fake name.
  if (!looksLikeOpaqueId(current)) {
    return [{ label: current, value: current }, ...items]
  }
  return items
}

export function fieldOptionsToSelectItems(
  options: FieldOption[],
  t: (key: string) => string,
): Array<{ label: string; value: string }> {
  return options
    .filter(option => option.value !== '')
    .map(option => ({
      label: option.labelKey ? t(option.labelKey) : option.label,
      value: option.value,
    }))
}

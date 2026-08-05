/**
 * Map record-type assigned attributes → document form field schemas.
 * Values bind under `details.<attributeCode>` (record_detail).
 */
import type { DocumentFieldSchema, DocumentSectionSchema, FieldOption, FieldType } from '~/types/docetra/common'
import type {
  AttributeDataType,
  RecordAttribute,
  RecordType,
  RecordTypeAttribute,
} from '~/types/docetra/configuration'

const DATA_TYPE_TO_FIELD: Record<AttributeDataType, FieldType> = {
  short_text: 'text',
  long_text: 'textarea',
  rich_text: 'textarea',
  integer: 'number',
  decimal: 'number',
  currency: 'number',
  boolean: 'boolean',
  date: 'date',
  time: 'text',
  datetime: 'datetime',
  email: 'text',
  phone: 'text',
  url: 'url',
  select: 'select',
  multi_select: 'multiselect',
  radio: 'select',
  checkbox_group: 'multiselect',
  file: 'file',
  image: 'image',
  organization: 'organization',
  officer: 'officer',
  user: 'officer',
  record_reference: 'relation',
}

export function attributeDataTypeToFieldType(dataType: AttributeDataType | string): FieldType {
  return DATA_TYPE_TO_FIELD[dataType as AttributeDataType] || 'text'
}

export function detailFieldKey(attributeCode: string): string {
  return `details.${attributeCode}`
}

function optionsFromCatalog(attr: RecordAttribute | undefined): FieldOption[] | undefined {
  if (!attr?.options?.length) return undefined
  return attr.options
    .filter(o => o.active !== false)
    .sort((a, b) => a.order - b.order)
    .map(o => ({
      label: o.label,
      value: o.value,
    }))
}

export function mapTypeAttributeToField(
  assigned: RecordTypeAttribute,
  catalogById?: Map<string, RecordAttribute>,
): DocumentFieldSchema | null {
  if (assigned.visible === false) return null
  const catalog = catalogById?.get(assigned.attributeId)
  const dataType = assigned.dataType || catalog?.dataType || 'short_text'
  const fieldType = attributeDataTypeToFieldType(dataType)
  const label = assigned.attributeLabel || catalog?.label || assigned.attributeCode
  const options = optionsFromCatalog(catalog)

  return {
    key: detailFieldKey(assigned.attributeCode),
    labelKey: `docetra.fields.${assigned.attributeCode}`,
    label,
    type: fieldType,
    required: assigned.required,
    readOnly: assigned.readOnly,
    colSpan: fieldType === 'textarea' || fieldType === 'file' || fieldType === 'image' ? 2 : 1,
    options,
    help: catalog?.helpText || undefined,
    placeholder: catalog?.placeholder || undefined,
    rows: dataType === 'long_text' || dataType === 'rich_text' ? 4 : undefined,
    meta: {
      attributeId: assigned.attributeId,
      attributeCode: assigned.attributeCode,
      dataType,
      section: assigned.section,
    },
  }
}

export function mapTypeAttributesToFields(
  attributes: RecordTypeAttribute[],
  catalog?: RecordAttribute[],
): DocumentFieldSchema[] {
  const byId = new Map((catalog || []).map(a => [a.id, a]))
  return [...attributes]
    .sort((a, b) => a.order - b.order)
    .map(a => mapTypeAttributeToField(a, byId))
    .filter((f): f is DocumentFieldSchema => Boolean(f))
}

/** Group assigned attributes into form sections (by `section` name). */
export function mapTypeAttributesToSections(
  attributes: RecordTypeAttribute[],
  catalog?: RecordAttribute[],
  fallbackTitle = 'Type fields',
): DocumentSectionSchema[] {
  const byId = new Map((catalog || []).map(a => [a.id, a]))
  const ordered = [...attributes].sort((a, b) => a.order - b.order)
  const groups = new Map<string, DocumentFieldSchema[]>()

  for (const assigned of ordered) {
    const field = mapTypeAttributeToField(assigned, byId)
    if (!field) continue
    const sectionName = (assigned.section || fallbackTitle).trim() || fallbackTitle
    const list = groups.get(sectionName) || []
    list.push(field)
    groups.set(sectionName, list)
  }

  return [...groups.entries()].map(([title, fields], index) => ({
    id: `type-fields-${index}`,
    title,
    fields,
  }))
}

export function stageOptionsFromType(type: RecordType | null | undefined): FieldOption[] | null {
  if (!type?.features?.enableWorkflow || !type.stages?.length) return null
  return [...type.stages]
    .sort((a, b) => a.order - b.order)
    .map(s => ({
      label: s.name,
      value: s.code,
    }))
}

/** Keep only detail keys still assigned on the new type. */
export function pruneDetailsForType(
  details: Record<string, unknown> | null | undefined,
  attributes: RecordTypeAttribute[],
): Record<string, unknown> {
  const allowed = new Set(attributes.map(a => a.attributeCode))
  const next: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(details || {})) {
    if (allowed.has(key)) next[key] = value
  }
  return next
}

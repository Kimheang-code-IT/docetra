import type { DocumentTabSchema, FieldOption } from '~/types/docetra/common'
import type { AttributeDataType, RecordAttribute } from '~/types/docetra/configuration'
import { ATTRIBUTE_DATA_TYPES } from '~/types/docetra/configuration'

const statusOptions: FieldOption[] = [
  { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
  { label: 'Disabled', value: 'disabled', labelKey: 'docetra.status.disabled' },
]

export function recordTypeTabs(ctx: {
  attributeCatalog: RecordAttribute[]
  availableAttributeOptions: FieldOption[]
}): DocumentTabSchema[] {
  return [
    {
      id: 'general',
      labelKey: 'docetra.config.tabs.general',
      sections: [{
        id: 'general',
        titleKey: 'docetra.config.tabs.general',
        fields: [
          { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
          { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
          { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2, rows: 2 },
          { key: 'icon', labelKey: 'docetra.common.icon', type: 'icon' },
          { key: 'color', labelKey: 'docetra.common.color', type: 'color' },
          { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusOptions },
        ],
      }],
    },
    {
      id: 'features',
      labelKey: 'docetra.config.tabs.features',
      sections: [{
        id: 'features',
        titleKey: 'docetra.config.tabs.features',
        fields: [
          { key: 'features.allowAttachments', labelKey: 'docetra.config.feature.attachments', type: 'boolean' },
          { key: 'features.allowComments', labelKey: 'docetra.config.feature.comments', type: 'boolean' },
          { key: 'features.allowAssignment', labelKey: 'docetra.config.feature.assignment', type: 'boolean' },
          { key: 'features.allowSharing', labelKey: 'docetra.config.feature.sharing', type: 'boolean' },
          { key: 'features.allowRelatedRecords', labelKey: 'docetra.config.feature.related', type: 'boolean' },
          { key: 'features.enableWorkflow', labelKey: 'docetra.config.feature.workflow', type: 'boolean' },
          { key: 'features.enableDueDate', labelKey: 'docetra.config.feature.dueDate', type: 'boolean' },
          { key: 'features.enableHistory', labelKey: 'docetra.config.feature.history', type: 'boolean' },
          { key: 'features.enableExport', labelKey: 'docetra.config.feature.export', type: 'boolean' },
        ],
      }],
    },
    {
      id: 'numbering',
      labelKey: 'docetra.config.tabs.numbering',
      sections: [{
        id: 'numbering',
        titleKey: 'docetra.config.tabs.numbering',
        fields: [
          { key: 'numbering.prefix', labelKey: 'docetra.config.prefix', type: 'text' },
          { key: 'numbering.sequenceLength', labelKey: 'docetra.config.sequenceLength', type: 'number' },
          { key: 'numbering.includeYear', labelKey: 'docetra.config.includeYear', type: 'boolean' },
          { key: 'numbering.resetYearly', labelKey: 'docetra.config.resetYearly', type: 'boolean' },
          { key: 'numbering', labelKey: 'docetra.config.numberPreview', type: 'numbering-preview', colSpan: 2 },
        ],
      }],
    },
    {
      id: 'attributes',
      labelKey: 'docetra.config.tabs.attributes',
      sections: [{
        id: 'attributes',
        titleKey: 'docetra.config.tabs.attributes',
        fields: [
          {
            key: 'attributes',
            labelKey: 'docetra.config.assignAttribute',
            type: 'assigned-attributes',
            colSpan: 2,
            options: ctx.availableAttributeOptions,
            meta: { catalog: ctx.attributeCatalog },
          },
        ],
      }],
    },
    {
      id: 'workflow',
      labelKey: 'docetra.config.tabs.workflow',
      sections: [{
        id: 'workflow',
        titleKey: 'docetra.config.tabs.workflow',
        fields: [
          { key: '__workflow', labelKey: 'docetra.config.tabs.workflow', type: 'workflow-builder', colSpan: 2 },
        ],
      }],
    },
  ]
}

export function recordAttributeTabs(ctx: {
  showOptions: boolean
  dataType: AttributeDataType
  codeReadOnly: boolean
  visibilityFieldOptions: FieldOption[]
}): DocumentTabSchema[] {
  const dataTypeOptions: FieldOption[] = ATTRIBUTE_DATA_TYPES.map(type => ({
    label: type,
    value: type,
    labelKey: `docetra.config.dataType.${type}`,
  }))

  const tabs: DocumentTabSchema[] = [
    {
      id: 'basic',
      labelKey: 'docetra.config.tabs.basic',
      sections: [{
        id: 'basic',
        titleKey: 'docetra.config.tabs.basic',
        fields: [
          { key: 'label', labelKey: 'docetra.fields.label', type: 'text', required: true },
          { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true, readOnly: ctx.codeReadOnly },
          { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2, rows: 2 },
          { key: 'helpText', labelKey: 'docetra.config.helpText', type: 'text' },
          { key: 'dataType', labelKey: 'docetra.config.dataTypeLabel', type: 'select', options: dataTypeOptions },
          { key: 'placeholder', labelKey: 'docetra.config.placeholder', type: 'text' },
          { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusOptions },
        ],
      }],
    },
    {
      id: 'field',
      labelKey: 'docetra.config.tabs.field',
      sections: [{
        id: 'field',
        titleKey: 'docetra.config.tabs.field',
        fields: [
          { key: 'required', labelKey: 'docetra.fields.required', type: 'boolean' },
          { key: 'unique', labelKey: 'docetra.config.unique', type: 'boolean' },
          { key: 'readOnly', labelKey: 'docetra.config.readOnly', type: 'boolean' },
          { key: 'searchable', labelKey: 'docetra.config.searchable', type: 'boolean' },
          { key: 'filterable', labelKey: 'docetra.config.filterable', type: 'boolean' },
          { key: 'sortable', labelKey: 'docetra.config.sortable', type: 'boolean' },
          { key: 'showInList', labelKey: 'docetra.config.showInList', type: 'boolean' },
        ],
      }],
    },
    {
      id: 'validation',
      labelKey: 'docetra.config.tabs.validation',
      sections: [{
        id: 'validation',
        titleKey: 'docetra.config.tabs.validation',
        fields: [
          {
            key: 'validation',
            labelKey: 'docetra.config.tabs.validation',
            type: 'validation-builder',
            colSpan: 2,
            meta: { dataType: ctx.dataType },
          },
        ],
      }],
    },
  ]

  if (ctx.showOptions) {
    tabs.push({
      id: 'options',
      labelKey: 'docetra.config.tabs.options',
      sections: [{
        id: 'options',
        titleKey: 'docetra.config.tabs.options',
        fields: [
          { key: 'options', labelKey: 'docetra.config.tabs.options', type: 'options-builder', colSpan: 2 },
        ],
      }],
    })
  }

  tabs.push({
    id: 'visibility',
    labelKey: 'docetra.config.tabs.visibility',
    sections: [{
      id: 'visibility',
      titleKey: 'docetra.config.tabs.visibility',
      fields: [
        {
          key: 'visibility',
          labelKey: 'docetra.config.tabs.visibility',
          type: 'visibility-builder',
          colSpan: 2,
          options: ctx.visibilityFieldOptions,
        },
      ],
    }],
  })

  return tabs
}

export function documentTypeTabs(ctx: {
  recordTypeOptions: FieldOption[]
}): DocumentTabSchema[] {
  return [
    {
      id: 'details',
      labelKey: 'docetra.config.tabs.general',
      sections: [{
        id: 'details',
        titleKey: 'docetra.config.tabs.general',
        fields: [
          { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
          { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
          { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2, rows: 2 },
          {
            key: 'direction',
            labelKey: 'docetra.config.direction',
            type: 'select',
            options: [
              { label: 'Incoming', value: 'incoming' },
              { label: 'Outgoing', value: 'outgoing' },
              { label: 'Internal', value: 'internal' },
              { label: 'Both', value: 'both' },
            ],
          },
          {
            key: 'relatedRecordTypeId',
            labelKey: 'docetra.config.relatedRecordType',
            type: 'select',
            options: ctx.recordTypeOptions,
          },
          {
            key: 'defaultPriority',
            labelKey: 'docetra.config.defaultPriority',
            type: 'select',
            options: [
              { label: 'Low', value: 'low' },
              { label: 'Normal', value: 'normal' },
              { label: 'High', value: 'high' },
              { label: 'Urgent', value: 'urgent' },
            ],
          },
          {
            key: 'defaultConfidentiality',
            labelKey: 'docetra.config.defaultConfidentiality',
            type: 'select',
            options: [
              { label: 'Public', value: 'public' },
              { label: 'Internal', value: 'internal' },
              { label: 'Confidential', value: 'confidential' },
              { label: 'Restricted', value: 'restricted' },
            ],
          },
          {
            key: 'allowedFileTypes',
            labelKey: 'docetra.config.allowedExtensions',
            type: 'csv-list',
            helpKey: 'docetra.config.extensionsHelp',
          },
          { key: 'maxFileSizeMb', labelKey: 'docetra.config.maxFileSizeMb', type: 'number' },
          { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusOptions },
        ],
      }],
    },
  ]
}

<script setup lang="ts">
import type { AttributeDataType, AttributeOption, RecordAttribute } from '~/types/docetra/configuration'
import type { DocumentFieldSchema, FieldType } from '~/types/docetra/common'

const props = defineProps<{
  attribute: Pick<
    RecordAttribute,
    'label' | 'code' | 'dataType' | 'placeholder' | 'required' | 'readOnly' | 'helpText' | 'options' | 'defaultValue'
  >
}>()

const previewValue = ref<unknown>(props.attribute.defaultValue ?? '')

watch(
  () => props.attribute.code,
  () => {
    previewValue.value = props.attribute.defaultValue ?? ''
  },
)

function mapDataType(type: AttributeDataType): FieldType {
  switch (type) {
    case 'long_text':
      return 'textarea'
    case 'rich_text':
      return 'textarea'
    case 'integer':
    case 'decimal':
    case 'currency':
      return 'number'
    case 'boolean':
      return 'boolean'
    case 'date':
      return 'date'
    case 'datetime':
    case 'time':
      return 'datetime'
    case 'select':
    case 'radio':
      return 'select'
    case 'multi_select':
    case 'checkbox_group':
      return 'multiselect'
    case 'organization':
      return 'organization'
    case 'officer':
    case 'user':
      return 'officer'
    case 'record_reference':
      return 'relation'
    case 'file':
    case 'image':
      return 'file'
    case 'url':
      return 'url'
    default:
      return 'text'
  }
}

const field = computed<DocumentFieldSchema>(() => ({
  key: props.attribute.code || 'preview',
  labelKey: props.attribute.label || 'Preview',
  type: mapDataType(props.attribute.dataType),
  required: props.attribute.required,
  readOnly: props.attribute.readOnly,
  options: (props.attribute.options || [])
    .filter((o: AttributeOption) => o.active)
    .map(o => ({ label: o.label, value: o.value })),
  placeholderKey: props.attribute.placeholder,
  helpKey: props.attribute.helpText,
}))
</script>

<template>
  <div class="rounded-lg border border-default bg-elevated/30 p-4">
    <p class="mb-3 text-xs font-medium uppercase tracking-wide text-muted">
      {{ $t('docetra.config.fieldPreview') }}
    </p>
    <DocumentAppDynamicFieldRenderer
      v-model="previewValue"
      :field="field"
      :disabled="attribute.readOnly"
    />
    <p v-if="attribute.dataType === 'rich_text'" class="mt-2 text-xs text-muted">
      {{ $t('docetra.config.richTextPreviewHint') }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { RecordType, RecordTypeAttribute } from '~/types/docetra/configuration'
import type { DocumentFieldSchema, FieldType } from '~/types/docetra/common'

const props = defineProps<{
  recordType: Pick<RecordType, 'name' | 'attributes'>
}>()

const values = reactive<Record<string, unknown>>({})

function mapDataType(type: RecordTypeAttribute['dataType']): FieldType {
  switch (type) {
    case 'long_text':
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

const ordered = computed(() =>
  [...props.recordType.attributes]
    .filter(a => a.visible)
    .sort((a, b) => a.order - b.order),
)

const sections = computed(() => {
  const map = new Map<string, RecordTypeAttribute[]>()
  for (const attr of ordered.value) {
    const key = attr.section || 'General'
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(attr)
  }
  return [...map.entries()]
})

function toField(attr: RecordTypeAttribute): DocumentFieldSchema {
  return {
    key: attr.attributeCode,
    labelKey: attr.attributeLabel,
    type: mapDataType(attr.dataType),
    required: attr.required,
    readOnly: attr.readOnly,
  }
}
</script>

<template>
  <div class="space-y-4 rounded-lg border border-default bg-elevated/30 p-4">
    <div>
      <h4 class="text-sm font-semibold text-highlighted">
        {{ recordType.name || $t('docetra.config.formPreview') }}
      </h4>
      <p class="text-xs text-muted">
        {{ $t('docetra.config.formPreviewHelp') }}
      </p>
    </div>

    <div v-if="!ordered.length" class="py-8 text-center text-sm text-muted">
      {{ $t('docetra.config.noAssignedAttributes') }}
    </div>

    <section
      v-for="[section, attrs] in sections"
      :key="section"
      class="space-y-3"
    >
      <h5 class="text-xs font-semibold uppercase tracking-wide text-muted">
        {{ section }}
      </h5>
      <div class="grid gap-3 md:grid-cols-2">
        <DocumentAppDynamicFieldRenderer
          v-for="attr in attrs"
          :key="attr.attributeId"
          v-model="values[attr.attributeCode]"
          :field="toField(attr)"
          :disabled="attr.readOnly"
        />
      </div>
    </section>
  </div>
</template>

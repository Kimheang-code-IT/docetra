<script setup lang="ts">
import type { DocumentTabSchema } from '~/types/docetra/common'

const props = withDefaults(defineProps<{
  tabs: DocumentTabSchema[]
  activeTab: string
  fieldValue: (key: string) => unknown
  setFieldValue: (key: string, value: unknown) => void
  readOnly?: boolean
  /** Force wider shell even without dense field types. */
  wide?: boolean
}>(), {
  readOnly: false,
  wide: false,
})

const emit = defineEmits<{
  'update:activeTab': [string]
}>()

const wideForm = computed(() =>
  props.wide
  || props.tabs.some(tab =>
    tab.sections.some(section =>
      section.fields.some(field =>
        field.type === 'telegram-destinations'
        || field.type === 'notification-rules'
        || field.type === 'card-fields-editor',
      ),
    ),
  ),
)

function isFullWidthField(field: DocumentTabSchema['sections'][0]['fields'][0]) {
  return field.colSpan === 2
    || field.type === 'textarea'
    || field.type === 'image'
    || field.type === 'permission-matrix'
    || field.type === 'telegram-destinations'
    || field.type === 'notification-rules'
    || field.type === 'connection-status'
    || field.type === 'alert'
    || field.type === 'assigned-attributes'
    || field.type === 'workflow-builder'
    || field.type === 'numbering-preview'
    || field.type === 'validation-builder'
    || field.type === 'options-builder'
    || field.type === 'visibility-builder'
    || field.type === 'card-fields-editor'
}
</script>

<template>
  <div class="min-w-0 w-full flex-1">
    <div
      v-if="tabs.length > 1"
      class="sticky top-0 z-10 w-full border-b border-default bg-default"
    >
      <UTabs
        :model-value="activeTab"
        :items="tabs.map(tab => ({ label: $t(tab.labelKey), value: tab.id }))"
        :content="false"
        color="neutral"
        variant="link"
        size="md"
        class="w-full"
        :ui="{
          root: 'w-full gap-0',
          list: 'w-full gap-0 rounded-none bg-transparent border-b-0 px-4 sm:px-6 lg:px-10',
          trigger: [
            'grow-0 shrink-0 justify-center rounded-none px-4 pb-2.5 pt-2.5',
            'font-normal text-muted',
            'data-[state=active]:font-medium data-[state=active]:text-highlighted',
          ].join(' '),
          indicator: 'h-0.5 rounded-none bg-highlighted',
        }"
        @update:model-value="(v: string | number) => emit('update:activeTab', String(v))"
      />
    </div>

    <DocumentAppDocumentContentShell :wide="wideForm">
      <template v-for="tab in tabs" :key="tab.id">
        <div v-show="activeTab === tab.id || tabs.length === 1" class="space-y-8 py-6">
          <section
            v-for="(section, sectionIndex) in tab.sections"
            :key="section.id"
            class="space-y-4"
            :class="sectionIndex > 0 ? 'border-t border-default pt-6' : ''"
          >
            <div v-if="section.title || section.titleKey || section.description || section.descriptionKey">
              <h3 v-if="section.title || section.titleKey" class="text-sm font-medium text-highlighted">
                {{ section.title || $t(section.titleKey!) }}
              </h3>
              <p v-if="section.description || section.descriptionKey" class="mt-1 text-xs text-muted">
                {{ section.description || $t(section.descriptionKey!) }}
              </p>
            </div>

            <div class="grid grid-cols-1 gap-x-5 gap-y-5 sm:grid-cols-2">
              <div
                v-for="field in section.fields"
                :key="field.key"
                :class="isFullWidthField(field) ? 'sm:col-span-2' : ''"
              >
                <DocumentAppDynamicFieldRenderer
                  :field="field"
                  :model-value="fieldValue(field.key)"
                  :disabled="readOnly"
                  @update:model-value="(v) => setFieldValue(field.key, v)"
                />
              </div>
            </div>
          </section>
        </div>
      </template>
    </DocumentAppDocumentContentShell>
  </div>
</template>

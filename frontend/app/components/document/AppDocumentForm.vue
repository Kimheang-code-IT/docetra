<script setup lang="ts">
import type { DocumentTabSchema } from '~/types/docetra/common'

const props = defineProps<{
  tabs: DocumentTabSchema[]
  activeTab: string
  fieldValue: (key: string) => unknown
  setFieldValue: (key: string, value: unknown) => void
  readOnly?: boolean
}>()

const emit = defineEmits<{
  'update:activeTab': [string]
}>()

const wideForm = computed(() =>
  props.tabs.some(tab =>
    tab.sections.some(section =>
      section.fields.some(field => field.type === 'permission-matrix'),
    ),
  ),
)
</script>

<template>
  <div class="min-w-0 w-full flex-1">
    <div class="sticky top-0 z-10 w-full border-b border-default bg-default">
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
          list: 'w-full gap-0 rounded-none bg-transparent border-b-0 px-4 sm:px-6',
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

    <div
      class="mx-auto w-full px-4 sm:px-6"
      :class="wideForm ? 'max-w-6xl xl:max-w-7xl' : 'max-w-3xl xl:max-w-4xl'"
    >
      <template v-for="tab in tabs" :key="tab.id">
        <div v-show="activeTab === tab.id" class="space-y-8 py-6">
          <section
            v-for="(section, sectionIndex) in tab.sections"
            :key="section.id"
            class="space-y-4"
            :class="sectionIndex > 0 ? 'border-t border-default pt-6' : ''"
          >
            <div v-if="section.titleKey || section.descriptionKey">
              <h3 class="text-sm font-medium text-highlighted">
                {{ $t(section.titleKey) }}
              </h3>
              <p v-if="section.descriptionKey" class="mt-1 text-xs text-muted">
                {{ $t(section.descriptionKey) }}
              </p>
            </div>

            <div class="grid grid-cols-1 gap-x-8 gap-y-5 md:grid-cols-2">
              <div
                v-for="field in section.fields"
                :key="field.key"
                :class="[
                  field.colSpan === 2
                    || field.type === 'textarea'
                    || field.type === 'permission-matrix'
                    ? 'md:col-span-2'
                    : '',
                ]"
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
    </div>
  </div>
</template>

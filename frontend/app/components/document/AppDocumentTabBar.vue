<script setup lang="ts">
import type { DocumentTabSchema } from '~/types/docetra/common'

const props = defineProps<{
  tabs: DocumentTabSchema[]
  activeTab: string
}>()

const emit = defineEmits<{
  'update:activeTab': [string]
}>()

const { t } = useI18n()

const tabItems = computed(() =>
  props.tabs.map(tab => ({ label: t(tab.labelKey), value: tab.id })),
)
</script>

<template>
  <div
    v-if="tabs.length > 1"
    class="w-full shrink-0 border-b border-default bg-default"
  >
    <div class="w-full touch-pan-x overflow-x-auto overflow-y-hidden overscroll-x-contain [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <UTabs
        :model-value="activeTab"
        :items="tabItems"
        :content="false"
        color="neutral"
        variant="link"
        size="md"
        class="min-w-max"
        :ui="{
          root: 'min-w-max gap-0',
          list: 'min-w-max w-max gap-0 rounded-none bg-transparent border-b-0 px-4 sm:px-6 lg:px-10',
          trigger: [
            'grow-0 shrink-0 justify-center whitespace-nowrap rounded-none px-4 pb-2.5 pt-2.5',
            'font-normal text-muted',
            'data-[state=active]:font-medium data-[state=active]:text-highlighted',
          ].join(' '),
          indicator: 'h-0.5 rounded-none bg-highlighted',
        }"
        @update:model-value="(value: string | number) => emit('update:activeTab', String(value))"
      />
    </div>
  </div>
</template>

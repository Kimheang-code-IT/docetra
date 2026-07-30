<script setup lang="ts">
import { DateFormatter, getLocalTimeZone } from '@internationalized/date'
import type { AnyChartDefinition, PageChartPanel } from '~/types/page-chart'
import { useChartDuration } from '~/composables/chart/useChartDuration'

const open = defineModel<boolean>('open')

const props = withDefaults(defineProps<{
  panels?: PageChartPanel[]
  definitions?: AnyChartDefinition[]
  sourceRows?: unknown[]
  getRowDate?: (row: unknown) => string | undefined
}>(), {
  panels: () => [],
  definitions: () => [],
  sourceRows: () => [],
})

const { t } = useI18n()
const activeChartId = ref('')
const chartPanelRef = ref<{ downloadChart?: () => void; isEmpty?: { value: boolean } } | null>(null)

const df = new DateFormatter('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

const useDefinitions = computed(() => props.definitions.length > 0 && Boolean(props.getRowDate))

const durationSource = computed(() => (
  useDefinitions.value ? props.sourceRows : []
))

const {
  dateRange,
  durationRows,
  resetRange,
} = useChartDuration(
  durationSource,
  (row) => props.getRowDate?.(row),
)

const tabItems = computed(() => {
  if (useDefinitions.value) {
    return props.definitions.map((def) => ({
      id: def.id,
      label: def.title(durationRows.value as never[], t),
    }))
  }
  return props.panels.map((panel) => ({
    id: panel.id,
    label: panel.title,
  }))
})

const activeDefinition = computed(() => (
  useDefinitions.value
    ? props.definitions.find((def) => def.id === activeChartId.value)
    : undefined
))

const activePanel = computed(() => (
  !useDefinitions.value
    ? props.panels.find((panel) => panel.id === activeChartId.value)
    : undefined
))

const canDownload = computed(() => Boolean(activeDefinition.value || activePanel.value?.option))

watch(tabItems, (items) => {
  if (!items.length) {
    activeChartId.value = ''
    return
  }
  if (!items.some((item) => item.id === activeChartId.value)) {
    activeChartId.value = items[0]!.id
  }
}, { immediate: true })

watch(open, (isOpen) => {
  if (isOpen && tabItems.value[0]) {
    activeChartId.value = tabItems.value[0].id
  }
})

function downloadActiveChart() {
  chartPanelRef.value?.downloadChart?.()
}

function selectChart(id: string) {
  activeChartId.value = id
}

function closeModal() {
  open.value = false
}
</script>

<template>
  <UModal
    v-model:open="open"
    fullscreen
    :ui="{
      content: 'bg-default dark:bg-[#18191a] flex flex-col h-dvh max-h-dvh overflow-hidden',
      body: 'flex-1 min-h-0 overflow-hidden p-0 bg-default dark:bg-[#18191a] flex flex-col',
      header: 'bg-default dark:bg-[#18191a] border-b border-default shrink-0',
    }"
  >
    <template #header>
      <div class="flex items-center justify-between gap-3 w-full px-3 py-2 min-w-0">
        <div
          v-if="tabItems.length"
          class="flex gap-1 overflow-x-auto min-w-0 flex-1"
        >
          <UButton
            v-for="tab in tabItems"
            :key="tab.id"
            :variant="activeChartId === tab.id ? 'soft' : 'ghost'"
            color="primary"
            size="md"
            class="shrink-0 text-base sm:text-lg font-semibold px-3 sm:px-4"
            @click="selectChart(tab.id)"
          >
            {{ tab.label }}
          </UButton>
        </div>
        <div v-else class="flex-1" />

        <div class="flex items-center gap-2 shrink-0">
          <UPopover v-if="useDefinitions" :content="{ align: 'end' }">
            <UButton
              color="neutral"
              variant="subtle"
              icon="i-lucide-calendar"
              trailing-icon="i-lucide-chevron-down"
              size="sm"
              class="shrink-0 font-normal"
            >
              <span class="hidden sm:inline-flex items-center gap-1 ml-1">
                <template v-if="dateRange.start">
                  <template v-if="dateRange.end">
                    <span class="text-xs opacity-70">{{ df.format(dateRange.start.toDate(getLocalTimeZone())) }}</span>
                    <span class="mx-1 text-primary">→</span>
                    <span class="text-xs font-bold">{{ df.format(dateRange.end.toDate(getLocalTimeZone())) }}</span>
                  </template>
                  <template v-else>
                    {{ df.format(dateRange.start.toDate(getLocalTimeZone())) }}
                  </template>
                </template>
                <template v-else>
                  {{ $t('components.pickDate') }}
                </template>
              </span>
            </UButton>

            <template #content>
              <div class="flex flex-col bg-background rounded-lg overflow-hidden min-w-[200px]">
                <UCalendar
                  v-model="dateRange"
                  class="p-2"
                  :number-of-months="1"
                  range
                />
                <div class="p-3 bg-muted/20 border-t flex justify-end">
                  <UButton
                    :label="$t('components.clear')"
                    size="xs"
                    variant="ghost"
                    color="neutral"
                    icon="i-lucide-rotate-ccw"
                    @click="resetRange"
                  />
                </div>
              </div>
            </template>
          </UPopover>

          <UButton
            v-if="canDownload"
            color="neutral"
            variant="outline"
            size="sm"
            icon="i-lucide-download"
            class="shrink-0"
            :aria-label="$t('components.downloadChart')"
            @click="downloadActiveChart"
          />

          <UButton
            icon="i-lucide-x"
            color="neutral"
            variant="ghost"
            class="shrink-0"
            @click="closeModal"
          />
        </div>
      </div>
    </template>

    <template #body>
      <div class="flex flex-col flex-1 min-h-0 h-full w-full p-2 sm:p-3 bg-default dark:bg-[#18191a]">
        <ChartAppChartPanel
          v-if="activeDefinition"
          :key="activeDefinition.id"
          ref="chartPanelRef"
          :definition="activeDefinition"
          :source-rows="durationRows"
          :get-row-date="getRowDate"
          height="100%"
          :download-filename="activeDefinition.id"
          class="flex-1 min-h-0 w-full"
        />

        <ChartAppChartPanel
          v-else-if="activePanel"
          :key="activePanel.id"
          ref="chartPanelRef"
          :option="activePanel.option"
          :empty="!activePanel.option"
          height="100%"
          :download-filename="activePanel.id"
          class="flex-1 min-h-0 w-full"
        />
      </div>
    </template>
  </UModal>
</template>

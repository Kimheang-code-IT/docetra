<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { DateFormatter, getLocalTimeZone, parseDate } from '@internationalized/date'
import type { DateValue } from '@internationalized/date'
import { exportToCSV } from '~/utils/helpers/common'

/**
 * AppExport — Universal export dialog
 * Accepts any data array, filters by date range, and exports as CSV or JSON.
 *
 * Usage:
 *   <CommonAppExport v-model:open="isExportOpen" :data="filteredEntries" filename="revenue-export" date-field="paymentDate" />
 */

const open = defineModel<boolean>('open')

interface Props {
  data?: unknown[]
  filename?: string
  /** The key in each data row that holds the date string (e.g. "paymentDate", "date") */
  dateField?: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  filename: 'export',
  dateField: '',
  title: '',
})

const { t, locale } = useI18n()
const { formattedRange } = useGlobalFilter()

const df = computed(() => new DateFormatter(locale.value, { month: 'short', day: 'numeric', year: 'numeric' }))

// Local export date range — synced from global filter when dialog opens
const localRange = ref<{
  start?: DateValue
  end?: DateValue
}>({
  start: undefined as DateValue | undefined,
  end: undefined as DateValue | undefined,
})

// Sync localRange when dialog opens
watch(open, (val) => {
  if (val) {
    localRange.value = {
      start: formattedRange.value.start ? parseDate(formattedRange.value.start) : undefined,
      end: formattedRange.value.end ? parseDate(formattedRange.value.end) : undefined,
    }
  }
})

const isLoading = ref(false)

// Filtered data by local date range
const exportData = computed(() => {
  if (!props.data.length) return []
  if (!props.dateField || (!localRange.value.start && !localRange.value.end)) {
    return props.data
  }
  const tz = getLocalTimeZone()
  const start = localRange.value.start?.toDate(tz)
  const end = localRange.value.end?.toDate(tz)

  return props.data.filter(row => {
    const raw = (row as Record<string, unknown>)[props.dateField!]
    if (!raw) return true
    const rowDate = new Date(String(raw))
    if (start && rowDate < start) return false
    if (end && rowDate > end) return false
    return true
  })
})

const recordCount = computed(() => exportData.value.length)

const dateRangeLabel = computed(() => {
  const s = localRange.value.start
  const e = localRange.value.end
  const tz = getLocalTimeZone()
  if (s && e) return `${df.value.format(s.toDate(tz))} → ${df.value.format(e.toDate(tz))}`
  if (s) return `${t('components.from')} ${df.value.format(s.toDate(tz))}`
  return t('components.allDates')
})

function resetRange() {
  localRange.value = { start: undefined, end: undefined }
}

async function handleExport() {
  if (!exportData.value.length) return
  isLoading.value = true

  // Simulate slight async delay for UX
  await new Promise(r => setTimeout(r, 400))

  const name = `${props.filename}_${new Date().toISOString().slice(0, 10)}`


  exportToCSV(exportData.value, `${name}.csv`)

  isLoading.value = false
  open.value = false
}

function onClose() {
  open.value = false
}
</script>

<template>
  <UModal v-model:open="open" :dismissible="false" :ui="{ content: 'max-w-md w-[95vw] sm:w-full', header: 'border-none p-0' }">
    <!-- Header -->
    <template #header>
      <div class="flex items-center justify-between w-full px-4 pt-4">
        <div class="flex items-center gap-2.5">
          <div>
            <h3 class="text-lg font-bold text-highlighted tracking-tight leading-tight">
              {{ title || $t('components.exportData') }}
            </h3>
          </div>
        </div>
      </div>
    </template>

    <!-- Body -->
    <template #body>
      <div class="px-4 space-y-4">
        <!-- Date Range Picker -->
        <div class="space-y-2">
          <div class="border border-border rounded-xl overflow-hidden bg-muted/10">
            <UCalendar
              :model-value="(localRange as any)"
              class="p-2 w-full"
              :number-of-months="1"
              range
              @update:model-value="(value: any) => { localRange = value }"
            />
            <div class="px-3 pb-3 pt-1 border-t border-border flex items-center justify-between gap-2">
              <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span class="i-lucide-calendar-range size-3.5" />
                <span class="">{{ dateRangeLabel }}</span>
              </div>
              <UButton size="xs" variant="ghost" color="neutral" icon="i-lucide-rotate-ccw"
                :label="$t('components.reset')" @click="resetRange" />
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Footer -->
    <template #footer>
      <div class="flex items-center justify-end gap-2 w-full">
        <UButton :label="$t('components.cancel')" color="neutral" variant="soft" size="md" class="font-semibold"
          @click="onClose" />
        <UButton :label="$t('components.exportNow')" color="primary" variant="solid" size="md" icon="i-lucide-download"
          class="font-semibold" :loading="isLoading" :disabled="recordCount === 0" @click="handleExport" />
      </div>
    </template>
  </UModal>
</template>

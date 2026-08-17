<script setup lang="ts">
import type { DateValue } from '@internationalized/date'
import type { DatePickerGranularity } from '~/utils/date-picker'
import {
  isDateTimeGranularity,
  parsePickerValue,
  serializePickerValue,
  datePickerPopoverContent,
} from '~/utils/date-picker'
import { getFilterDateUi, isFilterValueActive } from '~/utils/filter/select-ui'

const start = defineModel<string>('start', { default: '' })
const end = defineModel<string>('end', { default: '' })

const props = withDefaults(defineProps<{
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  disabled?: boolean
  granularity?: DatePickerGranularity
  label?: string
  placeholder?: string
  class?: string
  /** Render without extra mobile-only duplicate controls. */
  inline?: boolean
}>(), {
  size: 'sm',
  granularity: 'minute',
})

const { t } = useI18n()

const inputDate = useTemplateRef<{ inputsRef?: Array<{ $el?: HTMLElement }> } | null>('inputDate')
const pickerAnchor = useTemplateRef<HTMLElement | null>('pickerAnchor')

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))

const hasActiveFilter = computed(() =>
  isFilterValueActive(start.value) || isFilterValueActive(end.value),
)

const dateUi = computed(() => getFilterDateUi(hasActiveFilter.value, {
  isDateTime: isDateTime.value,
  isRange: true,
  fitContent: true,
}))

const containerClass = computed(() => {
  if (props.inline) return 'w-full min-w-0'
  return 'w-auto max-w-full'
})

/** Shared with UInputDate + UCalendar in popover (Nuxt UI pattern). */
const dateRangeValue = computed({
  get() {
    const startValue = parsePickerValue(start.value, isDateTime.value)
    const endValue = parsePickerValue(end.value, isDateTime.value)
    if (!startValue && !endValue) return undefined
    return {
      start: startValue ?? endValue!,
      end: endValue ?? startValue!,
    }
  },
  set(value: { start?: DateValue, end?: DateValue } | null | undefined) {
    if (!value?.start && !value?.end) {
      start.value = ''
      end.value = ''
      return
    }
    start.value = value.start ? serializePickerValue(value.start) : ''
    end.value = value.end ? serializePickerValue(value.end) : ''
  },
})

function clearFilter() {
  start.value = ''
  end.value = ''
}
</script>

<template>
  <div
    class="app-date-range-filter inline-flex items-center gap-1.5"
    :class="[props.class, containerClass]"
  >
    <div ref="pickerAnchor" class="relative min-w-0 w-auto max-w-full">
      <UInputDate
        ref="inputDate"
        v-model="dateRangeValue"
        range
        fixed
        :granularity="granularity"
        :disabled="disabled"
        :size="size"
        color="neutral"
        variant="outline"
        class="w-auto max-w-full shrink-0"
        :ui="dateUi"
        :aria-label="label || t('docetra.fields.meetingDate')"
      >
        <template #trailing>
          <UPopover
            :reference="pickerAnchor ?? inputDate?.inputsRef?.[0]?.$el"
            :content="datePickerPopoverContent"
          >
          <UButton
            color="neutral"
            variant="link"
            :size="size === 'xs' || size === 'sm' ? 'sm' : size"
            :icon="isDateTime ? 'i-lucide-calendar-clock' : 'i-lucide-calendar'"
            :aria-label="label || t('docetra.fields.meetingDate')"
            class="shrink-0 px-0"
            :disabled="disabled"
          />

          <template #content>
            <CommonAppDatePickerPopover
              v-model:range-value="dateRangeValue"
              mode="range"
              :granularity="granularity"
              :disabled="disabled"
            />
          </template>
        </UPopover>
      </template>
    </UInputDate>
    </div>

    <UButton
      v-if="hasActiveFilter"
      icon="i-lucide-x"
      color="neutral"
      variant="ghost"
      size="xs"
      square
      class="shrink-0"
      :aria-label="t('docetra.common.clear')"
      :title="t('docetra.common.clear')"
      @click="clearFilter"
    />
  </div>
</template>

<style scoped>
.app-date-range-filter :deep([data-slot="base"]) {
  width: fit-content;
  max-width: 100%;
  overflow-x: auto;
  scrollbar-width: none;
}

.app-date-range-filter :deep([data-slot="base"]::-webkit-scrollbar) {
  display: none;
}
</style>

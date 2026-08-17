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

const props = withDefaults(defineProps<{
  modelValue?: string | null
  disabled?: boolean
  required?: boolean
  granularity?: DatePickerGranularity
  color?: 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral'
  variant?: 'outline' | 'soft' | 'subtle' | 'ghost' | 'none'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  class?: string
}>(), {
  granularity: 'day',
  color: 'neutral',
  variant: 'soft',
  size: 'md',
})

const emit = defineEmits<{
  'update:modelValue': [string]
}>()

const inputDate = useTemplateRef<{ inputsRef?: Array<{ $el?: HTMLElement }> } | null>('inputDate')
const pickerAnchor = useTemplateRef<HTMLElement | null>('pickerAnchor')

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))
const isActive = computed(() => isFilterValueActive(props.modelValue))
const dateUi = computed(() => getFilterDateUi(isActive.value, {
  isDateTime: isDateTime.value,
  isRange: false,
}))

const pickerIcon = computed(() =>
  isDateTime.value ? 'i-lucide-calendar-clock' : 'i-lucide-calendar',
)

/** Shared with UInputDate + UCalendar in popover (Nuxt UI pattern). */
const dateValue = computed({
  get: () => parsePickerValue(props.modelValue, isDateTime.value),
  set: (value: DateValue | null | undefined) => {
    emit('update:modelValue', serializePickerValue(value))
  },
})
</script>

<template>
  <div
    ref="pickerAnchor"
    class="app-input-date relative min-w-0"
    :class="[props.class || 'w-full', isDateTime ? 'app-input-date--datetime' : '']"
  >
    <UInputDate
      ref="inputDate"
      v-model="dateValue"
      fixed
      :granularity="granularity"
      :disabled="disabled"
      :required="required"
      :color="color"
      :variant="variant"
      :size="size"
      class="w-full min-w-0"
      :ui="dateUi"
    />

    <div class="pointer-events-none absolute inset-y-0 end-0 z-10 flex items-center pe-1.5">
      <UPopover
        :reference="pickerAnchor ?? inputDate?.inputsRef?.[0]?.$el"
        :content="datePickerPopoverContent"
      >
        <UButton
          color="neutral"
          variant="ghost"
          size="xs"
          square
          :icon="pickerIcon"
          class="pointer-events-auto size-7 text-muted hover:text-highlighted"
          :aria-label="isDateTime ? 'Select date and time' : 'Select a date'"
          :disabled="disabled"
        />

        <template #content>
          <CommonAppDatePickerPopover
            v-model="dateValue"
            mode="single"
            :granularity="granularity"
            :disabled="disabled"
          />
        </template>
      </UPopover>
    </div>
  </div>
</template>

<style scoped>
.app-input-date :deep([data-slot="base"]) {
  width: 100%;
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  scrollbar-width: none;
}

.app-input-date--datetime :deep([data-slot="base"]) {
  padding-inline-end: 2.75rem;
}

.app-input-date :deep([data-slot="base"]::-webkit-scrollbar) {
  display: none;
}
</style>

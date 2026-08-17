<script setup lang="ts">
import type { DateValue } from '@internationalized/date'
import type { DatePickerGranularity } from '~/utils/date-picker'
import {
  isDateTimeGranularity,
  parsePickerValue,
  serializePickerValue,
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

const isDateTime = computed(() => isDateTimeGranularity(props.granularity))
const isActive = computed(() => isFilterValueActive(props.modelValue))
const dateUi = computed(() => getFilterDateUi(isActive.value, {
  isDateTime: isDateTime.value,
  isRange: false,
}))

/** Shared with UInputDate + UCalendar in popover (Nuxt UI pattern). */
const dateValue = computed({
  get: () => parsePickerValue(props.modelValue, isDateTime.value),
  set: (value: DateValue | null | undefined) => {
    emit('update:modelValue', serializePickerValue(value))
  },
})
</script>

<template>
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
    :class="props.class || 'w-full'"
    :ui="dateUi"
  >
    <template #trailing>
      <UPopover :reference="inputDate?.inputsRef?.[0]?.$el">
        <UButton
          color="neutral"
          variant="link"
          size="sm"
          :icon="isDateTime ? 'i-lucide-calendar-clock' : 'i-lucide-calendar'"
          :aria-label="isDateTime ? 'Select date and time' : 'Select a date'"
          class="shrink-0 px-0"
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
    </template>
  </UInputDate>
</template>

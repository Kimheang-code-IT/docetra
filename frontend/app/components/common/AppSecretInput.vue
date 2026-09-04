<script setup lang="ts">
import { FORM_CONTROL } from '~/utils/form-field-ui'

const props = withDefaults(defineProps<{
  modelValue?: string
  label?: string
  labelKey?: string
  placeholder?: string
  help?: string
  helpKey?: string
  required?: boolean
  disabled?: boolean
  autocomplete?: string
  /** Skip UFormField when the parent already provides label/help. */
  embedded?: boolean
}>(), {
  modelValue: '',
  autocomplete: 'new-password',
  required: false,
  disabled: false,
  embedded: false,
})

const emit = defineEmits<{
  'update:modelValue': [string]
}>()

const { t, te } = useI18n()
const revealed = ref(false)

const labelText = computed(() => {
  if (props.label) return props.label
  if (props.labelKey && te(props.labelKey)) return t(props.labelKey)
  return ''
})

const helpText = computed(() => {
  if (props.help) return props.help
  if (props.helpKey && te(props.helpKey)) return t(props.helpKey)
  return ''
})

const value = computed({
  get: () => props.modelValue ?? '',
  set: (v: string) => emit('update:modelValue', v),
})

const placeholderText = computed(() => {
  if (props.placeholder?.trim()) return props.placeholder.trim()
  if (labelText.value) return t('docetra.fields.placeholderEnter', { label: labelText.value })
  return t('docetra.fields.placeholderEnter', { label: t('docetra.fields.value') })
})
</script>

<template>
  <UFormField
    :label="embedded ? undefined : labelText"
    :required="embedded ? undefined : required"
    :hint="embedded ? undefined : (helpText || undefined)"
  >
    <UInput
      v-model="value"
      :type="revealed ? 'text' : 'password'"
      :placeholder="placeholderText"
      :disabled="disabled"
      :autocomplete="autocomplete"
      class="w-full"
      :color="FORM_CONTROL.color"
      :variant="FORM_CONTROL.variant"
      :size="FORM_CONTROL.size"
      :ui="{ trailing: 'pe-1' }"
    >
      <template #trailing>
        <UButton
          :icon="revealed ? 'i-lucide-eye-off' : 'i-lucide-eye'"
          color="neutral"
          variant="link"
          size="sm"
          :aria-label="revealed ? t('docetra.common.hideSecret') : t('docetra.common.showSecret')"
          :disabled="disabled"
          @click="revealed = !revealed"
        />
      </template>
    </UInput>
  </UFormField>
</template>

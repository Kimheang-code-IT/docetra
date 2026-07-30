<script setup lang="ts">
import { computed } from 'vue'

const open = defineModel<boolean>('open')

const props = withDefaults(defineProps<{
  title?: string
  description?: string | string[]
  icon?: string
  submitLabel?: string
  cancelLabel?: string
  type?: 'primary' | 'error' | 'warning' | 'neutral'
  loading?: boolean
  dismissible?: boolean
}>(), {
  type: 'primary',
  loading: false,
  dismissible: false,
})

const emit = defineEmits<{
  submit: []
  cancel: []
}>()

const { t } = useI18n()

const typeConfig = computed(() => {
  switch (props.type) {
    case 'error':
      return { color: 'error' as const, icon: props.icon || 'i-lucide-trash-2', text: 'text-error-600 dark:text-error-400' }
    case 'warning':
      return { color: 'warning' as const, icon: props.icon || 'i-lucide-alert-triangle', text: 'text-warning-600 dark:text-warning-400' }
    case 'neutral':
      return { color: 'neutral' as const, icon: props.icon || 'i-lucide-info', text: 'text-muted-foreground' }
    default:
      return { color: 'primary' as const, icon: props.icon || 'i-lucide-check-circle', text: 'text-primary-600 dark:text-primary-400' }
  }
})

const descriptionLines = computed(() => {
  const value = props.description || t('components.confirmDesc')
  if (Array.isArray(value)) return value.filter(Boolean)
  return value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
})

const leadDescription = computed(() => {
  const first = descriptionLines.value[0]
  return first?.replace(/^[-•]\s*/, '') || ''
})

const detailDescriptions = computed(() =>
  descriptionLines.value.slice(1).map((line) => line.replace(/^[-•]\s*/, '')),
)

function splitBoldText(text: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).filter(Boolean).map((part) => ({
    text: part.startsWith('**') && part.endsWith('**') ? part.slice(2, -2) : part,
    bold: part.startsWith('**') && part.endsWith('**'),
  }))
}

function onCancel() {
  if (props.loading) return
  open.value = false
  emit('cancel')
}

function onSubmit() {
  if (props.loading) return
  emit('submit')
}
</script>

<template>
  <UModal
    v-model:open="open"
    :dismissible="dismissible && !loading"
    :ui="{ content: 'max-w-md w-[95vw] sm:w-full transition-all duration-200', header: 'border-none p-0' }"
  >
    <template #header>
      <div class="flex items-center justify-between w-full px-4 pt-4">
        <div class="flex items-center gap-2 sm:gap-3 min-w-0">
          <UIcon :name="typeConfig.icon" :class="['size-5 sm:size-6 shrink-0', typeConfig.text]" />
          <h3 class="text-sm sm:text-base font-bold text-highlighted tracking-tight leading-tight truncate">
            {{ title || $t('components.confirmAction') }}
          </h3>
        </div>
        <UButton
          v-if="!loading"
          icon="i-lucide-x"
          color="neutral"
          variant="ghost"
          size="sm"
          @click="onCancel"
        />
      </div>
    </template>

    <template #body>
      <div class="space-y-4 pb-2 px-4">
        <p v-if="description || !$slots.default" class="text-sm text-muted-foreground font-medium leading-relaxed">
          <template v-for="(part, index) in splitBoldText(leadDescription)" :key="index">
            <strong v-if="part.bold" class="font-bold text-highlighted">{{ part.text }}</strong>
            <span v-else>{{ part.text }}</span>
          </template>
        </p>
        <ul
          v-if="detailDescriptions.length"
          class="space-y-2 rounded-lg border border-accented bg-muted/20 p-3 text-sm text-muted-foreground"
        >
          <li
            v-for="(line, index) in detailDescriptions"
            :key="index"
            class="flex gap-2 leading-relaxed"
          >
            <UIcon name="i-lucide-dot" class="size-4 text-primary shrink-0 mt-0.5" />
            <span>
              <template v-for="(part, partIndex) in splitBoldText(line)" :key="partIndex">
                <strong v-if="part.bold" class="font-bold text-highlighted">{{ part.text }}</strong>
                <span v-else>{{ part.text }}</span>
              </template>
            </span>
          </li>
        </ul>
        <div v-if="$slots.default" class="w-full">
          <slot />
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center justify-end gap-2 w-full">
        <UButton
          :label="cancelLabel || $t('components.cancel')"
          color="neutral"
          variant="soft"
          size="md"
          class="font-semibold"
          :disabled="loading"
          @click="onCancel"
        />
        <UButton
          :label="submitLabel || $t('components.proceed')"
          :color="typeConfig.color"
          variant="solid"
          size="md"
          class="font-semibold"
          :loading="loading"
          @click="onSubmit"
        />
      </div>
    </template>
  </UModal>
</template>

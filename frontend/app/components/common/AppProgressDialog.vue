<script setup lang="ts">
const open = defineModel<boolean>('open')

const props = withDefaults(defineProps<{
  title?: string
  description?: string
  progress?: number
  indeterminate?: boolean
}>(), {
  progress: 0,
  indeterminate: false,
})

const safeProgress = computed(() => Math.min(100, Math.max(0, Math.round(props.progress))))
</script>

<template>
  <UModal
    v-model:open="open"
    :dismissible="false"
    :ui="{ content: 'max-w-sm w-[95vw] sm:w-full', header: 'border-none p-0', body: 'py-2' }"
  >
    <template #body>
      <div class="px-6 py-8 text-center space-y-6">
        <div class="space-y-2">
          <p
            class="text-5xl sm:text-6xl font-black tabular-nums text-primary tracking-tight leading-none transition-all duration-200"
            :aria-label="$t('import.progressPercent', { n: safeProgress })"
          >
            {{ indeterminate ? '…' : `${safeProgress}%` }}
          </p>
          <h3 class="text-base font-semibold text-highlighted">
            {{ title || $t('import.progressTitle') }}
          </h3>
          <p class="text-sm text-muted-foreground leading-relaxed">
            {{ description || $t('import.progressDesc') }}
          </p>
        </div>

        <div class="space-y-2 px-1">
          <UProgress
            :model-value="indeterminate ? undefined : safeProgress"
            :animation="indeterminate ? 'carousel' : undefined"
            size="md"
          />
          <p v-if="!indeterminate" class="text-xs font-medium text-muted-foreground">
            {{ $t('import.progressPercent', { n: safeProgress }) }}
          </p>
        </div>
      </div>
    </template>
  </UModal>
</template>

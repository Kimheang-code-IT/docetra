<script setup lang="ts">
import type { PersonSummary } from '~/types/docetra/common'

const props = defineProps<{
  owner?: PersonSummary | null
  updatedAt?: string
  commentCount?: number
  liked?: boolean
}>()

const { t } = useI18n()

const relativeShort = computed(() => {
  if (!props.updatedAt) return '—'
  const diff = Date.now() - new Date(props.updatedAt).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return t('docetra.meta.justNow')
  if (mins < 60) return `${Math.max(1, mins)} m`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} h`
  const days = Math.floor(hours / 24)
  return `${days} d`
})
</script>

<template>
  <div
    class="flex w-full min-w-28 items-center justify-between gap-2 text-xs"
    @click.stop
  >
    <div class="flex min-w-0 items-center gap-1.5">
      <UAvatar
        :alt="owner?.name || $t('docetra.activity.system')"
        size="3xs"
      />
      <span class="truncate text-muted tabular-nums">{{ relativeShort }}</span>
    </div>

    <div class="flex shrink-0 items-center gap-1 text-muted">
      <span class="inline-flex items-center gap-0.5">
        <UIcon name="i-lucide-message-square" class="size-3.5" />
        <span class="tabular-nums">{{ commentCount || 0 }}</span>
      </span>
      <span class="text-muted/70">·</span>
      <UIcon
        name="i-lucide-heart"
        class="size-3.5"
        :class="liked ? 'fill-current text-error' : ''"
      />
    </div>
  </div>
</template>

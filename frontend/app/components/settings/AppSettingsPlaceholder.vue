<script setup lang="ts">
import { useAppHeader } from '~/composables/layout/useAppHeader'

const props = defineProps<{
  titleKey: string
  descriptionKey: string
  icon: string
}>()

const { t } = useI18n()
const { setTitle, clear } = useAppHeader()

watch(
  () => t(props.titleKey),
  (label) => setTitle(label),
  { immediate: true },
)

onBeforeUnmount(clear)

useHead(() => ({
  title: `${t(props.titleKey)} · ${t('docetra.brand.name')}`,
}))
</script>

<template>
  <div class="flex min-h-0 w-full flex-1 flex-col overflow-auto px-1.5 pt-1.5 pb-0">
    <LayoutAppHeaderPageActions :can-create="false" @refresh="() => {}" />

    <div class="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-4 py-4">
      <div class="flex items-start gap-4">
        <span class="grid size-12 shrink-0 place-items-center rounded-xl bg-primary/10 ring-1 ring-primary/20">
          <UIcon :name="icon" class="size-6 text-primary" />
        </span>
        <div class="min-w-0">
          <h1 class="text-xl font-semibold text-highlighted">{{ $t(titleKey) }}</h1>
          <p class="mt-1 text-sm text-muted">{{ $t(descriptionKey) }}</p>
        </div>
      </div>
      <UAlert
        color="neutral"
        variant="subtle"
        icon="i-lucide-construction"
        :title="$t('docetra.document.comingSoon')"
      />
    </div>
  </div>
</template>

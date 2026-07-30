<script setup lang="ts">
interface Props {
  titleKey: string
  icon: string
  groupKey?: string
}

const props = defineProps<Props>()
const { t } = useI18n()

useHead(() => ({
  title: `${t(props.titleKey)} · ${t('docetra.brand.name')}`,
}))
</script>

<template>
  <div class="sticky top-0 z-40 border-b border-default bg-default/95 backdrop-blur">
    <LayoutAppHeader :title="$t(titleKey)" />
  </div>

  <div class="flex min-h-0 flex-1 flex-col bg-muted/30">
    <div class="mx-auto flex w-full max-w-[1600px] flex-1 flex-col gap-5 p-4 sm:p-6">
      <UCard class="flex min-h-72 flex-1 items-center justify-center border-dashed shadow-none">
        <div class="mx-auto flex max-w-md flex-col items-center px-6 py-14 text-center">
          <span class="mb-5 grid size-14 place-items-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
            <UIcon :name="icon" class="size-7 text-primary" />
          </span>
          <h1 class="text-xl font-semibold tracking-tight text-highlighted">
            {{ $t(titleKey) }}
          </h1>
          <p class="mt-2 text-sm leading-6 text-muted">
            {{ $t('docetra.scaffold.ready') }}
          </p>
          <UBadge color="neutral" variant="soft" class="mt-5">
            {{ $t('docetra.scaffold.status') }}
          </UBadge>
        </div>
      </UCard>
    </div>
  </div>
</template>

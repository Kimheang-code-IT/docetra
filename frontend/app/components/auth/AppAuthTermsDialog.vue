<script setup lang="ts">
/**
 * Terms & Conditions dialog for login / system access.
 */
const open = defineModel<boolean>('open', { default: false })

const i18n = useI18n()
const t = i18n.t
const messageApi = i18n as unknown as {
  tm: (key: string) => unknown
  rt: (value: unknown) => string
}

const termsItems = computed(() => {
  const raw = messageApi.tm('pages.auth.termsItems')
  if (!Array.isArray(raw)) return [] as string[]
  return raw.map((item) => {
    if (typeof item === 'string') return item
    try {
      return messageApi.rt(item)
    }
    catch {
      return String(item)
    }
  })
})
</script>

<template>
  <UModal v-model:open="open">
    <template #content>
      <UCard :ui="{ root: 'sm:max-w-lg' }">
        <template #header>
          <h3 class="text-sm font-semibold text-highlighted">
            {{ t('pages.auth.termsTitle') }}
          </h3>
        </template>

        <ol class="list-decimal space-y-2 pl-4 text-xs text-toned">
          <li v-for="(item, index) in termsItems" :key="index" class="leading-relaxed">
            {{ item }}
          </li>
        </ol>

        <template #footer>
          <div class="flex justify-end">
            <UButton color="primary" size="sm" @click="open = false">
              {{ t('pages.auth.termsClose') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>

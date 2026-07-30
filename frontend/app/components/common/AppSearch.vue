<script setup lang="ts">
import { computed } from 'vue'

const modelValue = defineModel<string>()

const props = defineProps<{
  label?: string
  placeholder?: string
}>()

const { t } = useI18n()

const inputPlaceholder = computed(() => props.placeholder ?? t('components.search'))
</script>

<template>
  <div class="flex flex-col min-w-0">
    <ClientOnly>
      <UInput
        v-model="modelValue"
        :placeholder="inputPlaceholder"
        icon="i-lucide-search"
        class="w-full font-normal text-highlighted"
        size="md"
        v-bind="$attrs"
        :ui="{ trailing: 'pe-1' }"
      >
        <template v-if="modelValue?.length" #trailing>
          <UButton
            color="neutral"
            variant="link"
            size="sm"
            icon="i-lucide-circle-x"
            :aria-label="$t('components.clear')"
            @click="() => { modelValue = '' }"
          />
        </template>
      </UInput>
    </ClientOnly>
  </div>
</template>

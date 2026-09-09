<script setup lang="ts">
import { useRecordSurfacePage } from '~/composables/record/useRecordSurfacePage'

definePageMeta({
  titleKey: 'docetra.navigation.record',
  key: route => route.path,
})

const { surface, config, pageKey } = await useRecordSurfacePage('document')

useHead({ title: () => `New ${surface.value?.name || 'Record'}` })
</script>

<template>
  <DocumentEntityDocumentView :key="pageKey" :config="config" />
</template>

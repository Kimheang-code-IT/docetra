<script setup lang="ts">
import { useRecordSurfacePage } from '~/composables/record/useRecordSurfacePage'

definePageMeta({
  titleKey: 'docetra.navigation.meeting',
  key: route => route.path,
})

const { surface, config, pageKey } = await useRecordSurfacePage('meeting')

useHead({ title: () => `New ${surface.value?.name || 'Meeting'}` })
</script>

<template>
  <DocumentEntityDocumentView :key="pageKey" :config="config" />
</template>

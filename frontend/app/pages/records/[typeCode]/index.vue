<script setup lang="ts">
import { useRecordSurfacePage } from '~/composables/record/useRecordSurfacePage'

definePageMeta({
  titleKey: 'docetra.navigation.record',
  key: route => route.path,
})

const { param, surface, config, pageKey } = await useRecordSurfacePage('document')

if (param.value === 'logs' || param.value === 'record-logs') {
  await navigateTo('/records/logs', { replace: true })
}

watch(param, (value) => {
  if (value === 'logs' || value === 'record-logs') {
    void navigateTo('/records/logs', { replace: true })
  }
})

useHead({ title: () => surface.value?.name || 'Records' })
</script>

<template>
  <RecordAppRecordStageBoard
    :key="pageKey"
    :config="config"
    date-field="updatedAt"
    subtitle-field="recordTypeName"
    :state-key="`record-stage-${config.recordTypeCode}`"
  />
</template>

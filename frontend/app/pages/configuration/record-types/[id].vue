<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.recordType',
  permission: 'configuration.record_types.view',
})

const route = useRoute()
const id = computed(() => String(route.params.id || ''))
</script>

<template>
  <ConfigurationAppRecordTypeEditor :record-type-id="id" />
</template>

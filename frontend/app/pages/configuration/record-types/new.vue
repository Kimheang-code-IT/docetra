<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.recordType',
  permission: 'configuration.record_types.create',
})
</script>

<template>
  <ConfigurationAppRecordTypeEditor record-type-id="new" />
</template>

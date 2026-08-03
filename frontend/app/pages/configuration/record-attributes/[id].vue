<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.recordAttribute',
  permission: 'configuration.record_attributes.view',
})

const route = useRoute()
const id = computed(() => String(route.params.id || ''))
</script>

<template>
  <ConfigurationAppRecordAttributeEditor :attribute-id="id" />
</template>

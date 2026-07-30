<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('departments')

definePageMeta({
  titleKey: 'docetra.pages.department',
  permission: 'organizations.departments.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

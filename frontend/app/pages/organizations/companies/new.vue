<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('companies')

definePageMeta({
  titleKey: 'docetra.pages.company',
  permission: 'organizations.companies.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

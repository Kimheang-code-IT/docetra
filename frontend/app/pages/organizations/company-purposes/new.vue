<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('companyPurposes')

definePageMeta({
  titleKey: 'docetra.pages.companyPurpose',
  permission: 'organizations.company_purposes.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

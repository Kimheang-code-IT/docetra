<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('companyPurposes')

definePageMeta({
  titleKey: 'docetra.pages.companyPurpose',
  permission: 'organizations.company_purposes.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

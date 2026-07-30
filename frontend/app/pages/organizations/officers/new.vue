<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('officers')

definePageMeta({
  titleKey: 'docetra.pages.officer',
  permission: 'organizations.officers.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

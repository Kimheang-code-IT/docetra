<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const route = useRoute()
const param = String(route.params.orgType || '').toLowerCase()

const builtin: Record<string, string> = {
  department: 'departments',
  departments: 'departments',
  company: 'companies',
  companies: 'companies',
}

const entityKey = builtin[param]
if (!entityKey) {
  throw createError({ statusCode: 404, statusMessage: 'Organization type not found' })
}

// Prefer static shells for built-ins (menu routes).
if (param === 'department') {
  await navigateTo('/organizations/departments', { replace: true })
}
else if (param === 'company') {
  await navigateTo('/organizations/companies', { replace: true })
}

const config = getEntityConfig(entityKey)

definePageMeta({
  titleKey: 'docetra.navigation.organization',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

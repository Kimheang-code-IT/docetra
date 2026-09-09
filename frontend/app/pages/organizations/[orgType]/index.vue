<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'
import { organizationCanonicalPath, organizationEntityKeyFromParam } from '~/utils/organization/org-type-route'

definePageMeta({
  titleKey: 'docetra.navigation.organization',
  key: route => route.path,
})

const route = useRoute()
const param = computed(() => String(route.params.orgType || '').toLowerCase())
const entityKey = computed(() => organizationEntityKeyFromParam(param.value))
const pageKey = computed(() => route.path)

if (!entityKey.value) {
  throw createError({ statusCode: 404, statusMessage: 'Organization type not found' })
}

const canonical = organizationCanonicalPath(param.value)
if (canonical) {
  await navigateTo(canonical, { replace: true })
}

watch(param, (value) => {
  const next = organizationCanonicalPath(value)
  if (next) {
    void navigateTo(next, { replace: true })
    return
  }
  if (!organizationEntityKeyFromParam(value)) {
    showError(createError({ statusCode: 404, statusMessage: 'Organization type not found' }))
  }
})

const config = computed(() => entityKey.value ? getEntityConfig(entityKey.value) : null)
</script>

<template>
  <WorkspaceEntityWorkspaceView v-if="config" :key="pageKey" :config="config" />
</template>

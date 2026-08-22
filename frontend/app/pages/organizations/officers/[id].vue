<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.officer',
  permission: 'organizations.officers.view',
})
const id = String(useRoute().params.id || '')
await navigateTo(`/officers/${encodeURIComponent(id)}`, { replace: true })
</script>

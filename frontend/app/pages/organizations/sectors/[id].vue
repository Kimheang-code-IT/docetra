<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.sector',
  permission: 'organizations.sectors.view',
})
const id = String(useRoute().params.id || '')
await navigateTo(`/sector/${encodeURIComponent(id)}`, { replace: true })
</script>

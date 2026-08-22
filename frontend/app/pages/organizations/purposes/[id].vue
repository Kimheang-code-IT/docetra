<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.purpose',
  permission: 'organizations.purposes.view',
})
const id = String(useRoute().params.id || '')
await navigateTo(`/purpose/${encodeURIComponent(id)}`, { replace: true })
</script>

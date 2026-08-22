<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.sector',
  permission: 'organizations.sectors.create',
})
await navigateTo('/sector/new', { replace: true })
</script>

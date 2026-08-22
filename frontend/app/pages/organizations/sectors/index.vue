<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.sector',
  permission: 'organizations.sectors.view',
})
await navigateTo('/sector', { replace: true })
</script>

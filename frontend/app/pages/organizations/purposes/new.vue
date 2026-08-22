<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.purpose',
  permission: 'organizations.purposes.create',
})
await navigateTo('/purpose/new', { replace: true })
</script>

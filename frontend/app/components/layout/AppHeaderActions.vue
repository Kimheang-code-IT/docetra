<template>
  <Teleport defer to="#app-header-right">
    <div class="flex min-w-0 flex-wrap items-center justify-end gap-1.5 sm:gap-2">
      <slot />
    </div>
  </Teleport>
</template>

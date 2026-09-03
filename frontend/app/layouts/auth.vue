<template>
  <div
    class="relative min-h-svh bg-linear-to-br from-primary/20 via-white to-primary/10 dark:from-gray-900 dark:via-gray-950 dark:to-primary/20"
    style="min-height: 100vh; min-height: 100svh; width: 100%;"
  >
    <div
      class="absolute inset-e-4 top-4 z-20 sm:inset-e-6 sm:top-6"
      style="position: absolute; inset-inline-end: 1rem; top: 1rem; z-index: 20;"
    >
      <CommonAppAuthLocaleSwitch />
    </div>

    <!--
      Keep the critical centering geometry inline. On a cold Nuxt dev start the
      generated stylesheet can be replaced during compilation/HMR; these small
      SSR styles prevent the login card from flashing at the left edge.
    -->
    <div
      class="flex min-h-svh items-center justify-center px-4"
      style="display: flex; min-height: 100vh; min-height: 100svh; width: 100%; align-items: center; justify-content: center; padding-inline: 1rem;"
    >
      <UPageCard
        variant="subtle"
        class="w-full max-w-sm"
        style="width: 100%; max-width: 24rem;"
      >
        <slot />
      </UPageCard>
    </div>
  </div>
</template>

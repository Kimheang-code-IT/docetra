// nuxt.config.ts
// https://nuxt.com/docs/api/configuration/nuxt-config

export default defineNuxtConfig({
  modules: [
    '@nuxt/ui',
    '@nuxt/image',
    '@vueuse/nuxt',
    '@nuxtjs/i18n',
    '@nuxt/fonts',
    '@pinia/nuxt'
  ],

  devtools: {
    enabled: true
  },

  runtimeConfig: {
    public: {
      apiBase: import.meta.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      // Set `NUXT_PUBLIC_USE_MOCK_DATA=false` for API-only analytics and table fallbacks in dev/prod.
      useMockData: import.meta.env.NUXT_PUBLIC_USE_MOCK_DATA !== 'false'
    }
  },

  imports: {
    dirs: [
      'utils/**',
      'utils/api/**',
      'utils/auth/**',
      'utils/constants/**',
      'utils/format/**',
      'utils/helpers/**',
      'utils/storage/**',
      'utils/validation/**'
    ]
  },

  css: ['~/assets/css/main.css'],

  i18n: {
    locales: [
      {
        code: 'en',
        name: 'English',
        file: 'en.json'
      },
      {
        code: 'km',
        name: '?????????',
        file: 'km.json'
      }
    ],
    defaultLocale: 'km',
    strategy: 'no_prefix',
    langDir: 'locales',
    detectBrowserLanguage: false
  },

  routeRules: {
    '/api/**': {
      cors: true
    }
  },

  nitro: {
    preset: 'vercel'
  },

  compatibilityDate: '2024-07-11',

  vite: {
    build: {
      chunkSizeWarningLimit: 1000
    }
  }
})

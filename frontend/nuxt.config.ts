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
      useMockData: import.meta.env.NUXT_PUBLIC_USE_MOCK_DATA !== 'false',
      appVersion: import.meta.env.NUXT_PUBLIC_APP_VERSION || '0.1.0',
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

  // Menu icons live in .ts files — include them in the client icon scan
  icon: {
    serverBundle: 'local',
    clientBundle: {
      scan: {
        globInclude: ['**/*.{vue,jsx,tsx,md,mdc,mdx,ts,js}'],
      },
      sizeLimitKb: 512,
    },
  },

  i18n: {
    locales: [
      {
        code: 'en',
        name: 'English',
        file: 'en.json',
      },
      {
        code: 'km',
        name: 'ភាសាខ្មែរ',
        file: 'km.json',
      },
    ],
    defaultLocale: 'en',
    strategy: 'no_prefix',
    langDir: 'locales',
    detectBrowserLanguage: false,
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
    },
    // TipTap/ProseMirror must share one instance (avoids blank editor / duplicate cell ID)
    optimizeDeps: {
      include: [
        '@tiptap/core',
        '@tiptap/vue-3',
        '@tiptap/starter-kit',
        '@tiptap/extension-text-align',
        '@tiptap/extension-underline',
        '@tiptap/extension-highlight',
        '@tiptap/extension-text-style',
        '@tiptap/extension-table',
      ],
    },
    css: {
      // Silence noisy Uppy package sourcemap warnings in dev
      devSourcemap: false,
    },
  }
})

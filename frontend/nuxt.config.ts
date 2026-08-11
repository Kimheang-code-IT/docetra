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

  app: {
    head: {
      title: 'Docetra',
      htmlAttrs: {
        lang: 'en',
      },
      meta: [
        { name: 'format-detection', content: 'telephone=no' },
        { name: 'theme-color', content: '#e8472a' },
      ],
      link: [
        { rel: 'icon', type: 'image/png', href: '/logo.png' },
        { rel: 'apple-touch-icon', href: '/logo.png' },
      ],
    },
  },

  devtools: {
    enabled: import.meta.env.DEV
  },

  runtimeConfig: {
    public: {
      apiBase: import.meta.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      // Current release is mock-first. Set false later when the HTTP API is available.
      useMockData: import.meta.env.NUXT_PUBLIC_USE_MOCK_DATA !== 'false',
      appVersion: import.meta.env.NUXT_PUBLIC_APP_VERSION || '0.1.0',
      // Canonical public origin for Open Graph / Twitter image URLs (no trailing slash).
      // Example: https://app.docetra.com — required for link previews to show images.
      siteUrl: import.meta.env.NUXT_PUBLIC_SITE_URL || '',
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

  // Optimized font loading (no blocking CSS @import from Google)
  fonts: {
    families: [
      { name: 'Inter', provider: 'google', weights: [400, 500, 600, 700] },
      { name: 'Noto Sans Khmer', provider: 'google', weights: [400, 500, 600, 700] },
    ],
    defaults: {
      weights: [400, 500, 600, 700],
      styles: ['normal'],
    },
  },

  // Menu icons live in .ts/.vue — keep the scan tight for a smaller first client bundle
  icon: {
    serverBundle: 'local',
    clientBundle: {
      scan: {
        globInclude: [
          'app/components/**/*.{vue,ts}',
          'app/composables/**/*.ts',
          'app/layouts/**/*.vue',
          'app/pages/**/*.vue',
        ],
      },
      sizeLimitKb: 256,
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
    '/**': {
      headers: {
        'x-content-type-options': 'nosniff',
        'referrer-policy': 'strict-origin-when-cross-origin',
        'x-frame-options': 'DENY',
        'permissions-policy': 'camera=(), microphone=(), geolocation=()',
      },
    },
  },

  nitro: {
    preset: 'vercel'
  },

  compatibilityDate: '2024-07-11',

  vite: {
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            // CSS/virtual style modules must stay with Vite's CSS pipeline or Nitro
            // fails with UNRESOLVED_IMPORT on `*-styles-*.mjs-!~{…}~.js`.
            if (
              id.includes('.css')
              || id.includes('?vue&type=style')
              || id.includes('&lang.css')
              || id.includes('type=style')
            ) {
              return
            }
            if (id.includes('node_modules/echarts') || id.includes('vue-echarts')) return 'echarts'
            if (id.includes('@tiptap') || id.includes('prosemirror')) return 'tiptap'
            if (id.includes('@uppy')) return 'uppy'
          },
        },
      },
    },
    // Pre-bundle common deps only; TipTap/Uppy/ECharts load when their pages mount
    optimizeDeps: {
      include: [
        '@vueuse/core',
        '@internationalized/date',
      ],
    },
    css: {
      // Silence noisy Uppy package sourcemap warnings in dev
      devSourcemap: false,
    },
  }
})

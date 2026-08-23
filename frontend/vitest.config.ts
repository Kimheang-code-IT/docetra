import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  resolve: {
    alias: {
      '~': fileURLToPath(new URL('./app', import.meta.url)),
      '@': fileURLToPath(new URL('./app', import.meta.url)),
    },
  },
  test: {
    environment: 'node',
    include: ['tests/unit/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reportsDirectory: './coverage',
      reporter: ['text', 'lcov', 'json-summary'],
      include: [
        'app/utils/auth/**',
        'app/utils/api/concurrency.ts',
        'app/utils/api/error-policy.ts',
        'app/utils/api/query.ts',
        'app/utils/security/csrf.ts',
        'app/utils/security/files.ts',
        'app/utils/security/url.ts',
        'app/utils/object-path.ts',
        'app/utils/pagination.ts',
        'app/utils/role/access.ts',
        'app/utils/role/permissions.ts',
        'app/utils/format/summary-value.ts',
        'app/utils/preferences/font-size.ts',
        'app/utils/card-fields.ts',
        'app/utils/record-type-fields.ts',
        'app/utils/meeting/board.ts',
        'app/utils/workspace-list-stale.ts',
        'app/utils/config-code.ts',
        'app/utils/filter/select-ui.ts',
        'app/utils/pending-type-attributes.ts',
        'app/composables/common/usePathModel.ts',
        'app/utils/record/surfaces.ts',
        'app/adapters/createEntityAdapter.ts',
      ],
      exclude: [
        'app/utils/auth/session.ts',
      ],
      thresholds: {
        lines: 70,
        functions: 70,
        statements: 70,
        branches: 50,
      },
    },
  },
})

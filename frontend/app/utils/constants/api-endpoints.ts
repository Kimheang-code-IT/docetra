export const ApiEndpoints = {
  ANALYTICS_DASHBOARD: '/analytics/dashboard',
  REVENUE_ENTRIES: '/revenue-entries',
  REWARDS: '/rewards',
  PUBLIC_SERVICE_REVENUE: '/public-service-revenue',
  FINANCIAL_OBLIGATIONS: '/financial-obligations',
  ROYALTY_LAND_FEES: '/royalty-land-fees',
  ROYALTY_STATE_RESPONSES: '/royalty-state-responses',
  /** Current USD/KHR (and peers) for preview conversion — not full history */
  EXCHANGE_RATES_CURRENT: '/exchange-rates/current',
  EXCHANGE_RATES: '/exchange-rates',
  USERS: '/users',
  ROLES: '/roles',
  IMPORT_BATCHES: '/import-batches',
  AUDIT_LOGS: '/audit-logs',
  KIND_TOTAL_REVENUE: '/kind-total-revenue',
  DPME_TOTAL_REVENUE: '/dpme-total-revenue',
} as const

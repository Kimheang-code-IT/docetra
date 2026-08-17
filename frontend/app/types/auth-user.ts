export interface AuthUser {
  id?: number
  name: string
  email: string
  role?: string
  avatar?: string
  /** Flat permission keys (e.g. records.incoming_documents.view). */
  permissions?: string[]
  /** Route/page ids the user may access. Empty/undefined = no frontend restriction. */
  pageAccess?: string[]
}

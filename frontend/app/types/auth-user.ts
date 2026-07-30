export interface AuthUser {
  id?: number
  name: string
  email: string
  role?: string
  avatar?: string
  /** Route/page ids the user may access. Empty/undefined = no frontend restriction. */
  pageAccess?: string[]
}

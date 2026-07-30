export interface AuditLog {
    id: number
    typeAction: 'Login' | 'Logout' | 'Create' | 'Update' | 'Delete' | 'Export'
    username: string
    date: string
    description: string
    metadata?: any // Additional context for "View Details"
}

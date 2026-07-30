export interface FormField {
    key: string
    label: string
    type?: 'input' | 'select' | 'textarea' | 'password' | 'date' | 'permission-tree'
    icon?: string
    placeholder?: string
    items?: any[]
    childItems?: any[]
    required?: boolean
    class?: string
}

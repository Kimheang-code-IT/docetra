export interface ExchangeRate {
    id: number
    currency: string
    unitUsd: string
    rateToCurrency: number
    unitPerCurrency: string
    rateKhr: number
    date?: string
}

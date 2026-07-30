import type { ExchangeRate } from "~/types/exchange-rate";
import { DEFAULT_USD_KHR_RATE } from "~/utils/constants/exchange-rate";

type CurrencyEntry = {
  currency: string;
  rateKhr: number;
  rateToCurrency: number;
};

const currencyMap: CurrencyEntry[] = [
  { currency: "USD", rateKhr: DEFAULT_USD_KHR_RATE, rateToCurrency: 1.0 },
  { currency: "KHR", rateKhr: 1000, rateToCurrency: DEFAULT_USD_KHR_RATE },
  { currency: "THB", rateKhr: 115, rateToCurrency: 35.5 },
  { currency: "EUR", rateKhr: 4450, rateToCurrency: 0.92 },
  { currency: "GBP", rateKhr: 5200, rateToCurrency: 0.79 },
  { currency: "JPY", rateKhr: 27, rateToCurrency: 151 },
  { currency: "CNY", rateKhr: 560, rateToCurrency: 7.2 },
  { currency: "KRW", rateKhr: 3, rateToCurrency: 1340 },
  { currency: "SGD", rateKhr: 3050, rateToCurrency: 1.34 },
  { currency: "MYR", rateKhr: 870, rateToCurrency: 4.7 },
];

export const initialData: ExchangeRate[] = Array.from({ length: 30 }, (_, i) => {
  const id = i + 1;
  const entry = currencyMap[i % currencyMap.length]!;

  return {
    id,
    currency: entry.currency,
    unitUsd: "1 USD",
    rateToCurrency: entry.rateToCurrency,
    unitPerCurrency: `1 ${entry.currency}`,
    rateKhr: Math.round(entry.rateKhr + (i % 5) * 10),
    date: `2026-03-${String(28 - (i % 28)).padStart(2, "0")}`,
  };
});

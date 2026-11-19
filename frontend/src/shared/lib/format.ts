const integerFormatter = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 });
const decimalFormatter = new Intl.NumberFormat('ru-RU', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});
const moneyFormatters = new Map<string, Intl.NumberFormat | null>();

function formatDecimal(value: number): string {
  return decimalFormatter.format(value);
}

function moneyFormatter(currency: string): Intl.NumberFormat | null {
  if (!moneyFormatters.has(currency)) {
    try {
      moneyFormatters.set(
        currency,
        new Intl.NumberFormat('ru-RU', {
          style: 'currency',
          currency,
          maximumFractionDigits: 2,
        }),
      );
    } catch {
      moneyFormatters.set(currency, null);
    }
  }
  return moneyFormatters.get(currency) ?? null;
}

export function formatNumber(value: number): string {
  return integerFormatter.format(value);
}

export function formatMoney(value: number, currency: string | null): string {
  if (!currency) {
    return formatDecimal(value);
  }
  const formatter = moneyFormatter(currency);
  return formatter ? formatter.format(value) : `${formatDecimal(value)} ${currency}`;
}

export function pluralize(value: number, forms: [one: string, few: string, many: string]): string {
  const absolute = Math.abs(value) % 100;
  const last = absolute % 10;
  if (absolute > 10 && absolute < 20) {
    return forms[2];
  }
  if (last === 1) {
    return forms[0];
  }
  if (last >= 2 && last <= 4) {
    return forms[1];
  }
  return forms[2];
}

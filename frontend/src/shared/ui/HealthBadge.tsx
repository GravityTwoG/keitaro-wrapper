import { Tooltip } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '@/shared/api/client';
import { queryKeys } from '@/shared/api/queryKeys';
import type { HealthResponse } from '@/shared/api/types';

type HealthState = 'pending' | 'ok' | 'error';

export function HealthBadge() {
  const health = useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.get<HealthResponse>('/health/ready'),
    retry: false,
    refetchInterval: 30_000,
  });

  const state: HealthState = health.isPending ? 'pending' : health.isSuccess ? 'ok' : 'error';
  const label =
    state === 'ok'
      ? 'Keitaro на связи'
      : state === 'error'
        ? 'Keitaro недоступен'
        : 'Проверка связи';

  const checks = health.data?.checks;
  const tooltip =
    state === 'ok' && checks
      ? Object.entries(checks)
          .map(([key, value]) => `${key}: ${value}`)
          .join('\n')
      : 'Проверьте KEITARO_BASE_URL и KEITARO_API_KEY';

  return (
    <Tooltip label={tooltip} multiline maw={320} position="bottom-end">
      <output className="kw-health" aria-live="polite">
        <span className="kw-health-dot" data-state={state} />
        <span>{label}</span>
      </output>
    </Tooltip>
  );
}

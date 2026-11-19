import { Badge } from '@mantine/core';

import type { CampaignState } from '@/shared/api/types';

const CAMPAIGN_STATE: Record<CampaignState, { label: string; color: string }> = {
  active: { label: 'Активна', color: 'forest' },
  disabled: { label: 'Выключена', color: 'gray' },
  deleted: { label: 'Удалена', color: 'red' },
};

export function CampaignStateBadge({ state }: { state: CampaignState }) {
  const meta = CAMPAIGN_STATE[state] ?? CAMPAIGN_STATE.disabled;
  return (
    <Badge color={meta.color} variant="light" size="sm">
      {meta.label}
    </Badge>
  );
}

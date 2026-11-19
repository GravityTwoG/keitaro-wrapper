import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { api } from '@/shared/api/client';
import { queryKeys } from '@/shared/api/queryKeys';
import type { CampaignListResponse } from '@/shared/api/types';

export const CAMPAIGNS_PAGE_SIZE = 20;

export function useCampaigns(page: number) {
  return useQuery({
    queryKey: queryKeys.campaigns(page),
    queryFn: () => {
      const params = new URLSearchParams({
        limit: String(CAMPAIGNS_PAGE_SIZE),
        offset: String(page * CAMPAIGNS_PAGE_SIZE),
      });
      return api.get<CampaignListResponse>(`/campaigns?${params.toString()}`);
    },
    placeholderData: keepPreviousData,
  });
}

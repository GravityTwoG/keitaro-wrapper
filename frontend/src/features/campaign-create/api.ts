import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { api } from '@/shared/api/client';
import { queryKeys } from '@/shared/api/queryKeys';
import type {
  CampaignDetail,
  CreateCampaignPayload,
  OfferSearchResponse,
} from '@/shared/api/types';

const OFFER_PAGE_SIZE = 50;

export function useOfferSearch(search: string) {
  return useInfiniteQuery({
    queryKey: queryKeys.offers(search),
    initialPageParam: 0,
    queryFn: ({ pageParam }) => {
      const params = new URLSearchParams({
        limit: String(OFFER_PAGE_SIZE),
        offset: String(pageParam),
      });
      if (search) {
        params.set('search', search);
      }
      return api.get<OfferSearchResponse>(`/offers?${params.toString()}`);
    },
    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.offset + lastPage.items.length : undefined,
  });
}

export function useCreateCampaign() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateCampaignPayload) => api.post<CampaignDetail>('/campaigns', payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });
}

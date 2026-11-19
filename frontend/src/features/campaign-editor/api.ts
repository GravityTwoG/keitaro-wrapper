import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/shared/api/client';
import { queryKeys } from '@/shared/api/queryKeys';
import type { CampaignDetail, CampaignStreamView, CampaignEditorView } from '@/shared/api/types';

export function useCampaign(campaignId: number) {
  return useQuery({
    queryKey: queryKeys.campaign(campaignId),
    queryFn: () => api.get<CampaignDetail>(`/campaigns/${campaignId}`),
    enabled: campaignId > 0,
  });
}

export function useCampaignEditor(campaignId: number) {
  return useQuery({
    queryKey: queryKeys.editor(campaignId),
    queryFn: () => api.get<CampaignEditorView>(`/campaigns/${campaignId}/editor`),
    enabled: campaignId > 0,
  });
}

function useEditorMutation<TVariables>(
  campaignId: number,
  mutationFn: (variables: TVariables) => Promise<unknown>,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.editor(campaignId) });
    },
  });
}

export function useFetchStreams(campaignId: number) {
  return useEditorMutation(campaignId, () =>
    api.post<CampaignEditorView>(`/campaigns/${campaignId}/editor/fetch`, {}),
  );
}

export function useAddOffer(campaignId: number) {
  return useEditorMutation(
    campaignId,
    ({ streamId, offerId }: { streamId: number; offerId: number }) =>
      api.post<CampaignStreamView>(`/campaigns/${campaignId}/editor/streams/${streamId}/offers`, {
        offer_id: offerId,
      }),
  );
}

export function useRemoveOffer(campaignId: number) {
  return useEditorMutation(
    campaignId,
    ({ streamId, offerId }: { streamId: number; offerId: number }) =>
      api.delete<CampaignStreamView>(
        `/campaigns/${campaignId}/editor/streams/${streamId}/offers/${offerId}`,
      ),
  );
}

export function useRestoreOffer(campaignId: number) {
  return useEditorMutation(
    campaignId,
    ({ streamId, offerId }: { streamId: number; offerId: number }) =>
      api.post<CampaignStreamView>(
        `/campaigns/${campaignId}/editor/streams/${streamId}/offers/${offerId}/restore`,
        {},
      ),
  );
}

export function usePinOffer(campaignId: number) {
  return useEditorMutation(
    campaignId,
    ({ streamId, offerId, pinned }: { streamId: number; offerId: number; pinned: boolean }) =>
      api.post<CampaignStreamView>(
        `/campaigns/${campaignId}/editor/streams/${streamId}/offers/${offerId}/pin`,
        { pinned },
      ),
  );
}

export function usePublishOffers(campaignId: number) {
  return useEditorMutation(campaignId, () =>
    api.post<CampaignEditorView>(`/campaigns/${campaignId}/editor/publish`, {}),
  );
}

export function useCancelOffers(campaignId: number) {
  return useEditorMutation(campaignId, () =>
    api.post<CampaignEditorView>(`/campaigns/${campaignId}/editor/cancel`, {}),
  );
}

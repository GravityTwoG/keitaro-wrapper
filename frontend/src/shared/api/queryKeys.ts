export const queryKeys = {
  health: ['health'] as const,
  campaigns: (page: number) => ['campaigns', page] as const,
  campaign: (campaignId: number) => ['campaign', campaignId] as const,
  editor: (campaignId: number) => ['campaign', campaignId, 'editor'] as const,
  offers: (search: string) => ['offers', search] as const,
};

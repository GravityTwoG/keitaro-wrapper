export type CampaignState = 'active' | 'disabled' | 'deleted';

export interface CampaignSummary {
  id: number;
  name: string;
  alias: string;
  state: CampaignState;
}

export interface CampaignListResponse {
  items: CampaignSummary[];
  offset: number;
  has_more: boolean;
}

export type CampaignDetail = CampaignSummary;

export interface OfferSearchItem {
  id: number;
  name: string;
  payout_value: number | null;
  payout_currency: string | null;
  country: string[];
}

export interface OfferSearchResponse {
  items: OfferSearchItem[];
  total: number;
  offset: number;
  has_more: boolean;
}

export interface CreateCampaignPayload {
  name: string;
  geo: string[];
  offer_id: number;
}

export type CampaignOfferStatus = 'active' | 'pending' | 'removed' | 'archived';

export interface CampaignOfferView {
  offer_id: number;
  name: string;
  share: number;
  pinned_share: number | null;
  status: CampaignOfferStatus;
  can_remove: boolean;
  can_restore: boolean;
}

export interface CampaignStreamView {
  stream_id: number;
  name: string;
  position: number;
  has_offers: boolean;
  dirty: boolean;
  offers: CampaignOfferView[];
}

export interface CampaignEditorView {
  loaded: boolean;
  dirty: boolean;
  streams: CampaignStreamView[];
}

export interface HealthResponse {
  status: 'ok' | 'error';
  checks: Record<string, string>;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  request_id: string | null;
  details?: Record<string, unknown>;
}

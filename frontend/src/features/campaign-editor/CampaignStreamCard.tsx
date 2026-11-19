import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Paper,
  Stack,
  Table,
  Text,
  Tooltip,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconPin, IconPlus, IconRotate, IconTrash } from '@tabler/icons-react';

import { usePinOffer, useRemoveOffer, useRestoreOffer } from './api';
import { errorMessage } from '@/shared/api/client';
import type { CampaignOfferView, CampaignStreamView } from '@/shared/api/types';

function notifyError(error: unknown) {
  notifications.show({
    title: 'Не удалось изменить оффер',
    message: errorMessage(error),
    color: 'red',
  });
}

interface CampaignStreamCardProps {
  campaignId: number;
  stream: CampaignStreamView;
  onAddOffer: (stream: CampaignStreamView) => void;
}

const STATUS_LABELS: Record<string, string> = {
  pending: 'новый',
  removed: 'удалён',
  archived: 'в архиве',
};

export function CampaignStreamCard({ campaignId, stream, onAddOffer }: CampaignStreamCardProps) {
  if (!stream.has_offers) {
    return (
      <Paper
        className="kw-card"
        withBorder={false}
        p="md"
        data-testid={`campaign-stream-${stream.stream_id}`}
      >
        <Group gap="sm">
          <span className="kw-flow-index">{stream.position || 1}</span>
          <Text fw={650}>{stream.name}</Text>
          <Text size="xs" c="dimmed">
            Поток без офферов
          </Text>
        </Group>
      </Paper>
    );
  }

  return (
    <Paper
      className="kw-card"
      withBorder={false}
      p="lg"
      data-testid={`campaign-stream-${stream.stream_id}`}
      style={stream.dirty ? { borderColor: 'var(--mantine-color-yellow-5)' } : undefined}
    >
      <CampaignStreamHeader stream={stream} onAddOffer={onAddOffer} />
      <hr className="kw-divider" style={{ margin: '1rem 0' }} />
      <OfferTable campaignId={campaignId} stream={stream} />
    </Paper>
  );
}

function CampaignStreamHeader({
  stream,
  onAddOffer,
}: {
  stream: CampaignStreamView;
  onAddOffer: (stream: CampaignStreamView) => void;
}) {
  return (
    <Group justify="space-between" align="flex-start" wrap="wrap">
      <Group gap="sm" wrap="nowrap">
        <span className="kw-flow-index">{stream.position || 1}</span>
        <Stack gap={4}>
          <Group gap={8}>
            <Text fw={750}>{stream.name}</Text>
            <Badge size="xs" variant="light" color={stream.dirty ? 'yellow' : 'forest'}>
              {stream.dirty ? 'есть изменения' : 'опубликован'}
            </Badge>
          </Group>
          <Text size="xs" c="dimmed">
            Офферы и веса
          </Text>
        </Stack>
      </Group>
      <Button
        size="xs"
        variant="light"
        leftSection={<IconPlus size={14} />}
        onClick={() => onAddOffer(stream)}
        data-testid={`add-campaign-offer-${stream.stream_id}`}
      >
        Добавить оффер
      </Button>
    </Group>
  );
}

function OfferTable({ campaignId, stream }: { campaignId: number; stream: CampaignStreamView }) {
  return (
    <div className="kw-table-wrap">
      <Table verticalSpacing="xs" horizontalSpacing="sm">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Оффер</Table.Th>
            <Table.Th ta="right">Вес</Table.Th>
            <Table.Th>Статус</Table.Th>
            <Table.Th />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {stream.offers.map((offer) => (
            <OfferRow key={offer.offer_id} campaignId={campaignId} stream={stream} offer={offer} />
          ))}
        </Table.Tbody>
      </Table>
    </div>
  );
}

function OfferRow({
  campaignId,
  stream,
  offer,
}: {
  campaignId: number;
  stream: CampaignStreamView;
  offer: CampaignOfferView;
}) {
  const removeOffer = useRemoveOffer(campaignId);
  const restoreOffer = useRestoreOffer(campaignId);
  const pinOffer = usePinOffer(campaignId);
  const inactive = offer.status === 'removed' || offer.status === 'archived';
  const busy =
    (removeOffer.isPending && removeOffer.variables?.offerId === offer.offer_id) ||
    (restoreOffer.isPending && restoreOffer.variables?.offerId === offer.offer_id) ||
    (pinOffer.isPending && pinOffer.variables?.offerId === offer.offer_id);

  return (
    <Table.Tr
      data-testid={`campaign-offer-row-${offer.offer_id}`}
      style={inactive ? { opacity: 0.55 } : undefined}
    >
      <Table.Td>
        <Stack gap={1}>
          <Text size="sm" fw={600} lineClamp={2} maw={520}>
            {offer.name}
          </Text>
          <Text size="xs" c="dimmed" className="mono">
            #{offer.offer_id}
          </Text>
        </Stack>
      </Table.Td>
      <Table.Td ta="right">
        <Group gap={6} justify="flex-end">
          {offer.pinned_share !== null ? (
            <Tooltip label={`Вес закреплён: ${offer.pinned_share}%`}>
              <IconPin size={14} fill="currentColor" />
            </Tooltip>
          ) : null}
          <Text fw={700} className="tabular" data-testid={`campaign-offer-share-${offer.offer_id}`}>
            {offer.share}%
          </Text>
        </Group>
      </Table.Td>
      <Table.Td>
        {offer.status === 'active' ? (
          <Badge size="xs" variant="light" color="forest">
            активен
          </Badge>
        ) : (
          <Badge size="xs" variant="light" color={inactive ? 'gray' : 'blue'}>
            {STATUS_LABELS[offer.status] ?? offer.status}
          </Badge>
        )}
      </Table.Td>
      <Table.Td>
        <Group gap={4} justify="flex-end" wrap="nowrap">
          {offer.can_remove ? (
            <>
              <Tooltip label={offer.pinned_share !== null ? 'Открепить вес' : 'Закрепить вес'}>
                <ActionIcon
                  variant="subtle"
                  color="gray"
                  size="sm"
                  loading={busy}
                  onClick={() =>
                    pinOffer.mutate(
                      {
                        streamId: stream.stream_id,
                        offerId: offer.offer_id,
                        pinned: offer.pinned_share === null,
                      },
                      { onError: notifyError },
                    )
                  }
                  data-testid={`pin-offer-${offer.offer_id}`}
                >
                  <IconPin size={15} fill={offer.pinned_share !== null ? 'currentColor' : 'none'} />
                </ActionIcon>
              </Tooltip>
              <Tooltip label="Удалить оффер из потока">
                <ActionIcon
                  variant="subtle"
                  color="red"
                  size="sm"
                  loading={busy}
                  onClick={() =>
                    removeOffer.mutate(
                      { streamId: stream.stream_id, offerId: offer.offer_id },
                      { onError: notifyError },
                    )
                  }
                  data-testid={`remove-offer-${offer.offer_id}`}
                >
                  <IconTrash size={15} />
                </ActionIcon>
              </Tooltip>
            </>
          ) : null}
          {offer.can_restore ? (
            <Button
              size="xs"
              variant="light"
              leftSection={<IconRotate size={14} />}
              loading={busy}
              onClick={() =>
                restoreOffer.mutate(
                  { streamId: stream.stream_id, offerId: offer.offer_id },
                  { onError: notifyError },
                )
              }
              data-testid={`restore-offer-${offer.offer_id}`}
            >
              Вернуть
            </Button>
          ) : null}
        </Group>
      </Table.Td>
    </Table.Tr>
  );
}

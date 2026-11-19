import { Alert, Button, Group, Modal, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';

import { useAddOffer } from './api';
import { OfferSelect } from '@/features/campaign-create/OfferSelect';
import { errorMessage } from '@/shared/api/client';
import type { CampaignStreamView } from '@/shared/api/types';

interface AddOfferModalProps {
  opened: boolean;
  onClose: () => void;
  campaignId: number;
  stream: CampaignStreamView | null;
}

export function AddOfferModal({ opened, onClose, campaignId, stream }: AddOfferModalProps) {
  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={<Text fw={750}>Добавить оффер</Text>}
      centered
      size="lg"
    >
      {stream ? <AddOfferForm campaignId={campaignId} stream={stream} onClose={onClose} /> : null}
    </Modal>
  );
}

function AddOfferForm({
  campaignId,
  stream,
  onClose,
}: {
  campaignId: number;
  stream: CampaignStreamView;
  onClose: () => void;
}) {
  const addOffer = useAddOffer(campaignId);
  const [offerId, setOfferId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = () => {
    if (offerId === null) {
      setError('Выберите оффер');
      return;
    }
    addOffer.mutate(
      { streamId: stream.stream_id, offerId },
      {
        onSuccess: () => {
          notifications.show({
            title: 'Оффер добавлен',
            message: 'Изменения уйдут в Keitaro после публикации',
            color: 'forest',
          });
          onClose();
        },
        onError: (mutationError) => setError(errorMessage(mutationError)),
      },
    );
  };

  return (
    <Stack gap="md">
      <Text size="sm" c="dimmed">
        Поток «{stream.name}». Веса офферов пересчитаются автоматически. Оффер появится в Keitaro
        только после публикации.
      </Text>

      <OfferSelect
        value={offerId}
        onChange={(id) => {
          setOfferId(id);
          setError(null);
        }}
        excludeIds={stream.offers.map((offer) => offer.offer_id)}
        error={error}
      />

      {error ? (
        <Alert color="red" icon={<IconAlertCircle size={18} />}>
          {error}
        </Alert>
      ) : null}

      <Group justify="flex-end">
        <Button variant="default" onClick={onClose} disabled={addOffer.isPending}>
          Отмена
        </Button>
        <Button
          leftSection={<IconPlus size={16} />}
          loading={addOffer.isPending}
          onClick={submit}
          data-testid="add-offer-submit"
        >
          Добавить
        </Button>
      </Group>
    </Stack>
  );
}

import { Alert, Badge, Button, Card, Group, Skeleton, Stack, Text, Tooltip } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconCloudDownload,
  IconCloudUpload,
  IconPlus,
  IconX,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  useCampaign,
  useCampaignEditor,
  useCancelOffers,
  useFetchStreams,
  usePublishOffers,
} from './api';
import { AddOfferModal } from './AddOfferModal';
import { CampaignStreamCard } from './CampaignStreamCard';
import { NotFoundPage } from '@/app/NotFoundPage';
import { errorMessage } from '@/shared/api/client';
import type { CampaignStreamView } from '@/shared/api/types';
import { PageHeader } from '@/shared/ui/PageHeader';
import { EmptyState, ErrorState } from '@/shared/ui/States';
import { CampaignStateBadge } from '@/shared/ui/StatusBadge';

function notifyError(error: unknown) {
  notifications.show({
    title: 'Ошибка',
    message: errorMessage(error),
    color: 'red',
  });
}

export function CampaignEditorPage() {
  const { campaignId } = useParams();
  const parsedId = Number(campaignId);

  if (!Number.isInteger(parsedId) || parsedId <= 0) {
    return <NotFoundPage />;
  }

  return <CampaignEditor campaignId={parsedId} />;
}

function CampaignEditor({ campaignId }: { campaignId: number }) {
  const campaign = useCampaign(campaignId);
  const editor = useCampaignEditor(campaignId);
  const fetchStreams = useFetchStreams(campaignId);
  const publishOffers = usePublishOffers(campaignId);
  const cancelOffers = useCancelOffers(campaignId);
  const [addOfferStream, setAddOfferStream] = useState<CampaignStreamView | null>(null);

  if (campaign.isPending) {
    return (
      <Stack gap="lg">
        <Skeleton height={32} width="45%" />
        <Skeleton height={20} width="65%" />
        <Skeleton height={120} radius="lg" />
        <Skeleton height={260} radius="lg" />
      </Stack>
    );
  }

  if (campaign.isError) {
    return (
      <>
        <PageHeader
          title="Кампания"
          backTo={{ to: '/', label: 'Все кампании' }}
          description="Не удалось получить кампанию из Keitaro."
        />
        <ErrorState error={campaign.error} onRetry={() => void campaign.refetch()} />
      </>
    );
  }

  const data = campaign.data;
  const editorData = editor.data;
  const dirty = editorData?.dirty ?? false;

  return (
    <>
      <PageHeader
        eyebrow={`Кампания #${data.id}`}
        title={data.name}
        description={
          <Group gap={8} mt={4}>
            <Text size="sm" c="dimmed" className="mono">
              {data.alias}
            </Text>
            <CampaignStateBadge state={data.state} />
          </Group>
        }
        backTo={{ to: '/', label: 'Все кампании' }}
        actions={
          <Button
            component={Link}
            to="/campaigns/new"
            leftSection={<IconPlus size={16} />}
            variant="light"
          >
            Новая кампания
          </Button>
        }
      />

      <Card className="kw-card" withBorder={false} p="lg" mb="lg">
        <Group justify="space-between" gap="md" wrap="wrap">
          <Group gap="sm">
            <Tooltip
              label={
                dirty
                  ? 'Сначала опубликуйте или отмените изменения'
                  : 'Загрузить потоки и офферы из Keitaro'
              }
            >
              <Button
                variant="default"
                leftSection={<IconCloudDownload size={16} />}
                loading={fetchStreams.isPending}
                disabled={dirty}
                onClick={() =>
                  fetchStreams.mutate(undefined, {
                    onSuccess: () =>
                      notifications.show({
                        title: 'Потоки загружены',
                        message: 'Данные из Keitaro сохранены локально',
                        color: 'forest',
                      }),
                    onError: notifyError,
                  })
                }
                data-testid="fetch-streams"
              >
                Загрузить потоки
              </Button>
            </Tooltip>

            <Button
              leftSection={<IconCloudUpload size={16} />}
              disabled={!dirty}
              loading={publishOffers.isPending}
              onClick={() =>
                publishOffers.mutate(undefined, {
                  onSuccess: () =>
                    notifications.show({
                      title: 'Изменения опубликованы',
                      message: 'Потоки и веса офферов обновлены в Keitaro',
                      color: 'forest',
                    }),
                  onError: notifyError,
                })
              }
              data-testid="publish-offers"
            >
              Опубликовать
            </Button>

            <Button
              variant="light"
              color="red"
              leftSection={<IconX size={16} />}
              disabled={!dirty}
              loading={cancelOffers.isPending}
              onClick={() =>
                cancelOffers.mutate(undefined, {
                  onSuccess: () =>
                    notifications.show({
                      title: 'Изменения отменены',
                      message: 'Изменения возвращены к последней опубликованной версии',
                      color: 'orange',
                    }),
                  onError: notifyError,
                })
              }
              data-testid="cancel-offers"
            >
              Отмена
            </Button>
          </Group>

          {dirty ? (
            <Badge color="yellow" variant="light">
              Есть неопубликованные изменения
            </Badge>
          ) : editorData?.loaded ? (
            <Badge color="forest" variant="light">
              Всё опубликовано
            </Badge>
          ) : null}
        </Group>
      </Card>

      {editor.isPending ? (
        <Stack gap="md">
          <Skeleton height={160} radius="lg" />
          <Skeleton height={220} radius="lg" />
        </Stack>
      ) : editor.isError ? (
        <ErrorState error={editor.error} onRetry={() => void editor.refetch()} />
      ) : !editorData?.loaded ? (
        <EmptyState
          icon={<IconCloudDownload size={24} />}
          title="Потоки не загружены"
          description="Нажмите «Загрузить потоки», чтобы получить потоки и офферы кампании из Keitaro. Дальше изменения будут копиться локально до публикации."
          action={
            <Button
              leftSection={<IconCloudDownload size={16} />}
              loading={fetchStreams.isPending}
              onClick={() =>
                fetchStreams.mutate(undefined, {
                  onSuccess: () =>
                    notifications.show({
                      title: 'Потоки загружены',
                      message: 'Данные из Keitaro сохранены локально',
                      color: 'forest',
                    }),
                  onError: notifyError,
                })
              }
            >
              Загрузить потоки
            </Button>
          }
        />
      ) : editorData.streams.length === 0 ? (
        <Alert color="gray" icon={<IconAlertCircle size={18} />}>
          В кампании нет потоков.
        </Alert>
      ) : (
        <Stack gap="md">
          {editorData.streams.map((stream) => (
            <CampaignStreamCard
              key={stream.stream_id}
              campaignId={campaignId}
              stream={stream}
              onAddOffer={setAddOfferStream}
            />
          ))}
        </Stack>
      )}

      <AddOfferModal
        opened={addOfferStream !== null}
        onClose={() => setAddOfferStream(null)}
        campaignId={campaignId}
        stream={addOfferStream}
      />
    </>
  );
}

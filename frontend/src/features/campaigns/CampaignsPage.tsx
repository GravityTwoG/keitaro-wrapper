import {
  ActionIcon,
  Anchor,
  Button,
  Card,
  Group,
  Skeleton,
  Stack,
  Table,
  Text,
  TextInput,
  Tooltip,
} from '@mantine/core';
import {
  IconArrowRight,
  IconChevronLeft,
  IconChevronRight,
  IconHash,
  IconPlus,
  IconRefresh,
  IconTargetArrow,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useCampaigns } from './api';
import { formatNumber, pluralize } from '@/shared/lib/format';
import { PageHeader } from '@/shared/ui/PageHeader';
import { EmptyState, ErrorState } from '@/shared/ui/States';
import { CampaignStateBadge } from '@/shared/ui/StatusBadge';

export function CampaignsPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [campaignId, setCampaignId] = useState('');
  const campaigns = useCampaigns(page);
  const items = campaigns.data?.items ?? [];
  const hasMore = campaigns.data?.has_more ?? false;
  const parsedId = Number(campaignId);
  const canOpen = Number.isInteger(parsedId) && parsedId > 0;

  const refreshAll = () => {
    void campaigns.refetch();
  };

  const openCampaign = () => {
    if (canOpen) {
      navigate(`/campaigns/${parsedId}`);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Keitaro"
        title="Кампании"
        description="Создавайте кампании с гео-потоком на Google и редактируйте офферы в существующих кампаниях. Данные читаются напрямую из Keitaro."
        actions={
          <>
            <Tooltip label="Обновить данные">
              <ActionIcon
                variant="default"
                size="lg"
                aria-label="Обновить данные"
                onClick={refreshAll}
                loading={campaigns.isFetching}
              >
                <IconRefresh size={17} />
              </ActionIcon>
            </Tooltip>
            <Button
              component={Link}
              to="/campaigns/new"
              leftSection={<IconPlus size={17} />}
              data-testid="create-campaign-link"
            >
              Создать кампанию
            </Button>
          </>
        }
      />

      <Card className="kw-card" withBorder={false} padding="lg" mb="xl">
        <Group justify="space-between" mb="md" gap="md" align="flex-end">
          <Group gap="xs" align="flex-end">
            <TextInput
              label="Открыть по ID"
              placeholder="Например, 215127"
              leftSection={<IconHash size={16} />}
              value={campaignId}
              onChange={(event) => setCampaignId(event.currentTarget.value.trim())}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  openCampaign();
                }
              }}
              w={{ base: '100%', sm: 220 }}
              data-testid="open-campaign-id"
            />
            <Button
              variant="default"
              disabled={!canOpen}
              onClick={openCampaign}
              data-testid="open-campaign-submit"
            >
              Открыть
            </Button>
          </Group>
          <Text size="sm" c="dimmed">
            {campaigns.data
              ? `На странице: ${formatNumber(items.length)} ${pluralize(items.length, [
                  'кампания',
                  'кампании',
                  'кампаний',
                ])}`
              : 'Загрузка…'}
          </Text>
        </Group>

        {campaigns.isPending ? (
          <Stack gap="sm">
            {[0, 1, 2, 3].map((row) => (
              <Skeleton key={row} height={44} radius="sm" />
            ))}
          </Stack>
        ) : campaigns.isError ? (
          <ErrorState error={campaigns.error} onRetry={() => void campaigns.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={<IconTargetArrow size={24} />}
            title={page > 0 ? 'На этой странице кампаний нет' : 'Кампаний нет'}
            description={
              page > 0
                ? 'Вернитесь на предыдущую страницу.'
                : 'Keitaro вернул пустой список кампаний. Проверьте архив Keitaro: удалённые кампании не попадают в этот список.'
            }
            action={
              page > 0 ? (
                <Button variant="light" onClick={() => setPage((current) => current - 1)}>
                  Назад
                </Button>
              ) : (
                <Button component={Link} to="/campaigns/new" leftSection={<IconPlus size={16} />}>
                  Создать кампанию
                </Button>
              )
            }
          />
        ) : (
          <div className="kw-table-wrap">
            <Table highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Кампания</Table.Th>
                  <Table.Th>Статус</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((campaign) => (
                  <Table.Tr key={campaign.id} data-testid={`campaign-row-${campaign.id}`}>
                    <Table.Td>
                      <Group gap={8} wrap="nowrap">
                        <Stack gap={0}>
                          <Anchor
                            component={Link}
                            to={`/campaigns/${campaign.id}`}
                            fw={700}
                            underline="never"
                          >
                            {campaign.name}
                          </Anchor>
                          <Text size="xs" c="dimmed" className="mono">
                            #{campaign.id} · {campaign.alias}
                          </Text>
                        </Stack>
                      </Group>
                    </Table.Td>
                    <Table.Td>
                      <CampaignStateBadge state={campaign.state} />
                    </Table.Td>
                    <Table.Td>
                      <Group justify="flex-end">
                        <Button
                          component={Link}
                          to={`/campaigns/${campaign.id}`}
                          variant="light"
                          size="xs"
                          rightSection={<IconArrowRight size={14} />}
                        >
                          Редактор
                        </Button>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </div>
        )}

        <Group justify="space-between" mt="md">
          <Text size="xs" c="dimmed">
            Страница {page + 1}
            {campaigns.data ? ` · смещение ${campaigns.data.offset}` : ''}
          </Text>
          <Group gap="xs">
            <Button
              variant="default"
              size="xs"
              leftSection={<IconChevronLeft size={14} />}
              disabled={page === 0 || campaigns.isFetching}
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              data-testid="campaigns-prev"
            >
              Назад
            </Button>
            <Button
              variant="default"
              size="xs"
              rightSection={<IconChevronRight size={14} />}
              disabled={!hasMore || campaigns.isFetching}
              onClick={() => setPage((current) => current + 1)}
              data-testid="campaigns-next"
            >
              Дальше
            </Button>
          </Group>
        </Group>
      </Card>
    </>
  );
}

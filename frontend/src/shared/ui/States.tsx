import { Button, Card, Group, Stack, Text } from '@mantine/core';
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { errorMessage } from '@/shared/api/client';

interface ErrorStateProps {
  error: unknown;
  title?: string;
  onRetry?: () => void;
}

export function ErrorState({
  error,
  title = 'Не удалось загрузить данные',
  onRetry,
}: ErrorStateProps) {
  return (
    <Card className="kw-card" padding="lg" withBorder={false}>
      <Group align="flex-start" wrap="nowrap">
        <IconAlertTriangle size={22} color="var(--mantine-color-red-6)" />
        <Stack gap={4} style={{ flex: 1 }}>
          <Text fw={700}>{title}</Text>
          <Text size="sm" c="dimmed">
            {errorMessage(error)}
          </Text>
        </Stack>
        {onRetry ? (
          <Button
            variant="light"
            color="red"
            size="xs"
            leftSection={<IconRefresh size={14} />}
            onClick={onRetry}
          >
            Повторить
          </Button>
        ) : null}
      </Group>
    </Card>
  );
}

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Card className="kw-card-quiet" padding="xl" withBorder={false}>
      <Stack align="center" gap="sm" py="md">
        <div className="kw-empty-icon">{icon}</div>
        <Text fw={700} size="lg">
          {title}
        </Text>
        <Text c="dimmed" ta="center" maw={460}>
          {description}
        </Text>
        {action}
      </Stack>
    </Card>
  );
}

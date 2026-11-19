import { Button, Container, Group, Stack, Text, Title } from '@mantine/core';
import { IconAlertTriangle, IconArrowLeft, IconRefresh } from '@tabler/icons-react';
import { isRouteErrorResponse, Link, useRouteError } from 'react-router-dom';

export function RouteErrorPage() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : 'Неизвестная ошибка';

  return (
    <Container size="sm" py="xl">
      <Stack align="center" gap="md" py="xl">
        <IconAlertTriangle size={40} color="var(--mantine-color-red-6)" />
        <Title order={1} ta="center">
          Что-то пошло не так
        </Title>
        <Text c="dimmed" ta="center" maw={480}>
          {message}
        </Text>
        <Group>
          <Button
            leftSection={<IconRefresh size={16} />}
            onClick={() => window.location.reload()}
            variant="light"
          >
            Перезагрузить
          </Button>
          <Button component={Link} to="/" leftSection={<IconArrowLeft size={16} />}>
            На главную
          </Button>
        </Group>
      </Stack>
    </Container>
  );
}

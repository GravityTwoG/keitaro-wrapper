import { Button, Container, Stack, Text, Title } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <Container size="sm" py="xl">
      <Stack align="center" gap="md" py="xl">
        <Text className="kw-eyebrow">404</Text>
        <Title order={1} ta="center">
          Страница не найдена
        </Title>
        <Text c="dimmed" ta="center">
          Возможно, кампания была удалена или ссылка устарела.
        </Text>
        <Button component={Link} to="/" leftSection={<IconArrowLeft size={16} />}>
          К списку кампаний
        </Button>
      </Stack>
    </Container>
  );
}

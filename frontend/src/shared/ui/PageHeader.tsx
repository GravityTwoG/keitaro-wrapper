import { Anchor, Group, Stack, Text, Title } from '@mantine/core';
import { IconChevronLeft } from '@tabler/icons-react';
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';

interface PageHeaderProps {
  title: string;
  eyebrow?: string;
  description?: ReactNode;
  backTo?: { to: string; label: string };
  actions?: ReactNode;
}

export function PageHeader({ title, eyebrow, description, backTo, actions }: PageHeaderProps) {
  return (
    <Stack gap="sm" mb="xl">
      {backTo ? (
        <Anchor component={Link} to={backTo.to} size="sm" c="dimmed" underline="never">
          <Group gap={4} wrap="nowrap">
            <IconChevronLeft size={16} />
            {backTo.label}
          </Group>
        </Anchor>
      ) : null}
      <div className="kw-title-row">
        <div>
          {eyebrow ? <div className="kw-eyebrow">{eyebrow}</div> : null}
          <Title order={1}>{title}</Title>
          {description ? (
            <Text c="dimmed" mt={6} maw={720}>
              {description}
            </Text>
          ) : null}
        </div>
        {actions ? <Group gap="sm">{actions}</Group> : null}
      </div>
    </Stack>
  );
}

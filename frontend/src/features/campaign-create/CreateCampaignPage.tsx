import { Alert, Button, Card, Group, Stack, TagsInput, TextInput } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useForm } from '@tanstack/react-form';
import { IconInfoCircle, IconSparkles } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useCreateCampaign } from './api';
import { OfferSelect } from './OfferSelect';
import { errorMessage } from '@/shared/api/client';
import type { CreateCampaignPayload } from '@/shared/api/types';
import { COUNTRY_OPTIONS } from '@/shared/lib/countries';
import { PageHeader } from '@/shared/ui/PageHeader';

interface CreateFormValues {
  name: string;
  geo: string[];
  offerId: number | null;
}

const COUNTRY_CODE = /^[A-Z]{2}$/u;

const DEFAULT_VALUES: CreateFormValues = {
  name: '',
  geo: [],
  offerId: null,
};

function firstError(errors: unknown[]): string | null {
  if (errors.length === 0) {
    return null;
  }
  const [error] = errors;
  return error ? String(error) : null;
}

export function CreateCampaignPage() {
  const navigate = useNavigate();
  const createCampaign = useCreateCampaign();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm({
    defaultValues: DEFAULT_VALUES,
    onSubmit: ({ value }) => {
      if (!value.offerId) {
        return;
      }
      setServerError(null);
      const payload: CreateCampaignPayload = {
        name: value.name.trim(),
        geo: value.geo,
        offer_id: value.offerId,
      };
      createCampaign.mutate(payload, {
        onSuccess: (campaign) => {
          notifications.show({
            title: 'Кампания создана',
            message: `#${campaign.id} · ${campaign.name}`,
            color: 'forest',
          });
          navigate(`/campaigns/${campaign.id}`);
        },
        onError: (error) => {
          const message = errorMessage(error);
          setServerError(message);
          notifications.show({ title: 'Не удалось создать кампанию', message, color: 'red' });
        },
      });
    },
  });

  return (
    <>
      <PageHeader
        eyebrow="Новая кампания"
        title="Создать кампанию"
        description="Обёртка создаст кампанию в Keitaro с двумя потоками: гео-поток на Google и поток с выбранным оффером для остальных. Домен, группа и источник определяются автоматически."
        backTo={{ to: '/', label: 'Все кампании' }}
      />

      <Card className="kw-card" withBorder={false} padding="xl">
        <form
          noValidate
          onSubmit={(event) => {
            event.preventDefault();
            event.stopPropagation();
            void form.handleSubmit();
          }}
        >
          <Stack gap="lg">
            <form.Field
              name="name"
              validators={{
                onChange: ({ value }) =>
                  value.trim().length === 0 ? 'Введите название кампании' : undefined,
                onBlur: ({ value }) =>
                  value.trim().length === 0 ? 'Введите название кампании' : undefined,
                onSubmit: ({ value }) =>
                  value.trim().length === 0 ? 'Введите название кампании' : undefined,
              }}
            >
              {(field) => (
                <TextInput
                  label="Название кампании"
                  placeholder="Например, AU — Beauty RO"
                  required
                  value={field.state.value}
                  onChange={(event) => field.handleChange(event.currentTarget.value)}
                  onBlur={field.handleBlur}
                  error={firstError(field.state.meta.errors)}
                  data-testid="campaign-name"
                />
              )}
            </form.Field>

            <form.Field
              name="geo"
              validators={{
                onChange: ({ value }) => {
                  if (value.length === 0) {
                    return 'Укажите хотя бы одну страну';
                  }
                  const invalid = value.find((code) => !COUNTRY_CODE.test(code));
                  return invalid ? `Некорректный ISO-2 код: ${invalid}` : undefined;
                },
                onSubmit: ({ value }) =>
                  value.length === 0 ? 'Укажите хотя бы одну страну' : undefined,
              }}
            >
              {(field) => (
                <TagsInput
                  label="Гео-код страны"
                  description="ISO 3166-1 alpha-2. Можно добавить несколько стран — они попадут в один фильтр потока."
                  placeholder="AU, DE, RO"
                  data={COUNTRY_OPTIONS}
                  required
                  maxTags={20}
                  value={field.state.value}
                  onChange={(value) =>
                    field.handleChange(
                      value
                        .map((code) => code.trim().toUpperCase())
                        .filter((code) => code.length > 0),
                    )
                  }
                  onBlur={field.handleBlur}
                  error={firstError(field.state.meta.errors)}
                  data-testid="campaign-geo"
                />
              )}
            </form.Field>

            <form.Field
              name="offerId"
              validators={{
                onChange: ({ value }) => (value === null ? 'Выберите оффер' : undefined),
                onSubmit: ({ value }) => (value === null ? 'Выберите оффер' : undefined),
              }}
            >
              {(field) => (
                <OfferSelect
                  value={field.state.value}
                  onChange={(offerId) => field.handleChange(offerId)}
                  error={firstError(field.state.meta.errors)}
                />
              )}
            </form.Field>

            {serverError ? (
              <Alert
                color="red"
                icon={<IconInfoCircle size={18} />}
                title="Keitaro отклонил создание"
                data-testid="create-error"
              >
                {serverError}
              </Alert>
            ) : null}

            <form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
              {([canSubmit, isSubmitting]) => (
                <Group justify="flex-end">
                  <Button
                    type="submit"
                    leftSection={<IconSparkles size={17} />}
                    loading={Boolean(createCampaign.isPending || isSubmitting)}
                    disabled={!canSubmit}
                    data-testid="create-submit"
                  >
                    Создать кампанию
                  </Button>
                </Group>
              )}
            </form.Subscribe>
          </Stack>
        </form>
      </Card>
    </>
  );
}

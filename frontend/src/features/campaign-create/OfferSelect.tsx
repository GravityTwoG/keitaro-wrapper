import { Combobox, Group, Loader, Stack, Text, TextInput, useCombobox } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

import { useOfferSearch } from './api';
import type { OfferSearchItem } from '@/shared/api/types';
import { formatMoney } from '@/shared/lib/format';

const EMPTY_IDS: number[] = [];
const LOAD_MORE_OPTION = '__load_more__';

interface OfferSelectProps {
  value: number | null;
  onChange: (offerId: number | null, offer: OfferSearchItem | null) => void;
  excludeIds?: number[];
  error?: string | null;
  label?: string;
  required?: boolean;
  testId?: string;
}

export function OfferSelect({
  value,
  onChange,
  excludeIds = EMPTY_IDS,
  error = null,
  label = 'Оффер',
  required = true,
  testId = 'offer-select',
}: OfferSelectProps) {
  const combobox = useCombobox({
    onDropdownClose: () => combobox.resetSelectedOption(),
  });
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebouncedValue(search, 250);
  const offers = useOfferSearch(debouncedSearch);
  const loadedOffers = offers.data?.pages.flatMap((page) => page.items) ?? [];

  const excluded = new Set(excludeIds);
  const items = loadedOffers.filter((offer) => !excluded.has(offer.id));

  const handleSelect = (offer: OfferSearchItem) => {
    setSearch(offer.name);
    combobox.closeDropdown();
    onChange(offer.id, offer);
  };

  return (
    <Combobox
      store={combobox}
      onOptionSubmit={(optionValue) => {
        if (optionValue === LOAD_MORE_OPTION) {
          if (offers.hasNextPage && !offers.isFetchingNextPage) {
            void offers.fetchNextPage();
          }
          return;
        }
        const offer = items.find((item) => String(item.id) === optionValue);
        if (offer) {
          handleSelect(offer);
        }
      }}
      width="target"
      position="bottom-start"
    >
      <Combobox.Target>
        <TextInput
          label={label}
          required={required}
          value={search}
          onChange={(event) => {
            setSearch(event.currentTarget.value);
            combobox.openDropdown();
            onChange(null, null);
          }}
          onFocus={() => combobox.openDropdown()}
          onClick={() => combobox.openDropdown()}
          leftSection={<IconSearch size={15} />}
          rightSection={offers.isFetching ? <Loader size={14} /> : <Combobox.Chevron />}
          placeholder="Найдите оффер по названию или ID"
          error={error}
          aria-label={label}
          data-testid={testId}
        />
      </Combobox.Target>

      <Combobox.Dropdown>
        <Combobox.Options mah={340} style={{ overflowY: 'auto' }}>
          {offers.isPending ? (
            <Combobox.Empty>Загрузка…</Combobox.Empty>
          ) : items.length === 0 ? (
            <Combobox.Empty>Ничего не найдено</Combobox.Empty>
          ) : (
            items.map((offer) => (
              <Combobox.Option value={String(offer.id)} key={offer.id} active={offer.id === value}>
                <Stack gap={2}>
                  <Group gap={8} wrap="nowrap">
                    <Text size="xs" className="mono" c="dimmed">
                      #{offer.id}
                    </Text>
                    <Text size="sm" fw={600} lineClamp={2}>
                      {offer.name}
                    </Text>
                  </Group>
                  <Group gap={8}>
                    {offer.payout_value !== null ? (
                      <Text size="xs" c="dimmed">
                        {formatMoney(offer.payout_value, offer.payout_currency)}
                      </Text>
                    ) : null}
                    {offer.country.length > 0 ? (
                      <Text size="xs" c="dimmed" className="mono">
                        {offer.country.join(', ')}
                      </Text>
                    ) : null}
                  </Group>
                </Stack>
              </Combobox.Option>
            ))
          )}
          {offers.hasNextPage ? (
            <Combobox.Option value={LOAD_MORE_OPTION} disabled={offers.isFetchingNextPage}>
              <Text size="sm" fw={600} c="forest.7">
                {offers.isFetchingNextPage ? 'Загрузка…' : 'Показать ещё'}
              </Text>
            </Combobox.Option>
          ) : null}
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}

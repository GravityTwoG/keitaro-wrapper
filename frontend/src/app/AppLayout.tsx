import { Box } from '@mantine/core';
import { IconArrowUpRight } from '@tabler/icons-react';
import { Link, Outlet, useLocation } from 'react-router-dom';

import { HealthBadge } from '@/shared/ui/HealthBadge';

const NAV_ITEMS = [
  {
    to: '/',
    label: 'Кампании',
    match: (pathname: string) => !pathname.startsWith('/campaigns/new'),
  },
  {
    to: '/campaigns/new',
    label: 'Создать',
    match: (pathname: string) => pathname.startsWith('/campaigns/new'),
  },
];

export function AppLayout() {
  const location = useLocation();

  return (
    <>
      <header className="kw-header">
        <div className="kw-header-inner">
          <Link to="/" className="kw-logo">
            <span className="kw-logo-mark">K</span>
            <span>
              <span className="kw-logo-title">Keitaro Wrapper</span>
              <span className="kw-logo-subtitle">ad ops console</span>
            </span>
          </Link>

          <nav className="kw-nav" aria-label="Основная навигация">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="kw-nav-link"
                data-active={item.match(location.pathname)}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="kw-header-spacer" />
          <HealthBadge />
        </div>
      </header>

      <main className="kw-page">
        <Outlet />
      </main>

      <Box component="footer" pb="xl" ta="center">
        <a
          href="https://docs.keitaro.io/en/development/admin-api.html"
          target="_blank"
          rel="noreferrer"
          style={{
            fontSize: '0.75rem',
            color: 'var(--kw-muted)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          Keitaro Admin API
          <IconArrowUpRight size={12} />
        </a>
      </Box>
    </>
  );
}

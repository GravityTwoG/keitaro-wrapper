import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from './AppLayout';
import { NotFoundPage } from './NotFoundPage';
import { RouteErrorPage } from './RouteErrorPage';

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      {
        path: '/',
        lazy: async () => {
          const module = await import('@/features/campaigns/CampaignsPage');
          return { Component: module.CampaignsPage };
        },
      },
      {
        path: '/campaigns/new',
        lazy: async () => {
          const module = await import('@/features/campaign-create/CreateCampaignPage');
          return { Component: module.CreateCampaignPage };
        },
      },
      {
        path: '/campaigns/:campaignId',
        lazy: async () => {
          const module = await import('@/features/campaign-editor/CampaignEditorPage');
          return { Component: module.CampaignEditorPage };
        },
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

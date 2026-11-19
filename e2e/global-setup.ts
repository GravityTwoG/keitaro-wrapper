import { request } from '@playwright/test';

const baseURL = process.env['E2E_BASE_URL'] ?? 'http://127.0.0.1:8080';

export default async function globalSetup(): Promise<void> {
  const context = await request.newContext({ baseURL });
  try {
    for (let attempt = 0; attempt < 60; attempt += 1) {
      try {
        const response = await context.get('/api/v1/health/ready');
        if (response.ok()) {
          return;
        }
      } catch {
        // The stack is still starting.
      }
      await new Promise((resolve) => setTimeout(resolve, 1_000));
    }
    throw new Error(`Stack at ${baseURL} did not become healthy in 60 seconds`);
  } finally {
    await context.dispose();
  }
}

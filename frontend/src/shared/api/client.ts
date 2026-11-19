import type { ApiErrorBody } from './types';

const API_BASE = import.meta.env['VITE_API_BASE_URL'] ?? '/api/v1';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown> | undefined;

  constructor(message: string, status: number, code: string, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function extractErrorMessage(payload: unknown): string {
  if (!isRecord(payload)) {
    return 'Не удалось выполнить запрос';
  }
  if (typeof payload['message'] === 'string' && payload['message']) {
    return payload['message'];
  }
  const detail = payload['detail'];
  if (typeof detail === 'string' && detail) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (isRecord(item) && typeof item['msg'] === 'string' ? item['msg'] : null))
      .filter((item): item is string => Boolean(item));
    if (messages.length > 0) {
      return messages.join('; ');
    }
  }
  return 'Не удалось выполнить запрос';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError('Нет соединения с сервером', 0, 'network_error');
  }

  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    const body = isRecord(payload) ? (payload as unknown as ApiErrorBody) : null;
    throw new ApiError(
      extractErrorMessage(payload),
      response.status,
      body?.code ?? 'http_error',
      body?.details,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  get<T>(path: string): Promise<T> {
    return request<T>(path);
  },
  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
  },
  delete<T>(path: string): Promise<T> {
    return request<T>(path, { method: 'DELETE' });
  },
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return 'Неизвестная ошибка';
}

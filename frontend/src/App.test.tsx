import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { App } from './App';

describe('App', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders tasks and creates a new one', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', service: 'taskpulse', database: 'db', task_count: 1 }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ([{ id: 1, title: 'existing task', completed: false, created_at: 'now' }]) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 2, title: 'new task', completed: false, created_at: 'now' }) });

    vi.stubGlobal('fetch', fetchMock as unknown as typeof fetch);

    render(<App />);

    expect(await screen.findByText('existing task')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('task-title'), { target: { value: 'new task' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add Task' }));

    await waitFor(() => {
      expect(screen.getByText('new task')).toBeInTheDocument();
    });

    expect(fetchMock).toHaveBeenCalledWith('/api/tasks', expect.objectContaining({ method: 'POST' }));
  });
});

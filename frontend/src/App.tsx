import { FormEvent, useEffect, useState } from 'react';

type Task = {
  id: number;
  title: string;
  completed: boolean;
  created_at: string;
};

type Health = {
  status: string;
  service: string;
  database: string;
  task_count: number;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    try {
      const [healthRes, tasksRes] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/tasks`)
      ]);

      if (!healthRes.ok || !tasksRes.ok) {
        throw new Error('Backend request failed');
      }

      const healthJson = (await healthRes.json()) as Health;
      const tasksJson = (await tasksRes.json()) as Task[];
      setHealth(healthJson);
      setTasks(tasksJson);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  };

  useEffect(() => {
    void load();
    const timer = setInterval(() => {
      void load();
    }, 10_000);
    return () => clearInterval(timer);
  }, []);

  const createTask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!title.trim()) {
      return;
    }

    const response = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title })
    });

    if (!response.ok) {
      setError('Failed to create task');
      return;
    }

    const created = (await response.json()) as Task;
    setTasks((current) => [created, ...current]);
    setTitle('');
  };

  const toggleTask = async (taskId: number) => {
    const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: 'PATCH'
    });

    if (!response.ok) {
      setError('Failed to toggle task');
      return;
    }

    const updated = (await response.json()) as Task;
    setTasks((current) => current.map((task) => (task.id === updated.id ? updated : task)));
  };

  return (
    <main className="container">
      <header className="hero">
        <h1>TaskPulse</h1>
        <p>Fullstack benchmark lab for make vs just vs please.</p>
      </header>

      <section className="layout">
        <article className="card">
          <h2>System Health</h2>
          {health ? (
            <>
              <p>
                Status: <span className="status-pill">{health.status}</span>
              </p>
              <p>Service: {health.service}</p>
              <p>Tasks in DB: {health.task_count}</p>
            </>
          ) : (
            <p>Loading health...</p>
          )}
          {error ? <p className="error">{error}</p> : null}
          <button onClick={() => void load()}>Refresh</button>
        </article>

        <article className="card">
          <h2>Create Task</h2>
          <form onSubmit={createTask}>
            <input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="New task title"
              aria-label="task-title"
            />
            <button type="submit">Add Task</button>
          </form>
        </article>
      </section>

      <section className="card" style={{ marginTop: '1rem' }}>
        <h2>Tasks</h2>
        <div className="task-list">
          {tasks.map((task) => (
            <div className={`task-row ${task.completed ? 'done' : ''}`} key={task.id}>
              <span>{task.title}</span>
              <button onClick={() => void toggleTask(task.id)}>
                {task.completed ? 'Undo' : 'Complete'}
              </button>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

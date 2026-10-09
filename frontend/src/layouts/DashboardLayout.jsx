import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import RoleSidebar from '../components/RoleSidebar';

export default function DashboardLayout({ title, children, role, headingLevel = 1 }) {
  const auth = useAuth();
  const user = auth?.user;
  const logout = auth?.logout;
  const navigate = useNavigate();
  const [theme, setTheme] = useState(() => {
    try {
      if (typeof window !== 'undefined' && window.localStorage?.getItem) {
        return window.localStorage.getItem('codemind-theme') || 'light';
      }
    } catch {
      // ignore (e.g. during tests where localStorage is mocked/missing)
    }
    return 'light';
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try {
      if (typeof window !== 'undefined' && window.localStorage?.setItem) {
        window.localStorage.setItem('codemind-theme', theme);
      }
    } catch {
      // ignore in tests/unsupported environments
    }
  }, [theme]);

  const handleLogout = () => {
    logout?.();
    navigate('/login');
  };

  const HeadingTag = headingLevel === 2 ? 'h2' : 'h1';

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)]">
      <div className="flex min-h-screen">
        <RoleSidebar role={role} />

        <main className="flex-1">
          <header className="sticky top-0 z-20 border-b border-[var(--border-subtle)] bg-[var(--surface)]/90 backdrop-blur">
            <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
              <div className="flex items-center gap-3">
                <div>
                  <p className="kicker">{role} Workspace</p>
                  <HeadingTag className="text-lg font-semibold sm:text-xl">{title}</HeadingTag>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="metric-pill hidden sm:inline-flex">{user?.full_name || user?.email || user?.role || 'User'}</span>
                <button className="btn-secondary hidden sm:inline-flex" onClick={() => setTheme((current) => (current === 'dark' ? 'light' : 'dark'))}>
                  {theme === 'dark' ? 'Light' : 'Dark'}
                </button>
              </div>
            </div>
          </header>
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

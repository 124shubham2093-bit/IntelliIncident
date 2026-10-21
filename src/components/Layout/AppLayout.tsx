import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  SearchCode,
  BrainCircuit,
  FileText,
  ShieldCheck,
  Menu,
  X,
  Clock,
  Server,
  Layers,
  Sun,
  Moon,
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { getGitHubStatus } from '@/api/github';

export const AppLayout: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [githubStatus, setGithubStatus] = useState<'Operational' | 'Unconfigured' | 'Unreachable' | 'Checking'>('Checking');
  const location = useLocation();

  useEffect(() => {
    let isMounted = true;
    getGitHubStatus()
      .then(({ data }) => {
        if (!isMounted) return;
        if (data && data.reachable && data.configured) {
          setGithubStatus('Operational');
        } else if (data && !data.configured) {
          setGithubStatus('Unconfigured');
        } else {
          setGithubStatus('Unreachable');
        }
      })
      .catch(() => {
        if (!isMounted) return;
        setGithubStatus('Unreachable');
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/incidents', label: 'Incidents', icon: AlertTriangle },
    { to: '/investigation', label: 'Investigation', icon: SearchCode },
    { to: '/topology', label: 'Applications', icon: Server },
    { to: '/ml-analytics', label: 'ML Analytics', icon: BrainCircuit },
    { to: '/reports', label: 'Reports', icon: FileText },
  ];

  const nowUTC = new Date().toISOString().replace('T', ' ').substring(0, 16) + ' UTC';

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans antialiased transition-colors duration-150">
      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden backdrop-blur-xs"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Persistent Enterprise Sidebar */}
      <aside
        className={`fixed md:sticky top-0 z-50 h-screen w-64 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        } no-print`}
      >
        {/* Brand & Navigation */}
        <div>
          <div className="h-16 px-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-slate-100 block leading-tight">
                  IntelliIncident
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-normal block">
                  Incident Management
                </span>
              </div>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-1 rounded md:hidden text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive =
                location.pathname === item.to ||
                (item.to === '/incidents' && location.pathname.startsWith('/incidents/'));
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 font-semibold border-l-2 border-blue-600 pl-2.5'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* System Status Section at Sidebar Bottom */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/60">
          <div className="flex items-center justify-between mb-2.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              System Status
            </span>
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Operational
            </span>
          </div>

          <div className="space-y-1.5 text-xs">
            {/* Frontend */}
            <div className="flex items-center justify-between py-1 border-b border-slate-200/60 dark:border-slate-800/60">
              <span className="text-slate-600 dark:text-slate-400">Frontend</span>
              <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Ready
              </span>
            </div>

            {/* API Gateway */}
            <div className="flex items-center justify-between py-1 border-b border-slate-200/60 dark:border-slate-800/60">
              <span className="text-slate-600 dark:text-slate-400">API Gateway</span>
              <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Connected
              </span>
            </div>

            {/* ML Models */}
            <div className="flex items-center justify-between py-1 border-b border-slate-200/60 dark:border-slate-800/60">
              <span className="text-slate-600 dark:text-slate-400">ML Engine</span>
              <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Ready
              </span>
            </div>

            {/* Fuzzy Engine */}
            <div className="flex items-center justify-between py-1 border-b border-slate-200/60 dark:border-slate-800/60">
              <span className="text-slate-600 dark:text-slate-400">Fuzzy Logic</span>
              <span className="flex items-center gap-1.5 text-slate-700 dark:text-slate-300 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                Ready
              </span>
            </div>

            {/* GitHub Integration */}
            <div className="flex items-center justify-between py-1" title={`GitHub code intelligence: ${githubStatus}`}>
              <span className="text-slate-600 dark:text-slate-400">GitHub</span>
              <span
                className={`flex items-center gap-1.5 font-medium ${
                  githubStatus === 'Operational'
                    ? 'text-emerald-700 dark:text-emerald-400'
                    : githubStatus === 'Unconfigured'
                    ? 'text-slate-500 dark:text-slate-400'
                    : githubStatus === 'Unreachable'
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-slate-500'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    githubStatus === 'Operational'
                      ? 'bg-emerald-500'
                      : githubStatus === 'Unconfigured'
                      ? 'bg-slate-400'
                      : githubStatus === 'Unreachable'
                      ? 'bg-red-500'
                      : 'bg-slate-400'
                  }`}
                />
                {githubStatus}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-30 px-4 sm:px-6 flex items-center justify-between no-print shadow-xs transition-colors duration-150">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 rounded-md md:hidden text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2 text-sm">
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                Production
              </span>
              <span className="text-slate-300 dark:text-slate-700 hidden sm:inline">|</span>
              <span className="text-slate-600 dark:text-slate-400 font-medium hidden sm:inline">
                Incident Response & Investigation Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Dark / Light Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              type="button"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/80 transition-colors text-xs font-medium cursor-pointer shadow-2xs"
              title={theme === 'dark' ? 'Switch to Light mode' : 'Switch to Dark mode'}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span className="hidden sm:inline">Light</span>
                </>
              ) : (
                <>
                  <Moon className="w-3.5 h-3.5 text-slate-600" />
                  <span className="hidden sm:inline">Dark</span>
                </>
              )}
            </button>

            <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 px-2.5 py-1 rounded-md border border-slate-200 dark:border-slate-700">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{nowUTC}</span>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-slate-700 dark:text-slate-300 px-2.5 py-1 rounded-md bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Healthy</span>
            </div>
          </div>
        </header>

        {/* Route Page Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

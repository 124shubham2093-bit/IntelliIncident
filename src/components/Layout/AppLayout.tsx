import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  SearchCode,
  BrainCircuit,
  Sliders,
  FileText,
  ShieldCheck,
  Menu,
  X,
  Radio,
  Clock,
  Activity,
  Server,
} from 'lucide-react';
import { getGitHubStatus } from '@/api/github';

export const AppLayout: React.FC = () => {
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
    { to: '/fuzzy-risk', label: 'Fuzzy Risk', icon: Sliders },
    { to: '/reports', label: 'Reports', icon: FileText },
  ];

  const nowUTC = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';

  return (
    <div className="flex min-h-screen bg-[#0b0f19] text-slate-100 font-sans antialiased">
      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/70 z-40 md:hidden backdrop-blur-xs"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Persistent Sidebar */}
      <aside
        className={`fixed md:sticky top-0 z-50 h-screen w-64 bg-[#0d1322] border-r border-slate-800 flex flex-col justify-between transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        } no-print`}
      >
        {/* Brand & Navigation */}
        <div>
          <div className="h-16 px-5 border-b border-slate-800/90 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
                <Radio className="w-4 h-4 text-teal-400" />
              </div>
              <div>
                <span className="font-bold tracking-tight text-base font-mono text-slate-100 flex items-center gap-1.5">
                  IntelliIncident
                </span>
                <span className="text-[10px] font-mono text-slate-400 tracking-wider block">
                  Incident Intelligence
                </span>
              </div>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="p-1 rounded md:hidden text-slate-400 hover:text-white"
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
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-xs font-mono font-medium transition-colors ${
                    isActive
                      ? 'bg-teal-500/15 text-teal-300 border border-teal-500/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-teal-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* System Status Section at Sidebar Bottom */}
        <div className="p-4 border-t border-slate-800 bg-[#090d18]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
              System Telemetry
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-teal-500/10 text-teal-400 border border-teal-500/30 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse"></span>
              Live
            </span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            {/* Frontend */}
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400 text-[11px]">Frontend</span>
              <span className="flex items-center gap-1.5 text-teal-400 text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                Operational
              </span>
            </div>

            {/* API Gateway */}
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400 text-[11px]">API Gateway</span>
              <span className="flex items-center gap-1.5 text-teal-400 text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                Operational
              </span>
            </div>

            {/* ML Models */}
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400 text-[11px]">ML Models</span>
              <span className="flex items-center gap-1.5 text-teal-400 text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                Active
              </span>
            </div>

            {/* Fuzzy Engine */}
            <div className="flex items-center justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400 text-[11px]">Fuzzy Engine</span>
              <span className="flex items-center gap-1.5 text-teal-400 text-[11px] font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400"></span>
                Active
              </span>
            </div>

            {/* GitHub Intelligence */}
            <div className="flex items-center justify-between py-1" title={`GitHub code intelligence: ${githubStatus}`}>
              <span className="text-slate-400 text-[11px]">GitHub Intel</span>
              <span
                className={`flex items-center gap-1.5 text-[11px] font-medium ${
                  githubStatus === 'Operational'
                    ? 'text-teal-400'
                    : githubStatus === 'Unconfigured'
                    ? 'text-slate-400'
                    : githubStatus === 'Unreachable'
                    ? 'text-rose-400'
                    : 'text-slate-500'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    githubStatus === 'Operational'
                      ? 'bg-teal-400'
                      : githubStatus === 'Unconfigured'
                      ? 'bg-slate-500'
                      : githubStatus === 'Unreachable'
                      ? 'bg-rose-400'
                      : 'bg-slate-500 animate-pulse'
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
        <header className="h-14 bg-[#0d1322]/80 border-b border-slate-800 sticky top-0 z-30 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between no-print">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 rounded-md md:hidden text-slate-400 hover:text-white hover:bg-slate-800"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
              <Activity className="w-3.5 h-3.5 text-teal-400" />
              <span className="text-slate-200 font-semibold tracking-wide">
                Operations Platform
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs font-mono text-slate-400 bg-slate-900 px-2.5 py-1 rounded border border-slate-800">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>{nowUTC}</span>
            </div>

            <div className="flex items-center gap-1.5 text-xs font-mono text-slate-300 px-2.5 py-1 rounded bg-slate-900 border border-slate-800">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
              <span>SRE Telemetry</span>
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

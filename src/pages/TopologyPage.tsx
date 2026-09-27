import React, { useEffect, useState } from 'react';
import {
  Layers,
  Server,
  Globe,
  GitBranch,
  GitCommit,
  Copy,
  Check,
  Terminal,
  Plus,
  Trash2,
  Key,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  ShieldAlert,
  Code2,
  X,
} from 'lucide-react';
import {
  Project,
  Application,
  Environment,
  ConnectionGuide,
  IngestionTestResult,
  GitHubApplicationVerification,
} from '@/types';
import {
  getProjects,
  createProject,
  deleteProject,
  getApplications,
  createApplication,
  deleteApplication,
  getEnvironments,
  createEnvironment,
  deleteEnvironment,
  regenerateEnvironmentKey,
  getConnectionGuide,
  testEnvironmentIngestion,
  verifyApplicationGitHub,
  updateEnvironmentCommit,
} from '@/api/projects';

export const TopologyPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [appsByProject, setAppsByProject] = useState<Record<string, Application[]>>({});
  const [envsByApp, setEnvsByApp] = useState<Record<string, Environment[]>>({});
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modals state
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showAppModalForProject, setShowAppModalForProject] = useState<string | null>(null);
  const [showEnvModalForApp, setShowEnvModalForApp] = useState<string | null>(null);
  const [newKeyDialog, setNewKeyDialog] = useState<{ key: string; preview: string; envName: string } | null>(null);
  const [activeGuide, setActiveGuide] = useState<ConnectionGuide | null>(null);
  const [activeGuideTab, setActiveGuideTab] = useState<'curl' | 'python' | 'node' | 'github'>('curl');
  const [testResult, setTestResult] = useState<{ envId: string; res: IngestionTestResult | null; err: string | null } | null>(null);
  const [testingEnvId, setTestingEnvId] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [ghVerificationMap, setGhVerificationMap] = useState<Record<string, GitHubApplicationVerification>>({});
  const [verifyingAppId, setVerifyingAppId] = useState<string | null>(null);

  // Form states
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  const [newAppName, setNewAppName] = useState('');
  const [newAppDesc, setNewAppDesc] = useState('');
  const [newAppLang, setNewAppLang] = useState('python');
  const [newAppFramework, setNewAppFramework] = useState('FastAPI');
  const [newAppRepoOwner, setNewAppRepoOwner] = useState('');
  const [newAppRepoName, setNewAppRepoName] = useState('');
  const [newAppDefaultBranch, setNewAppDefaultBranch] = useState('main');

  const [newEnvName, setNewEnvName] = useState('production');
  const [newEnvUrl, setNewEnvUrl] = useState('');
  const [newEnvCommit, setNewEnvCommit] = useState('');
  const [newEnvIsProd, setNewEnvIsProd] = useState(true);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const projRes = await getProjects();
      setProjects(projRes.data);

      const appsMap: Record<string, Application[]> = {};
      const envsMap: Record<string, Environment[]> = {};

      for (const p of projRes.data) {
        const appsRes = await getApplications(p.id);
        appsMap[p.id] = appsRes.data;

        for (const a of appsRes.data) {
          const envsRes = await getEnvironments(a.id);
          envsMap[a.id] = envsRes.data;

          // Trigger background GitHub verification for applications with repository bindings
          if (a.repo_owner && a.repo_name) {
            verifyApplicationGitHub(a.id)
              .then((vRes) => {
                setGhVerificationMap((prev) => ({ ...prev, [a.id]: vRes }));
              })
              .catch(() => {});
          }
        }
      }

      setAppsByProject(appsMap);
      setEnvsByApp(envsMap);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load system topology.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      await createProject({
        name: newProjectName.trim(),
        description: newProjectDesc.trim() || undefined,
      });
      setShowProjectModal(false);
      setNewProjectName('');
      setNewProjectDesc('');
      await loadData();
    } catch (err: any) {
      alert(`Failed to create project: ${err.message}`);
    }
  };

  const handleDeleteProject = async (projectId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete project "${name}"? Dependent applications must be removed first.`)) {
      return;
    }
    try {
      await deleteProject(projectId);
      await loadData();
    } catch (err: any) {
      alert(`Deletion rejected: ${err.message}`);
    }
  };

  const handleCreateApp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showAppModalForProject || !newAppName.trim()) return;
    try {
      await createApplication(showAppModalForProject, {
        name: newAppName.trim(),
        description: newAppDesc.trim() || undefined,
        language: newAppLang,
        framework: newAppFramework.trim() || undefined,
        repo_owner: newAppRepoOwner.trim() || undefined,
        repo_name: newAppRepoName.trim() || undefined,
        default_branch: newAppDefaultBranch.trim() || 'main',
      });
      setShowAppModalForProject(null);
      setNewAppName('');
      setNewAppDesc('');
      setNewAppRepoOwner('');
      setNewAppRepoName('');
      await loadData();
    } catch (err: any) {
      alert(`Failed to create application: ${err.message}`);
    }
  };

  const handleDeleteApp = async (appId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete application "${name}"? Environments must be removed first.`)) {
      return;
    }
    try {
      await deleteApplication(appId);
      await loadData();
    } catch (err: any) {
      alert(`Deletion rejected: ${err.message}`);
    }
  };

  const handleCreateEnv = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showEnvModalForApp || !newEnvName.trim()) return;
    try {
      const created = await createEnvironment(showEnvModalForApp, {
        name: newEnvName.trim(),
        endpoint_url: newEnvUrl.trim() || undefined,
        current_commit: newEnvCommit.trim() || undefined,
        is_production: newEnvIsProd,
      });

      setShowEnvModalForApp(null);
      setNewEnvName('production');
      setNewEnvUrl('');
      setNewEnvCommit('');
      setNewEnvIsProd(true);

      // Show one-time key revelation dialog
      if (created.api_key) {
        setNewKeyDialog({
          key: created.api_key,
          preview: created.api_key_preview,
          envName: created.name,
        });
      }

      await loadData();
    } catch (err: any) {
      alert(`Failed to create environment: ${err.message}`);
    }
  };

  const handleDeleteEnv = async (envId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete environment "${name}"?`)) {
      return;
    }
    try {
      await deleteEnvironment(envId);
      await loadData();
    } catch (err: any) {
      alert(`Deletion rejected: ${err.message}`);
    }
  };

  const handleRegenerateKey = async (envId: string, name: string) => {
    if (!confirm(`Regenerate API key for environment "${name}"? The previous key will be immediately invalidated.`)) {
      return;
    }
    try {
      const regenerated = await regenerateEnvironmentKey(envId);
      setNewKeyDialog({
        key: regenerated.api_key,
        preview: regenerated.api_key_preview,
        envName: name,
      });
      await loadData();
    } catch (err: any) {
      alert(`Failed to regenerate API key: ${err.message}`);
    }
  };

  const handleOpenGuide = async (envId: string) => {
    try {
      const guideRes = await getConnectionGuide(envId);
      if (guideRes.data) {
        setActiveGuide(guideRes.data);
      }
    } catch (err: any) {
      alert(`Failed to fetch connection guide: ${err.message}`);
    }
  };

  const handleTestIngestion = async (envId: string) => {
    setTestingEnvId(envId);
    setTestResult(null);
    try {
      const res = await testEnvironmentIngestion(envId);
      setTestResult({ envId, res, err: null });
    } catch (err: any) {
      setTestResult({ envId, res: null, err: err.message || 'Ingestion test failed' });
    } finally {
      setTestingEnvId(null);
    }
  };

  const handleVerifyGitHub = async (appId: string) => {
    setVerifyingAppId(appId);
    try {
      const res = await verifyApplicationGitHub(appId);
      setGhVerificationMap((prev) => ({ ...prev, [appId]: res }));
    } catch (err: any) {
      alert(`GitHub verification failed: ${err.message}`);
    } finally {
      setVerifyingAppId(null);
    }
  };

  const handleUpdateCommit = async (envId: string, currentVal: string) => {
    const input = prompt('Enter deployed Git commit SHA for this environment:', currentVal);
    if (input === null) return;
    try {
      await updateEnvironmentCommit(envId, input.trim());
      await loadData();
    } catch (err: any) {
      alert(`Failed to update deployment commit: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string, isSnippet = false) => {
    navigator.clipboard.writeText(text);
    if (isSnippet) {
      setCopiedSnippet(true);
      setTimeout(() => setCopiedSnippet(false), 2000);
    } else {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-teal-400" />
            <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
              System Topology & Connected Applications
            </h1>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Manage organizational software hierarchy, application code repositories, and environment ingestion keys.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowProjectModal(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-mono text-xs font-semibold transition-colors shadow-sm cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>New Project</span>
          </button>
          <button
            onClick={loadData}
            title="Refresh Topology"
            className="p-1.5 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded text-rose-300 text-xs font-mono flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="py-16 text-center text-xs font-mono text-slate-400">
          Loading system topology hierarchy...
        </div>
      ) : projects.length === 0 ? (
        /* Empty State */
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-10 text-center space-y-4 max-w-2xl mx-auto my-8">
          <div className="w-12 h-12 rounded-full bg-slate-950 border border-slate-800 flex items-center justify-center mx-auto text-teal-400">
            <Layers className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="text-sm font-semibold font-mono text-slate-200">
              No applications connected yet.
            </h3>
            <p className="text-xs text-slate-400 font-sans max-w-md mx-auto leading-relaxed">
              Create your first software project to register applications, bind GitHub repositories,
              and generate environment ingestion API keys.
            </p>
          </div>
          <div>
            <button
              onClick={() => setShowProjectModal(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-mono text-xs font-semibold transition-colors cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Create Project</span>
            </button>
          </div>
        </div>
      ) : (
        /* Projects Hierarchy List */
        <div className="space-y-6">
          {projects.map((project) => {
            const apps = appsByProject[project.id] || [];
            return (
              <div
                key={project.id}
                className="bg-slate-900/80 border border-slate-800 rounded-lg overflow-hidden shadow-sm"
              >
                {/* Project Header Bar */}
                <div className="p-4 bg-slate-950/80 border-b border-slate-800/90 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Layers className="w-4 h-4 text-teal-400" />
                      <h2 className="text-sm font-bold font-mono text-slate-100 uppercase tracking-wide">
                        {project.name}
                      </h2>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                        slug: {project.slug}
                      </span>
                    </div>
                    {project.description && (
                      <p className="text-xs text-slate-400 font-sans">{project.description}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowAppModalForProject(project.id)}
                      className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-mono text-xs transition-colors cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5 text-teal-400" />
                      <span>Add Application</span>
                    </button>
                    <button
                      onClick={() => handleDeleteProject(project.id, project.name)}
                      className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                      title="Delete Project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Applications Inside Project */}
                <div className="p-4 space-y-4">
                  {apps.length === 0 ? (
                    <div className="py-6 text-center text-xs font-mono text-slate-500 border border-dashed border-slate-800 rounded">
                      No applications registered in this project. Click "+ Add Application" to connect a service.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 gap-4">
                      {apps.map((app) => {
                        const envs = envsByApp[app.id] || [];
                        return (
                          <div
                            key={app.id}
                            className="bg-slate-950/60 border border-slate-800/80 rounded-md p-4 space-y-3"
                          >
                            {/* App Header */}
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800/60">
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <Server className="w-4 h-4 text-cyan-400" />
                                  <h3 className="text-xs font-bold font-mono text-slate-200">
                                    {app.name}
                                  </h3>
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                                    slug: {app.slug}
                                  </span>
                                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                    {app.language} {app.framework ? `• ${app.framework}` : ''}
                                  </span>
                                </div>
                                {app.description && (
                                  <p className="text-[11px] text-slate-400">{app.description}</p>
                                )}
                              </div>

                              {/* GitHub Binding Info & Connection Verification */}
                              <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                                {app.repo_owner && app.repo_name ? (
                                  <div className="flex flex-col gap-1">
                                    <div className="flex items-center gap-2">
                                      <div className="flex items-center gap-1.5 text-xs font-mono text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
                                        <GitBranch className="w-3.5 h-3.5" />
                                        <span>
                                          {app.repo_owner}/{app.repo_name}
                                        </span>
                                        <span className="text-[10px] text-teal-300/70">
                                          ({app.default_branch})
                                        </span>
                                      </div>

                                      <button
                                        onClick={() => handleVerifyGitHub(app.id)}
                                        disabled={verifyingAppId === app.id}
                                        className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 flex items-center gap-1 transition-colors"
                                        title="Verify repository and branch accessibility"
                                      >
                                        <CheckCircle2 className={`w-3 h-3 ${verifyingAppId === app.id ? 'animate-spin text-teal-400' : 'text-slate-400'}`} />
                                        <span>{verifyingAppId === app.id ? 'Checking...' : 'Verify'}</span>
                                      </button>
                                    </div>

                                    {/* Factual GitHub Connection Status Badge */}
                                    {ghVerificationMap[app.id] && (
                                      <div className={`p-2 rounded text-[10px] font-mono border ${
                                        ghVerificationMap[app.id].connected
                                          ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
                                          : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
                                      }`}>
                                        <div className="flex items-center gap-2 font-semibold">
                                          <span>GitHub:</span>
                                          <span>{ghVerificationMap[app.id].connected ? '✓ Connected' : '✗ Verification Failed'}</span>
                                        </div>
                                        <div className="grid grid-cols-2 gap-x-3 text-[9px] text-slate-400 mt-0.5">
                                          <div>Repo: <span className={ghVerificationMap[app.id].repository_accessible ? 'text-emerald-400 font-semibold' : 'text-rose-400'}>{ghVerificationMap[app.id].repository_accessible ? 'Accessible' : 'Not Found'}</span></div>
                                          <div>Branch: <span className={ghVerificationMap[app.id].branch_accessible ? 'text-emerald-400 font-semibold' : 'text-rose-400'}>{ghVerificationMap[app.id].branch_accessible ? 'Accessible' : 'Not Found'}</span></div>
                                        </div>
                                        {ghVerificationMap[app.id].message && (
                                          <div className="text-[9px] mt-0.5 text-slate-400 italic">
                                            {ghVerificationMap[app.id].message}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <span className="text-[11px] font-mono text-slate-500 italic">
                                    Inherits Global GitHub Repository
                                  </span>
                                )}

                                <div className="flex items-center gap-2 ml-auto">
                                  <button
                                    onClick={() => setShowEnvModalForApp(app.id)}
                                    className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 border border-slate-800 text-[11px] font-mono text-slate-300 transition-colors"
                                  >
                                    <Plus className="w-3 h-3 text-teal-400" />
                                    <span>Add Environment</span>
                                  </button>
                                  <button
                                    onClick={() => handleDeleteApp(app.id, app.name)}
                                    className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                                    title="Delete Application"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>
                            </div>

                            {/* Environments for App */}
                            <div className="space-y-2">
                              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block">
                                Deployment Environments ({envs.length})
                              </span>

                              {envs.length === 0 ? (
                                <p className="text-xs font-mono text-slate-500 italic">
                                  No environments defined. Add Production or Staging to generate an ingestion key.
                                </p>
                              ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                  {envs.map((env) => (
                                    <div
                                      key={env.id}
                                      className="bg-slate-900/60 border border-slate-800 rounded p-3 space-y-2 text-xs font-mono"
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-1.5">
                                          <span
                                            className={`w-2 h-2 rounded-full ${
                                              env.is_production ? 'bg-emerald-400' : 'bg-amber-400'
                                            }`}
                                          />
                                          <span className="font-semibold text-slate-200">
                                            {env.name}
                                          </span>
                                        </div>
                                        <span
                                          className={`text-[10px] px-1.5 py-0.2 rounded border ${
                                            env.is_production
                                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                          }`}
                                        >
                                          {env.is_production ? 'PROD' : 'NON-PROD'}
                                        </span>
                                      </div>

                                      {/* Masked Key & Actions */}
                                      <div className="p-1.5 bg-slate-950 rounded border border-slate-800 flex items-center justify-between text-[11px]">
                                        <div className="flex items-center gap-1 text-slate-400">
                                          <Key className="w-3 h-3 text-slate-400" />
                                          <span className="text-slate-300">{env.api_key_preview}</span>
                                        </div>
                                        <button
                                          onClick={() => handleRegenerateKey(env.id, env.name)}
                                          title="Regenerate API Key"
                                          className="text-[10px] text-amber-400/80 hover:text-amber-300 transition-colors"
                                        >
                                          Regenerate
                                        </button>
                                      </div>

                                      {/* Endpoint / Commit Metadata */}
                                      <div className="text-[10px] text-slate-400 space-y-1">
                                        {env.endpoint_url && (
                                          <div className="truncate flex items-center gap-1">
                                            <Globe className="w-3 h-3 shrink-0" />
                                            <span className="truncate">{env.endpoint_url}</span>
                                          </div>
                                        )}
                                        <div className="flex items-center justify-between gap-1 p-1.5 bg-slate-950/80 rounded border border-slate-800">
                                          <div className="flex items-center gap-1.5 truncate">
                                            <GitCommit className="w-3 h-3 shrink-0 text-cyan-400" />
                                            <span className="text-slate-400">Deployed commit:</span>
                                            <span className="text-cyan-400 font-semibold" title={env.current_commit || 'None'}>
                                              {env.current_commit ? env.current_commit.slice(0, 7) : 'Not set'}
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-1.5 shrink-0">
                                            {env.current_commit && (
                                              <button
                                                onClick={() => copyToClipboard(env.current_commit || '')}
                                                className="text-[9px] text-slate-500 hover:text-slate-300"
                                                title="Copy full commit SHA"
                                              >
                                                Copy
                                              </button>
                                            )}
                                            <button
                                              onClick={() => handleUpdateCommit(env.id, env.current_commit || '')}
                                              className="text-[9px] text-cyan-400 hover:text-cyan-300"
                                              title="Update deployed commit"
                                            >
                                              Edit
                                            </button>
                                          </div>
                                        </div>
                                      </div>

                                      {/* Action Buttons */}
                                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between gap-1 text-[11px]">
                                        <button
                                          onClick={() => handleOpenGuide(env.id)}
                                          className="flex items-center gap-1 px-2 py-1 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 border border-teal-500/30 transition-colors"
                                        >
                                          <Code2 className="w-3 h-3" />
                                          <span>Connect</span>
                                        </button>

                                        <button
                                          onClick={() => handleTestIngestion(env.id)}
                                          disabled={testingEnvId === env.id}
                                          className="flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                                        >
                                          <Terminal className="w-3 h-3" />
                                          <span>{testingEnvId === env.id ? 'Testing...' : 'Test Ingestion'}</span>
                                        </button>

                                        <button
                                          onClick={() => handleDeleteEnv(env.id, env.name)}
                                          className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                                          title="Delete Environment"
                                        >
                                          <Trash2 className="w-3 h-3" />
                                        </button>
                                      </div>

                                      {/* Ingestion Test Feedback if active */}
                                      {testResult && testResult.envId === env.id && (
                                        <div
                                          className={`p-1.5 rounded text-[10px] flex items-center gap-1 border ${
                                            testResult.res
                                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                                          }`}
                                        >
                                          {testResult.res ? (
                                            <>
                                              <CheckCircle2 className="w-3 h-3 shrink-0" />
                                              <span>Channel Verified & Active</span>
                                            </>
                                          ) : (
                                            <>
                                              <AlertCircle className="w-3 h-3 shrink-0" />
                                              <span>{testResult.err}</span>
                                            </>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ==========================================
          MODALS
         ========================================== */}

      {/* 1. Create Project Modal */}
      {showProjectModal && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#0e1424] border border-slate-800 rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                <Layers className="w-4 h-4 text-teal-400" />
                <span>Create New Software Project</span>
              </h3>
              <button
                onClick={() => setShowProjectModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-3 text-xs font-mono">
              <div>
                <label className="text-slate-300 block mb-1">Project Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. E-Commerce Core, Fintech Platform"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="High-level product scope, team ownership, or service domain"
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60 font-sans"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowProjectModal(false)}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. Create Application Modal */}
      {showAppModalForProject && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#0e1424] border border-slate-800 rounded-lg max-w-lg w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                <Server className="w-4 h-4 text-cyan-400" />
                <span>Register Application / Microservice</span>
              </h3>
              <button
                onClick={() => setShowAppModalForProject(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateApp} className="space-y-3 text-xs font-mono">
              <div>
                <label className="text-slate-300 block mb-1">Application Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Payment Gateway, Checkout API"
                  value={newAppName}
                  onChange={(e) => setNewAppName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-300 block mb-1">Runtime / Language *</label>
                  <select
                    value={newAppLang}
                    onChange={(e) => setNewAppLang(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                  >
                    <option value="python">Python</option>
                    <option value="typescript">TypeScript / Node.js</option>
                    <option value="go">Go</option>
                    <option value="java">Java</option>
                    <option value="rust">Rust</option>
                    <option value="ruby">Ruby</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-300 block mb-1">Framework</label>
                  <input
                    type="text"
                    placeholder="e.g. FastAPI, Express, Spring"
                    value={newAppFramework}
                    onChange={(e) => setNewAppFramework(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                  />
                </div>
              </div>

              {/* GitHub Repository Binding Section */}
              <div className="p-3 bg-slate-950 border border-slate-800 rounded space-y-2">
                <div className="flex items-center gap-1.5 text-teal-400 font-semibold text-[11px]">
                  <GitBranch className="w-3.5 h-3.5" />
                  <span>GitHub Repository Binding (Optional)</span>
                </div>
                <p className="text-[10px] text-slate-400 font-sans">
                  Bind this specific application to its GitHub repository so RCA analyzes the exact source code and diffs. Leave blank to inherit default global repository.
                </p>

                <div className="grid grid-cols-3 gap-2 pt-1">
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Repo Owner</label>
                    <input
                      type="text"
                      placeholder="e.g. 124shubham2093-bit"
                      value={newAppRepoOwner}
                      onChange={(e) => setNewAppRepoOwner(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-teal-500/60"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Repo Name</label>
                    <input
                      type="text"
                      placeholder="e.g. payment-service"
                      value={newAppRepoName}
                      onChange={(e) => setNewAppRepoName(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-teal-500/60"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-400 block mb-0.5">Branch</label>
                    <input
                      type="text"
                      placeholder="main"
                      value={newAppDefaultBranch}
                      onChange={(e) => setNewAppDefaultBranch(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-2 py-1 text-[11px] text-slate-200 focus:outline-none focus:border-teal-500/60"
                    />
                  </div>
                </div>
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Description (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Service role and architectural scope"
                  value={newAppDesc}
                  onChange={(e) => setNewAppDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60 font-sans"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAppModalForProject(null)}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold"
                >
                  Register Application
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. Create Environment Modal */}
      {showEnvModalForApp && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#0e1424] border border-slate-800 rounded-lg max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                <Key className="w-4 h-4 text-emerald-400" />
                <span>Add Environment & Generate Key</span>
              </h3>
              <button
                onClick={() => setShowEnvModalForApp(null)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateEnv} className="space-y-3 text-xs font-mono">
              <div>
                <label className="text-slate-300 block mb-1">Environment Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. production, staging, canary"
                  value={newEnvName}
                  onChange={(e) => setNewEnvName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Deployment URL (Optional)</label>
                <input
                  type="url"
                  placeholder="https://api.internal.service"
                  value={newEnvUrl}
                  onChange={(e) => setNewEnvUrl(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60"
                />
              </div>

              <div>
                <label className="text-slate-300 block mb-1">Current Active Git Commit SHA (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. 7f3a8b2"
                  value={newEnvCommit}
                  onChange={(e) => setNewEnvCommit(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-200 focus:outline-none focus:border-teal-500/60 font-mono"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="isProd"
                  checked={newEnvIsProd}
                  onChange={(e) => setNewEnvIsProd(e.target.checked)}
                  className="rounded bg-slate-950 border-slate-800 text-teal-500 focus:ring-0"
                />
                <label htmlFor="isProd" className="text-slate-300 cursor-pointer">
                  Mark as Production Tier Environment
                </label>
              </div>

              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded text-[11px] text-amber-300 flex items-start gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5" />
                <span>
                  A cryptographically secure ingestion API key (<code className="font-mono">ii_live_...</code>) will be generated.
                </span>
              </div>

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowEnvModalForApp(null)}
                  className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold"
                >
                  Create & Generate Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. One-Time New API Key Revelation Modal */}
      {newKeyDialog && (
        <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#0e1424] border border-amber-500/40 rounded-lg max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-2 text-amber-400">
              <Key className="w-5 h-5" />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wide">
                Ingestion API Key for {newKeyDialog.envName}
              </h3>
            </div>

            <div className="p-3 bg-amber-500/15 border border-amber-500/30 rounded text-xs text-amber-200 space-y-1">
              <span className="font-semibold block flex items-center gap-1.5">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                Store this key securely. It will not be fully displayed again.
              </span>
              <p className="text-[11px] text-amber-300/80 font-sans leading-relaxed">
                For security reasons, IntelliIncident only stores salted cryptographic hashes or masked previews. Use this key in the <code className="font-mono bg-amber-950 px-1 py-0.5 rounded">X-API-Key</code> HTTP header when sending telemetry from your deployed service or CI/CD pipelines.
              </p>
            </div>

            <div className="space-y-1.5 font-mono text-xs">
              <span className="text-slate-400 block">Your Secret Ingestion Key:</span>
              <div className="flex items-center gap-2 p-2.5 bg-slate-950 rounded border border-slate-800">
                <code className="text-teal-300 text-xs break-all flex-1 select-all">
                  {newKeyDialog.key}
                </code>
                <button
                  onClick={() => copyToClipboard(newKeyDialog.key)}
                  className="flex items-center gap-1 px-3 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold shrink-0 transition-colors"
                >
                  {copiedKey ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedKey ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setNewKeyDialog(null)}
                className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs font-semibold"
              >
                I have securely stored this key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 5. Connection Guide Modal */}
      {activeGuide && (
        <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#0e1424] border border-slate-800 rounded-lg max-w-2xl w-full p-6 space-y-4 shadow-2xl max-h-[90vh] flex flex-col">
            {/* Guide Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-teal-400" />
                  <h3 className="text-sm font-bold font-mono text-slate-100">
                    Application Connection Guide: {activeGuide.application_name} ({activeGuide.environment_name})
                  </h3>
                </div>
                <span className="text-[11px] font-mono text-slate-400 block">
                  Project: {activeGuide.project_name} &bull; Endpoint: {activeGuide.ingestion_endpoint}
                </span>
              </div>
              <button
                onClick={() => setActiveGuide(null)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Architecture Explanation Box */}
            <div className="p-3 bg-slate-950 border border-teal-500/20 rounded text-xs text-slate-300 font-sans leading-relaxed">
              <span className="font-mono font-semibold text-teal-400 block mb-1">
                Dual-Signal Intelligence Integration
              </span>
              {activeGuide.explanation}
            </div>

            {/* Language Code Tabs */}
            <div className="flex items-center justify-between border-b border-slate-800 pt-1">
              <div className="flex items-center gap-1 font-mono text-xs">
                {(['curl', 'python', 'node', 'github'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveGuideTab(tab)}
                    className={`px-3 py-1.5 border-b-2 font-medium transition-colors ${
                      activeGuideTab === tab
                        ? 'border-teal-400 text-teal-300 bg-teal-500/10'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {tab === 'curl'
                      ? 'cURL'
                      : tab === 'python'
                      ? 'Python'
                      : tab === 'node'
                      ? 'Node.js'
                      : 'GitHub Actions CI/CD'}
                  </button>
                ))}
              </div>

              <button
                onClick={() => {
                  const snippet =
                    activeGuideTab === 'curl'
                      ? activeGuide.curl_snippet
                      : activeGuideTab === 'python'
                      ? activeGuide.python_snippet
                      : activeGuideTab === 'node'
                      ? activeGuide.node_snippet
                      : activeGuide.github_actions_snippet;
                  copyToClipboard(snippet, true);
                }}
                className="flex items-center gap-1 text-xs font-mono text-slate-300 hover:text-teal-300 transition-colors px-2 py-1 rounded hover:bg-slate-800"
              >
                {copiedSnippet ? <Check className="w-3.5 h-3.5 text-teal-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedSnippet ? 'Copied Snippet' : 'Copy Snippet'}</span>
              </button>
            </div>

            {/* Snippet Display */}
            <div className="flex-1 overflow-auto bg-slate-950 p-4 rounded border border-slate-800 font-mono text-xs text-slate-200">
              <pre className="whitespace-pre overflow-x-auto leading-relaxed">
                {activeGuideTab === 'curl' && activeGuide.curl_snippet}
                {activeGuideTab === 'python' && activeGuide.python_snippet}
                {activeGuideTab === 'node' && activeGuide.node_snippet}
                {activeGuideTab === 'github' && activeGuide.github_actions_snippet}
              </pre>
            </div>

            {/* Footer */}
            <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">
                Key Preview: <code className="text-slate-300">{activeGuide.api_key_preview}</code>
              </span>
              <button
                onClick={() => setActiveGuide(null)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  Sliders,
  ArrowRight,
} from 'lucide-react';
import { SeverityBadge } from '@/components/Common/SeverityBadge';
import { RiskBadge } from '@/components/Common/RiskBadge';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { MembershipChart } from '@/components/Fuzzy/MembershipChart';
import { getFuzzyMembershipDefinitions, getFuzzyRuleBase, evaluateFuzzyRisk } from '@/api/fuzzy';
import { getIncidents, getIncidentById } from '@/api/incidents';
import { Incident, IncidentDetails, FuzzyRiskResult } from '@/types';

export const FuzzyRiskPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [incidentDetail, setIncidentDetail] = useState<IncidentDetails | null>(null);
  const [loading, setLoading] = useState(true);

  // Simulation & standalone interactive crisp values
  const [showSimulation, setShowSimulation] = useState(false);
  const [simErrorRate, setSimErrorRate] = useState<number>(18.5);
  const [simLatency, setSimLatency] = useState<number>(1250);
  const [simImpact, setSimImpact] = useState<number>(65);
  const [simRecency, setSimRecency] = useState<number>(15);
  const [simCriticality, setSimCriticality] = useState<number>(3);

  const [evaluatedFuzzy, setEvaluatedFuzzy] = useState<FuzzyRiskResult | null>(null);

  const membershipDefs = getFuzzyMembershipDefinitions();
  const ruleBase = getFuzzyRuleBase();

  useEffect(() => {
    async function loadIncidents() {
      setLoading(true);
      const res = await getIncidents();
      setIncidents(res.data);
      if (res.data.length > 0) {
        setSelectedId(res.data[0].id);
      } else {
        setSelectedId('');
        setIncidentDetail(null);
        setLoading(false);
      }
    }
    loadIncidents();
  }, []);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedId) {
        setIncidentDetail(null);
        setLoading(false);
        return;
      }
      setLoading(true);
      const res = await getIncidentById(selectedId);
      setIncidentDetail(res.data);
      if (res.data) {
        setSimErrorRate(res.data.metrics.errorRate);
        setSimLatency(res.data.metrics.latencyP99);
        setSimImpact(
          res.data.metrics.affectedUsers > 10000
            ? 85
            : res.data.metrics.affectedUsers > 3000
            ? 50
            : 20
        );
        setSimRecency(res.data.metrics.deploymentRecencyMinutes);
        setSimCriticality(res.data.service.toLowerCase().includes('payment') ? 4 : 3);
      }
      setLoading(false);
    }
    loadDetail();
  }, [selectedId]);

  // Compute fuzzy risk dynamically via POST /api/fuzzy-risk when in standalone mode or simulation
  useEffect(() => {
    let active = true;
    async function recompute() {
      if (!incidentDetail || showSimulation) {
        try {
          const res = await evaluateFuzzyRisk({
            errorRate: simErrorRate,
            latency: simLatency,
            userImpact: simImpact,
            deploymentRecency: simRecency,
            serviceCriticality: simCriticality,
          });
          if (active && res.data) {
            setEvaluatedFuzzy(res.data);
          }
        } catch (err) {
          console.warn('Fuzzy evaluation error:', err);
        }
      }
    }
    recompute();
    return () => {
      active = false;
    };
  }, [incidentDetail, showSimulation, simErrorRate, simLatency, simImpact, simRecency, simCriticality]);

  const fuzzy: FuzzyRiskResult | null =
    incidentDetail && !showSimulation ? incidentDetail.fuzzyRisk : evaluatedFuzzy;

  const activeErrorRate = incidentDetail && !showSimulation
    ? incidentDetail.metrics.errorRate
    : simErrorRate;

  const activeLatency = incidentDetail && !showSimulation
    ? incidentDetail.metrics.latencyP99
    : simLatency;

  const activeImpact = incidentDetail && !showSimulation
    ? incidentDetail.metrics.affectedUsers > 10000
      ? 85
      : incidentDetail.metrics.affectedUsers > 3000
      ? 50
      : 20
    : simImpact;

  const activeRecency = incidentDetail && !showSimulation
    ? incidentDetail.metrics.deploymentRecencyMinutes
    : simRecency;

  const activeCriticalityTier = incidentDetail && !showSimulation
    ? incidentDetail.service.toLowerCase().includes('payment') ? 4 : 3
    : simCriticality;

  const activeServiceLabel = incidentDetail && !showSimulation
    ? incidentDetail.service
    : simCriticality === 1
    ? 'Internal / Non-Critical'
    : simCriticality === 2
    ? 'Standard Service'
    : simCriticality === 3
    ? 'Core Business API'
    : simCriticality === 4
    ? 'Tier-1 Gateway / Auth'
    : 'Mission Critical Transaction Core';

  if (!fuzzy || loading) {
    return (
      <div className="py-20 text-center font-mono text-sm text-slate-400">
        Loading fuzzy risk assessment workspace...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Incident Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold font-mono tracking-tight text-slate-100">
            Fuzzy Risk Assessment
          </h1>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="text-xs font-mono text-slate-400 uppercase tracking-wider shrink-0">
            Target Incident:
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            disabled={incidents.length === 0}
            className="bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs font-mono text-teal-300 font-semibold focus:outline-none focus:border-teal-500 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
          >
            {incidents.length === 0 ? (
              <option value="">No incidents stored (Standalone Mode)</option>
            ) : (
              incidents.map((inc) => (
                <option key={inc.id} value={inc.id}>
                  {inc.id} — {inc.service} ({inc.severity})
                </option>
              ))
            )}
          </select>

          {incidentDetail && (
            <button
              type="button"
              onClick={() => setShowSimulation(!showSimulation)}
              className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors cursor-pointer flex items-center gap-1.5 ${
                showSimulation
                  ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border-slate-800'
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>{showSimulation ? 'Exit Simulation' : 'Scenario Simulation'}</span>
            </button>
          )}
        </div>
      </div>

      {/* A. Selected Incident Header Card / Standalone Info Banner */}
      {incidentDetail ? (
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2.5">
                <span className="text-lg font-bold font-mono text-teal-400">{incidentDetail.id}</span>
                <span className="text-xs font-mono text-slate-300 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  Service: {incidentDetail.service}
                </span>
                <SeverityBadge severity={incidentDetail.severity} size="sm" />
                <StatusBadge status={incidentDetail.status} />
                <span className="text-[10px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                  Fuzzy Risk: Read-Only
                </span>
              </div>
              <h2 className="text-sm sm:text-base font-semibold text-slate-100 font-sans">
                {incidentDetail.title}
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed max-w-4xl font-sans">
                {incidentDetail.summary}
              </p>
            </div>

            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-xs font-mono space-y-1 shrink-0">
              <div className="flex justify-between gap-4 text-slate-400">
                <span>Timestamp:</span>
                <span className="text-slate-200">{incidentDetail.timestamp.substring(11, 19)} UTC</span>
              </div>
              <div className="flex justify-between gap-4 text-slate-400">
                <span>Inference Method:</span>
                <span className="text-teal-400">Mamdani Min-Max</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-teal-400 uppercase tracking-wider bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
                  Standalone Soft Computing Workspace
                </span>
                <span className="text-xs font-mono text-slate-400">Real-Data Mode (Empty DB)</span>
              </div>
              <h2 className="text-base font-semibold text-slate-100 font-sans">
                Interactive Mamdani Fuzzy Inference Engine
              </h2>
              <p className="text-xs text-slate-400 font-sans leading-relaxed">
                Adjust the crisp operational inputs below to evaluate real-time set memberships, rule firing strengths, and centroid defuzzification directly against <code className="text-teal-400 font-mono">POST /api/fuzzy-risk</code>.
              </p>
            </div>
            <div className="bg-slate-950/80 border border-slate-800 p-3 rounded text-xs font-mono space-y-1 shrink-0">
              <div className="flex justify-between gap-4 text-slate-400">
                <span>Engine:</span>
                <span className="text-teal-400">scikit-fuzzy Mamdani</span>
              </div>
              <div className="flex justify-between gap-4 text-slate-400">
                <span>Defuzzification:</span>
                <span className="text-slate-200">Centroid of Area (COA)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Stage Architecture Bar */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[720px] text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            1. Crisp Telemetry
          </span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            2. Feature Extraction
          </span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="flex items-center gap-1.5 text-teal-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
            3. Fuzzification &amp; Membership \(\mu(x)\)
          </span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            4. Fuzzy Rule Evaluation
          </span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
          <span className="flex items-center gap-1.5 text-rose-400 font-bold">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            5. Centroid Defuzzification (Risk)
          </span>
        </div>
      </div>

      {/* Primary Result & Fuzzy Inputs Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* E. Defuzzification Result (Main Result Card - 5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  Defuzzification Result (Main Output)
                </h3>
                {incidentDetail && !showSimulation ? (
                  <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30 font-semibold">
                    AUTHORITATIVE (READ-ONLY)
                  </span>
                ) : (
                  <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30 font-semibold">
                    SIMULATION SANDBOX
                  </span>
                )}
              </div>

              <div className="flex items-baseline justify-between">
                <div>
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    Composite Risk Score
                  </span>
                  <div className="flex items-baseline gap-2 mt-1">
                    <span className="text-5xl font-extrabold font-mono text-rose-400 tracking-tight">
                      {fuzzy.riskScore}
                    </span>
                    <span className="text-sm font-mono text-slate-400">/ 100</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block mb-1">
                    Risk Classification
                  </span>
                  <RiskBadge risk={fuzzy.riskLevel} />
                </div>
              </div>

              <div className="mt-4 p-3 bg-slate-950/90 rounded border border-slate-800/80 space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Defuzzification Method:</span>
                  <span className="text-slate-200 font-semibold">{fuzzy.defuzzificationMethod}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-900">
                  <span className="text-slate-400">Inference Structure:</span>
                  <span className="text-slate-200">Mamdani Standard Rule-Base</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Active Rules Fired:</span>
                  <span className="text-amber-400 font-bold">{fuzzy.triggeredRules.length} Rules</span>
                </div>
              </div>
            </div>

            {/* Simulation controls when toggled or in standalone mode */}
            {(showSimulation || !incidentDetail) && (
              <div className="mt-4 pt-4 border-t border-slate-800 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between text-amber-300 text-[11px] font-semibold">
                  <span>
                    {!incidentDetail
                      ? 'Interactive Crisp Signal Controls'
                      : 'What-If Telemetry Simulation'}
                  </span>
                  <span className="text-[10px] bg-amber-500/20 px-1.5 py-0.5 rounded">Active</span>
                </div>

                {incidentDetail && (
                  <p className="text-[10px] text-amber-400/80 font-mono leading-relaxed bg-amber-500/10 p-2 rounded border border-amber-500/20">
                    Simulation sandbox only: evaluations run in memory and do not overwrite the authoritative stored incident risk.
                  </p>
                )}

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Error Rate: {simErrorRate}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    step="0.5"
                    value={simErrorRate}
                    onChange={(e) => setSimErrorRate(parseFloat(e.target.value))}
                    className="w-full accent-teal-500 bg-slate-950 h-1.5 rounded cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>P99 Latency: {simLatency}ms</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="3000"
                    step="25"
                    value={simLatency}
                    onChange={(e) => setSimLatency(parseFloat(e.target.value))}
                    className="w-full accent-teal-500 bg-slate-950 h-1.5 rounded cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>User Impact Index: {simImpact}/100</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="1"
                    value={simImpact}
                    onChange={(e) => setSimImpact(parseFloat(e.target.value))}
                    className="w-full accent-teal-500 bg-slate-950 h-1.5 rounded cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Deployment Recency: {simRecency}m ago</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="120"
                    step="1"
                    value={simRecency}
                    onChange={(e) => setSimRecency(parseFloat(e.target.value))}
                    className="w-full accent-teal-500 bg-slate-950 h-1.5 rounded cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                    <span>Service Criticality: Tier {simCriticality}</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="1"
                    value={simCriticality}
                    onChange={(e) => setSimCriticality(parseInt(e.target.value))}
                    className="w-full accent-teal-500 bg-slate-950 h-1.5 rounded cursor-pointer"
                  />
                </div>
              </div>
            )}
          </div>

          {/* D. Active Fuzzy Rules */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <h3 className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Active Fired Fuzzy Rules
              </h3>
              <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                {fuzzy.triggeredRules.length} Rules Activated
              </span>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              {fuzzy.triggeredRules.map((rule) => (
                <div
                  key={rule.id}
                  className="p-3 bg-slate-950/90 border border-slate-800 rounded-md"
                >
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="font-bold text-amber-400">{rule.id}</span>
                    <span className="text-teal-400 font-semibold">
                      Weight: {rule.weight}
                    </span>
                  </div>
                  <p className="text-slate-200 text-xs font-mono font-medium leading-relaxed">
                    {rule.ruleText}
                  </p>
                  <p className="mt-1 text-[11px] text-slate-400 font-sans">
                    {rule.contribution}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: B. Fuzzy Input Signals + C. Membership Function Visualizations (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* B. Fuzzy Input Signals Display */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Incident Fuzzy Input Signals (Fuzzified)
              </h3>
              <span className="text-[10px] font-mono text-slate-400">Continuous Vectors</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 font-mono text-xs">
              {/* Error Rate */}
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Error Rate
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-rose-400">
                    {activeErrorRate}%
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    {fuzzy.inputs.errorRateState}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block">Fuzzified Crisp Signal</span>
              </div>

              {/* P99 Latency */}
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  P99 Latency
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-amber-400">
                    {activeLatency}ms
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    {fuzzy.inputs.latencyState}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block">Fuzzified Crisp Signal</span>
              </div>

              {/* User Impact */}
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  User Impact
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-slate-200">
                    {incidentDetail
                      ? incidentDetail.metrics.affectedUsers.toLocaleString()
                      : `${activeImpact}/100`}
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    {fuzzy.inputs.userImpactState}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block">Index: {activeImpact}/100</span>
              </div>

              {/* Deployment Recency */}
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 space-y-1">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Deployment Recency
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-cyan-400">
                    {activeRecency}m ago
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                    {fuzzy.inputs.deploymentRecencyState}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block">Temporal Proximity</span>
              </div>

              {/* Service Criticality */}
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 space-y-1 sm:col-span-2 lg:col-span-2">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider block">
                  Service Criticality Tier
                </span>
                <div className="flex items-baseline justify-between">
                  <span className="text-base font-bold text-slate-200">
                    Tier-{activeCriticalityTier} ({activeServiceLabel})
                  </span>
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                    {fuzzy.inputs.serviceCriticalityState}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 block">Operational SLA Weight</span>
              </div>
            </div>
          </div>

          {/* C. Membership Function Curves Visualizations */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
                  Fuzzy Membership Functions \(\mu(x)\)
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Triangular & trapezoidal fuzzy sets with current incident telemetry cursor
                </p>
              </div>
              <span className="text-[10px] font-mono text-teal-400 bg-teal-500/10 px-2 py-0.5 rounded border border-teal-500/30">
                Continuous Partitions
              </span>
            </div>

            <div className="space-y-4">
              <MembershipChart
                curveDef={membershipDefs.errorRate}
                currentValue={activeErrorRate}
              />
              <MembershipChart
                curveDef={membershipDefs.latency}
                currentValue={activeLatency}
              />
              <MembershipChart
                curveDef={membershipDefs.userImpact}
                currentValue={activeImpact}
              />
            </div>
          </div>

          {/* Rule Base Catalogue */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-semibold text-slate-100 font-mono uppercase tracking-wider">
                Mamdani Operational Rule-Base
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                Total {ruleBase.length} Standard Rules
              </span>
            </div>

            <div className="space-y-2 font-mono text-xs max-h-40 overflow-y-auto pr-1">
              {ruleBase.map((r) => (
                <div
                  key={r.id}
                  className="p-2.5 bg-slate-950/60 rounded border border-slate-800/80 flex items-start gap-2"
                >
                  <span className="text-slate-400 font-semibold text-[11px] shrink-0">
                    {r.id}:
                  </span>
                  <div>
                    <span className="text-slate-300 block">{r.ruleText}</span>
                    <span className="text-[10px] text-slate-500 font-sans">{r.description}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

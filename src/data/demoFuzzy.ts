import { FuzzyInputValues, FuzzyRiskResult } from '@/types';

export interface MembershipCurveDefinition {
  name: string;
  unit: string;
  min: number;
  max: number;
  sets: {
    label: 'LOW' | 'MEDIUM' | 'HIGH';
    points: { x: number; y: number }[];
    color: string;
  }[];
}

export const FUZZY_MEMBERSHIP_DEFINITIONS: Record<string, MembershipCurveDefinition> = {
  errorRate: {
    name: 'Error Rate',
    unit: '%',
    min: 0,
    max: 50,
    sets: [
      {
        label: 'LOW',
        color: '#3b82f6',
        points: [{ x: 0, y: 1 }, { x: 5, y: 1 }, { x: 12, y: 0 }],
      },
      {
        label: 'MEDIUM',
        color: '#eab308',
        points: [{ x: 8, y: 0 }, { x: 18, y: 1 }, { x: 28, y: 0 }],
      },
      {
        label: 'HIGH',
        color: '#ef4444',
        points: [{ x: 22, y: 0 }, { x: 35, y: 1 }, { x: 50, y: 1 }],
      },
    ],
  },
  userImpact: {
    name: 'User Impact',
    unit: 'score (0-100)',
    min: 0,
    max: 100,
    sets: [
      {
        label: 'LOW',
        color: '#3b82f6',
        points: [{ x: 0, y: 1 }, { x: 15, y: 1 }, { x: 35, y: 0 }],
      },
      {
        label: 'MEDIUM',
        color: '#eab308',
        points: [{ x: 25, y: 0 }, { x: 50, y: 1 }, { x: 75, y: 0 }],
      },
      {
        label: 'HIGH',
        color: '#ef4444',
        points: [{ x: 65, y: 0 }, { x: 85, y: 1 }, { x: 100, y: 1 }],
      },
    ],
  },
  latency: {
    name: 'P99 Latency',
    unit: 'ms',
    min: 0,
    max: 3000,
    sets: [
      {
        label: 'LOW',
        color: '#3b82f6',
        points: [{ x: 0, y: 1 }, { x: 200, y: 1 }, { x: 600, y: 0 }],
      },
      {
        label: 'MEDIUM',
        color: '#eab308',
        points: [{ x: 400, y: 0 }, { x: 1000, y: 1 }, { x: 1600, y: 0 }],
      },
      {
        label: 'HIGH',
        color: '#ef4444',
        points: [{ x: 1300, y: 0 }, { x: 2200, y: 1 }, { x: 3000, y: 1 }],
      },
    ],
  },
  deploymentRecency: {
    name: 'Deployment Recency',
    unit: 'mins ago',
    min: 0,
    max: 180,
    sets: [
      {
        label: 'LOW', // High risk because very recent!
        color: '#ef4444',
        points: [{ x: 0, y: 1 }, { x: 15, y: 1 }, { x: 45, y: 0 }],
      },
      {
        label: 'MEDIUM',
        color: '#eab308',
        points: [{ x: 30, y: 0 }, { x: 75, y: 1 }, { x: 120, y: 0 }],
      },
      {
        label: 'HIGH', // Low risk because long ago
        color: '#3b82f6',
        points: [{ x: 90, y: 0 }, { x: 150, y: 1 }, { x: 180, y: 1 }],
      },
    ],
  },
  serviceCriticality: {
    name: 'Service Criticality',
    unit: 'tier score (1-5)',
    min: 1,
    max: 5,
    sets: [
      {
        label: 'LOW',
        color: '#3b82f6',
        points: [{ x: 1, y: 1 }, { x: 1.5, y: 1 }, { x: 2.5, y: 0 }],
      },
      {
        label: 'MEDIUM',
        color: '#eab308',
        points: [{ x: 2, y: 0 }, { x: 3, y: 1 }, { x: 4, y: 0 }],
      },
      {
        label: 'HIGH',
        color: '#ef4444',
        points: [{ x: 3.5, y: 0 }, { x: 4.5, y: 1 }, { x: 5, y: 1 }],
      },
    ],
  },
};

export const FUZZY_RULE_BASE = [
  {
    id: 'RULE-01',
    ruleText: 'IF Error Rate is HIGH AND User Impact is HIGH THEN Risk is VERY HIGH',
    description: 'Catastrophic business failure pattern with broad customer-facing errors.',
  },
  {
    id: 'RULE-02',
    ruleText: 'IF Latency is HIGH AND Service Criticality is HIGH THEN Risk is HIGH',
    description: 'Tier-1 SLA breach due to severe responsiveness degradation.',
  },
  {
    id: 'RULE-03',
    ruleText: 'IF Deployment Recency is RECENT AND Error Rate is HIGH THEN Risk is VERY HIGH',
    description: 'Defective deployment anomaly with immediate regression impact.',
  },
  {
    id: 'RULE-04',
    ruleText: 'IF Error Rate is MEDIUM AND User Impact is MEDIUM THEN Risk is MEDIUM',
    description: 'Moderate operational incident with contained blast radius.',
  },
  {
    id: 'RULE-05',
    ruleText: 'IF Latency is MEDIUM AND Service Criticality is LOW THEN Risk is LOW',
    description: 'Background or non-critical latency elevation within tolerable limits.',
  },
  {
    id: 'RULE-06',
    ruleText: 'IF Error Rate is LOW AND User Impact is LOW THEN Risk is LOW',
    description: 'Nominal baseline operational state.',
  },
];

// Demo computation placeholder (until FastAPI POST /api/fuzzy-risk is connected)
export function calculateDemoFuzzyRisk(inputs: FuzzyInputValues): FuzzyRiskResult {
  // Simple deterministic demonstration scoring mapping for UI display
  const errorRateScore = Math.min(inputs.errorRate * 2.5, 100);
  const userImpactScore = inputs.userImpact;
  const latencyScore = Math.min((inputs.latency / 2000) * 100, 100);
  const recencyScore = inputs.deploymentRecency < 30 ? 95 : inputs.deploymentRecency < 60 ? 60 : 20;
  const criticalityScore = (inputs.serviceCriticality / 5) * 100;

  const combined = (
    errorRateScore * 0.35 +
    userImpactScore * 0.25 +
    latencyScore * 0.2 +
    recencyScore * 0.1 +
    criticalityScore * 0.1
  );

  const roundedScore = Math.round(combined);

  const errorRateState = inputs.errorRate > 20 ? 'HIGH' : inputs.errorRate > 8 ? 'MEDIUM' : 'LOW';
  const userImpactState = inputs.userImpact > 60 ? 'HIGH' : inputs.userImpact > 25 ? 'MEDIUM' : 'LOW';
  const latencyState = inputs.latency > 1200 ? 'HIGH' : inputs.latency > 400 ? 'MEDIUM' : 'LOW';
  const deploymentRecencyState = inputs.deploymentRecency < 30 ? 'RECENT' : inputs.deploymentRecency < 90 ? 'MODERATE' : 'OLD';
  const serviceCriticalityState = inputs.serviceCriticality >= 4 ? 'HIGH' : inputs.serviceCriticality >= 2.5 ? 'MEDIUM' : 'LOW';

  let riskLevel: FuzzyRiskResult['riskLevel'] = 'LOW';
  if (roundedScore >= 80) riskLevel = 'CRITICAL';
  else if (roundedScore >= 60) riskLevel = 'HIGH';
  else if (roundedScore >= 35) riskLevel = 'MEDIUM';

  const triggered = [];
  if (errorRateState === 'HIGH' && userImpactState === 'HIGH') {
    triggered.push({
      id: 'RULE-01',
      ruleText: 'IF Error Rate is HIGH AND User Impact is HIGH THEN Risk is VERY HIGH',
      weight: 0.94,
      contribution: 'High activation from concurrent error rate and broad user impact.',
    });
  }
  if (latencyState === 'HIGH' && serviceCriticalityState === 'HIGH') {
    triggered.push({
      id: 'RULE-02',
      ruleText: 'IF Latency is HIGH AND Service Criticality is HIGH THEN Risk is HIGH',
      weight: 0.86,
      contribution: 'Elevated latency on mission-critical service.',
    });
  }
  if (deploymentRecencyState === 'RECENT' && (errorRateState === 'HIGH' || errorRateState === 'MEDIUM')) {
    triggered.push({
      id: 'RULE-03',
      ruleText: 'IF Deployment Recency is RECENT AND Error Rate is HIGH THEN Risk is VERY HIGH',
      weight: 0.89,
      contribution: 'Temporal proximity to recent release correlates strongly with failure.',
    });
  }
  if (triggered.length === 0) {
    triggered.push({
      id: 'RULE-04',
      ruleText: 'IF Error Rate is MEDIUM AND User Impact is MEDIUM THEN Risk is MEDIUM',
      weight: 0.65,
      contribution: 'Moderate operating telemetry within acceptable variance.',
    });
  }

  return {
    riskScore: roundedScore,
    riskLevel,
    inputs: {
      errorRateState,
      userImpactState,
      latencyState,
      deploymentRecencyState,
      serviceCriticalityState,
    },
    triggeredRules: triggered,
    defuzzificationMethod: 'Centroid of Area (COA)',
  };
}

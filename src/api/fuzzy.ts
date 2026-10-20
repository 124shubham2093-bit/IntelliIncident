import { apiClient } from './client';
import { FuzzyInputValues, FuzzyRiskResult } from '@/types';
import {
  FUZZY_MEMBERSHIP_DEFINITIONS,
  FUZZY_RULE_BASE,
  MembershipCurveDefinition,
} from '@/data/demoFuzzy';

/**
 * Submit input parameters to fuzzy risk assessment engine via POST /api/fuzzy-risk.
 */
export async function evaluateFuzzyRisk(
  inputs: FuzzyInputValues
): Promise<{ data: FuzzyRiskResult; isDemo: boolean }> {
  const result = await apiClient<FuzzyRiskResult>('/api/fuzzy-risk', {
    method: 'POST',
    body: JSON.stringify(inputs),
  });
  return { data: result, isDemo: false };
}

/**
 * Returns membership function definitions for visual charting.
 */
export function getFuzzyMembershipDefinitions(): Record<string, MembershipCurveDefinition> {
  return FUZZY_MEMBERSHIP_DEFINITIONS;
}

/**
 * Returns the soft computing fuzzy rule-base catalogue.
 */
export function getFuzzyRuleBase() {
  return FUZZY_RULE_BASE;
}

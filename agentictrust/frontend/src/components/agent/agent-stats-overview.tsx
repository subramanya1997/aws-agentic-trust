"use client";

import React from "react";
import { StatCard, StatsGrid } from "@/components/stats";
import { 
  UserCog,
  Activity,
  Wrench,
  Shield
} from "lucide-react";
import type { AgentStatusSummary } from "@/lib/types";
import { formatPercentage } from "@/lib/utils";

interface AgentStatsOverviewProps {
  summary: AgentStatusSummary | null;
}

export function AgentStatsOverview({ summary }: AgentStatsOverviewProps) {
  const totalAgents = summary?.total || 0;
  const uniqueToolsCount = summary?.capabilities?.tools || 0;
  const uniqueResourcesCount = summary?.capabilities?.resources || 0;
  const uniquePromptsCount = summary?.capabilities?.prompts || 0;
  const totalUniqueCapabilities = summary?.capabilities?.total_unique || 0;
  const avgCapabilitiesPerAgent = summary?.avg_capabilities_per_agent || 0;
  const recentRegistrations = summary?.recent_registrations || 0;

  return (
    <StatsGrid columns={4}>
      <StatCard
        title="Total Agents"
        value={totalAgents}
        description="Registered agents"
        icon={UserCog}
        trend={summary?.trends ? {
          value: Math.abs(summary.trends.trend_percentage),
          isPositive: summary.trends.is_positive,
          label: "this week"
        } : undefined}
      />
      
      <StatCard
        title="Total Unique"
        value={totalUniqueCapabilities}
        description={`${uniqueToolsCount} tools, ${uniqueResourcesCount} resources, ${uniquePromptsCount} prompts in use`}
        icon={Wrench}
        valueClassName="text-blue-600"
      />
      
      <StatCard
        title="Avg Capabilities"
        value={avgCapabilitiesPerAgent}
        description="Per agent"
        icon={Activity}
        valueClassName={avgCapabilitiesPerAgent >= 3 ? "text-green-600" : avgCapabilitiesPerAgent >= 1 ? "text-yellow-600" : "text-gray-600"}
      />
      
      <StatCard
        title="Recent Activity"
        value={recentRegistrations}
        description="New registrations this week"
        icon={Shield}
        valueClassName="text-green-600"
      />
    </StatsGrid>
  );
} 
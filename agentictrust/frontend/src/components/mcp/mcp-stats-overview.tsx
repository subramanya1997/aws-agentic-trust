"use client";

import React from "react";
import { StatCard, StatsGrid } from "@/components/stats";
import { 
  Server,
  Activity,
  AlertCircle,
  CheckCircle
} from "lucide-react";
import type { MCPStatusSummary, MCPHealthReport } from "@/lib/types";
import { MCP_STATUS } from "@/lib/constants";
import { formatPercentage } from "@/lib/utils";

interface MCPStatsOverviewProps {
  summary: MCPStatusSummary | null;
  report?: MCPHealthReport | null;
  onHealthClick?: () => void;
}

export function MCPStatsOverview({ summary, report, onHealthClick }: MCPStatsOverviewProps) {
  const activeMCPs = summary?.by_status[MCP_STATUS.ACTIVE] || 0;
  const totalMCPs = summary?.total || 0;
  const errorMCPs = summary?.by_status[MCP_STATUS.ERROR] || 0;
  const healthPercentage = totalMCPs > 0 ? formatPercentage(activeMCPs, totalMCPs) : 0;

  const renderHealthValue = () => {
    if (!report) return "Checking...";
    return report.is_healthy ? "Healthy" : `${report.issues.length} issues`;
  };

  const renderHealthDesc = () => {
    if (!report) return "Running health checks";
    return report.is_healthy ? "All MCPs reachable" : "Click to view issues";
  };

  return (
    <StatsGrid columns={4}>
      <StatCard
        title="Total MCPs"
        value={totalMCPs}
        description="Registered protocols"
        icon={Server}
        trend={summary?.trends ? {
          value: Math.abs(summary.trends.trend_percentage),
          isPositive: summary.trends.is_positive,
          label: "this week"
        } : undefined}
      />
      
      <StatCard
        title="Active MCPs"
        value={activeMCPs}
        description="Currently running"
        icon={CheckCircle}
        valueClassName="text-green-600"
      />
      
      <StatCard
        title="Fleet Health"
        value={renderHealthValue()}
        description={renderHealthDesc()}
        icon={Activity}
        valueClassName={!report ? "" : report.is_healthy ? "text-green-600" : "text-red-600"}
        onClick={report && !report.is_healthy ? onHealthClick : undefined}
      />
      
      <StatCard
        title="Issues"
        value={errorMCPs}
        description={errorMCPs > 0 ? 'Errors detected' : 'No critical issues'}
        icon={AlertCircle}
        valueClassName={errorMCPs > 0 ? 'text-red-600' : 'text-green-600'}
      />
    </StatsGrid>
  );
} 
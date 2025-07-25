"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  ArcElement,
  Tooltip,
  Legend,
  TimeScale,
} from "chart.js";
import type { ChartOptions } from "chart.js";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Clock,
  Activity,
  Zap,
  AlertTriangle,
  Download,
  Calendar,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { StatCard, StatsGrid } from "@/components/stats";

import { TopHeader } from "@/components/top-header";
import { pageConfig } from "@/lib/config";
import { api, ApiError } from "@/lib/api";
import type { 
  LogStats,
  LogEntryListResponse,
  MCPStatusSummary,
  HealthResponse,
  MCPConnectionStats,
  ToolUsageStats,
  ResourceUsageStats,
  PromptUsageStats
} from "@/lib/types";
import { 
  CHART_COLORS,
  LOG_SEVERITY,
  SEVERITY_COLORS,
  POLLING_INTERVAL
} from "@/lib/constants";
import { handleError, formatPercentage } from "@/lib/utils";

ChartJS.register(
  CategoryScale, 
  LinearScale, 
  TimeScale,
  BarElement, 
  LineElement,
  PointElement,
  ArcElement,
  Tooltip, 
  Legend
);

const chartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: 'hsl(var(--foreground))' },
    },
  },
  scales: {
    x: {
      ticks: { color: 'hsl(var(--muted-foreground))' },
      grid: { color: 'hsl(var(--border))' },
    },
    y: {
      ticks: { color: 'hsl(var(--muted-foreground))' },
      grid: { color: 'hsl(var(--border))' },
    },
  },
};

const doughnutOptions: ChartOptions<'doughnut'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { color: 'hsl(var(--foreground))' },
    },
  },
};

interface AnalyticsState {
  logStats: LogStats | null;
  mcpSummary: MCPStatusSummary | null;
  recentLogs: LogEntryListResponse | null;
  health: HealthResponse | null;
  mcpConnections: MCPConnectionStats[];
  toolUsage: ToolUsageStats[];
  resourceUsage: ResourceUsageStats[];
  promptUsage: PromptUsageStats[];
  loading: boolean;
  error: string | null;
}

export default function AnalyticsPage() {
  const [state, setState] = useState<AnalyticsState>({
    logStats: null,
    mcpSummary: null,
    recentLogs: null,
    health: null,
    mcpConnections: [],
    toolUsage: [],
    resourceUsage: [],
    promptUsage: [],
    loading: true,
    error: null,
  });

  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h' | '7d'>('24h');

  const fetchAnalyticsData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const [
        logStatsResult, 
        mcpSummaryResult, 
        recentLogsResult, 
        healthResult,
        mcpConnectionsResult,
        toolUsageResult,
        resourceUsageResult,
        promptUsageResult
      ] = await Promise.allSettled([
        api.logs.getStats(),
        api.mcp.getStatusSummary(),
        api.logs.list({ limit: 100 }),
        api.health.getHealth(),
        api.usage.getMCPConnections(),
        api.usage.getToolUsage(),
        api.usage.getResourceUsage(),
        api.usage.getPromptUsage(),
      ]);

      setState(prev => ({
        ...prev,
        logStats: logStatsResult.status === 'fulfilled' ? logStatsResult.value : null,
        mcpSummary: mcpSummaryResult.status === 'fulfilled' ? mcpSummaryResult.value : null,
        recentLogs: recentLogsResult.status === 'fulfilled' ? recentLogsResult.value : null,
        health: healthResult.status === 'fulfilled' ? healthResult.value : null,
        mcpConnections: mcpConnectionsResult.status === 'fulfilled' ? mcpConnectionsResult.value : [],
        toolUsage: toolUsageResult.status === 'fulfilled' ? toolUsageResult.value : [],
        resourceUsage: resourceUsageResult.status === 'fulfilled' ? resourceUsageResult.value : [],
        promptUsage: promptUsageResult.status === 'fulfilled' ? promptUsageResult.value : [],
        loading: false,
      }));

    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch analytics data";
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      handleError(err, errorMessage);
    }
  }, []);

  useEffect(() => {
    fetchAnalyticsData();
  }, [fetchAnalyticsData]);

  const { logStats, mcpSummary, recentLogs, health, mcpConnections, toolUsage, resourceUsage, promptUsage, loading, error } = state;

  // Calculate metrics
  const totalEvents = logStats?.total || 0;
  const errorCount = logStats?.error_count || 0;
  const successCount = totalEvents - errorCount;
  const successRate = totalEvents > 0 ? (successCount / totalEvents) * 100 : 100;
  const errorRate = totalEvents > 0 ? (errorCount / totalEvents) * 100 : 0;

  // Usage statistics
  const totalConnections = mcpConnections.reduce((sum, mcp) => sum + mcp.connected_instances, 0);
  const totalAgents = new Set(mcpConnections.flatMap(mcp => mcp.connected_agents.map(agent => agent.agent_id))).size;
  const totalToolCalls = toolUsage.reduce((sum, tool) => sum + tool.total_calls, 0);
  const totalResourceReads = resourceUsage.reduce((sum, resource) => sum + resource.total_reads, 0);
  const totalPromptGets = promptUsage.reduce((sum, prompt) => sum + prompt.total_gets, 0);

  // Chart data
  const eventChartData = logStats?.by_event_type ? {
    labels: Object.keys(logStats.by_event_type),
    datasets: [
      {
        label: "Event Count",
        data: Object.values(logStats.by_event_type),
        backgroundColor: CHART_COLORS.slice(0, Object.keys(logStats.by_event_type).length),
      },
    ],
  } : null;

  const severityChartData = logStats?.by_severity ? {
    labels: Object.keys(logStats.by_severity),
    datasets: [
      {
        label: "Log Count",
        data: Object.values(logStats.by_severity),
        backgroundColor: Object.keys(logStats.by_severity).map(severity => 
          SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || 'rgba(156, 163, 175, 0.8)'
        ),
      },
    ],
  } : null;

  const performanceData = {
    labels: ['Success', 'Errors'],
    datasets: [
      {
        data: [successCount, errorCount],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(239, 68, 68)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const mcpStatusData = mcpSummary?.by_status ? {
    labels: Object.keys(mcpSummary.by_status),
    datasets: [
      {
        data: Object.values(mcpSummary.by_status),
        backgroundColor: CHART_COLORS.slice(0, Object.keys(mcpSummary.by_status).length),
      },
    ],
  } : null;

  // Usage charts
  const usageDistributionData = {
    labels: ['Tool Calls', 'Resource Reads', 'Prompt Gets'],
    datasets: [
      {
        data: [totalToolCalls, totalResourceReads, totalPromptGets],
        backgroundColor: [CHART_COLORS[0], CHART_COLORS[1], CHART_COLORS[2]],
      },
    ],
  };

  const topToolsData = toolUsage.length > 0 ? {
    labels: toolUsage.slice(0, 5).map(tool => tool.tool_name),
    datasets: [
      {
        label: "Total Calls",
        data: toolUsage.slice(0, 5).map(tool => tool.total_calls),
        backgroundColor: CHART_COLORS[3],
      },
    ],
  } : null;

  return (
    <div className="hidden flex-col md:flex">
      <TopHeader 
        page={pageConfig.analytics}
        onRefresh={fetchAnalyticsData}
        isLoading={loading}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Calendar className="mr-2 h-4 w-4" />
              {timeRange.toUpperCase()}
            </Button>
            <Button variant="outline" size="sm">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
          </div>
        }
      />

      <div className="flex-1 space-y-6 p-8 pt-6">
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Key Metrics */}
        <StatsGrid columns={5}>
          <StatCard
            title="Total Events"
            value={totalEvents.toLocaleString()}
            description="All time events"
            icon={Activity}
            status={totalEvents > 0 ? "healthy" : "neutral"}
            trend={logStats?.trends ? {
              value: Math.abs(((logStats.trends.recent_logs - logStats.trends.previous_week_logs) / Math.max(logStats.trends.previous_week_logs, 1)) * 100),
              isPositive: logStats.trends.recent_logs >= logStats.trends.previous_week_logs,
              label: "this week"
            } : undefined}
          />
          
          <StatCard
            title="Active MCPs"
            value={mcpSummary?.total || 0}
            description="Registered protocols"
            icon={Zap}
            status={(mcpSummary?.total || 0) > 0 ? "healthy" : "neutral"}
            trend={mcpSummary?.trends ? {
              value: Math.abs(mcpSummary.trends.trend_percentage),
              isPositive: mcpSummary.trends.is_positive,
              label: "this week"
            } : undefined}
          />

          <StatCard
            title="Active Connections"
            value={totalConnections.toLocaleString()}
            description={`${totalAgents} agents connected`}
            icon={Activity}
            status={totalConnections > 0 ? "healthy" : "neutral"}
          />
          
          <StatCard
            title="Success Rate"
            value={`${successRate.toFixed(1)}%`}
            description={`${successCount} successful operations`}
            icon={TrendingUp}
            valueClassName="text-green-600"
            status={successRate >= 95 ? "healthy" : successRate >= 90 ? "warning" : "error"}
            trend={logStats?.trends ? {
              value: Math.abs(logStats.trends.success_rate_trend),
              isPositive: logStats.trends.is_improving,
              label: "vs last week"
            } : undefined}
          />
          
          <StatCard
            title="Error Rate"
            value={`${errorRate.toFixed(1)}%`}
            description={`${errorCount} error events`}
            icon={AlertTriangle}
            valueClassName="text-red-600"
            status={errorRate <= 5 ? "healthy" : errorRate <= 10 ? "warning" : "error"}
            trend={logStats?.trends ? {
              value: Math.abs(((logStats.trends.recent_errors - logStats.trends.previous_week_errors) / Math.max(logStats.trends.previous_week_errors, 1)) * 100),
              isPositive: logStats.trends.recent_errors <= logStats.trends.previous_week_errors,
              label: "vs last week"
            } : undefined}
          />
        </StatsGrid>

        {/* Charts Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Event Type Distribution</CardTitle>
              <CardDescription>
                Breakdown of different event types
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {eventChartData ? (
                  <Bar data={eventChartData} options={chartOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    {loading ? (
                      <div className="flex items-center">
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                        Loading data...
                      </div>
                    ) : (
                      "No event data available"
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
              <CardDescription>
                Success vs error distribution
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {totalEvents > 0 ? (
                  <Doughnut data={performanceData} options={doughnutOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No performance data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Log Severity Distribution</CardTitle>
              <CardDescription>
                Breakdown by severity levels
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {severityChartData ? (
                  <Bar data={severityChartData} options={chartOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No severity data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>MCP Status Distribution</CardTitle>
              <CardDescription>
                Status breakdown of all MCPs
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {mcpStatusData ? (
                  <Doughnut data={mcpStatusData} options={doughnutOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No MCP status data
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Usage Statistics Charts */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Usage Distribution</CardTitle>
              <CardDescription>
                Breakdown of MCP usage by type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {(totalToolCalls + totalResourceReads + totalPromptGets) > 0 ? (
                  <Doughnut data={usageDistributionData} options={doughnutOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No usage data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Top Tools by Usage</CardTitle>
              <CardDescription>
                Most frequently called tools
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                {topToolsData ? (
                  <Bar data={topToolsData} options={chartOptions} />
                ) : (
                  <div className="flex h-full items-center justify-center text-muted-foreground">
                    No tool usage data available
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Statistics */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Event Type Breakdown</CardTitle>
              <CardDescription>
                Detailed statistics for each event type
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {logStats?.by_event_type ? 
                  Object.entries(logStats.by_event_type)
                    .sort(([,a], [,b]) => (b as number) - (a as number))
                    .map(([eventType, count]) => (
                      <div key={eventType} className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge variant={
                            eventType.includes('error') ? "destructive" :
                            eventType.includes('call') ? "default" :
                            "secondary"
                          }>
                            {eventType}
                          </Badge>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{count}</span>
                          <span className="text-xs text-muted-foreground">
                            ({formatPercentage(count as number, totalEvents)}%)
                          </span>
                        </div>
                      </div>
                    )) : (
                    <div className="text-center text-muted-foreground py-8">
                      No event data available
                    </div>
                  )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Health Metrics</CardTitle>
              <CardDescription>
                Overall system performance indicators
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${health?.tables_accessible ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="font-medium">Database Status</span>
                  </div>
                  <Badge variant={health?.tables_accessible ? "default" : "destructive"}>
                    {health?.tables_accessible ? "Connected" : "Issues"}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="font-medium">System Uptime</span>
                  <span className="text-sm">
                    {health?.uptime ? `${Math.floor(health.uptime / 60)}m` : 'Unknown'}
                  </span>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="font-medium">Schema Version</span>
                  <Badge variant="outline">
                    {health?.schema_version || "Unknown"}
                  </Badge>
                </div>
                
                {logStats?.by_severity && (
                  <>
                    <div className="pt-4 border-t">
                      <h4 className="font-medium mb-2">Severity Breakdown</h4>
                      {Object.entries(logStats.by_severity).map(([severity, count]) => (
                        <div key={severity} className="flex items-center justify-between text-sm">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${SEVERITY_COLORS[severity as keyof typeof SEVERITY_COLORS] || 'bg-gray-500'}`} />
                            <span className="capitalize">{severity}</span>
                          </div>
                          <span>{count}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Usage Statistics Summary</CardTitle>
              <CardDescription>
                Detailed breakdown of MCP usage patterns
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{totalToolCalls.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground">Tool Calls</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {toolUsage.length} unique tools
                    </div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{totalResourceReads.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground">Resource Reads</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {resourceUsage.length} unique resources
                    </div>
                  </div>
                  <div className="p-4 bg-muted/50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">{totalPromptGets.toLocaleString()}</div>
                    <div className="text-sm text-muted-foreground">Prompt Gets</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {promptUsage.length} unique prompts
                    </div>
                  </div>
                </div>

                {mcpConnections.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium mb-3">Active MCP Connections</h4>
                    <div className="space-y-2">
                      {mcpConnections.slice(0, 5).map((mcp) => (
                        <div key={mcp.mcp_id} className="flex items-center justify-between text-sm">
                          <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${mcp.status === 'active' ? 'bg-green-500' : 'bg-gray-500'}`} />
                            <span className="font-medium">{mcp.name}</span>
                            <Badge variant="outline" className="text-xs">{mcp.server_type}</Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                            <span>{mcp.connected_instances} active</span>
                            <span>{mcp.connected_agents.length} agents</span>
                          </div>
                        </div>
                      ))}
                      {mcpConnections.length > 5 && (
                        <div className="text-xs text-muted-foreground text-center pt-2">
                          +{mcpConnections.length - 5} more connections
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {toolUsage.length > 0 && (
                  <div className="pt-4 border-t">
                    <h4 className="font-medium mb-3">Most Used Tools</h4>
                    <div className="space-y-2">
                      {toolUsage.slice(0, 5).map((tool) => (
                        <div key={tool.tool_id} className="flex items-center justify-between text-sm">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium">{tool.tool_name}</span>
                            <Badge variant="outline" className="text-xs">{tool.mcp_name}</Badge>
                          </div>
                          <div className="flex items-center space-x-4 text-xs text-muted-foreground">
                            <span>{tool.total_calls} calls</span>
                            <span>{tool.agent_count} agents</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 
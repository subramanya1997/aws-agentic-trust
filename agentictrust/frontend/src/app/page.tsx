"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Activity, 
  Database, 
  Zap, 
  CheckCircle, 
  Network, 
  TrendingUp, 
  ArrowRight, 
  AlertCircle, 
  Clock,
  Users,
  Shield,
  Key,
  Wrench,
  FileText,
  MessageSquare,
  BarChart3,
  UserCog,
  RefreshCw,
  Home
} from "lucide-react";
import { StatCard, StatsGrid } from "@/components/stats";
import { CapabilityDistributionCard, SystemPerformanceCard, LiveIndicator } from "@/components/dashboard";
import { api, ApiError } from "@/lib/api";
import type { 
  HealthResponse, 
  MCPStatusSummary, 
  AgentStatusSummary,
  LogEntryListResponse, 
  LogStats,
  MCPListResponse,
  AgentListResponse
} from "@/lib/types";
import { 
  PAGINATION,
  MCP_STATUS,
  LOG_SEVERITY,
  STATUS_COLORS,
  SEVERITY_COLORS,
  POLLING_INTERVAL
} from "@/lib/constants";
import { handleError, formatPercentage } from "@/lib/utils";

interface DashboardState {
  health: HealthResponse | null;
  mcpSummary: MCPStatusSummary | null;
  agentSummary: AgentStatusSummary | null;
  mcpList: MCPListResponse | null;
  agentList: AgentListResponse | null;
  logStats: LogStats | null;
  recentLogs: LogEntryListResponse | null;
  loading: boolean;
  error: string | null;
  lastUpdate: Date | null;
}

export default function Dashboard() {
  const [state, setState] = useState<DashboardState>({
    health: null,
    mcpSummary: null,
    agentSummary: null,
    mcpList: null,
    agentList: null,
    logStats: null,
    recentLogs: null,
    loading: true,
    error: null,
    lastUpdate: null,
  });

  const fetchDashboardData = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      // Fetch all dashboard data in parallel
      const [health, mcpSummary, agentSummary, mcpList, agentList, logStats, recentLogs] = await Promise.allSettled([
        api.health.getHealth(),
        api.mcp.getStatusSummary(),
        api.agents.getStatusSummary(),
        api.mcp.list({ limit: 10 }),
        api.agents.list({ limit: 10 }),
        api.logs.getStats(),
        api.logs.list({ limit: PAGINATION.DASHBOARD_LOGS_LIMIT }),
      ]);

      // Log any API failures for monitoring
      [health, mcpSummary, agentSummary, mcpList, agentList, logStats, recentLogs].forEach((result, index) => {
        if (result.status === 'rejected') {
          const names = ['Health', 'MCP Summary', 'Agent Summary', 'MCP List', 'Agent List', 'Log Stats', 'Recent Logs'];
          console.error(`${names[index]} API failed:`, result.reason);
        }
      });

      setState(prev => ({
        ...prev,
        health: health.status === 'fulfilled' ? health.value : null,
        mcpSummary: mcpSummary.status === 'fulfilled' ? mcpSummary.value : null,
        agentSummary: agentSummary.status === 'fulfilled' ? agentSummary.value : null,
        mcpList: mcpList.status === 'fulfilled' ? mcpList.value : null,
        agentList: agentList.status === 'fulfilled' ? agentList.value : null,
        logStats: logStats.status === 'fulfilled' ? logStats.value : null,
        recentLogs: recentLogs.status === 'fulfilled' ? recentLogs.value : null,
        loading: false,
        lastUpdate: new Date(),
      }));

    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch dashboard data";
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      handleError(err, errorMessage);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    
    // Set up polling for real-time updates
    const interval = setInterval(fetchDashboardData, POLLING_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  const { health, mcpSummary, agentSummary, mcpList, agentList, logStats, recentLogs, loading, error, lastUpdate } = state;

  // Calculate derived metrics
  const totalMCPs = mcpSummary?.total || 0;
  const activeMCPs = mcpSummary?.by_status[MCP_STATUS.ACTIVE] || 0;
  const totalAgents = agentSummary?.total || 0;
  const totalLogs = logStats?.total || 0;
  const errorLogs = logStats?.error_count || 0;
  const successRate = totalLogs > 0 ? ((totalLogs - errorLogs) / totalLogs) * 100 : 100;
  const systemHealthy = health?.status === "ok" && health?.tables_accessible;
  const totalCapabilities = agentSummary?.capabilities?.total_unique || 0;
  const avgCapabilitiesPerAgent = agentSummary?.avg_capabilities_per_agent || 0;
  const recentAgentRegistrations = agentSummary?.recent_registrations || 0;

  return (
    <div className="hidden flex-col md:flex">
      {/* Consolidated Dashboard Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="flex h-20 items-center px-8">
          <div className="flex items-center space-x-4">
            <div className="p-2 rounded-lg bg-primary/10">
              <Home className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">AgenticTrust Dashboard</h1>
              <p className="text-sm text-muted-foreground">
                Monitor and manage your Model Context Protocol integrations and agent identities in real-time
              </p>
            </div>
          </div>
          
          <div className="ml-auto flex items-center space-x-4">
            {/* Live Status & Update Info */}
            <div className="flex items-center space-x-3">
              <LiveIndicator 
                isConnected={!error} 
                lastUpdate={lastUpdate || undefined} 
                isLoading={loading}
              />
              
              {/* Error Display */}
              {error && (
                <div className="flex items-center space-x-2 text-red-600 bg-red-50 px-3 py-1 rounded-md border border-red-200">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm font-medium">{error}</span>
                </div>
              )}
            </div>
            
            {/* Refresh Button */}
            <Button
              onClick={fetchDashboardData}
              variant="outline"
              size="sm"
              disabled={loading}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-6 p-8 pt-6">

        {/* System Overview - Top 4 Cards */}
        <StatsGrid columns={4}>
          <StatCard
            title="System Health"
            value={systemHealthy ? 'Healthy' : 'Issues'}
            description={health?.uptime ? `Uptime: ${Math.floor(health.uptime / 60)}m` : 'Status unknown'}
            icon={Database}
            valueClassName={systemHealthy ? 'text-green-600' : 'text-red-600'}
            onClick={() => window.location.href = '/analytics'}
          />
          
          <StatCard
            title="Active MCPs"
            value={activeMCPs}
            description={`${totalMCPs} total registered`}
            icon={Network}
            valueClassName="text-blue-600"
            trend={mcpSummary?.trends ? {
              value: Math.abs(mcpSummary.trends.trend_percentage),
              isPositive: mcpSummary.trends.is_positive,
              label: "this week"
            } : undefined}
            onClick={() => window.location.href = '/mcp'}
          />
          
          <StatCard
            title="Total Agents"
            value={totalAgents}
            description={recentAgentRegistrations > 0 ? `+${recentAgentRegistrations} this week` : 'No recent activity'}
            icon={UserCog}
            valueClassName="text-purple-600"
            trend={agentSummary?.trends ? {
              value: Math.abs(agentSummary.trends.trend_percentage),
              isPositive: agentSummary.trends.is_positive,
              label: "this week"
            } : undefined}
            onClick={() => window.location.href = '/agents'}
          />
          
          <StatCard
            title="Success Rate"
            value={`${successRate.toFixed(1)}%`}
            description={`${totalLogs} total events`}
            icon={CheckCircle}
            valueClassName="text-green-600"
            trend={logStats?.trends ? {
              value: Math.abs(logStats.trends.success_rate_trend),
              isPositive: logStats.trends.is_improving,
              label: "vs last week"
            } : undefined}
            onClick={() => window.location.href = '/activities'}
          />
        </StatsGrid>

        {/* Entity Management - 3 Enhanced Cards */}
        <div className="grid gap-6 md:grid-cols-3">
          {/* Enhanced MCP Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="h-5 w-5 text-blue-600" />
                MCP Status
              </CardTitle>
              <CardDescription>
                Server status and capabilities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {mcpSummary?.by_status ? (
                Object.entries(mcpSummary.by_status).map(([status, count]) => (
                  <div key={status} className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${STATUS_COLORS[status as keyof typeof STATUS_COLORS] || 'bg-gray-500'}`} />
                      <span className="text-sm capitalize">{status}</span>
                    </div>
                    <Badge variant="secondary">{count}</Badge>
                  </div>
                ))
              ) : (
                <div className="text-center text-muted-foreground py-4">
                  No MCP data available
                </div>
              )}
              
              {mcpSummary?.capabilities && (
                <div className="pt-4 border-t space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-1">
                      <Wrench className="h-3 w-3" />
                      Tools
                    </span>
                    <span className="font-medium">{mcpSummary.capabilities.tools}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-1">
                      <FileText className="h-3 w-3" />
                      Resources
                    </span>
                    <span className="font-medium">{mcpSummary.capabilities.resources}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      Prompts
                    </span>
                    <span className="font-medium">{mcpSummary.capabilities.prompts}</span>
                  </div>
                </div>
              )}
              
              <div className="mt-4 pt-4 border-t">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <a href="/mcp">
                    Manage MCPs
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Agent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-600" />
                Agent Activity
              </CardTitle>
              <CardDescription>
                Agent registrations and capabilities
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-purple-50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">{totalAgents}</div>
                  <div className="text-xs text-purple-600">Total Agents</div>
                </div>
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">{totalCapabilities}</div>
                  <div className="text-xs text-green-600">Capabilities</div>
                </div>
              </div>
              
              {agentSummary?.capabilities && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Avg per Agent</span>
                    <span className="font-medium">{avgCapabilitiesPerAgent}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Tools in Use</span>
                    <span className="font-medium">{agentSummary.capabilities.tools}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Resources in Use</span>
                    <span className="font-medium">{agentSummary.capabilities.resources}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Prompts in Use</span>
                    <span className="font-medium">{agentSummary.capabilities.prompts}</span>
                  </div>
                </div>
              )}
              
              {recentAgentRegistrations > 0 && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <div className="text-sm font-medium text-blue-800">
                    +{recentAgentRegistrations} new agents this week
                  </div>
                </div>
              )}
              
              <div className="mt-4 pt-4 border-t">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <a href="/agents">
                    Manage Agents
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-orange-600" />
                Recent Activity
              </CardTitle>
              <CardDescription>
                Activity from the last hour
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {(() => {
                  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
                  const lastHourLogs = recentLogs?.items.filter(log => 
                    new Date(log.timestamp).getTime() > oneHourAgo.getTime()
                  ) || [];
                  
                  if (lastHourLogs.length === 0) {
                    return (
                      <div className="text-center text-muted-foreground py-4">
                        No activity in the last hour
                      </div>
                    );
                  }
                  
                  return lastHourLogs.slice(0, 8).map((log) => {
                    const toolName = (log.data as any)?.tool_name;
                    const agentName = (log.data as any)?.agent_name;
                    const errorMessage = (log.data as any)?.error;
                    const operation = (log.data as any)?.arguments?.operation;
                    
                    return (
                      <div key={log.id} className="flex items-center justify-between py-2 hover:bg-muted/30 rounded px-2 transition-colors">
                        <div className="flex items-center space-x-2 flex-1 min-w-0">
                          <div className={`w-1.5 h-1.5 rounded-full ${SEVERITY_COLORS[log.severity as keyof typeof SEVERITY_COLORS] || 'bg-gray-500'}`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-1 text-sm">
                              <span className="font-medium">{log.event_type}</span>
                              {toolName && (
                                <span className="text-blue-600 truncate">
                                  → {toolName}
                                  {operation && <span className="text-muted-foreground text-xs">({operation})</span>}
                                </span>
                              )}
                              {log.event_type === 'tool_error' && errorMessage && (
                                <span className="text-red-600 text-xs truncate" title={errorMessage}>
                                  - {errorMessage}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                              <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                              {agentName && (
                                <>
                                  <span>•</span>
                                  <span className="truncate max-w-20" title={agentName}>{agentName}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <Badge variant="outline" className="text-xs ml-2">
                          {log.severity}
                        </Badge>
                      </div>
                    );
                  });
                                 })()}
              </div>
              
              {logStats && (
                <div className="mt-4 pt-4 border-t">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex justify-between">
                      <span>Total Events:</span>
                      <span className="font-medium">{totalLogs}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Errors:</span>
                      <span className={`font-medium ${errorLogs > 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {errorLogs}
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="mt-4 pt-4 border-t">
                <Button variant="outline" size="sm" className="w-full" asChild>
                  <a href="/activities">
                    View All Activities
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Insights & Analytics - Bottom Section */}
        <div className="grid gap-6 md:grid-cols-2">
          {/* Capability Distribution */}
          <CapabilityDistributionCard 
            agentSummary={agentSummary} 
            loading={loading}
          />

          {/* System Performance Overview */}
          <SystemPerformanceCard 
            health={health}
            logStats={logStats}
            loading={loading}
          />
        </div>

        {/* Getting Started Guide - Enhanced */}
        {(totalMCPs === 0 || totalAgents === 0) && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">🚀 Getting Started with AgenticTrust</CardTitle>
              <CardDescription className="text-blue-600">
                Your AgenticTrust system is running and ready to monitor MCP integrations and manage agent identities
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-3">
                <div className="p-4 bg-white rounded-lg border">
                  <div className="flex items-center space-x-2 mb-2">
                    <Network className="h-5 w-5 text-blue-600" />
                    <h3 className="font-semibold">1. Register MCPs</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Add your Model Context Protocol servers to start monitoring
                  </p>
                  <Button size="sm" asChild disabled={totalMCPs > 0}>
                    <a href="/mcp">
                      {totalMCPs > 0 ? `${totalMCPs} MCPs Registered` : 'Register MCPs'}
                    </a>
                  </Button>
                </div>
                
                <div className="p-4 bg-white rounded-lg border">
                  <div className="flex items-center space-x-2 mb-2">
                    <UserCog className="h-5 w-5 text-purple-600" />
                    <h3 className="font-semibold">2. Create Agents</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Register agent identities and assign capability permissions
                  </p>
                  <Button size="sm" variant="outline" asChild disabled={totalAgents > 0}>
                    <a href="/agents">
                      {totalAgents > 0 ? `${totalAgents} Agents Created` : 'Create Agents'}
                    </a>
                  </Button>
                </div>
                
                <div className="p-4 bg-white rounded-lg border">
                  <div className="flex items-center space-x-2 mb-2">
                    <Activity className="h-5 w-5 text-green-600" />
                    <h3 className="font-semibold">3. Monitor Activity</h3>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    Watch real-time events and system performance
                  </p>
                  <Button size="sm" variant="outline" asChild>
                    <a href="/activities">View Activities</a>
                  </Button>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-white rounded-lg border">
                <h4 className="font-semibold mb-2">📖 Need Help?</h4>
                <p className="text-sm text-muted-foreground">
                  Check out the documentation for examples of MCP server configurations and agent identity management patterns.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

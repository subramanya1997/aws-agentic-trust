"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  Download,
  TrendingUp
} from "lucide-react";
import { StatCard, StatsGrid } from "@/components/stats";

import { TopHeader } from "@/components/top-header";
import { pageConfig } from "@/lib/config";
import { api, ApiError } from "@/lib/api";
import type { 
  LogEntryResponse, 
  LogStats,
  LogSeverity 
} from "@/lib/types";
import { 
  PAGINATION,
  LOG_SEVERITY
} from "@/lib/constants";
import { handleError } from "@/lib/utils";
import {
  EventLogList 
} from "@/components/activities";

interface ActivitiesState {
  logs: LogEntryResponse[];
  stats: LogStats | null;
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  filters: {
    event_type?: string;
    severity?: LogSeverity;
  };
}

export default function ActivitiesPage() {
  const [state, setState] = useState<ActivitiesState>({
    logs: [],
    stats: null,
    loading: true,
    error: null,
    total: 0,
    currentPage: 1,
    filters: {},
  });

  const fetchLogs = useCallback(async (page: number = 1, filters: { event_type?: string; severity?: LogSeverity } = {}) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const [logsResult, statsResult] = await Promise.allSettled([
        api.logs.list({ 
          skip: (page - 1) * PAGINATION.LOGS_DEFAULT_LIMIT,
          limit: PAGINATION.LOGS_DEFAULT_LIMIT,
          ...filters
        }),
        api.logs.getStats(),
      ]);

      const logs = logsResult.status === 'fulfilled' ? logsResult.value : null;
      const stats = statsResult.status === 'fulfilled' ? statsResult.value : null;

      setState(prev => ({
        ...prev,
        logs: logs?.items || [],
        stats: stats,
        total: logs?.total || 0,
        currentPage: page,
        filters: filters,
        loading: false,
      }));

    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch logs";
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      handleError(err, errorMessage);
    }
  }, []);

  const handleFilterChange = useCallback((key: string, value: string | undefined) => {
    const newFilters = { ...state.filters };
    if (value && value !== 'all') {
      if (key === 'severity') {
        newFilters.severity = value as LogSeverity;
      } else if (key === 'event_type') {
        newFilters.event_type = value;
      }
    } else {
      delete newFilters[key as keyof typeof newFilters];
    }
    
    setState(prev => ({ ...prev, filters: newFilters }));
    fetchLogs(1, newFilters);
  }, [state.filters, fetchLogs]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const { logs, stats, loading, error, total, currentPage, filters } = state;

  // Calculate derived metrics
  const recentLogs = logs.slice(0, 5);
  const errorCount = stats?.error_count || 0;
  const totalLogs = stats?.total || 0;
  const successRate = totalLogs > 0 ? ((totalLogs - errorCount) / totalLogs) * 100 : 100;
  
  // Recent activity (logs from last hour)
  const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
  const recentActivity = logs.filter(log => 
    new Date(log.timestamp).getTime() > oneHourAgo.getTime()
  ).length;

  return (
    <div className="hidden flex-col md:flex">
      <TopHeader 
        page={pageConfig.logs}
        showLiveIndicator={true}
        onRefresh={() => fetchLogs(currentPage, filters)}
        isLoading={loading}
        actions={[]}
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

        {/* Real-time Stats */}
        <StatsGrid columns={4}>
          <StatCard
            title="Recent Activity"
            value={recentActivity}
            description="Events in last hour"
            icon={Activity}
            status={recentActivity > 0 ? "healthy" : "neutral"}
          />
          
          <StatCard
            title="Total Events"
            value={totalLogs}
            description="All time"
            icon={TrendingUp}
            trend={stats?.trends ? {
              value: Math.abs(((stats.trends.recent_logs - stats.trends.previous_week_logs) / Math.max(stats.trends.previous_week_logs, 1)) * 100),
              isPositive: stats.trends.recent_logs >= stats.trends.previous_week_logs,
              label: "this week"
            } : undefined}
          />
          
          <StatCard
            title="Success Rate"
            value={`${successRate.toFixed(1)}%`}
            description="Non-error events"
            icon={CheckCircle}
            valueClassName="text-green-600"
            trend={stats?.trends ? {
              value: Math.abs(stats.trends.success_rate_trend),
              isPositive: stats.trends.is_improving,
              label: "vs last week"
            } : undefined}
          />
          
          <StatCard
            title="Errors"
            value={errorCount}
            description="Critical + Error logs"
            icon={AlertCircle}
            valueClassName={errorCount > 0 ? 'text-red-600' : 'text-green-600'}
            trend={stats?.trends ? {
              value: Math.abs(((stats.trends.recent_errors - stats.trends.previous_week_errors) / Math.max(stats.trends.previous_week_errors, 1)) * 100),
              isPositive: stats.trends.recent_errors <= stats.trends.previous_week_errors,
              label: "vs last week"
            } : undefined}
          />
        </StatsGrid>

        {/* Full Event Log */}
        <EventLogList logs={logs} loading={loading} total={total} />
      </div>
    </div>
  );
} 
"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  TrendingUp, 
  TrendingDown,
  ArrowRight,
  Database,
  Clock,
  Activity,
  AlertTriangle,
  CheckCircle
} from "lucide-react";
import type { HealthResponse, LogStats } from "@/lib/types";

interface SystemPerformanceCardProps {
  health: HealthResponse | null;
  logStats: LogStats | null;
  loading?: boolean;
}

export function SystemPerformanceCard({ health, logStats, loading }: SystemPerformanceCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-indigo-600" />
            System Performance
          </CardTitle>
          <CardDescription>Loading performance data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {[1, 2].map((i) => (
                <div key={i} className="h-16 bg-muted rounded-lg" />
              ))}
            </div>
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-4 bg-muted rounded" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const totalLogs = logStats?.total || 0;
  const errorLogs = logStats?.error_count || 0;
  const successRate = totalLogs > 0 ? ((totalLogs - errorLogs) / totalLogs) * 100 : 100;
  const systemHealthy = health?.status === "ok" && health?.tables_accessible;
  const uptime = health?.uptime || 0;
  const uptimeHours = Math.floor(uptime / 3600);
  const uptimeMinutes = Math.floor((uptime % 3600) / 60);

  const getPerformanceStatus = () => {
    if (!systemHealthy) return "error";
    if (successRate < 95) return "warning";
    return "healthy";
  };

  const performanceStatus = getPerformanceStatus();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-indigo-600" />
          System Performance
        </CardTitle>
        <CardDescription>
          Health and performance metrics
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-green-50 rounded-lg border border-green-200 text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              {successRate >= 95 ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
              )}
              <div className={`text-lg font-bold ${successRate >= 95 ? 'text-green-600' : 'text-yellow-600'}`}>
                {successRate.toFixed(1)}%
              </div>
            </div>
            <div className="text-xs text-green-600 font-medium">Success Rate</div>
            <div className="text-xs text-muted-foreground">
              {totalLogs} total events
            </div>
          </div>
          
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 text-center">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Clock className="h-4 w-4 text-blue-600" />
              <div className="text-lg font-bold text-blue-600">
                {uptimeHours > 0 ? `${uptimeHours}h` : `${uptimeMinutes}m`}
              </div>
            </div>
            <div className="text-xs text-blue-600 font-medium">System Uptime</div>
            <div className="text-xs text-muted-foreground">
              {uptimeHours > 0 && uptimeMinutes > 0 ? `${uptimeMinutes}m` : 'Running'}
            </div>
          </div>
        </div>

        {/* System Status Details */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Database Status</span>
            </div>
            <Badge variant={health?.tables_accessible ? "default" : "destructive"}>
              {health?.tables_accessible ? "Connected" : "Issues"}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Schema Version</span>
            </div>
            <Badge variant="outline">
              {health?.schema_version || "Unknown"}
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {performanceStatus === "healthy" ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : performanceStatus === "warning" ? (
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
              ) : (
                <AlertTriangle className="h-4 w-4 text-red-600" />
              )}
              <span className="text-sm">Overall Status</span>
            </div>
            <Badge 
              variant={
                performanceStatus === "healthy" ? "default" : 
                performanceStatus === "warning" ? "secondary" : 
                "destructive"
              }
            >
              {performanceStatus === "healthy" ? "Operational" : 
               performanceStatus === "warning" ? "Attention" : 
               "Issues Detected"}
            </Badge>
          </div>
        </div>

        {/* Error Breakdown */}
        {logStats?.by_severity && Object.keys(logStats.by_severity).length > 0 && (
          <div className="pt-4 border-t">
            <h4 className="text-sm font-medium mb-3">Event Severity Breakdown</h4>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {Object.entries(logStats.by_severity).map(([severity, count]) => (
                <div key={severity} className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${
                      severity === 'error' || severity === 'critical' ? 'bg-red-500' :
                      severity === 'warning' ? 'bg-yellow-500' :
                      severity === 'info' ? 'bg-blue-500' :
                      'bg-gray-500'
                    }`} />
                    <span className="capitalize">{severity}</span>
                  </div>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Performance Trends */}
        <div className="pt-4 border-t">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium">Performance Trend</span>
            <div className="flex items-center gap-1">
              {successRate >= 95 ? (
                <>
                  <TrendingUp className="h-3 w-3 text-green-600" />
                  <span className="text-xs text-green-600 font-medium">Stable</span>
                </>
              ) : (
                <>
                  <TrendingDown className="h-3 w-3 text-yellow-600" />
                  <span className="text-xs text-yellow-600 font-medium">Needs Attention</span>
                </>
              )}
            </div>
          </div>
          
          <Button variant="outline" size="sm" className="w-full" asChild>
            <a href="/analytics">
              View Detailed Analytics
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
} 
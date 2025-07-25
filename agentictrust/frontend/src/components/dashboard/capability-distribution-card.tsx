"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  BarChart3, 
  Wrench, 
  FileText, 
  MessageSquare, 
  ArrowRight,
  TrendingUp,
  Users
} from "lucide-react";
import type { AgentStatusSummary } from "@/lib/types";
import { formatPercentage } from "@/lib/utils";

interface CapabilityDistributionCardProps {
  agentSummary: AgentStatusSummary | null;
  loading?: boolean;
}

export function CapabilityDistributionCard({ agentSummary, loading }: CapabilityDistributionCardProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-green-600" />
            Capability Distribution
          </CardTitle>
          <CardDescription>Loading capability data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-muted rounded-lg" />
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

  if (!agentSummary?.capabilities) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-green-600" />
            Capability Distribution
          </CardTitle>
          <CardDescription>No capability data available</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Register agents and assign capabilities to see distribution
            </p>
            <Button variant="outline" size="sm" className="mt-4" asChild>
              <a href="/agents">Create First Agent</a>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const { capabilities } = agentSummary;
  const totalAvailable = (capabilities.available?.tools || 0) + 
                         (capabilities.available?.resources || 0) + 
                         (capabilities.available?.prompts || 0);
  
  const utilizationRate = totalAvailable > 0 ? 
    formatPercentage(capabilities.total_unique, totalAvailable) : 0;

  const toolsUtilization = capabilities.available?.tools ? 
    formatPercentage(capabilities.tools, capabilities.available.tools) : 0;
  
  const resourcesUtilization = capabilities.available?.resources ? 
    formatPercentage(capabilities.resources, capabilities.available.resources) : 0;
  
  const promptsUtilization = capabilities.available?.prompts ? 
    formatPercentage(capabilities.prompts, capabilities.available.prompts) : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-green-600" />
          Capability Distribution
        </CardTitle>
        <CardDescription>
          How capabilities are allocated across {agentSummary.total} agents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
            <div className="text-lg font-bold text-blue-600">
              {capabilities.tools}
            </div>
            <div className="text-xs text-blue-600 font-medium">Tools in Use</div>
            <div className="text-xs text-muted-foreground">
              of {capabilities.available?.tools || 0} available
            </div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="text-lg font-bold text-green-600">
              {capabilities.resources}
            </div>
            <div className="text-xs text-green-600 font-medium">Resources in Use</div>
            <div className="text-xs text-muted-foreground">
              of {capabilities.available?.resources || 0} available
            </div>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
            <div className="text-lg font-bold text-purple-600">
              {capabilities.prompts}
            </div>
            <div className="text-xs text-purple-600 font-medium">Prompts in Use</div>
            <div className="text-xs text-muted-foreground">
              of {capabilities.available?.prompts || 0} available
            </div>
          </div>
        </div>

        {/* Utilization Bars */}
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <Wrench className="h-4 w-4 text-blue-600" />
                <span>Tools Utilization</span>
              </div>
              <span className="font-medium">{toolsUtilization}%</span>
            </div>
            <Progress value={toolsUtilization} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-green-600" />
                <span>Resources Utilization</span>
              </div>
              <span className="font-medium">{resourcesUtilization}%</span>
            </div>
            <Progress value={resourcesUtilization} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-purple-600" />
                <span>Prompts Utilization</span>
              </div>
              <span className="font-medium">{promptsUtilization}%</span>
            </div>
            <Progress value={promptsUtilization} className="h-2" />
          </div>
        </div>

        {/* Summary */}
        <div className="pt-4 border-t space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Overall Utilization</span>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <span className="font-bold text-green-600">{utilizationRate}%</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Avg per Agent</span>
            <span className="font-medium">{agentSummary.avg_capabilities_per_agent || 0}</span>
          </div>

          <Button variant="outline" size="sm" className="w-full mt-4" asChild>
            <a href="/agents">
              Manage Agent Capabilities
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
} 
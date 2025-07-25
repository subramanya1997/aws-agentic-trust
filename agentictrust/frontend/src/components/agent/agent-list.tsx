import React from "react";
import { Button } from "@/components/ui/button";
import { RefreshCw, UserCog } from "lucide-react";
import { AgentCard } from "./agent-card";
import type { AgentResponse } from "@/lib/types";

interface AgentListProps {
  agents: AgentResponse[];
  total: number;
  loading?: boolean;
  onEdit?: (agent: AgentResponse) => void;
  onDelete?: (id: string) => void;
  onRefresh?: () => void;
}

export function AgentList({ 
  agents, 
  total, 
  loading = false, 
  onEdit,
  onDelete,
  onRefresh 
}: AgentListProps) {

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <RefreshCw className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading Agents…</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header section */}
      <div>
        <h2 className="text-lg font-semibold">Registered Agents</h2>
        <p className="text-sm text-muted-foreground">
          All agents registered with the system ({total} total)
        </p>
      </div>

      {/* Content */}
      {agents.length === 0 ? (
        <div className="text-center py-8 border rounded-lg">
          <UserCog className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Agents Registered</h3>
          <p className="text-muted-foreground mb-4">
            Start by registering your first agent
          </p>
          <Button onClick={onRefresh}>
            <UserCog className="mr-2 h-4 w-4" />
            Register First Agent
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
} 
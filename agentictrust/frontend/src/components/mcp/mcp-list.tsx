"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Network, 
  Plus,
  RefreshCw
} from "lucide-react";
import { RegisterMCPSheet, MCPCard } from "@/components/mcp";
import type { MCPResponse } from "@/lib/types";

interface MCPListProps {
  mcps: MCPResponse[];
  total: number;
  loading: boolean;
  onEdit: (mcp: MCPResponse) => void;
  onDelete: (id: string) => void;
  onRefresh: () => void;
}

export function MCPList({ 
  mcps, 
  total, 
  loading, 
  onEdit, 
  onDelete, 
  onRefresh 
}: MCPListProps) {
  return (
    <div className="space-y-4">
      {/* Header section */}
      <div>
        <h2 className="text-lg font-semibold">Registered MCPs</h2>
        <p className="text-sm text-muted-foreground">
          All Model Context Protocols registered with the system ({total} total)
        </p>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading MCPs...</span>
        </div>
      ) : mcps.length === 0 ? (
        <div className="text-center py-8 border rounded-lg">
          <Network className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No MCPs Registered</h3>
          <p className="text-muted-foreground mb-4">
            Start by registering your first Model Context Protocol
          </p>
          <RegisterMCPSheet 
            onSuccess={onRefresh}
            trigger={
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Register First MCP
              </Button>
            }
          />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mcps.map((mcp) => (
            <MCPCard
              key={mcp.id}
              mcp={mcp}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
} 
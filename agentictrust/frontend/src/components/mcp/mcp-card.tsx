import React from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  Edit, 
  Trash2, 
  Globe, 
  Terminal, 
  ChevronDown, 
  ChevronUp, 
  Wrench, 
  FileText, 
  MessageSquare,
  MoreVertical,
  ExternalLink,
  Copy
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { MCPResponse } from "@/lib/types";
import { MCP_STATUS } from "@/lib/constants";
import { ViewMCPSheet } from "./view-mcp-sheet";

interface MCPCardProps {
  mcp: MCPResponse;
  onEdit: (mcp: MCPResponse) => void;
  onDelete: (id: string) => void;
}

export function MCPCard({ mcp, onEdit, onDelete }: MCPCardProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [viewSheetOpen, setViewSheetOpen] = React.useState(false);
  
  const getServerIcon = () => {
    return mcp.server_type === "sse" ? Globe : Terminal;
  };

  const ServerIcon = getServerIcon();

  const getStatusColor = (status: string) => {
    switch (status) {
      case MCP_STATUS.ACTIVE:
        return "bg-green-500";
      case MCP_STATUS.ERROR:
        return "bg-red-500";
      case MCP_STATUS.INACTIVE:
        return "bg-gray-400";
      default:
        return "bg-blue-500";
    }
  };

  const hasCapabilities = (mcp.tools_count ?? 0) > 0 || 
                         (mcp.resources_count ?? 0) > 0 || 
                         (mcp.prompts_count ?? 0) > 0;

  return (
    <div>
      <Card className="group hover:shadow-lg transition-all duration-200 overflow-hidden">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className={`p-2 rounded-lg bg-muted flex-shrink-0`}>
                <ServerIcon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-base truncate">
                    {mcp.name || 'Unnamed MCP'}
                  </h3>
                  <div className={`w-2 h-2 rounded-full ${getStatusColor(mcp.status)} flex-shrink-0`} 
                       title={mcp.status} />
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className="text-xs px-2 py-0">
                    {mcp.server_type.toUpperCase()}
                  </Badge>
                  {mcp.environment && (
                    <span className="truncate">{mcp.environment}</span>
                  )}
                </div>
              </div>
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm"
                  className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setViewSheetOpen(true)}>
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View Details
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit(mcp)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigator.clipboard.writeText(mcp.id)}>
                  <Copy className="mr-2 h-4 w-4" />
                  Copy ID
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem 
                  onClick={() => onDelete(mcp.id)}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </CardHeader>
        
        <CardContent className="pt-0 pb-4">
          {/* Connection Info */}
          <div className="mb-4 p-3 bg-muted/50 rounded-lg">
            {mcp.url ? (
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">URL</p>
                <code className="text-xs block truncate">
                  {mcp.url}
                </code>
              </div>
            ) : mcp.command ? (
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">Command</p>
                <code className="text-xs block truncate">
                  {mcp.command} {mcp.args?.join(' ')}
                </code>
              </div>
            ) : null}
          </div>

          {/* Capabilities Section */}
          {hasCapabilities && (
            <div className="space-y-3">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4 text-sm">
                  {(mcp.tools_count ?? 0) > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Wrench className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{mcp.tools_count}</span>
                      <span className="text-muted-foreground">Tools</span>
                    </div>
                  )}
                  {(mcp.resources_count ?? 0) > 0 && (
                    <div className="flex items-center gap-1.5">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{mcp.resources_count}</span>
                      <span className="text-muted-foreground">Resources</span>
                    </div>
                  )}
                  {(mcp.prompts_count ?? 0) > 0 && (
                    <div className="flex items-center gap-1.5">
                      <MessageSquare className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{mcp.prompts_count}</span>
                      <span className="text-muted-foreground">Prompts</span>
                    </div>
                  )}
                </div>
                {isExpanded ? 
                  <ChevronUp className="h-4 w-4 text-muted-foreground" /> : 
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                }
              </button>
              
              {isExpanded && (
                <div className="px-3 space-y-3 animate-in slide-in-from-top-2 duration-200">
                  {/* Tools */}
                  {mcp.tool_names && mcp.tool_names.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                        <Wrench className="h-3 w-3" />
                        TOOLS
                      </div>
                      <div className="grid grid-cols-2 gap-1.5">
                        {mcp.tool_names.map((name, idx) => (
                          <div key={idx} className="text-xs px-2 py-1 bg-muted rounded-md truncate" title={name}>
                            {name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Resources */}
                  {mcp.resource_names && mcp.resource_names.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                        <FileText className="h-3 w-3" />
                        RESOURCES
                      </div>
                      <div className="grid grid-cols-2 gap-1.5">
                        {mcp.resource_names.map((name, idx) => (
                          <div key={idx} className="text-xs px-2 py-1 bg-muted rounded-md truncate" title={name}>
                            {name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Prompts */}
                  {mcp.prompt_names && mcp.prompt_names.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                        <MessageSquare className="h-3 w-3" />
                        PROMPTS
                      </div>
                      <div className="grid grid-cols-2 gap-1.5">
                        {mcp.prompt_names.map((name, idx) => (
                          <div key={idx} className="text-xs px-2 py-1 bg-muted rounded-md truncate" title={name}>
                            {name}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="mt-4 pt-3 border-t flex items-center justify-between text-xs text-muted-foreground">
            <span title={mcp.id} className="font-mono truncate max-w-[120px]">
              {mcp.id.slice(0, 8)}
            </span>
            <span>
              Updated {new Date(mcp.updated_at).toLocaleDateString()}
            </span>
          </div>
        </CardContent>
      </Card>

      <ViewMCPSheet 
        mcp={mcp} 
        open={viewSheetOpen}
        onOpenChange={setViewSheetOpen}
        trigger={<span />}
      />
    </div>
  );
} 
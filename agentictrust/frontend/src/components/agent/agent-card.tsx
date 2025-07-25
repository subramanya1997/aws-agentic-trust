import React from "react";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  UserCog, 
  Wrench, 
  FileText, 
  MessageSquare, 
  Calendar, 
  Copy,
  MoreVertical,
  Edit,
  Trash2,
  ExternalLink
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { AgentResponse } from "@/lib/types";
import { ViewAgentSheet } from "./view-agent-sheet";

interface AgentCardProps {
  agent: AgentResponse;
  onEdit?: (agent: AgentResponse) => void;
  onDelete?: (id: string) => void;
  onView?: (agent: AgentResponse) => void;
}

export function AgentCard({ agent, onEdit, onDelete, onView }: AgentCardProps) {
  const [viewSheetOpen, setViewSheetOpen] = React.useState(false);
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div>
      <Card className="group hover:shadow-lg transition-shadow duration-200 overflow-hidden">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="p-2 rounded-lg bg-muted flex-shrink-0">
              <UserCog className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-base sm:text-lg font-semibold truncate mb-1">
                {agent.name || "Unnamed Agent"}
              </CardTitle>
              <CardDescription className="text-xs font-mono bg-muted px-2 py-1 rounded flex items-center gap-1 max-w-full">
                <span className="truncate flex-1">{agent.client_id}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0 hover:bg-muted-foreground/20 flex-shrink-0"
                  onClick={() => copyToClipboard(agent.client_id)}
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </CardDescription>
            </div>
          </div>
          
          {/* Dropdown Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="bottom" sideOffset={4} className="w-48">
              <DropdownMenuItem onClick={() => setViewSheetOpen(true)}>
                <ExternalLink className="mr-2 h-4 w-4" />
                View Details
              </DropdownMenuItem>
              {onEdit ? (
                <DropdownMenuItem onClick={() => onEdit(agent)}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem disabled className="text-muted-foreground cursor-not-allowed">
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => copyToClipboard(agent.client_id)}>
                <Copy className="mr-2 h-4 w-4" />
                Copy Client ID
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {onDelete && (
                <DropdownMenuItem 
                  onClick={() => onDelete(agent.id)}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        
        {agent.description && (
          <p className="text-sm text-muted-foreground mt-2 overflow-hidden text-ellipsis" style={{ 
            display: '-webkit-box', 
            WebkitLineClamp: 2, 
            WebkitBoxOrient: 'vertical' 
          }}>
            {agent.description}
          </p>
        )}
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Tools Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Wrench className="h-4 w-4 text-blue-600 flex-shrink-0" />
            <span className="text-sm font-medium">Tools ({agent.tools.length})</span>
          </div>
          {agent.tools.length > 0 ? (
            <div className="space-y-1">
              {agent.tools.slice(0, 3).map((tool) => (
                <div key={tool.id} className="flex items-center justify-between gap-2 text-xs min-w-0">
                  <span className="font-medium text-foreground truncate flex-1">{tool.name}</span>
                  {tool.mcp_name && (
                    <Badge variant="outline" className="text-xs px-1 py-0 flex-shrink-0">
                      {tool.mcp_name}
                    </Badge>
                  )}
                </div>
              ))}
              {agent.tools.length > 3 && (
                <p className="text-xs text-muted-foreground">
                  +{agent.tools.length - 3} more
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No tools assigned</p>
          )}
        </div>

        {/* Resources Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-green-600 flex-shrink-0" />
            <span className="text-sm font-medium">Resources ({agent.resources.length})</span>
          </div>
          {agent.resources.length > 0 ? (
            <div className="space-y-1">
              {agent.resources.slice(0, 3).map((resource) => (
                <div key={resource.id} className="flex items-center justify-between gap-2 text-xs min-w-0">
                  <span className="font-medium text-foreground truncate flex-1">{resource.name}</span>
                  {resource.mcp_name && (
                    <Badge variant="outline" className="text-xs px-1 py-0 flex-shrink-0">
                      {resource.mcp_name}
                    </Badge>
                  )}
                </div>
              ))}
              {agent.resources.length > 3 && (
                <p className="text-xs text-muted-foreground">
                  +{agent.resources.length - 3} more
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No resources assigned</p>
          )}
        </div>

        {/* Prompts Section */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-purple-600 flex-shrink-0" />
            <span className="text-sm font-medium">Prompts ({agent.prompts.length})</span>
          </div>
          {agent.prompts.length > 0 ? (
            <div className="space-y-1">
              {agent.prompts.slice(0, 3).map((prompt) => (
                <div key={prompt.id} className="flex items-center justify-between gap-2 text-xs min-w-0">
                  <span className="font-medium text-foreground truncate flex-1">{prompt.name}</span>
                  {prompt.mcp_name && (
                    <Badge variant="outline" className="text-xs px-1 py-0 flex-shrink-0">
                      {prompt.mcp_name}
                    </Badge>
                  )}
                </div>
              ))}
              {agent.prompts.length > 3 && (
                <p className="text-xs text-muted-foreground">
                  +{agent.prompts.length - 3} more
                </p>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">No prompts assigned</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center gap-2 pt-2 border-t">
          <Calendar className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">
            Created {new Date(agent.created_at).toLocaleDateString()}
          </span>
        </div>
      </CardContent>
    </Card>

      <ViewAgentSheet 
        agent={agent} 
        open={viewSheetOpen}
        onOpenChange={setViewSheetOpen}
        trigger={<span />}
      />
    </div>
  );
} 
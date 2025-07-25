"use client";

import React from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  UserCog, 
  Wrench, 
  FileText, 
  MessageSquare, 
  Calendar,
  Copy,
  Check
} from "lucide-react";
import type { AgentResponse } from "@/lib/types";

interface ViewAgentSheetProps {
  agent: AgentResponse;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trigger?: React.ReactNode;
}

export function ViewAgentSheet({ agent, open, onOpenChange, trigger }: ViewAgentSheetProps) {
  const [copiedField, setCopiedField] = React.useState<string | null>(null);

  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      {trigger}
      <SheetContent className="w-[600px] sm:w-[700px] sm:max-w-none overflow-y-auto p-0">
        <div className="p-6 pb-0">
          <SheetHeader className="pb-6">
            <SheetTitle className="text-xl font-semibold flex items-center gap-2">
              <UserCog className="h-5 w-5" />
              {agent.name || "Unnamed Agent"}
            </SheetTitle>
            <SheetDescription>
              Agent details and capability information
            </SheetDescription>
          </SheetHeader>
        </div>

        <div className="px-6 pb-6 space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Basic Information</h3>
            
            <div className="space-y-4 p-4 bg-muted/30 rounded-lg">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Name</label>
                <p className="text-sm font-medium">{agent.name || "Unnamed Agent"}</p>
              </div>
              
              {agent.description && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-muted-foreground">Description</label>
                  <p className="text-sm">{agent.description}</p>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Client ID</label>
                <div className="flex items-center space-x-2">
                  <code className="text-xs bg-muted px-3 py-2 rounded font-mono flex-1 border">
                    {agent.client_id}
                  </code>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(agent.client_id, "client_id")}
                  >
                    {copiedField === "client_id" ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Created</label>
                <p className="text-sm flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  {new Date(agent.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {/* Tools */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Wrench className="h-5 w-5 text-blue-600" />
              Tools ({agent.tools.length})
            </h3>
            
            {agent.tools.length > 0 ? (
              <div className="space-y-3">
                {agent.tools.map((tool) => (
                  <div key={tool.id} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                    <div className="space-y-1 flex-1 min-w-0">
                      <p className="font-medium text-sm">{tool.name}</p>
                      <p className="text-xs text-muted-foreground font-mono truncate">{tool.id}</p>
                    </div>
                    {tool.mcp_name && (
                      <Badge variant="outline" className="text-xs ml-3 flex-shrink-0">
                        {tool.mcp_name}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-muted/30 rounded-lg border">
                <p className="text-sm text-muted-foreground">No tools assigned</p>
              </div>
            )}
          </div>

          {/* Resources */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5 text-green-600" />
              Resources ({agent.resources.length})
            </h3>
            
            {agent.resources.length > 0 ? (
              <div className="space-y-3">
                {agent.resources.map((resource) => (
                  <div key={resource.id} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                    <div className="space-y-1 flex-1 min-w-0">
                      <p className="font-medium text-sm">{resource.name}</p>
                      <p className="text-xs text-muted-foreground font-mono truncate">{resource.id}</p>
                    </div>
                    {resource.mcp_name && (
                      <Badge variant="outline" className="text-xs ml-3 flex-shrink-0">
                        {resource.mcp_name}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-muted/30 rounded-lg border">
                <p className="text-sm text-muted-foreground">No resources assigned</p>
              </div>
            )}
          </div>

          {/* Prompts */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-purple-600" />
              Prompts ({agent.prompts.length})
            </h3>
            
            {agent.prompts.length > 0 ? (
              <div className="space-y-3">
                {agent.prompts.map((prompt) => (
                  <div key={prompt.id} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                    <div className="space-y-1 flex-1 min-w-0">
                      <p className="font-medium text-sm">{prompt.name}</p>
                      <p className="text-xs text-muted-foreground font-mono truncate">{prompt.id}</p>
                    </div>
                    {prompt.mcp_name && (
                      <Badge variant="outline" className="text-xs ml-3 flex-shrink-0">
                        {prompt.mcp_name}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-muted/30 rounded-lg border">
                <p className="text-sm text-muted-foreground">No prompts assigned</p>
              </div>
            )}
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
} 
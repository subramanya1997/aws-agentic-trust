"use client";

import React, { useEffect, useState } from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Loader2, 
  Wrench, 
  AlertCircle, 
  Eye, 
  FileText, 
  Zap,
  Play,
  Code,
  Link,
  Type,
  Hash,
  CheckSquare,
  Square
} from "lucide-react";

import type { MCPResponse, MCPDetailedResponse, MCPBase } from "@/lib/types";
import { api, ApiError } from "@/lib/api";

interface ViewMCPSheetProps {
  mcp: MCPResponse;
  trigger?: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

// Helper component for rendering JSON schema properties
function SchemaProperty({ name, property, required }: { 
  name: string; 
  property: any; 
  required: boolean;
}) {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'string': return <Type className="h-3 w-3" />;
      case 'integer': 
      case 'number': return <Hash className="h-3 w-3" />;
      default: return <Code className="h-3 w-3" />;
    }
  };

  return (
    <div className="flex items-start space-x-3 p-3 border border-muted rounded-lg bg-muted/30">
      <div className="flex items-center space-x-2 min-w-0 flex-1">
        {getTypeIcon(property.type)}
        <code className="text-sm font-mono font-medium text-foreground">{name}</code>
        <Badge variant={required ? "default" : "secondary"} className="text-xs">
          {property.type}
        </Badge>
        {required && (
          <Badge variant="destructive" className="text-xs">
            required
          </Badge>
        )}
      </div>
      {property.title && property.title !== name && (
        <span className="text-xs text-muted-foreground">{property.title}</span>
      )}
      {/* Enum values */}
      {property.enum && Array.isArray(property.enum) && property.enum.length > 0 && (
        <div className="flex flex-wrap gap-1 ml-4">
          {property.enum.map((val: string, idx: number) => (
            <Badge
              key={idx}
              variant="secondary"
              className="text-xs bg-yellow-100 text-yellow-800 border-yellow-200"
            >
              {val}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// Tools section component
function ToolsSection({ tools }: { tools: any[] }) {
  return (
    <div className="space-y-4">
      {tools.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No tools available.</p>
      ) : (
        <div className="space-y-4">
          {tools.map((tool, idx) => (
            <Card key={idx} className="border border-muted">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg font-mono">{tool.name}</CardTitle>
                    {tool.description && (
                      <p className="text-sm text-muted-foreground">{tool.description}</p>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/**
                 * Backend returns `input_schema` (snake_case) while frontend
                 * expects `inputSchema` (camelCase). Support both for
                 * compatibility.
                 */}
                {(tool.inputSchema ?? tool.input_schema)?.properties && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium flex items-center space-x-2">
                      <Code className="h-4 w-4" />
                      <span>Arguments</span>
                    </h4>
                    <div className="space-y-2">
                      {Object.entries((tool.inputSchema ?? tool.input_schema).properties).map(([propName, propSchema]: [string, any]) => (
                        <SchemaProperty
                          key={propName}
                          name={propName}
                          property={propSchema}
                          required={(tool.inputSchema ?? tool.input_schema).required?.includes(propName) || false}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// Resources section component
function ResourcesSection({ resources }: { resources: any[] }) {
  return (
    <div className="space-y-4">
      {resources.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No resources available.</p>
      ) : (
        <div className="space-y-4">
          {resources.map((resource, idx) => (
            <Card key={idx} className="border border-muted">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-2 flex-1">
                    <CardTitle className="text-lg font-mono">{resource.name}</CardTitle>
                    {resource.description && (
                      <p className="text-sm text-muted-foreground">{resource.description}</p>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <Link className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs font-medium text-muted-foreground">URI</span>
                    </div>
                    <code className="block px-3 py-2 bg-muted rounded text-xs font-mono break-all">
                      {resource.uri}
                    </code>
                  </div>
                  {/** Accept both `mimeType` (camelCase) and `mime_type` (snake_case) */}
                  {(resource.mimeType ?? resource.mime_type) && (
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <FileText className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs font-medium text-muted-foreground">MIME Type</span>
                      </div>
                      <Badge variant="secondary" className="text-xs font-mono">
                        {resource.mimeType ?? resource.mime_type}
                      </Badge>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

// Prompts section component
function PromptsSection({ prompts }: { prompts: any[] }) {
  return (
    <div className="space-y-4">
      {prompts.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">No prompts available.</p>
      ) : (
        <div className="space-y-4">
          {prompts.map((prompt, idx) => (
            <Card key={idx} className="border border-muted">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg font-mono">{prompt.name}</CardTitle>
                    {prompt.description && (
                      <p className="text-sm text-muted-foreground">{prompt.description}</p>
                    )}
                  </div>
                  <Button variant="outline" size="sm" className="ml-4">
                    <Zap className="h-3 w-3 mr-1" />
                    Use
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {prompt.arguments && prompt.arguments.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium flex items-center space-x-2">
                      <Code className="h-4 w-4" />
                      <span>Arguments</span>
                    </h4>
                    <div className="space-y-2">
                      {prompt.arguments.map((arg: any, argIdx: number) => (
                        <div key={argIdx} className="flex items-center space-x-3 p-3 border border-muted rounded-lg bg-muted/30">
                          <div className="flex items-center space-x-2 min-w-0 flex-1">
                            {arg.required ? (
                              <CheckSquare className="h-3 w-3 text-destructive" />
                            ) : (
                              <Square className="h-3 w-3 text-muted-foreground" />
                            )}
                            <code className="text-sm font-mono font-medium text-foreground">{arg.name}</code>
                            <Badge variant={arg.required ? "destructive" : "secondary"} className="text-xs">
                              {arg.required ? "required" : "optional"}
                            </Badge>
                          </div>
                          {arg.description && (
                            <span className="text-xs text-muted-foreground">{arg.description}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export function ViewMCPSheet({ mcp, trigger, open: externalOpen, onOpenChange }: ViewMCPSheetProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen !== undefined ? externalOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<MCPDetailedResponse | null>(null);

  // Helper to build MCPBase config from full MCP object
  const toMCPBase = (m: MCPResponse): MCPBase => {
    const base: MCPBase = {
      name: m.name,
      server_type: m.server_type,
      environment: m.environment,
    } as MCPBase;

    if (m.server_type === "sse") {
      base.url = m.url;
    } else {
      base.command = m.command;
      base.args = m.args;
    }
    if (m.env) base.env = m.env;
    return base;
  };

  // Fetch capabilities when sheet opens
  useEffect(() => {
    if (!open) return;

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.mcp.view(mcp.id);
        setData(result);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to fetch MCP capabilities");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const defaultTrigger = (
    <Button variant="ghost" size="sm" className="h-8 w-8 p-0" title="View MCP">
      <Eye className="h-3 w-3" />
    </Button>
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>{trigger || defaultTrigger}</SheetTrigger>
      <SheetContent className="w-[800px] sm:w-[900px] sm:max-w-none overflow-y-auto p-0">
        <div className="p-6 space-y-6">
          <SheetHeader className="space-y-3">
            <SheetTitle className="text-xl font-semibold">{mcp.name || mcp.id}</SheetTitle>
            <SheetDescription>Explore MCP capabilities and documentation</SheetDescription>
            
            {/* Quick stats */}
            {data && (
              <div className="flex items-center space-x-4 pt-2">
                <div className="flex items-center space-x-2 text-sm">
                  <Wrench className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">{data.tools.length}</span>
                  <span className="text-muted-foreground">tools</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <FileText className="h-4 w-4 text-green-600" />
                  <span className="font-medium">{data.resources.length}</span>
                  <span className="text-muted-foreground">resources</span>
                </div>
                <div className="flex items-center space-x-2 text-sm">
                  <Zap className="h-4 w-4 text-purple-600" />
                  <span className="font-medium">{data.prompts.length}</span>
                  <span className="text-muted-foreground">prompts</span>
                </div>
              </div>
            )}
          </SheetHeader>

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-20 text-muted-foreground">
              <Loader2 className="h-6 w-6 animate-spin mr-2" /> 
              <span>Fetching capabilities...</span>
            </div>
          )}

          {/* Error */}
          {error && (
            <Card className="border-red-200 bg-red-50/50">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2 text-red-700 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Main Content */}
          {data && (
            <Tabs defaultValue="tools" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="tools" className="flex items-center space-x-2">
                  <Wrench className="h-4 w-4" />
                  <span>Tools ({data.tools.length})</span>
                </TabsTrigger>
                <TabsTrigger value="resources" className="flex items-center space-x-2">
                  <FileText className="h-4 w-4" />
                  <span>Resources ({data.resources.length})</span>
                </TabsTrigger>
                <TabsTrigger value="prompts" className="flex items-center space-x-2">
                  <Zap className="h-4 w-4" />
                  <span>Prompts ({data.prompts.length})</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="tools">
                <ScrollArea className="h-[70vh] pr-4">
                  <ToolsSection tools={data.tools} />
                </ScrollArea>
              </TabsContent>

              <TabsContent value="resources">
                <ScrollArea className="h-[70vh] pr-4">
                  <ResourcesSection resources={data.resources} />
                </ScrollArea>
              </TabsContent>

              <TabsContent value="prompts">
                <ScrollArea className="h-[70vh] pr-4">
                  <PromptsSection prompts={data.prompts} />
                </ScrollArea>
              </TabsContent>
            </Tabs>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
} 
"use client";

import * as React from "react";
import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Loader2, AlertCircle, Globe, Terminal, Edit, CheckCircle, Wrench, FileText, Zap } from "lucide-react";

import { api, ApiError } from "@/lib/api";
import type { MCPResponse, ServerType, MCPTestResult } from "@/lib/types";
import { handleError } from "@/lib/utils";

// Types
interface RegisterMCPSheetProps {
  onSuccess?: () => void;
  trigger?: React.ReactNode;
  editMcp?: MCPResponse;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface FormData {
  name: string;
  server_type: ServerType;
  command_type: "npx";
  args: string;
  url: string;
  env: string;
  environment: string;
}

type ErrorType = string | { message: string; conflicts?: string[] };

// Constants
const INITIAL_FORM_DATA: FormData = {
  name: "",
  server_type: "command",
  command_type: "npx",
  args: "[\"@smithery/cli@latest\", \"run\", \"<package>\"]",
  url: "",
  env: "",
  environment: "",
};

const SERVER_TYPE_CONFIG = {
  command: {
    icon: Terminal,
    title: "Command Server",
    description: "Execute a command-line MCP server (npx or python)",
  },
  sse: {
    icon: Globe,
    title: "SSE Server", 
    description: "Connect to a Server-Sent Events MCP endpoint",
  },
} as const;

// Helper functions
function parseArgs(argsString: string): string[] {
  if (!argsString.trim()) return [];
  
  try {
    const parsed = JSON.parse(argsString);
    if (Array.isArray(parsed)) return parsed;
  } catch {
    // Fall back to space-separated parsing
    return argsString.trim().split(/\s+/);
  }
  
  return [];
}

function parseEnv(envString: string): Record<string, string> {
  if (!envString.trim()) return {};
  
  try {
    return JSON.parse(envString);
  } catch {
    // Fall back to KEY=VALUE parsing
    const env: Record<string, string> = {};
    envString.split('\n').forEach(line => {
      const [key, ...valueParts] = line.trim().split('=');
      if (key && valueParts.length > 0) {
        env[key] = valueParts.join('=');
      }
    });
    return env;
  }
}

function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

// Form components
function ErrorAlert({ error }: { error: ErrorType }) {
  const isDetailedError = typeof error === 'object' && error.message;
  
  return (
    <Card className="border-red-200 bg-red-50/50">
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <span className="text-sm text-red-700 font-medium">
              {isDetailedError ? error.message : String(error)}
            </span>
            {isDetailedError && error.conflicts && error.conflicts.length > 0 && (
              <ul className="mt-2 space-y-1">
                {error.conflicts.map((conflict, index) => (
                  <li key={index} className="text-xs text-red-600 flex items-start space-x-2">
                    <span className="w-1 h-1 bg-red-600 rounded-full mt-2 flex-shrink-0" />
                    <span>{conflict}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ServerTypeSelector({ 
  value, 
  onChange, 
  disabled 
}: { 
  value: ServerType; 
  onChange: (value: ServerType) => void; 
  disabled: boolean;
}) {
  const configEntry = SERVER_TYPE_CONFIG[value as keyof typeof SERVER_TYPE_CONFIG];
  const Icon = configEntry.icon;
  
  return (
    <div className="space-y-2">
      <Label className="text-sm font-medium">Server Type *</Label>
      <div className="space-y-3">
        <Select value={value} onValueChange={onChange} disabled={disabled}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.entries(SERVER_TYPE_CONFIG).map(([type, config]) => {
              const TypeIcon = config.icon;
              return (
                <SelectItem key={type} value={type}>
                  <div className="flex items-center space-x-2">
                    <TypeIcon className="h-4 w-4" />
                    <span>{config.title}</span>
                  </div>
                </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
        <div className="text-xs text-muted-foreground flex items-center space-x-2 px-1">
          <Icon className="h-3.5 w-3.5 flex-shrink-0" />
          <span>{configEntry.description}</span>
        </div>
      </div>
    </div>
  );
}

function CommandTypeSelector({
  value,
  onChange,
  disabled
}: {
  value: "npx";
  onChange: (value: "npx") => void;
  disabled: boolean;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor="command_type" className="text-sm font-medium">Command Runtime *</Label>
      <div className="space-y-3">
        <Select value={value} onValueChange={onChange} disabled>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="npx">
              <div className="flex items-center space-x-2">
                <Terminal className="h-4 w-4" />
                <span>NPX Package</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>
        <div className="text-xs text-muted-foreground flex items-center space-x-2 px-1">
          <Terminal className="h-3.5 w-3.5 flex-shrink-0" />
          <span>Currently only NPX + @smithery/cli servers are supported</span>
        </div>
      </div>
    </div>
  );
}

function TestResultsDisplay({ result }: { result: MCPTestResult }) {
  return (
    <Card className="border-green-200 bg-green-50/30">
      <CardContent className="p-4">
        <div className="flex items-center space-x-3 mb-4">
          <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
          <span className="text-sm font-medium text-green-700">
            Connection successful! MCP server is ready to use.
          </span>
        </div>
        
        <div className="grid grid-cols-3 gap-4 text-center">
          {/* Tools */}
          <div className="space-y-1">
            <div className="flex items-center justify-center space-x-1">
              <Wrench className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-gray-700">Tools</span>
            </div>
            <div className="text-lg font-semibold text-blue-600">
              {result.tools.length}
            </div>
            {result.tools.length > 0 && (
              <div className="text-xs text-gray-500">
                {result.tools.slice(0, 2).map(tool => tool.name).join(", ")}
                {result.tools.length > 2 && `, +${result.tools.length - 2} more`}
              </div>
            )}
          </div>

          {/* Resources */}
          <div className="space-y-1">
            <div className="flex items-center justify-center space-x-1">
              <FileText className="h-4 w-4 text-green-600" />
              <span className="text-sm font-medium text-gray-700">Resources</span>
            </div>
            <div className="text-lg font-semibold text-green-600">
              {result.resources.length}
            </div>
            {result.resources.length > 0 && (
              <div className="text-xs text-gray-500">
                {result.resources.slice(0, 2).map(resource => resource.name).join(", ")}
                {result.resources.length > 2 && `, +${result.resources.length - 2} more`}
              </div>
            )}
          </div>

          {/* Prompts */}
          <div className="space-y-1">
            <div className="flex items-center justify-center space-x-1">
              <Zap className="h-4 w-4 text-purple-600" />
              <span className="text-sm font-medium text-gray-700">Prompts</span>
            </div>
            <div className="text-lg font-semibold text-purple-600">
              {result.prompts.length}
            </div>
            {result.prompts.length > 0 && (
              <div className="text-xs text-gray-500">
                {result.prompts.slice(0, 2).map(prompt => prompt.name).join(", ")}
                {result.prompts.length > 2 && `, +${result.prompts.length - 2} more`}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Main component
export function RegisterMCPSheet({ 
  onSuccess, 
  trigger, 
  editMcp, 
  open: externalOpen, 
  onOpenChange 
}: RegisterMCPSheetProps) {
  const isEditMode = !!editMcp;
  const [internalOpen, setInternalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ErrorType | null>(null);
  
  // Test connection state
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<MCPTestResult | null>(null);
  const [testError, setTestError] = useState<string | null>(null);
  const [hasTestedSuccessfully, setHasTestedSuccessfully] = useState(false);
  
  // Use external open state if provided, otherwise use internal state
  const open = externalOpen !== undefined ? externalOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;
  
  // Initialize form data
  const getInitialFormData = useCallback((): FormData => {
    if (!editMcp) return INITIAL_FORM_DATA;
    
    let commandType: "npx" = "npx";
    let args = "[\"@smithery/cli@latest\", \"run\", \"<package>\"]";
    
    if (editMcp.server_type === "command") {
      if (editMcp.args && editMcp.args.length > 0) {
        const argsList = [...editMcp.args];
        if (argsList[0] === "-y") argsList.shift();
        args = JSON.stringify(argsList);
      }
    }
    
    return {
      name: editMcp.name || "",
      server_type: editMcp.server_type === "stdio" ? "command" : editMcp.server_type as ServerType,
      command_type: commandType,
      args: args,
      url: editMcp.url || "",
      env: editMcp.env ? JSON.stringify(editMcp.env, null, 2) : "",
      environment: editMcp.environment || "",
    };
  }, [editMcp]);
  
  const [formData, setFormData] = useState<FormData>(getInitialFormData);

  // Reset form when dialog opens
  React.useEffect(() => {
    if (open) {
      setFormData(getInitialFormData());
      setError(null);
      setTestResult(null);
      setTestError(null);
      setHasTestedSuccessfully(false);
    }
  }, [open, editMcp, getInitialFormData]);

  // Form handlers
  const handleInputChange = useCallback((field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setError(null);
    // Reset test state when form changes
    setTestResult(null);
    setTestError(null);
    setHasTestedSuccessfully(false);
  }, []);

  const validateForm = useCallback((): string | null => {
    if (!formData.name.trim()) {
      return "Name is required";
    }

    if (formData.server_type === "sse") {
      if (!formData.url.trim()) {
        return "URL is required for SSE servers";
      }
      if (!validateUrl(formData.url)) {
        return "Please enter a valid URL";
      }
    } else {
      if (!formData.args.trim()) {
        return "Arguments must start with @smithery/cli@latest run <package>";
      }

      const userArgs = parseArgs(formData.args);
      if (userArgs.length < 3) {
        return "Arguments must include @smithery/cli@latest run <package>";
      }
      if (!userArgs[0].includes("@smithery/cli")) {
        return "First argument must be @smithery/cli@latest";
      }
      if (userArgs[1] !== "run") {
        return "Second argument must be 'run'";
      }
    }

    if (formData.env.trim()) {
      try {
        parseEnv(formData.env);
      } catch {
        return "Environment must be valid JSON object or KEY=VALUE format";
      }
    }

    return null;
  }, [formData]);

  const handleTestConnection = async () => {
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setTestLoading(true);
    setTestError(null);
    setTestResult(null);

    try {
      const mcpData: any = {
        name: formData.name.trim(),
        server_type: formData.server_type,
        environment: formData.environment.trim() || undefined,
      };

      // Configure based on server type
      if (formData.server_type === "sse") {
        mcpData.url = formData.url.trim();
      } else {
        mcpData.command = "npx";
        
        const userArgs = parseArgs(formData.args);
        if (userArgs.length === 0) {
          throw new Error("Please provide at least the target in arguments");
        }

        mcpData.args = ["-y", ...userArgs];
      }

      // Add environment variables
      if (formData.env.trim()) {
        mcpData.env = parseEnv(formData.env);
      }

      const result = await api.mcp.test(mcpData);
      setTestResult(result);
      setHasTestedSuccessfully(true);
      setError(null);
      
    } catch (err) {
      let errorMessage: string;
      
      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else {
        errorMessage = "Failed to test MCP connection";
      }
      
      setTestError(errorMessage);
      setHasTestedSuccessfully(false);
    } finally {
      setTestLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const mcpData: any = {
        name: formData.name.trim(),
        server_type: formData.server_type,
        environment: formData.environment.trim() || undefined,
      };

      // Configure based on server type
      if (formData.server_type === "sse") {
        mcpData.url = formData.url.trim();
      } else {
        mcpData.command = "npx";
        
        const userArgs = parseArgs(formData.args);
        if (userArgs.length === 0) {
          throw new Error("Please provide at least the target in arguments");
        }

        mcpData.args = ["-y", ...userArgs];
      }

      // Add environment variables
      if (formData.env.trim()) {
        mcpData.env = parseEnv(formData.env);
      }

      // Create or update
      if (isEditMode && editMcp) {
        await api.mcp.update(editMcp.id, mcpData);
        await api.mcp.update(editMcp.id, { status: "active" });
      } else {
        // Create the MCP
        const createdMcp = await api.mcp.create(mcpData);
        
        // Immediately activate the newly created MCP
        await api.mcp.update(createdMcp.id, { status: "active" });
      }
      
      if (!isEditMode) {
        setFormData(INITIAL_FORM_DATA);
      }
      setOpen(false);
      onSuccess?.();
      
    } catch (err) {
      console.log('Error caught:', err);
      console.log('Error instanceof ApiError:', err instanceof ApiError);
      if (err instanceof ApiError) {
        console.log('Error status:', err.status);
        console.log('Error detail:', err.detail);
      }
      
      let errorToDisplay: ErrorType;
      
      if (err instanceof ApiError && err.status === 409 && err.detail) {
        // Use the parsed detail from ApiError
        if (typeof err.detail === 'object' && err.detail.conflicts) {
          errorToDisplay = {
            message: err.detail.message || "Conflict detected",
            conflicts: err.detail.conflicts || []
          };
        } else {
          errorToDisplay = err.message;
        }
      } else if (err instanceof ApiError) {
        errorToDisplay = err.message;
      } else {
        errorToDisplay = `Failed to ${isEditMode ? 'update' : 'register'} MCP`;
      }
      
      setError(errorToDisplay);
      // handleError(err, typeof errorToDisplay === 'string' ? errorToDisplay : errorToDisplay.message);
    } finally {
      setLoading(false);
    }
  };

  const defaultTrigger = (
    <Button size="sm">
      <Plus className="mr-2 h-4 w-4" />
      Register MCP
    </Button>
  );

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      {!isEditMode && (
        <SheetTrigger asChild>
          {trigger || defaultTrigger}
        </SheetTrigger>
      )}
      <SheetContent className="w-[600px] sm:w-[700px] sm:max-w-none overflow-y-auto p-0">
        <div className="p-6 pb-0">
          <SheetHeader className="pb-6">
            <SheetTitle className="text-xl font-semibold">{isEditMode ? 'Edit MCP Server' : 'Register New MCP Server'}</SheetTitle>
            <SheetDescription className="text-sm text-muted-foreground">
              {isEditMode 
                ? 'Update the Model Context Protocol server configuration' 
                : 'Add a new Model Context Protocol server to your system'}
            </SheetDescription>
          </SheetHeader>
        </div>

        <form onSubmit={handleSubmit} className="px-6 pb-6">
          <div className="space-y-6">
          {error !== null && <ErrorAlert error={error as ErrorType} />}

          {/* Basic Information */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium">Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleInputChange("name", e.target.value)}
                placeholder="My MCP Server"
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="environment" className="text-sm font-medium">Environment</Label>
              <Input
                id="environment"
                value={formData.environment}
                onChange={(e) => handleInputChange("environment", e.target.value)}
                placeholder="production, development, staging..."
                disabled={loading}
              />
            </div>

            {/* Server Type & Command Type Row */}
            {formData.server_type === "command" ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ServerTypeSelector
                  value={formData.server_type}
                  onChange={(value) => handleInputChange("server_type", value)}
                  disabled={loading}
                />
                <CommandTypeSelector
                  value={formData.command_type}
                  onChange={(value) => handleInputChange("command_type", value)}
                  disabled={loading}
                />
              </div>
            ) : (
              <div className="space-y-2">
                <ServerTypeSelector
                  value={formData.server_type}
                  onChange={(value) => handleInputChange("server_type", value)}
                  disabled={loading}
                />
              </div>
            )}
          </div>

          {/* Configuration Section */}
          <div className="space-y-4">
            {formData.server_type === "command" ? (
              <div className="space-y-2">
                <Label htmlFor="args" className="text-sm font-medium">Arguments *</Label>
                <Input
                  id="args"
                  value={formData.args}
                  onChange={(e) => handleInputChange("args", e.target.value)}
                  placeholder='["@smithery/cli@latest", "run", "<package>"]'
                  disabled={loading}
                />
                <p className="text-xs text-muted-foreground">
                  First element is the target followed by optional args
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label htmlFor="url" className="text-sm font-medium">URL *</Label>
                <Input
                  id="url"
                  type="url"
                  value={formData.url}
                  onChange={(e) => handleInputChange("url", e.target.value)}
                  placeholder="https://my-mcp-server.com/sse"
                  disabled={loading}
                />
              </div>
            )}

            <div className="space-y-2 pt-2">
              <Label htmlFor="env" className="text-sm font-medium">Environment Variables</Label>
              <Textarea
                id="env"
                value={formData.env}
                onChange={(e) => handleInputChange("env", e.target.value)}
                placeholder='{"API_KEY": "your-key"} or API_KEY=your-key'
                rows={4}
                disabled={loading}
                className="font-mono text-sm resize-none"
              />
              <p className="text-xs text-muted-foreground">
                JSON object or KEY=VALUE format (one per line)
              </p>
            </div>
          </div>

          {/* Test Connection Section - available for all server types in both new and edit modes */}
          <div className="space-y-4">
            <div className="border-t pt-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Test Connection</h3>
                  <p className="text-xs text-muted-foreground">
                    {formData.server_type === "sse" ? (
                      "Verify connectivity and discover MCP server capabilities"
                    ) : (
                      "NPX command servers can be tested when args include @smithery/cli@latest"
                    )}
                  </p>
                </div>
                {(
                  formData.server_type === "sse" ||
                  (formData.server_type === "command" && formData.args.includes("@smithery/cli"))
                ) && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={testLoading || loading || !!validateForm()}
                    className="px-4"
                  >
                    {testLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Testing...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Test Connection
                      </>
                    )}
                  </Button>
                )}
              </div>

              {/* Test Error Display */}
              {testError && (
                <Card className="border-red-200 bg-red-50/50">
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <span className="text-sm text-red-700 font-medium">
                          Connection failed: {testError}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Test Results Display */}
              {testResult && <TestResultsDisplay result={testResult} />}
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3 pt-6 mt-6 border-t">
            <div className="flex justify-end space-x-3">
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => setOpen(false)}
              disabled={loading}
              className="px-6"
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
                disabled={
                  loading || 
                  (formData.server_type === "sse" && !hasTestedSuccessfully)
                }
              className="px-6"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {isEditMode ? 'Saving...' : 'Registering...'}
                </>
              ) : (
                <>
                  {isEditMode ? <Edit className="mr-2 h-4 w-4" /> : <Plus className="mr-2 h-4 w-4" />}
                  {isEditMode ? 'Save Changes' : 'Register MCP'}
                </>
              )}
            </Button>
            </div>
            
            {/* Helper text below buttons */}
            {formData.server_type === "sse" && !hasTestedSuccessfully && !testError && (
              <div className="flex justify-end">
                <p className="text-xs text-muted-foreground text-right max-w-md">
                  <AlertCircle className="inline h-3 w-3 mr-1" />
                  Test connection first to verify MCP server capabilities
                </p>
              </div>
            )}
          </div>
          </div>
        </form>
      </SheetContent>
    </Sheet>
  );
}
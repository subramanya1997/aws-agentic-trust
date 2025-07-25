"use client";

import React, { useState, useEffect } from "react";
import { Plus, Loader2, AlertCircle, UserCog, Wrench, FileText, Zap, Copy, Check, Edit } from "lucide-react";
import { Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { api, ApiError } from "@/lib/api";
import { handleError } from "@/lib/utils";
import { MultiSelect, MultiSelectOption } from "@/components/ui/multi-select";
import { CapabilityItem, AgentResponse } from "@/lib/types";

interface RegisterAgentSheetProps {
  trigger?: React.ReactNode;
  onSuccess?: () => void;
  editAgent?: AgentResponse;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

interface CredentialsDisplay {
  client_id: string;
  client_secret: string;
}

export function RegisterAgentSheet({ trigger, onSuccess, editAgent, open: externalOpen, onOpenChange }: RegisterAgentSheetProps) {
  const isEditMode = !!editAgent;

  // Manage controlled vs uncontrolled open state
  const [internalOpen, setInternalOpen] = useState(false);
  const open = externalOpen !== undefined ? externalOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [name, setName] = useState<string>(isEditMode ? (editAgent?.name || "") : "");
  const [description, setDescription] = useState<string>(isEditMode ? (editAgent?.description || "") : "");
  
  // Capabilities
  const [toolsOptions, setToolsOptions] = useState<MultiSelectOption[]>([]);
  const [resourcesOptions, setResourcesOptions] = useState<MultiSelectOption[]>([]);
  const [promptsOptions, setPromptsOptions] = useState<MultiSelectOption[]>([]);
  
  const [selectedTools, setSelectedTools] = useState<string[]>(isEditMode ? (editAgent?.allowed_tool_ids || []) : []);
  const [selectedResources, setSelectedResources] = useState<string[]>(isEditMode ? (editAgent?.allowed_resource_ids || []) : []);
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>(isEditMode ? (editAgent?.allowed_prompt_ids || []) : []);
  
  // Success state
  const [credentials, setCredentials] = useState<CredentialsDisplay | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Fetch capabilities when sheet opens
  useEffect(() => {
    if (open && !credentials) {
      (async () => {
        try {
          const [toolsRes, resRes, promRes] = await Promise.all([
            api.capabilities.listTools(),
            api.capabilities.listResources(),
            api.capabilities.listPrompts(),
          ]);
          const toOption = (it: CapabilityItem): MultiSelectOption => {
            let label = it.name || it.id;
            if (it.mcp_name) label = `${label} (${it.mcp_name})`;
            return { value: it.id, label };
          };
          setToolsOptions(toolsRes.items.map(toOption));
          setResourcesOptions(resRes.items.map(toOption));
          setPromptsOptions(promRes.items.map(toOption));
        } catch (err) {
          console.error("Failed to load capabilities", err);
        }
      })();
    }
  }, [open, credentials]);

  const resetForm = () => {
    setName(isEditMode ? (editAgent?.name || "") : "");
    setDescription(isEditMode ? (editAgent?.description || "") : "");
    setSelectedTools(isEditMode ? (editAgent?.allowed_tool_ids || []) : []);
    setSelectedResources(isEditMode ? (editAgent?.allowed_resource_ids || []) : []);
    setSelectedPrompts(isEditMode ? (editAgent?.allowed_prompt_ids || []) : []);
    setError(null);
    setCredentials(null);
    setCopiedField(null);
  };

  const handleClose = () => {
    setOpen(false);
    // Reset after animation
    setTimeout(resetForm, 300);
  };

  const submitAgent = async () => {
    if (!name.trim()) {
      setError("Name is required");
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const payload = {
        name: name.trim(),
        description: description.trim() || undefined,
        tool_ids: selectedTools,
        resource_ids: selectedResources,
        prompt_ids: selectedPrompts,
      };
      
      if (isEditMode && editAgent) {
        await api.agents.update(editAgent.id, payload);
        // Close sheet and signal success
        setOpen(false);
        onSuccess?.();
      } else {
        const res = await api.agents.create(payload);
        setCredentials(res.credentials);
        onSuccess?.();
      }
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : (isEditMode ? "Failed to update agent" : "Failed to create agent");
      setError(msg);
      handleError(err, msg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const totalSelected = selectedTools.length + selectedResources.length + selectedPrompts.length;

  const defaultTrigger = (
    <Button size="sm">
      {isEditMode ? (
        <Edit className="mr-2 h-4 w-4" />
      ) : (
        <Plus className="mr-2 h-4 w-4" />
      )}
      {isEditMode ? "Edit Agent" : "Register Agent"}
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
            <SheetTitle className="text-xl font-semibold">
              {credentials ? "Agent Created Successfully" : isEditMode ? "Edit Agent" : "Register New Agent"}
            </SheetTitle>
            <SheetDescription className="text-sm text-muted-foreground">
              {credentials
                ? "Save these credentials securely. The secret will not be shown again."
                : isEditMode
                ? "Update the agent details and capability permissions"
                : "Create a new agent identity with specific capability permissions"}
            </SheetDescription>
          </SheetHeader>
        </div>

        <div className="px-6 pb-6">
          {!credentials ? (
            <div className="space-y-6">
              {/* Error Display */}
              {error && (
                <Card className="border-red-200 bg-red-50/50">
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-red-700 font-medium">{error}</span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Basic Information Section */}
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="agent-name" className="text-sm font-medium">Name *</Label>
                  <Input
                    id="agent-name"
                    placeholder="My Agent"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="agent-description" className="text-sm font-medium">Description</Label>
                  <Textarea
                    id="agent-description"
                    placeholder="Describe what this agent will do..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={loading}
                    rows={3}
                    className="resize-none"
                  />
                </div>
              </div>

              {/* Capabilities Section */}
              <div className="space-y-4">
                <div className="border-t pt-6">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">Capabilities</h3>
                  
                  {/* Tools */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Wrench className="h-4 w-4 text-blue-600" />
                        <Label className="text-sm font-medium">Tools</Label>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {selectedTools.length} selected
                      </span>
                    </div>
                    <MultiSelect 
                      options={toolsOptions} 
                      selected={selectedTools} 
                      onChange={setSelectedTools}
                      heightClass="h-32"
                    />
                  </div>

                  {/* Resources */}
                  <div className="space-y-3 mt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <FileText className="h-4 w-4 text-green-600" />
                        <Label className="text-sm font-medium">Resources</Label>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {selectedResources.length} selected
                      </span>
                    </div>
                    <MultiSelect 
                      options={resourcesOptions} 
                      selected={selectedResources} 
                      onChange={setSelectedResources}
                      heightClass="h-32"
                    />
                  </div>

                  {/* Prompts */}
                  <div className="space-y-3 mt-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Zap className="h-4 w-4 text-purple-600" />
                        <Label className="text-sm font-medium">Prompts</Label>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {selectedPrompts.length} selected
                      </span>
                    </div>
                    <MultiSelect 
                      options={promptsOptions} 
                      selected={selectedPrompts} 
                      onChange={setSelectedPrompts}
                      heightClass="h-32"
                    />
                  </div>

                  {/* Summary */}
                  {totalSelected > 0 && (
                    <div className="mt-4 text-xs text-muted-foreground">
                      Total capabilities selected: {totalSelected}
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="space-y-3 pt-6 mt-6 border-t">
                <div className="flex justify-end space-x-3">
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={handleClose}
                    disabled={loading}
                    className="px-6"
                  >
                    Cancel
                  </Button>
                  <Button 
                    onClick={submitAgent} 
                    disabled={loading || !name.trim()}
                    className="px-6"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {isEditMode ? "Saving..." : "Creating..."}
                      </>
                    ) : (
                      <>
                        {isEditMode ? (
                          <Edit className="mr-2 h-4 w-4" />
                        ) : (
                          <UserCog className="mr-2 h-4 w-4" />
                        )}
                        {isEditMode ? "Save Changes" : "Create Agent"}
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          ) : (
            /* Success State - Show Credentials */
            <div className="space-y-6">
              <Card className="border-green-200 bg-green-50/30">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <Check className="h-5 w-5 text-green-600 flex-shrink-0" />
                    <span className="text-sm font-medium text-green-700">
                      Agent created successfully!
                    </span>
                  </div>
                </CardContent>
              </Card>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Client ID</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      value={credentials.client_id}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(credentials.client_id, "client_id")}
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
                  <Label className="text-sm font-medium">Client Secret</Label>
                  <div className="flex items-center space-x-2">
                    <Input
                      value={credentials.client_secret}
                      readOnly
                      className="font-mono text-sm"
                      type="password"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(credentials.client_secret, "client_secret")}
                    >
                      {copiedField === "client_secret" ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>

              <Card className="border-amber-200 bg-amber-50/30">
                <CardContent className="p-4">
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                    <div className="text-sm text-amber-700">
                      <p className="font-medium">Important:</p>
                      <p>Save these credentials securely. The secret will not be shown again.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="pt-6 border-t">
                <Button 
                  onClick={handleClose}
                  className="w-full"
                >
                  Done
                </Button>
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
} 
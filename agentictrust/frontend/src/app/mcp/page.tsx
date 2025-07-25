"use client";

import React, { useEffect, useState, useCallback } from "react";
import { TopHeader } from "@/components/top-header";
import { 
  RegisterMCPSheet, 
  MCPStatsOverview,
  MCPList,
  MCPErrorAlert
} from "@/components/mcp";
import { pageConfig } from "@/lib/config";
import { api, ApiError } from "@/lib/api";
import type { 
  MCPResponse, 
  MCPStatusSummary,
  MCPHealthReport
} from "@/lib/types";
import { 
  PAGINATION,
} from "@/lib/constants";
import { handleError } from "@/lib/utils";
import { MCPHealthIssuesSheet } from "@/components/mcp";

interface MCPPageState {
  mcps: MCPResponse[];
  summary: MCPStatusSummary | null;
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  editingMcp: MCPResponse | null;
  healthReport: MCPHealthReport | null;
  showHealth: boolean;
}

export default function MCPRegistryPage() {
  const [state, setState] = useState<MCPPageState>({
    mcps: [],
    summary: null,
    loading: true,
    error: null,
    total: 0,
    currentPage: 1,
    editingMcp: null,
    healthReport: null,
    showHealth: false,
  });

  const fetchMCPData = useCallback(async (page: number = 1) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const [mcpListResult, summaryResult, healthResult] = await Promise.allSettled([
        api.mcp.list({ 
          skip: (page - 1) * PAGINATION.DEFAULT_PAGE_SIZE,
          limit: PAGINATION.DEFAULT_PAGE_SIZE 
        }),
        api.mcp.getStatusSummary(),
        api.mcp.getHealthReport(),
      ]);

      const mcpList = mcpListResult.status === 'fulfilled' ? mcpListResult.value : null;
      const summary = summaryResult.status === 'fulfilled' ? summaryResult.value : null;
      const healthReport = healthResult.status === 'fulfilled' ? healthResult.value : null;

      setState(prev => ({
        ...prev,
        mcps: mcpList?.items || [],
        summary: summary,
        total: mcpList?.total || 0,
        currentPage: page,
        loading: false,
        healthReport,
      }));

    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch MCP data";
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      handleError(err, errorMessage);
    }
  }, []);

  const editMCP = useCallback((mcp: MCPResponse) => {
    setState(prev => ({ ...prev, editingMcp: mcp }));
  }, []);

  const deleteMCP = useCallback(async (id: string) => {
    try {
      await api.mcp.delete(id);
      await fetchMCPData(state.currentPage);
    } catch (err) {
      handleError(err, "Failed to delete MCP");
    }
  }, [fetchMCPData, state.currentPage]);

  const handleEditSuccess = useCallback(() => {
    setState(prev => ({ ...prev, editingMcp: null }));
    fetchMCPData(state.currentPage);
  }, [fetchMCPData, state.currentPage]);

  const openHealthSheet = useCallback(() => {
    setState(prev => ({ ...prev, showHealth: true }));
  }, []);

  useEffect(() => {
    fetchMCPData();
  }, [fetchMCPData]);

  const { mcps, summary, loading, error, total, currentPage } = state;

  return (
    <div className="hidden flex-col md:flex">
      <TopHeader 
        page={pageConfig.mcp}
        onRefresh={() => fetchMCPData(currentPage)}
        isLoading={loading}
        actions={
          <RegisterMCPSheet onSuccess={() => fetchMCPData(currentPage)} />
        }
      />

      <div className="flex-1 space-y-6 p-8 pt-6">
        <MCPErrorAlert error={error} />

        <MCPStatsOverview summary={summary} report={state.healthReport} onHealthClick={openHealthSheet} />

        <MCPList
          mcps={mcps}
          total={total}
          loading={loading}
          onEdit={editMCP}
          onDelete={deleteMCP}
          onRefresh={() => fetchMCPData(currentPage)}
        />
      </div>

      {/* Sheet for Editing MCP */}
      {state.editingMcp && (
        <RegisterMCPSheet
          editMcp={state.editingMcp}
          open={!!state.editingMcp}
          onOpenChange={(isOpen: boolean) => {
            if (!isOpen) {
              setState(prev => ({ ...prev, editingMcp: null }));
            }
          }}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Health issues sheet */}
      <MCPHealthIssuesSheet
        open={state.showHealth}
        onOpenChange={(o: boolean) => setState(prev => ({ ...prev, showHealth: o }))}
        report={state.healthReport}
      />
    </div>
  );
} 
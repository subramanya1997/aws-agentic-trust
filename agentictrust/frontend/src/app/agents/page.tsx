"use client";

import React, { useEffect, useState, useCallback } from "react";
import { TopHeader } from "@/components/top-header";
import { 
  RegisterAgentSheet, 
  AgentList,
  AgentStatsOverview,
  AgentErrorAlert
} from "@/components/agent";
import { pageConfig } from "@/lib/config";
import { api, ApiError } from "@/lib/api";
import type { 
  AgentResponse, 
  AgentStatusSummary 
} from "@/lib/types";
import { PAGINATION } from "@/lib/constants";
import { handleError } from "@/lib/utils";

interface AgentsPageState {
  agents: AgentResponse[];
  summary: AgentStatusSummary | null;
  loading: boolean;
  error: string | null;
  total: number;
  currentPage: number;
  editingAgent: AgentResponse | null;
}

export default function AgentRegistryPage() {
  const [state, setState] = useState<AgentsPageState>({
    agents: [],
    summary: null,
    loading: true,
    error: null,
    total: 0,
    currentPage: 1,
    editingAgent: null,
  });

  const fetchAgentData = useCallback(async (page: number = 1) => {
    try {
      setState(prev => ({ ...prev, loading: true, error: null }));
      
      const [agentListResult, summaryResult] = await Promise.allSettled([
        api.agents.list({ 
          skip: (page - 1) * PAGINATION.DEFAULT_PAGE_SIZE,
          limit: PAGINATION.DEFAULT_PAGE_SIZE 
        }),
        api.agents.getStatusSummary(),
      ]);

      const agentList = agentListResult.status === 'fulfilled' ? agentListResult.value : null;
      const summary = summaryResult.status === 'fulfilled' ? summaryResult.value : null;

      setState(prev => ({
        ...prev,
        agents: agentList?.items || [],
        summary: summary,
        total: agentList?.total || 0,
        currentPage: page,
        loading: false,
      }));

    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : "Failed to fetch agent data";
      setState(prev => ({ ...prev, error: errorMessage, loading: false }));
      handleError(err, errorMessage);
    }
  }, []);

  const editAgent = useCallback((agent: AgentResponse) => {
    setState(prev => ({ ...prev, editingAgent: agent }));
  }, []);

  const deleteAgent = useCallback(async (id: string) => {
    try {
      await api.agents.delete(id);
      await fetchAgentData(state.currentPage);
    } catch (err) {
      handleError(err, "Failed to delete agent");
    }
  }, [fetchAgentData, state.currentPage]);

  const handleEditSuccess = useCallback(() => {
    setState(prev => ({ ...prev, editingAgent: null }));
    fetchAgentData(state.currentPage);
  }, [fetchAgentData, state.currentPage]);

  useEffect(() => {
    fetchAgentData();
  }, [fetchAgentData]);

  const { agents, summary, loading, error, total, currentPage } = state;

  return (
    <div className="hidden flex-col md:flex">
      <TopHeader 
        page={pageConfig.agents}
        onRefresh={() => fetchAgentData(currentPage)}
        isLoading={loading}
        actions={
          <RegisterAgentSheet onSuccess={() => fetchAgentData(currentPage)} />
        }
      />

      <div className="flex-1 space-y-6 p-8 pt-6">
        <AgentErrorAlert error={error} />

        <AgentStatsOverview summary={summary} />

        <AgentList
          agents={agents}
          total={total}
          loading={loading}
          onEdit={editAgent}
          onDelete={deleteAgent}
          onRefresh={() => fetchAgentData(currentPage)}
        />
      </div>

      {/* Sheet for Editing Agent */}
      {state.editingAgent && (
        <RegisterAgentSheet
          editAgent={state.editingAgent}
          open={!!state.editingAgent}
          onOpenChange={(isOpen: boolean) => {
            if (!isOpen) {
              setState(prev => ({ ...prev, editingAgent: null }));
            }
          }}
          onSuccess={handleEditSuccess}
        />
      )}
    </div>
  );
} 
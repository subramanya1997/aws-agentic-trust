"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowUpDown, ExternalLink, Copy } from "lucide-react"
import type { MCPEntry } from "@/lib/types"

export const mcpColumns: ColumnDef<MCPEntry>[] = [
  {
    accessorKey: "id",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          MCP ID
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const id = row.getValue("id") as string
      return (
        <div className="font-mono text-xs max-w-[200px] truncate" title={id}>
          {id}
        </div>
      )
    },
  },
  {
    accessorKey: "command",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Command
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const command = row.getValue("command") as string
      return (
        <Badge variant="outline" className="font-mono">
          {command}
        </Badge>
      )
    },
  },
  {
    accessorKey: "args",
    header: "Arguments",
    cell: ({ row }) => {
      const args = row.getValue("args") as string[]
      return (
        <div className="max-w-[300px] truncate text-sm font-mono">
          {args.length > 0 ? args.join(" ") : "-"}
        </div>
      )
    },
  },
  {
    id: "status",
    header: "Status",
    cell: () => {
      // For now, we'll assume all registered MCPs are active
      return (
        <Badge variant="default" className="text-green-600 bg-green-100">
          Active
        </Badge>
      )
    },
  },
  {
    id: "capabilities",
    header: "Capabilities",
    cell: ({ row }) => {
      const tools = row.original.tools_count || 0
      const resources = row.original.resources_count || 0
      const prompts = row.original.prompts_count || 0
      return (
        <div className="flex gap-1">
          <Badge variant="secondary" className="text-xs" title={row.original.tool_names?.join(', ') ?? ''}>
            {tools} Tools
          </Badge>
          <Badge variant="secondary" className="text-xs" title={row.original.resource_names?.join(', ') ?? ''}>
            {resources} Res
          </Badge>
          <Badge variant="secondary" className="text-xs" title={row.original.prompt_names?.join(', ') ?? ''}>
            {prompts} Pr
          </Badge>
        </div>
      )
    },
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => {
      const mcp = row.original
      return (
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigator.clipboard.writeText(mcp.id)}
            className="h-8 w-8 p-0"
            title="Copy MCP ID"
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-8 w-8 p-0"
            title="View Details"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      )
    },
  },
] 
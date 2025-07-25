"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowUpDown } from "lucide-react"
import type { LogEntryResponse } from "@/lib/types"
import { EVENT_TYPES } from "@/lib/constants"
import { formatTimestamp } from "@/lib/utils"

export const columns: ColumnDef<LogEntryResponse>[] = [
  {
    accessorKey: "timestamp",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Timestamp
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const timestamp = row.getValue("timestamp") as string
      return (
        <div className="font-mono text-xs">
          {formatTimestamp(timestamp)}
        </div>
      )
    },
  },
  {
    accessorKey: "event_type",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Event Type
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const eventType = row.getValue("event_type") as string
      const getVariant = (type: string) => {
        switch (type) {
          case EVENT_TYPES.CALL_TOOL:
            return "default"
          case EVENT_TYPES.TOOL_RESULT:
            return "secondary"
          case EVENT_TYPES.ERROR:
            return "destructive"
          default:
            return "outline"
        }
      }
      return (
        <Badge variant={getVariant(eventType)}>
          {eventType}
        </Badge>
      )
    },
  },
  {
    id: "tool",
    accessorKey: "data",
    header: "Tool",
    cell: ({ row }) => {
      const data = row.original.data as Record<string, unknown>
      const tool = data?.tool as string
      return tool ? (
        <Badge variant="outline" className="font-mono">
          {tool}
        </Badge>
      ) : (
        <span className="text-muted-foreground">-</span>
      )
    },
  },
  {
    id: "summary",
    accessorKey: "data",
    header: "Summary",
    cell: ({ row }) => {
      const data = row.original.data as Record<string, unknown>
      const summary = data?.summary ?? data?.arguments ?? data?.count
      return (
        <div className="max-w-[500px] truncate text-sm">
          {summary ? JSON.stringify(summary) : "-"}
        </div>
      )
    },
  },
] 
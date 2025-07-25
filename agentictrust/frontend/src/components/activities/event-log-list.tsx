"use client";

import React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table";
import { 
  Activity as ActivityIcon, 
  AlertCircle, 
  RefreshCw, 
  AlertTriangle, 
  Info, 
  Database, 
  ChevronDown, 
  ChevronRight,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  Filter,
  Download,
  Eye,
  EyeOff,
  Calendar,
  Clock
} from "lucide-react";
import type { LogEntryResponse } from "@/lib/types";
import { LOG_SEVERITY } from "@/lib/constants";

interface EventLogListProps {
  logs: LogEntryResponse[];
  loading: boolean;
  total: number;
  onRefresh?: () => void;
}

export function EventLogList({ logs, loading, total, onRefresh }: EventLogListProps) {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "timestamp", desc: true } // Default to newest first
  ]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({});
  const [globalFilter, setGlobalFilter] = React.useState("");
  const [expandedRows, setExpandedRows] = React.useState<Set<string>>(new Set());

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case LOG_SEVERITY.ERROR:
      case LOG_SEVERITY.CRITICAL:
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      case LOG_SEVERITY.WARNING:
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case LOG_SEVERITY.INFO:
        return <Info className="h-4 w-4 text-blue-500" />;
      case LOG_SEVERITY.DEBUG:
        return <Database className="h-4 w-4 text-gray-500" />;
      default:
        return <ActivityIcon className="h-4 w-4 text-green-500" />;
    }
  };

  const getSeverityBadgeVariant = (severity: string) => {
    if (severity === LOG_SEVERITY.ERROR || severity === LOG_SEVERITY.CRITICAL) {
      return "destructive";
    }
    if (severity === LOG_SEVERITY.WARNING) {
      return "secondary";
    }
    return "outline";
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return {
      full: date.toLocaleString(),
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString(),
      relative: getRelativeTime(date)
    };
  };

  const getRelativeTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const toggleRowExpansion = (rowId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(rowId)) {
      newExpanded.delete(rowId);
    } else {
      newExpanded.add(rowId);
    }
    setExpandedRows(newExpanded);
  };

  const columns: ColumnDef<LogEntryResponse>[] = [
    {
      id: "expand",
      header: "",
             cell: ({ row }) => {
         const hasData = Object.keys(row.original.data || {}).length > 0;
         if (!hasData) return null;
         
         return (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={(e) => {
              e.stopPropagation();
              toggleRowExpansion(row.id);
            }}
          >
            {expandedRows.has(row.id) ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        );
      },
      enableSorting: false,
      enableHiding: false,
      size: 50,
    },
    {
      accessorKey: "timestamp",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="h-8 px-2"
          >
            <Calendar className="mr-2 h-4 w-4" />
            Timestamp
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        const timestamp = formatTimestamp(row.getValue("timestamp"));
        return (
          <div className="space-y-1">
            <div className="font-mono text-sm">{timestamp.time}</div>
            <div className="text-xs text-muted-foreground">{timestamp.date}</div>
            <div className="text-xs text-blue-600">{timestamp.relative}</div>
          </div>
        );
      },
      sortingFn: (rowA, rowB) => {
        const a = new Date(rowA.getValue("timestamp")).getTime();
        const b = new Date(rowB.getValue("timestamp")).getTime();
        return a - b;
      },
    },
    {
      accessorKey: "event_type",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="h-8 px-2"
          >
            Event Type
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        const severity = row.getValue("severity") as string;
        const eventType = row.getValue("event_type") as string;
        return (
          <div className="flex items-center space-x-2">
            {getSeverityIcon(severity)}
            <span className="font-medium">{eventType}</span>
          </div>
        );
      },
      filterFn: "includesString",
    },
    {
      accessorKey: "severity",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="h-8 px-2"
          >
            Severity
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        const severity = row.getValue("severity") as string;
        return (
          <Badge variant={getSeverityBadgeVariant(severity)}>
            {severity}
          </Badge>
        );
      },
      sortingFn: (rowA, rowB) => {
        const severityOrder = { critical: 4, error: 3, warning: 2, info: 1, debug: 0 };
        const a = severityOrder[rowA.getValue("severity") as keyof typeof severityOrder] || 0;
        const b = severityOrder[rowB.getValue("severity") as keyof typeof severityOrder] || 0;
        return a - b;
      },
      filterFn: "equals",
    },
    {
      id: "tool_agent",
      header: "Tool/Agent",
             cell: ({ row }) => {
         const data = row.original.data || {};
         const toolName = (data as any)?.tool_name || '-';
         const agentName = (data as any)?.agent_name || (data as any)?.agent_id || '-';
         const isError = row.getValue("event_type") === 'tool_error';
         
         return (
           <div className="space-y-1">
             <div className={`text-sm font-medium ${isError ? 'text-red-600' : ''}`}>
               {String(toolName)}
             </div>
             <div className="text-xs text-muted-foreground truncate max-w-32">
               {String(agentName)}
             </div>
           </div>
         );
       },
      enableSorting: false,
             filterFn: (row, id, value) => {
         const data = row.original.data || {};
         const toolName = (data as any)?.tool_name || '';
         const agentName = (data as any)?.agent_name || (data as any)?.agent_id || '';
         return String(toolName).toLowerCase().includes(value.toLowerCase()) || 
                String(agentName).toLowerCase().includes(value.toLowerCase());
       },
    },
    {
      accessorKey: "source",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="h-8 px-2"
          >
            Source
            {column.getIsSorted() === "asc" ? (
              <ArrowUp className="ml-2 h-4 w-4" />
            ) : column.getIsSorted() === "desc" ? (
              <ArrowDown className="ml-2 h-4 w-4" />
            ) : (
              <ArrowUpDown className="ml-2 h-4 w-4" />
            )}
          </Button>
        );
      },
      cell: ({ row }) => {
        return <span className="text-sm">{row.getValue("source")}</span>;
      },
      filterFn: "equals",
    },
    {
      id: "details",
      header: "Details",
             cell: ({ row }) => {
         const eventType = row.getValue("event_type") as string;
         const data = row.original.data || {};
         const correlationId = row.original.correlation_id;
         
         if (eventType === 'tool_error') {
           const error = (data as any)?.error || 'Unknown error';
           return (
             <span className="text-sm text-red-600 font-medium truncate max-w-64" title={String(error)}>
               {String(error)}
             </span>
           );
         }
         
         if (correlationId) {
           return (
             <span className="text-xs font-mono text-muted-foreground">
               {correlationId.slice(0, 8)}...
             </span>
           );
         }
         
         return <span className="text-muted-foreground">-</span>;
       },
      enableSorting: false,
    },
    {
      accessorKey: "correlation_id",
      header: "Correlation ID",
      cell: ({ row }) => {
        const correlationId = row.getValue("correlation_id") as string | undefined;
        if (!correlationId) return <span className="text-muted-foreground">-</span>;
        
        return (
          <span className="text-xs font-mono text-muted-foreground" title={correlationId}>
            {correlationId.slice(0, 8)}...
          </span>
        );
      },
      filterFn: "includesString",
    },
  ];

  const table = useReactTable({
    data: logs,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: "includesString",
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize: 50,
      },
      columnVisibility: {
        correlation_id: false, // Hide by default
      },
    },
  });

  // Get unique values for filters
  const uniqueEventTypes = Array.from(new Set(logs.map(log => log.event_type)));
  const uniqueSeverities = Array.from(new Set(logs.map(log => log.severity)));
  const uniqueSources = Array.from(new Set(logs.map(log => log.source).filter(Boolean))) as string[];

  const exportLogs = () => {
    const filteredData = table.getFilteredRowModel().rows.map(row => row.original);
    const csv = [
      // Header
      ['Timestamp', 'Event Type', 'Severity', 'Tool', 'Agent', 'Source', 'Correlation ID', 'Details'].join(','),
      // Data
      ...filteredData.map(log => [
        log.timestamp,
        log.event_type,
        log.severity,
        (log.data as any)?.tool_name || '',
        (log.data as any)?.agent_name || (log.data as any)?.agent_id || '',
        log.source,
        log.correlation_id || '',
        log.event_type === 'tool_error' ? (log.data as any)?.error || '' : ''
      ].map(field => `"${String(field).replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `event-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Header section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Event Log</h2>
          <p className="text-sm text-muted-foreground">
            Complete activity log with advanced filtering and analysis ({total} total entries)
          </p>
        </div>
        {onRefresh && (
          <Button variant="outline" size="sm" onClick={onRefresh} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        )}
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center h-32 border rounded-lg">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="ml-2">Loading logs...</span>
        </div>
      ) : logs.length === 0 ? (
        <div className="text-center py-8 border rounded-lg">
          <ActivityIcon className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Log Entries</h3>
          <p className="text-muted-foreground">No log entries match the current filters</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Advanced Filters and Controls */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Global Search */}
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search across all fields..."
                value={globalFilter ?? ""}
                onChange={(event) => setGlobalFilter(event.target.value)}
                className="pl-8"
              />
            </div>

            {/* Severity Filter */}
            <Select
              value={(table.getColumn("severity")?.getFilterValue() as string) ?? "all"}
              onValueChange={(value) =>
                table.getColumn("severity")?.setFilterValue(value === "all" ? "" : value)
              }
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                {uniqueSeverities.map(severity => (
                  <SelectItem key={severity} value={severity}>{severity}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Event Type Filter */}
            <Select
              value={(table.getColumn("event_type")?.getFilterValue() as string) ?? "all"}
              onValueChange={(value) =>
                table.getColumn("event_type")?.setFilterValue(value === "all" ? "" : value)
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Event Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Events</SelectItem>
                {uniqueEventTypes.map(eventType => (
                  <SelectItem key={eventType} value={eventType}>{eventType}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Source Filter */}
            <Select
              value={(table.getColumn("source")?.getFilterValue() as string) ?? "all"}
              onValueChange={(value) =>
                table.getColumn("source")?.setFilterValue(value === "all" ? "" : value)
              }
            >
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {uniqueSources.map(source => (
                  <SelectItem key={source} value={source}>{source}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Column Visibility */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Eye className="mr-2 h-4 w-4" />
                  Columns
                  <ChevronDown className="ml-2 h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {table
                  .getAllColumns()
                  .filter((column) => column.getCanHide())
                  .map((column) => {
                    return (
                      <DropdownMenuCheckboxItem
                        key={column.id}
                        className="capitalize"
                        checked={column.getIsVisible()}
                        onCheckedChange={(value) =>
                          column.toggleVisibility(!!value)
                        }
                      >
                        {column.id.replace('_', ' ')}
                      </DropdownMenuCheckboxItem>
                    )
                  })}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Export */}
            <Button variant="outline" size="sm" onClick={exportLogs}>
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
          </div>

          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => {
                      return (
                        <TableHead key={header.id} style={{ width: header.getSize() }}>
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                        </TableHead>
                      )
                    })}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <React.Fragment key={row.id}>
                      <TableRow
                        data-state={row.getIsSelected() && "selected"}
                        className="hover:bg-muted/50"
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                      {expandedRows.has(row.id) && (
                        <TableRow>
                          <TableCell colSpan={columns.length} className="bg-muted/30 p-4">
                            <div className="space-y-3">
                              <div className="text-sm font-medium">Event Details:</div>
                              {row.original.correlation_id && (
                                <div className="text-sm">
                                  <span className="font-medium">Correlation ID:</span>{' '}
                                  <span className="font-mono text-muted-foreground">{row.original.correlation_id}</span>
                                </div>
                              )}
                              {row.original.session_id && (
                                <div className="text-sm">
                                  <span className="font-medium">Session ID:</span>{' '}
                                  <span className="font-mono text-muted-foreground">{row.original.session_id}</span>
                                </div>
                              )}
                              <div className="text-sm">
                                <span className="font-medium">Event Data:</span>
                                <pre className="mt-2 p-3 bg-background rounded border text-xs overflow-auto max-h-64">
                                  {JSON.stringify(row.original.data, null, 2)}
                                </pre>
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center"
                    >
                      No results found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination and Stats */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>
                Showing {table.getRowModel().rows.length} of{" "}
                {table.getFilteredRowModel().rows.length} entries
              </span>
              {table.getFilteredRowModel().rows.length !== logs.length && (
                <span>
                  (filtered from {logs.length} total)
                </span>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.previousPage()}
                disabled={!table.getCanPreviousPage()}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {table.getState().pagination.pageIndex + 1} of{" "}
                {table.getPageCount()}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => table.nextPage()}
                disabled={!table.getCanNextPage()}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 
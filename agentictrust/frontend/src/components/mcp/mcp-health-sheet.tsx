import React from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { MCPHealthReport } from "@/lib/types";
import { AlertCircle, Server, Wrench, FileText, MessageSquare, WifiOff } from "lucide-react";

interface MCPHealthSheetProps {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  report: MCPHealthReport | null;
}

export function MCPHealthIssuesSheet({ open, onOpenChange, report }: MCPHealthSheetProps) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Fleet Health Report</SheetTitle>
        </SheetHeader>
        {report === null ? (
          <div className="p-4 text-muted-foreground">Loading health data…</div>
        ) : report.issues.length === 0 ? (
          <div className="p-4 flex items-center gap-2 text-green-600">
            <Server className="h-4 w-4" />
            <span>All {report.total} MCPs are healthy.</span>
          </div>
        ) : (
          <div className="space-y-4 p-4">
            {report.issues.map((issue) => (
              <div key={issue.id} className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  {issue.unreachable ? (
                    <WifiOff className="h-4 w-4 text-red-600" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                  )}
                  <span className="font-semibold truncate">
                    {issue.name || issue.id}
                  </span>
                  {issue.unreachable && (
                    <Badge variant="destructive" className="ml-auto">Unreachable</Badge>
                  )}
                </div>

                {!issue.unreachable && (
                  <div className="space-y-2 text-sm">
                    {issue.tool_diff && (
                      <DiffBlock title="Tools" icon={<Wrench className="h-3 w-3" />} diff={issue.tool_diff} />
                    )}
                    {issue.resource_diff && (
                      <DiffBlock title="Resources" icon={<FileText className="h-3 w-3" />} diff={issue.resource_diff} />
                    )}
                    {issue.prompt_diff && (
                      <DiffBlock title="Prompts" icon={<MessageSquare className="h-3 w-3" />} diff={issue.prompt_diff} />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function DiffBlock({ title, icon, diff }: { title: string; icon: React.ReactNode; diff: { missing: string[]; extra: string[] } }) {
  return (
    <div>
      <div className="flex items-center gap-1 font-medium mb-1">
        {icon}
        <span>{title}</span>
      </div>
      {diff.missing.length > 0 && (
        <p className="text-xs text-red-600 mb-1">Missing: {diff.missing.join(", ")}</p>
      )}
      {diff.extra.length > 0 && (
        <p className="text-xs text-yellow-600">Unexpected: {diff.extra.join(", ")}</p>
      )}
    </div>
  );
} 
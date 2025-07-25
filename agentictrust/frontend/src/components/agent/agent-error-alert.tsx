"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

interface AgentErrorAlertProps {
  error: string | null;
}

export function AgentErrorAlert({ error }: AgentErrorAlertProps) {
  if (!error) {
    return null;
  }

  return (
    <Card className="border-red-200 bg-red-50">
      <CardContent className="pt-6">
        <div className="flex items-center space-x-2 text-red-600">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      </CardContent>
    </Card>
  );
} 
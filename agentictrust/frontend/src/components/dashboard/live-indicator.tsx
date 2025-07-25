"use client";

import React, { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

interface LiveIndicatorProps {
  isConnected?: boolean;
  lastUpdate?: Date;
  isLoading?: boolean;
}

export function LiveIndicator({ isConnected = true, lastUpdate, isLoading }: LiveIndicatorProps) {
  const [timeAgo, setTimeAgo] = useState<string>("");

  useEffect(() => {
    if (!lastUpdate) return;

    const updateTimeAgo = () => {
      const now = new Date();
      const diff = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);
      
      if (diff < 60) {
        setTimeAgo("just now");
      } else if (diff < 3600) {
        setTimeAgo(`${Math.floor(diff / 60)}m ago`);
      } else {
        setTimeAgo(`${Math.floor(diff / 3600)}h ago`);
      }
    };

    updateTimeAgo();
    const interval = setInterval(updateTimeAgo, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [lastUpdate]);

  if (isLoading) {
    return (
      <Badge variant="secondary" className="flex items-center gap-1">
        <RefreshCw className="h-3 w-3 animate-spin" />
        <span className="text-xs">Updating...</span>
      </Badge>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant={isConnected ? "default" : "destructive"} 
        className="flex items-center gap-1"
      >
        {isConnected ? (
          <Wifi className="h-3 w-3" />
        ) : (
          <WifiOff className="h-3 w-3" />
        )}
        <span className="text-xs">
          {isConnected ? "Live" : "Offline"}
        </span>
      </Badge>
      
      {lastUpdate && (
        <span className="text-xs text-muted-foreground">
          Updated {timeAgo}
        </span>
      )}
    </div>
  );
} 
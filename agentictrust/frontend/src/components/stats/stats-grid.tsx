"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface StatsGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

export function StatsGrid({ 
  children, 
  columns = 4, 
  className 
}: StatsGridProps) {
  const gridClasses = {
    2: "md:grid-cols-2",
    3: "md:grid-cols-2 lg:grid-cols-3",
    4: "md:grid-cols-2 lg:grid-cols-4",
    5: "md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
  };

  return (
    <div className={cn(
      "grid gap-4 grid-cols-1",
      gridClasses[columns],
      className
    )}>
      {children}
    </div>
  );
} 
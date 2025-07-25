"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  valueClassName?: string;
  trend?: {
    value: number;
    isPositive: boolean;
    label?: string;
  };
  status?: "healthy" | "warning" | "error" | "neutral";
  onClick?: () => void;
}

export function StatCard({ 
  title, 
  value, 
  description, 
  icon: Icon, 
  valueClassName = "",
  trend,
  status = "neutral",
  onClick
}: StatCardProps) {
  const getStatusStyles = () => {
    switch (status) {
      case "healthy":
        return "border-green-200 bg-green-50/30 hover:bg-green-50/50";
      case "warning":
        return "border-yellow-200 bg-yellow-50/30 hover:bg-yellow-50/50";
      case "error":
        return "border-red-200 bg-red-50/30 hover:bg-red-50/50";
      default:
        return "hover:bg-muted/50";
    }
  };

  return (
    <Card 
      className={`transition-all duration-200 ${getStatusStyles()} ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        {Icon && (
          <div className="p-1 rounded-md bg-background/50">
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold mb-1 ${valueClassName}`}>
          {value}
        </div>
        
        <div className="flex items-center justify-between">
          {description && (
            <p className="text-xs text-muted-foreground flex-1">
              {description}
            </p>
          )}
          
          {trend && (
            <div className="flex items-center space-x-1">
              {trend.isPositive ? (
                <TrendingUp className="h-3 w-3 text-green-600" />
              ) : (
                <TrendingDown className="h-3 w-3 text-red-600" />
              )}
              <span className={`text-xs font-medium ${trend.isPositive ? "text-green-600" : "text-red-600"}`}>
                {trend.isPositive ? "+" : ""}{trend.value}%
              </span>
              {trend.label && (
                <span className="text-xs text-muted-foreground ml-1">
                  {trend.label}
                </span>
              )}
            </div>
          )}
        </div>
        
        {status !== "neutral" && (
          <div className="mt-2">
            <Badge 
              variant={
                status === "healthy" ? "default" : 
                status === "warning" ? "secondary" : 
                "destructive"
              }
              className="text-xs"
            >
              {status === "healthy" ? "Operational" : 
               status === "warning" ? "Attention" : 
               "Issues"}
            </Badge>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 
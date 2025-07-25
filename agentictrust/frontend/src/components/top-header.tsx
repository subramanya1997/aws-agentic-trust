"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { RefreshCw } from "lucide-react"
import { type PageConfig } from "@/lib/config"

interface TopHeaderProps {
  page: PageConfig
  showLiveIndicator?: boolean
  onRefresh?: () => void
  isLoading?: boolean
  actions?: React.ReactNode
}

export function TopHeader({
  page,
  showLiveIndicator = false,
  onRefresh,
  isLoading = false,
  actions,
}: TopHeaderProps) {
  const IconComponent = page.icon

  return (
    <div className="border-b">
      <div className="flex h-16 items-center px-4">
        <div className="flex items-center space-x-4">
          <IconComponent className="h-6 w-6" />
          <div>
            <h1 className="text-lg font-semibold">{page.title}</h1>
            <p className="text-sm text-muted-foreground">{page.description}</p>
          </div>
        </div>
        <div className="ml-auto flex items-center space-x-4">
          {showLiveIndicator && (
            <Badge variant="outline" className="flex items-center gap-2">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Live
            </Badge>
          )}
          {onRefresh && (
            <Button
              onClick={onRefresh}
              variant="outline"
              size="sm"
              disabled={isLoading}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
          {actions}
        </div>
      </div>
    </div>
  )
} 
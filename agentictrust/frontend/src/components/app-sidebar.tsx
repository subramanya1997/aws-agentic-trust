"use client"

import * as React from "react"
import { NavMain } from "@/components/nav-main"
import { NavSecondary } from "@/components/nav-secondary"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { navigationConfig, brandConfig } from "@/lib/config"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const BrandIcon = brandConfig.icon

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href={brandConfig.url}>
                <BrandIcon className="h-5 w-5" />
                <span className="text-base font-semibold">{brandConfig.name}</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navigationConfig.main} />
        <NavSecondary items={navigationConfig.bottom} className="mt-auto" />
      </SidebarContent>
    </Sidebar>
  )
} 
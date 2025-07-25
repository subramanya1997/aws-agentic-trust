"use client"

import { useRouter } from "next/navigation"
import { type PageConfig } from "@/lib/config"

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

export function NavSecondary({
  items,
  ...props
}: {
  items: PageConfig[]
} & React.ComponentPropsWithoutRef<typeof SidebarGroup>) {
  const router = useRouter()

  return (
    <SidebarGroup {...props}>
      <SidebarMenu>
        {items.map((item) => (
          <SidebarMenuItem key={item.title}>
            <SidebarMenuButton asChild size="sm">
              <a href="#" onClick={(e) => {
                e.preventDefault()
                router.push(item.url)
              }}>
                <item.icon />
                <span>{item.title}</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  )
} 
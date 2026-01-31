'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FileText, Files, Combine, Table2, History, Info, Home } from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';

const navItems = [
  { title: 'Início', href: '/', icon: Home },
  { title: 'Extrair', href: '/extract', icon: FileText },
  { title: 'Lote', href: '/batch', icon: Files },
  { title: 'Mesclar', href: '/merge', icon: Combine },
  { title: 'Tabelas', href: '/tables', icon: Table2 },
  { title: 'Histórico', href: '/jobs', icon: History },
  { title: 'Info', href: '/info', icon: Info },
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <Sidebar>
      <SidebarHeader className="border-b px-6 py-4">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <FileText className="h-6 w-6" />
          <span>Lex PDFtoText</span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.href}>
                  <SidebarMenuButton asChild isActive={pathname === item.href}>
                    <Link href={item.href}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

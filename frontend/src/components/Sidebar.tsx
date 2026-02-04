"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { 
  Zap, 
  Home, 
  TrendingUp, 
  Sparkles, 
  PenTool, 
  Settings,
  HelpCircle,
  BarChart3,
  Flame
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/trending", label: "🔥 Trending", icon: Flame },
  { href: "/scanner", label: "Trend Scanner", icon: TrendingUp },
  { href: "/trends", label: "Trend Analytics", icon: BarChart3 },
  { href: "/generator", label: "Design Generator", icon: Sparkles },
  { href: "/converter", label: "Sketch Converter", icon: PenTool },
];

const bottomItems = [
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/help", label: "Help", icon: HelpCircle },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <Link href="/" className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-fashion">
            <Zap className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold gradient-text">TrendMuse</h1>
            <p className="text-xs text-muted-foreground">AI Fashion Agent</p>
          </div>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3 px-3">
          Main
        </p>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all
                ${isActive 
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }
              `}
            >
              <item.icon className="h-5 w-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Bottom Navigation */}
      <div className="p-4 border-t border-border space-y-2">
        {bottomItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all
                ${isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }
              `}
            >
              <item.icon className="h-5 w-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Status Badge */}
      <div className="p-4 m-4 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-medium">Demo Mode</span>
        </div>
        <p className="text-xs text-muted-foreground">
          Running with sample data
        </p>
      </div>
    </aside>
  );
}

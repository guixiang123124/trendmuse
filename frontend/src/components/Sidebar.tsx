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
  Flame,
  Globe
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Home },
  { href: "/discovery", label: "Trend Discovery", icon: Globe, badge: "NEW" },
  { href: "/trending", label: "Trending Products", icon: Flame },
  { href: "/scanner", label: "Trend Scanner", icon: TrendingUp },
  { href: "/trends", label: "Analytics", icon: BarChart3 },
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
    <aside className="w-64 h-screen bg-card border-r border-border flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="p-5 border-b border-border">
        <Link href="/" className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-fashion">
            <Zap className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold gradient-text">TrendMuse</h1>
            <p className="text-[10px] text-muted-foreground">AI Fashion Intelligence</p>
          </div>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2 px-3">
          Platform
        </p>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2 rounded-xl transition-all text-sm
                ${isActive 
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }
              `}
            >
              <item.icon className="h-4 w-4 flex-shrink-0" />
              <span className="font-medium flex-1">{item.label}</span>
              {item.badge && (
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full ${
                  isActive 
                    ? "bg-white/20 text-white" 
                    : "bg-emerald-500/20 text-emerald-400"
                }`}>
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Navigation */}
      <div className="p-3 border-t border-border space-y-1">
        {bottomItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                flex items-center gap-3 px-3 py-2 rounded-xl transition-all text-sm
                ${isActive 
                  ? "bg-primary text-primary-foreground" 
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }
              `}
            >
              <item.icon className="h-4 w-4" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Version Badge */}
      <div className="p-3 mx-3 mb-3 rounded-xl bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
        <div className="flex items-center gap-2 mb-1">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-medium">TrendMuse 2.0</span>
        </div>
        <p className="text-[10px] text-muted-foreground">
          AI Trend Discovery Engine Active
        </p>
      </div>
    </aside>
  );
}

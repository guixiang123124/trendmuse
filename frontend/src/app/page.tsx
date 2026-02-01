"use client";

import { useState, useEffect } from "react";
import { 
  TrendingUp, 
  Sparkles, 
  PenTool, 
  ArrowRight,
  Zap,
  Image as ImageIcon,
  BarChart3
} from "lucide-react";
import Link from "next/link";

interface Stats {
  itemsScanned: number;
  designsGenerated: number;
  sketchesCreated: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({
    itemsScanned: 0,
    designsGenerated: 0,
    sketchesCreated: 0,
  });

  useEffect(() => {
    // Animate stats on load
    const targets = { itemsScanned: 247, designsGenerated: 86, sketchesCreated: 42 };
    const duration = 1500;
    const steps = 60;
    const interval = duration / steps;

    let step = 0;
    const timer = setInterval(() => {
      step++;
      const progress = step / steps;
      setStats({
        itemsScanned: Math.round(targets.itemsScanned * progress),
        designsGenerated: Math.round(targets.designsGenerated * progress),
        sketchesCreated: Math.round(targets.sketchesCreated * progress),
      });
      if (step >= steps) clearInterval(timer);
    }, interval);

    return () => clearInterval(timer);
  }, []);

  const features = [
    {
      title: "Trend Scanner",
      description: "Analyze fashion e-commerce sites to discover trending styles and patterns",
      icon: TrendingUp,
      href: "/scanner",
      gradient: "from-pink-500 to-rose-500",
    },
    {
      title: "Design Generator",
      description: "Create AI-powered design variations from any fashion piece",
      icon: Sparkles,
      href: "/generator",
      gradient: "from-purple-500 to-violet-500",
    },
    {
      title: "Sketch Converter",
      description: "Transform product photos into professional fashion sketches",
      icon: PenTool,
      href: "/converter",
      gradient: "from-blue-500 to-indigo-500",
    },
  ];

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-fashion">
            <Zap className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-4xl font-bold gradient-text">TrendMuse</h1>
            <p className="text-muted-foreground">Fashion Design AI Agent</p>
          </div>
        </div>
        <p className="text-lg text-muted-foreground max-w-2xl">
          Discover trends, generate designs, and create sketches with the power of AI.
          Your intelligent assistant for fashion innovation.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-pink-500/20">
              <BarChart3 className="h-6 w-6 text-pink-500" />
            </div>
            <div>
              <p className="text-3xl font-bold">{stats.itemsScanned}</p>
              <p className="text-muted-foreground">Items Scanned</p>
            </div>
          </div>
        </div>
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-purple-500/20">
              <Sparkles className="h-6 w-6 text-purple-500" />
            </div>
            <div>
              <p className="text-3xl font-bold">{stats.designsGenerated}</p>
              <p className="text-muted-foreground">Designs Generated</p>
            </div>
          </div>
        </div>
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-blue-500/20">
              <ImageIcon className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <p className="text-3xl font-bold">{stats.sketchesCreated}</p>
              <p className="text-muted-foreground">Sketches Created</p>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {features.map((feature) => (
          <Link
            key={feature.title}
            href={feature.href}
            className="group p-6 rounded-2xl bg-card border border-border card-hover"
          >
            <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-4`}>
              <feature.icon className="h-6 w-6 text-white" />
            </div>
            <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors">
              {feature.title}
            </h3>
            <p className="text-muted-foreground mb-4">
              {feature.description}
            </p>
            <div className="flex items-center text-primary gap-2">
              <span className="text-sm font-medium">Get Started</span>
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="p-6 rounded-2xl bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
        <h2 className="text-xl font-semibold mb-4">Quick Start</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/scanner?demo=true"
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Load Demo Data
          </Link>
          <Link
            href="/scanner"
            className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Scan SHEIN
          </Link>
          <Link
            href="/scanner"
            className="px-4 py-2 rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
          >
            Scan ZARA
          </Link>
        </div>
      </div>

      {/* Demo Mode Banner */}
      <div className="mt-8 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
        <div className="flex items-center gap-3">
          <Zap className="h-5 w-5 text-amber-500" />
          <div>
            <p className="text-sm font-medium text-amber-500">Demo Mode Active</p>
            <p className="text-xs text-muted-foreground">
              Using sample data and placeholder generations. Add a Replicate API key to enable real AI.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { Zap, TrendingUp, Sparkles, Download, ShoppingBag, Twitter, Globe, BookOpen, Check, ArrowRight } from "lucide-react";

const steps = [
  { icon: TrendingUp, title: "Discover Trends", desc: "AI scans Shopify stores, Twitter/X, fashion blogs & Google Trends in real-time" },
  { icon: Sparkles, title: "AI Generates Designs", desc: "Turn trending insights into production-ready fashion designs instantly" },
  { icon: Download, title: "Export & Sell", desc: "Download designs, tech packs, and sketches ready for manufacturing" },
];

const sources = [
  { icon: ShoppingBag, name: "Shopify Stores", count: "33 stores" },
  { icon: Twitter, name: "Twitter / X", count: "Real-time" },
  { icon: BookOpen, name: "Fashion Blogs", count: "50+ sources" },
  { icon: Globe, name: "Google Trends", count: "Global data" },
];

const stats = [
  { value: "1,100+", label: "Products Tracked" },
  { value: "33", label: "Stores Monitored" },
  { value: "6", label: "Categories" },
  { value: "24/7", label: "Live Scanning" },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    period: "forever",
    features: ["5 searches / day", "10 AI designs / month", "Basic trend data", "1 data source"],
    cta: "Get Started Free",
    href: "/register",
    highlight: false,
  },
  {
    name: "Starter",
    price: "$19",
    period: "/ month",
    features: ["50 searches / day", "100 AI designs / month", "All data sources", "Export to PNG & SVG", "Trend alerts"],
    cta: "Start Free Trial",
    href: "/register",
    highlight: true,
  },
  {
    name: "Pro",
    price: "$49",
    period: "/ month",
    features: ["Unlimited searches", "Unlimited AI designs", "All data sources", "API access", "Priority support", "Custom trend reports"],
    cta: "Start Free Trial",
    href: "/register",
    highlight: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-bold">TrendMuse</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/discovery" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:block">
              Trends
            </Link>
            <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Sign In
            </Link>
            <Link
              href="/register"
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 text-white text-sm font-medium hover:opacity-90 transition-opacity"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-medium mb-6">
            <Sparkles className="h-3 w-3" /> AI-Powered Fashion Intelligence
          </div>
          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            Stop Guessing What&apos;s Trending.{" "}
            <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-orange-400 bg-clip-text text-transparent">
              Start Designing What Sells.
            </span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            TrendMuse scans thousands of products, social signals, and fashion data sources to surface what&apos;s trending — then generates AI designs you can sell.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/register"
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold text-base hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
            >
              Get Started Free <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/discovery"
              className="px-8 py-3.5 rounded-xl border border-border text-foreground font-semibold text-base hover:bg-muted transition-colors flex items-center justify-center gap-2"
            >
              View Trends <TrendingUp className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 px-6 border-y border-border/50">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                {s.value}
              </p>
              <p className="text-sm text-muted-foreground mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">How It Works</h2>
          <p className="text-muted-foreground text-center mb-14 max-w-xl mx-auto">
            From trend discovery to sellable designs in three simple steps.
          </p>
          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <div key={step.title} className="relative p-6 rounded-2xl bg-card border border-border hover:border-purple-500/30 transition-colors">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20">
                    <step.icon className="h-5 w-5 text-purple-400" />
                  </div>
                  <span className="text-xs font-bold text-muted-foreground">STEP {i + 1}</span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data Sources */}
      <section className="py-20 px-6 bg-card/50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">Powered by Real Data</h2>
          <p className="text-muted-foreground text-center mb-14 max-w-xl mx-auto">
            We aggregate signals from the platforms that matter most in fashion.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {sources.map((src) => (
              <div key={src.name} className="p-6 rounded-2xl bg-background border border-border text-center hover:border-purple-500/30 transition-colors">
                <div className="inline-flex p-3 rounded-xl bg-purple-500/10 mb-4">
                  <src.icon className="h-6 w-6 text-purple-400" />
                </div>
                <h3 className="font-semibold text-sm mb-1">{src.name}</h3>
                <p className="text-xs text-muted-foreground">{src.count}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-4">Simple Pricing</h2>
          <p className="text-muted-foreground text-center mb-14 max-w-xl mx-auto">
            Start free. Upgrade when you&apos;re ready.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`p-6 rounded-2xl border ${
                  plan.highlight
                    ? "border-purple-500 bg-purple-500/5 ring-1 ring-purple-500/20"
                    : "border-border bg-card"
                } relative`}
              >
                {plan.highlight && (
                  <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold px-3 py-1 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                    Most Popular
                  </span>
                )}
                <h3 className="text-lg font-semibold mb-1">{plan.name}</h3>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-sm text-muted-foreground">{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.href}
                  className={`block text-center py-2.5 rounded-xl font-medium text-sm transition-colors ${
                    plan.highlight
                      ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:opacity-90"
                      : "bg-muted text-foreground hover:bg-muted/80"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 bg-card/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Ready to discover what&apos;s{" "}
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">next in fashion</span>?
          </h2>
          <p className="text-muted-foreground mb-8">Join designers using AI to stay ahead of every trend.</p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:opacity-90 transition-opacity"
          >
            Get Started Free <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-12 px-6">
        <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-1.5 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
                <Zap className="h-3.5 w-3.5 text-white" />
              </div>
              <span className="font-bold">TrendMuse</span>
            </div>
            <p className="text-xs text-muted-foreground">AI-powered fashion trend intelligence and design generation.</p>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Product</h4>
            <div className="space-y-2">
              <Link href="/discovery" className="block text-sm text-muted-foreground hover:text-foreground">Trend Discovery</Link>
              <Link href="/dashboard" className="block text-sm text-muted-foreground hover:text-foreground">Dashboard</Link>
              <Link href="/generator" className="block text-sm text-muted-foreground hover:text-foreground">Design Generator</Link>
              <Link href="/scanner" className="block text-sm text-muted-foreground hover:text-foreground">Trend Scanner</Link>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Resources</h4>
            <div className="space-y-2">
              <Link href="/help" className="block text-sm text-muted-foreground hover:text-foreground">Help Center</Link>
              <Link href="/settings" className="block text-sm text-muted-foreground hover:text-foreground">Settings</Link>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold mb-3">Account</h4>
            <div className="space-y-2">
              <Link href="/login" className="block text-sm text-muted-foreground hover:text-foreground">Sign In</Link>
              <Link href="/register" className="block text-sm text-muted-foreground hover:text-foreground">Create Account</Link>
            </div>
          </div>
        </div>
        <div className="max-w-6xl mx-auto mt-8 pt-8 border-t border-border text-center">
          <p className="text-xs text-muted-foreground">© 2025 TrendMuse. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

"use client";

import { Settings, Key, Palette, Bell, Database } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-gray-500 to-slate-600">
            <Settings className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">Configure your TrendMuse experience</p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl space-y-6">
        {/* API Configuration */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-primary/20">
              <Key className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">API Configuration</h2>
              <p className="text-sm text-muted-foreground">Connect to AI services</p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Replicate API Token</label>
              <input
                type="password"
                placeholder="Enter your Replicate API token"
                className="w-full px-4 py-3 rounded-xl bg-background border border-input focus:border-primary focus:outline-none"
              />
              <p className="text-xs text-muted-foreground mt-2">
                Required for real AI image generation. Get one at{" "}
                <a href="https://replicate.com" target="_blank" rel="noopener" className="text-primary hover:underline">
                  replicate.com
                </a>
              </p>
            </div>
          </div>
        </div>

        {/* Theme */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-purple-500/20">
              <Palette className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Appearance</h2>
              <p className="text-sm text-muted-foreground">Customize the look and feel</p>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm">Dark Mode</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">On</span>
              <div className="w-12 h-6 bg-primary rounded-full relative">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
              </div>
            </div>
          </div>
        </div>

        {/* Data */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg bg-blue-500/20">
              <Database className="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Data Management</h2>
              <p className="text-sm text-muted-foreground">Manage your saved data</p>
            </div>
          </div>
          
          <div className="space-y-3">
            <button className="w-full px-4 py-3 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-left">
              Clear Scanned Items
            </button>
            <button className="w-full px-4 py-3 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-left">
              Clear Generated Designs
            </button>
            <button className="w-full px-4 py-3 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors text-left">
              Clear Sketches
            </button>
            <button className="w-full px-4 py-3 rounded-xl bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-left">
              Clear All Data
            </button>
          </div>
        </div>

        {/* Version Info */}
        <div className="p-4 rounded-xl bg-muted text-center">
          <p className="text-sm text-muted-foreground">
            TrendMuse v1.0.0 • Demo Mode Active
          </p>
        </div>
      </div>
    </div>
  );
}

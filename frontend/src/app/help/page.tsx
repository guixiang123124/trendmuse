"use client";

import { HelpCircle, TrendingUp, Sparkles, PenTool, Zap, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function HelpPage() {
  const faqs = [
    {
      question: "How does the Trend Scanner work?",
      answer: "The Trend Scanner analyzes fashion e-commerce websites to identify trending styles. It scrapes product data including images, prices, reviews, and sales counts, then calculates a trend score based on these metrics. In demo mode, it uses sample fashion data."
    },
    {
      question: "What is the Design Generator?",
      answer: "The Design Generator uses AI to create variations of fashion pieces. You select a source image and style parameters, and it generates new design variations. In demo mode, placeholder images are shown. With a Replicate API key, it uses Stable Diffusion for actual generation."
    },
    {
      question: "How does the Sketch Converter work?",
      answer: "The Sketch Converter transforms fashion photos into sketch-style illustrations. It currently uses image processing techniques like edge detection. With ControlNet integration, it can produce higher quality fashion sketches."
    },
    {
      question: "What is Demo Mode?",
      answer: "Demo Mode runs without API keys, using sample data and placeholder images. It's perfect for exploring the UI and understanding the workflow. To enable real AI features, add a Replicate API token."
    },
    {
      question: "How do I enable real AI generation?",
      answer: "Get a Replicate API token from replicate.com, then set it as REPLICATE_API_TOKEN in the backend .env file. The app will automatically switch to production mode."
    }
  ];

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500">
            <HelpCircle className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Help & Documentation</h1>
            <p className="text-muted-foreground">Learn how to use TrendMuse</p>
          </div>
        </div>
      </div>

      <div className="max-w-4xl">
        {/* Quick Start */}
        <div className="mb-8 p-6 rounded-2xl bg-gradient-to-br from-primary/10 to-accent/10 border border-primary/20">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            Quick Start Guide
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link href="/scanner" className="p-4 rounded-xl bg-card hover:bg-muted transition-colors">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-pink-500/20">
                  <TrendingUp className="h-5 w-5 text-pink-500" />
                </div>
                <span className="font-medium">1. Scan Trends</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Start by scanning a fashion website or loading demo data
              </p>
            </Link>
            <Link href="/generator" className="p-4 rounded-xl bg-card hover:bg-muted transition-colors">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-purple-500/20">
                  <Sparkles className="h-5 w-5 text-purple-500" />
                </div>
                <span className="font-medium">2. Generate Designs</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Select items and create AI-powered variations
              </p>
            </Link>
            <Link href="/converter" className="p-4 rounded-xl bg-card hover:bg-muted transition-colors">
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <PenTool className="h-5 w-5 text-blue-500" />
                </div>
                <span className="font-medium">3. Create Sketches</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Convert any image to professional fashion sketches
              </p>
            </Link>
          </div>
        </div>

        {/* FAQs */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Frequently Asked Questions</h2>
          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="p-4 rounded-xl bg-card border border-border">
                <h3 className="font-medium mb-2">{faq.question}</h3>
                <p className="text-sm text-muted-foreground">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Resources */}
        <div className="p-6 rounded-2xl bg-card border border-border">
          <h2 className="text-lg font-semibold mb-4">Resources</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <a
              href="https://replicate.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
            >
              <ExternalLink className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">Replicate</p>
                <p className="text-sm text-muted-foreground">AI model hosting</p>
              </div>
            </a>
            <a
              href="https://fastapi.tiangolo.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 p-4 rounded-xl bg-muted hover:bg-muted/80 transition-colors"
            >
              <ExternalLink className="h-5 w-5 text-muted-foreground" />
              <div>
                <p className="font-medium">FastAPI Docs</p>
                <p className="text-sm text-muted-foreground">Backend framework</p>
              </div>
            </a>
          </div>
        </div>

        {/* API Docs Link */}
        <div className="mt-6 p-4 rounded-xl bg-muted text-center">
          <p className="text-sm text-muted-foreground">
            Backend API documentation available at{" "}
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener" className="text-primary hover:underline">
              localhost:8000/docs
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

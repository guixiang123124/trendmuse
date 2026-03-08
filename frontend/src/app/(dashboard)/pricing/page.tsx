"use client";

import { useState } from "react";
import { 
  Check, 
  Zap, 
  Star,
  ArrowRight,
  Sparkles,
  BarChart3,
  Globe,
  Crown,
  CreditCard
} from "lucide-react";
import { apiUrl } from "@/lib/api";

interface PricingTier {
  id: string;
  name: string;
  description: string;
  price: {
    monthly: number;
    annual: number;
  };
  priceIds: {
    monthly: string;
    annual: string;
  };
  features: string[];
  popular?: boolean;
  icon: any;
  gradient: string;
}

const pricingTiers: PricingTier[] = [
  {
    id: "free",
    name: "Free",
    description: "Perfect for trying out TrendMuse",
    price: { monthly: 0, annual: 0 },
    priceIds: { monthly: "", annual: "" },
    features: [
      "50 design credits/month",
      "Basic trend analysis",
      "3 design generations/day",
      "Standard support",
      "Trend discovery access"
    ],
    icon: Sparkles,
    gradient: "from-gray-500 to-gray-600"
  },
  {
    id: "pro",
    name: "Pro",
    description: "Best for fashion designers & small teams",
    price: { monthly: 19, annual: 182.40 },
    priceIds: { 
      monthly: "price_1T8V4SGSVXwaPFBEtTmydTHl", 
      annual: "price_1T8V4SGSVXwaPFBEnSZVoN6V" 
    },
    features: [
      "500 design credits/month",
      "Advanced trend analytics",
      "Unlimited design generations",
      "Priority support",
      "AI design variations",
      "Export in high resolution",
      "Color palette extraction"
    ],
    popular: true,
    icon: Star,
    gradient: "from-purple-500 to-violet-600"
  },
  {
    id: "business",
    name: "Business",
    description: "For fashion brands & agencies",
    price: { monthly: 49, annual: 470.40 },
    priceIds: { 
      monthly: "price_1T8V4TGSVXwaPFBEijoJWWai", 
      annual: "price_1T8V4TGSVXwaPFBEGpbLSTKy" 
    },
    features: [
      "2000 design credits/month",
      "Enterprise trend intelligence",
      "Unlimited everything",
      "24/7 priority support",
      "Custom model training",
      "Team collaboration",
      "API access",
      "White-label options"
    ],
    icon: Crown,
    gradient: "from-amber-500 to-orange-600"
  }
];

export default function Pricing() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);

  const calculateSavings = (monthly: number, annual: number) => {
    if (monthly === 0) return 0;
    const annualEquivalent = monthly * 12;
    return Math.round(((annualEquivalent - annual) / annualEquivalent) * 100);
  };

  const handleGetStarted = async (tier: PricingTier) => {
    if (tier.id === "free") {
      // Redirect to signup for free tier
      window.location.href = "/register";
      return;
    }

    // Check if user is logged in first
    const token = localStorage.getItem("token");
    if (!token) {
      // Redirect to login with return URL
      window.location.href = `/login?redirect=/pricing&plan=${tier.id}&billing=${isAnnual ? 'annual' : 'monthly'}`;
      return;
    }

    setLoading(tier.id);
    
    try {
      const priceId = isAnnual ? tier.priceIds.annual : tier.priceIds.monthly;
      const response = await fetch(apiUrl("/api/stripe/create-checkout-session"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Add auth header if user is logged in
          ...(localStorage.getItem("token") && {
            "Authorization": `Bearer ${localStorage.getItem("token")}`
          })
        },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/dashboard?payment=success`,
          cancel_url: `${window.location.origin}/pricing?payment=cancelled`
        })
      });

      if (response.ok) {
        const { url } = await response.json();
        window.location.href = url;
      } else {
        throw new Error("Failed to create checkout session");
      }
    } catch (error) {
      console.error("Checkout error:", error);
      alert("Something went wrong. Please try again or contact support.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen p-8">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="p-3 rounded-xl bg-gradient-fashion">
            <CreditCard className="h-8 w-8 text-white" />
          </div>
        </div>
        <h1 className="text-5xl font-bold gradient-text mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Unlock the full power of AI-driven fashion intelligence. Start free, upgrade as you grow.
        </p>
      </div>

      {/* Billing Toggle */}
      <div className="flex items-center justify-center mb-12">
        <div className="flex items-center gap-4 p-2 rounded-2xl bg-card border border-border">
          <button
            onClick={() => setIsAnnual(false)}
            className={`px-6 py-2 rounded-xl text-sm font-medium transition-all ${
              !isAnnual 
                ? "bg-primary text-primary-foreground shadow-md" 
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setIsAnnual(true)}
            className={`px-6 py-2 rounded-xl text-sm font-medium transition-all relative ${
              isAnnual 
                ? "bg-primary text-primary-foreground shadow-md" 
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Annual
            <span className="absolute -top-2 -right-2 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500 text-white">
              20% OFF
            </span>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-16">
        {pricingTiers.map((tier) => (
          <div
            key={tier.id}
            className={`relative p-8 rounded-3xl border transition-all duration-200 ${
              tier.popular 
                ? "border-primary bg-primary/5 shadow-lg shadow-primary/20 scale-105" 
                : "border-border bg-card hover:border-primary/50 hover:shadow-lg"
            }`}
          >
            {/* Popular Badge */}
            {tier.popular && (
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <div className="bg-gradient-fashion text-white px-6 py-2 rounded-full text-sm font-bold">
                  Most Popular
                </div>
              </div>
            )}

            {/* Icon */}
            <div className={`inline-flex p-3 rounded-2xl bg-gradient-to-br ${tier.gradient} mb-6`}>
              <tier.icon className="h-8 w-8 text-white" />
            </div>

            {/* Header */}
            <div className="mb-6">
              <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
              <p className="text-muted-foreground mb-4">{tier.description}</p>
              
              {/* Price */}
              <div className="flex items-baseline gap-2">
                <span className="text-4xl font-bold">
                  ${isAnnual ? Math.round(tier.price.annual / 12) : tier.price.monthly}
                </span>
                <span className="text-muted-foreground">
                  /{isAnnual ? "month" : "month"}
                </span>
              </div>
              
              {/* Annual Savings */}
              {isAnnual && tier.price.monthly > 0 && (
                <div className="mt-2">
                  <span className="text-sm text-emerald-500 font-medium">
                    Save {calculateSavings(tier.price.monthly, tier.price.annual)}% annually
                  </span>
                  <div className="text-sm text-muted-foreground">
                    ${tier.price.annual}/year
                  </div>
                </div>
              )}
            </div>

            {/* Features */}
            <ul className="space-y-4 mb-8">
              {tier.features.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <Check className="h-5 w-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA Button */}
            <button
              onClick={() => handleGetStarted(tier)}
              disabled={loading === tier.id}
              className={`w-full py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
                tier.popular
                  ? "bg-gradient-fashion text-white hover:shadow-lg hover:shadow-primary/25 disabled:opacity-50"
                  : "bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 disabled:opacity-50"
              }`}
            >
              {loading === tier.id ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-current border-t-transparent" />
              ) : (
                <>
                  {tier.id === "free" ? "Get Started Free" : "Choose Plan"}
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        ))}
      </div>

      {/* Features Comparison */}
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">
          Everything you need to dominate fashion trends
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-teal-500/20 inline-flex mb-4">
              <BarChart3 className="h-10 w-10 text-emerald-500" />
            </div>
            <h3 className="text-xl font-bold mb-3">Trend Intelligence</h3>
            <p className="text-muted-foreground">
              AI-powered analysis of fashion trends from 100+ sources including Google Trends, Amazon, and social media.
            </p>
          </div>
          
          <div className="text-center">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-violet-500/20 inline-flex mb-4">
              <Sparkles className="h-10 w-10 text-purple-500" />
            </div>
            <h3 className="text-xl font-bold mb-3">AI Design Generation</h3>
            <p className="text-muted-foreground">
              Generate unlimited design variations using state-of-the-art AI models trained on fashion data.
            </p>
          </div>
          
          <div className="text-center">
            <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 inline-flex mb-4">
              <Globe className="h-10 w-10 text-blue-500" />
            </div>
            <h3 className="text-xl font-bold mb-3">Global Market Insights</h3>
            <p className="text-muted-foreground">
              Track trends across international markets and get insights into regional fashion preferences.
            </p>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="max-w-4xl mx-auto mt-16 text-center">
        <h2 className="text-3xl font-bold mb-8">Questions?</h2>
        <p className="text-lg text-muted-foreground mb-6">
          We&apos;re here to help. Contact us for custom enterprise solutions or if you need help choosing the right plan.
        </p>
        <div className="flex items-center justify-center gap-4">
          <button className="px-6 py-3 rounded-xl border border-border text-muted-foreground hover:text-foreground hover:border-primary transition-all">
            Contact Sales
          </button>
          <button className="px-6 py-3 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 transition-all">
            View FAQ
          </button>
        </div>
      </div>
    </div>
  );
}
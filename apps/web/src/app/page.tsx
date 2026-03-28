"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import {
  Network,
  Shield,
  Zap,
  ArrowRight,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Brain,
  GitBranch,
  Layers,
  Sparkles
} from "lucide-react";

function GithubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
    </svg>
  );
}

// Mock data for the floating dashboard
const mockStats = {
  total: 247,
  critical: 12,
  open: 34,
  resolved: 189,
};

const mockIncidents = [
  { id: 1, title: "Database connection pool exhausted", severity: "critical", service: "order-api", time: "2m ago", status: "open" },
  { id: 2, title: "High memory usage on auth-service", severity: "high", service: "auth-service", time: "5m ago", status: "investigating" },
  { id: 3, title: "SSL certificate expiring soon", severity: "medium", service: "gateway", time: "12m ago", status: "acknowledged" },
  { id: 4, title: "Elevated error rate in payments", severity: "high", service: "payments", time: "18m ago", status: "resolved" },
];

const severityColors: Record<string, string> = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-blue-500/20 text-blue-400 border-blue-500/30",
};

const statusColors: Record<string, string> = {
  open: "bg-red-500",
  investigating: "bg-yellow-500",
  acknowledged: "bg-blue-500",
  resolved: "bg-green-500",
};

// Liquid Glass Card Component
function LiquidGlassCard({
  children,
  className = "",
  glowColor = "indigo",
  delay = 0,
  hoverScale = true
}: {
  children: React.ReactNode;
  className?: string;
  glowColor?: "indigo" | "purple" | "pink" | "cyan" | "emerald";
  delay?: number;
  hoverScale?: boolean;
}) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const glowColors = {
    indigo: "from-indigo-500/20 via-indigo-400/10 to-transparent",
    purple: "from-purple-500/20 via-purple-400/10 to-transparent",
    pink: "from-pink-500/20 via-pink-400/10 to-transparent",
    cyan: "from-cyan-500/20 via-cyan-400/10 to-transparent",
    emerald: "from-emerald-500/20 via-emerald-400/10 to-transparent",
  };

  return (
    <div
      className={`
        relative transition-all duration-700 ease-out
        ${mounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 translate-y-8 scale-95"}
        ${hoverScale ? "hover:scale-[1.02]" : ""}
        ${className}
      `}
    >
      {/* Glow effect */}
      <div className={`absolute -inset-1 bg-gradient-to-b ${glowColors[glowColor]} blur-xl rounded-3xl opacity-60`} />

      {/* Glass surface */}
      <div className="relative rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 via-white/5 to-transparent backdrop-blur-2xl shadow-2xl overflow-hidden">
        {/* Inner glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 via-transparent to-transparent pointer-events-none" />
        {children}
      </div>
    </div>
  );
}

// Floating Dashboard Component
function FloatingDashboard() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className={`relative transition-all duration-1000 ease-out ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-16"}`}>
      {/* Multi-layer glow effects */}
      <div className="absolute -inset-8 bg-gradient-to-r from-indigo-600/30 via-purple-600/30 to-pink-600/30 blur-[100px] rounded-full animate-pulse" />
      <div className="absolute -inset-4 bg-gradient-to-r from-cyan-500/20 via-indigo-500/20 to-purple-500/20 blur-3xl rounded-3xl" />

      <LiquidGlassCard glowColor="purple" delay={200} hoverScale={false}>
        {/* Browser chrome */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/10 bg-gradient-to-r from-white/5 to-transparent">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-gradient-to-br from-red-400 to-red-600 shadow-lg shadow-red-500/30" />
            <div className="w-3 h-3 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 shadow-lg shadow-yellow-500/30" />
            <div className="w-3 h-3 rounded-full bg-gradient-to-br from-green-400 to-green-600 shadow-lg shadow-green-500/30" />
          </div>
          <div className="flex-1 flex justify-center">
            <div className="px-4 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-white/50 font-mono backdrop-blur">
              opsmesh.io/dashboard
            </div>
          </div>
        </div>

        {/* Dashboard content */}
        <div className="p-5 space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
                <Network className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-semibold text-lg">OpsMesh</span>
            </div>
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-xs text-emerald-400 backdrop-blur">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-lg shadow-emerald-400/50" />
              Live
            </span>
          </div>

          {/* Stats cards with colorful glass effect */}
          <div className="grid grid-cols-4 gap-3">
            {[
              { icon: Activity, label: "Total", value: mockStats.total, color: "from-slate-500/20 to-slate-600/10", text: "text-white", border: "border-white/10" },
              { icon: AlertTriangle, label: "Critical", value: mockStats.critical, color: "from-red-500/30 to-red-600/10", text: "text-red-400", border: "border-red-500/30" },
              { icon: Clock, label: "Open", value: mockStats.open, color: "from-amber-500/30 to-amber-600/10", text: "text-amber-400", border: "border-amber-500/30" },
              { icon: CheckCircle2, label: "Resolved", value: mockStats.resolved, color: "from-emerald-500/30 to-emerald-600/10", text: "text-emerald-400", border: "border-emerald-500/30" },
            ].map((stat, i) => (
              <div key={i} className={`p-3 rounded-xl bg-gradient-to-br ${stat.color} border ${stat.border} backdrop-blur-xl`}>
                <div className={`flex items-center gap-1.5 ${stat.text} text-xs mb-1 opacity-80`}>
                  <stat.icon className="w-3.5 h-3.5" /> {stat.label}
                </div>
                <div className={`text-2xl font-bold ${stat.text}`}>{stat.value}</div>
              </div>
            ))}
          </div>

          {/* Incidents table */}
          <div className="rounded-xl border border-white/10 overflow-hidden bg-gradient-to-br from-white/5 to-transparent backdrop-blur-xl">
            <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between bg-white/5">
              <span className="text-sm font-medium text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                Recent Incidents
              </span>
              <span className="text-xs text-white/40">Live feed</span>
            </div>
            <div className="divide-y divide-white/5">
              {mockIncidents.map((incident, idx) => (
                <div
                  key={incident.id}
                  className="px-4 py-3 flex items-center gap-4 hover:bg-white/5 transition-colors"
                  style={{ animationDelay: `${idx * 100}ms` }}
                >
                  <div className={`w-2 h-2 rounded-full ${statusColors[incident.status]} shadow-lg`} style={{ boxShadow: `0 0 8px ${statusColors[incident.status].replace('bg-', '')}` }} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white truncate">{incident.title}</div>
                    <div className="text-xs text-white/40">{incident.service}</div>
                  </div>
                  <span className={`px-2 py-0.5 rounded-md text-xs border backdrop-blur ${severityColors[incident.severity]}`}>
                    {incident.severity}
                  </span>
                  <span className="text-xs text-white/40 w-14 text-right">{incident.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </LiquidGlassCard>

      {/* Floating AI Card */}
      <div className={`absolute -right-8 top-1/4 transition-all duration-1000 delay-500 ${mounted ? "opacity-100 translate-x-0 rotate-0" : "opacity-0 translate-x-12 rotate-6"}`}>
        <LiquidGlassCard glowColor="pink" delay={600} className="w-56">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-pink-500 via-purple-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-pink-500/30">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-white">AI Insight</span>
            </div>
            <p className="text-xs text-white/60 leading-relaxed mb-3">
              Connection pool exhausted due to <span className="text-cyan-400">slow query</span> on orders table.
            </p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                <div className="h-full w-[94%] rounded-full bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 animate-pulse" />
              </div>
              <span className="text-xs text-purple-400 font-medium">94%</span>
            </div>
          </div>
        </LiquidGlassCard>
      </div>

      {/* Floating Metrics Card */}
      <div className={`absolute -left-8 bottom-1/4 transition-all duration-1000 delay-700 ${mounted ? "opacity-100 translate-x-0 -rotate-0" : "opacity-0 -translate-x-12 -rotate-6"}`}>
        <LiquidGlassCard glowColor="emerald" delay={800} className="w-44">
          <div className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <span className="text-xs font-medium text-white/70">MTTR</span>
            </div>
            <div className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">-42%</div>
            <div className="text-xs text-white/40 mt-1">vs last month</div>
          </div>
        </LiquidGlassCard>
      </div>
    </div>
  );
}

// Tree/Vortex Feature Cards
function FeatureVortex() {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.2 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  const features = [
    {
      icon: <Layers className="w-6 h-6" />,
      title: "Smart Clustering",
      description: "Fingerprint-based deduplication groups related incidents automatically. See 100 alerts as 1 actionable cluster.",
      gradient: "from-indigo-500 via-blue-500 to-cyan-500",
      glowColor: "indigo" as const,
      stats: { value: "90%", label: "Noise Reduced" }
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Severity Scoring",
      description: "ML-powered scoring based on service criticality, blast radius, time patterns, and historical impact data.",
      gradient: "from-purple-500 via-pink-500 to-rose-500",
      glowColor: "purple" as const,
      stats: { value: "0.3s", label: "Score Time" }
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "AI Root Cause",
      description: "GPT-4 powered analysis with confidence scores, suggested actions, and prevention recommendations.",
      gradient: "from-amber-500 via-orange-500 to-red-500",
      glowColor: "pink" as const,
      stats: { value: "94%", label: "Accuracy" }
    },
  ];

  return (
    <div ref={ref} className="relative">
      {/* Central connecting line with glow */}
      <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-white/20 to-transparent" />

      {/* Vortex glow effect */}
      <div className={`absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] transition-all duration-1000 ${isVisible ? "opacity-100 scale-100" : "opacity-0 scale-50"}`}>
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/20 via-purple-600/20 to-pink-600/20 rounded-full blur-[100px] animate-spin" style={{ animationDuration: "20s" }} />
      </div>

      <div className="relative space-y-8">
        {features.map((feature, index) => {
          const isLeft = index % 2 === 0;
          const rotation = isLeft ? "-rotate-1" : "rotate-1";
          const translateX = isLeft ? "-translate-x-4" : "translate-x-4";

          return (
            <div
              key={index}
              className={`
                flex items-center gap-8
                ${isLeft ? "flex-row" : "flex-row-reverse"}
              `}
            >
              {/* Feature Card */}
              <div
                className={`
                  flex-1 transition-all duration-700 ease-out
                  ${isVisible ? `opacity-100 ${translateX} ${rotation}` : "opacity-0 translate-y-12"}
                `}
                style={{ transitionDelay: `${index * 200}ms` }}
              >
                <LiquidGlassCard glowColor={feature.glowColor} delay={index * 200}>
                  <div className="p-8">
                    <div className="flex items-start justify-between mb-6">
                      <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-2xl`}>
                        {feature.icon}
                      </div>
                      <div className="text-right">
                        <div className={`text-3xl font-bold bg-gradient-to-r ${feature.gradient} bg-clip-text text-transparent`}>
                          {feature.stats.value}
                        </div>
                        <div className="text-xs text-white/40">{feature.stats.label}</div>
                      </div>
                    </div>
                    <h3 className="text-2xl font-bold text-white mb-3">{feature.title}</h3>
                    <p className="text-white/50 leading-relaxed">{feature.description}</p>

                    {/* Decorative bottom bar */}
                    <div className={`mt-6 h-1 rounded-full bg-gradient-to-r ${feature.gradient} opacity-50`} />
                  </div>
                </LiquidGlassCard>
              </div>

              {/* Center Node */}
              <div
                className={`
                  relative w-16 h-16 flex-shrink-0 transition-all duration-500
                  ${isVisible ? "opacity-100 scale-100" : "opacity-0 scale-0"}
                `}
                style={{ transitionDelay: `${index * 200 + 100}ms` }}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} rounded-full blur-xl opacity-50 animate-pulse`} />
                <div className={`relative w-full h-full rounded-full bg-gradient-to-br ${feature.gradient} flex items-center justify-center shadow-2xl border border-white/20`}>
                  <GitBranch className="w-6 h-6 text-white" />
                </div>
                {/* Connecting lines */}
                {index < features.length - 1 && (
                  <div className="absolute top-full left-1/2 w-px h-8 bg-gradient-to-b from-white/30 to-transparent -translate-x-1/2" />
                )}
              </div>

              {/* Spacer for alternating layout */}
              <div className="flex-1" />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#020203] text-white overflow-hidden">
      {/* Animated gradient background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-[800px] h-[800px] bg-indigo-600/20 rounded-full blur-[150px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-600/15 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/3 right-1/3 w-[400px] h-[400px] bg-pink-600/10 rounded-full blur-[120px] animate-pulse" style={{ animationDelay: "2s" }} />
        <div className="absolute bottom-1/3 left-1/3 w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[150px] animate-pulse" style={{ animationDelay: "1.5s" }} />
      </div>

      {/* Subtle grid */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.015]"
        style={{
          backgroundImage: `radial-gradient(circle at center, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: "48px 48px"
        }}
      />

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50">
        <div className="mx-4 mt-4">
          <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 backdrop-blur-2xl">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/20">
                <Network className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight">OpsMesh</span>
            </div>

            <div className="hidden md:flex items-center gap-8 text-sm text-white/50">
              <a href="#features" className="hover:text-white transition">Features</a>
              <a href="#platform" className="hover:text-white transition">Platform</a>
              <a href="https://github.com/saifhaque18/opsmesh" target="_blank" rel="noreferrer" className="flex items-center gap-2 hover:text-white transition">
                <GithubIcon className="w-4 h-4" /> GitHub
              </a>
            </div>

            <div className="flex items-center gap-2">
              <Link href="/login" className="text-sm text-white/60 hover:text-white transition px-4 py-2">
                Sign In
              </Link>
              <Link href="/dashboard" className="text-sm font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-4 py-2 rounded-xl hover:opacity-90 transition shadow-lg shadow-purple-500/20">
                Dashboard
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-36 pb-24 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-20 items-center">
            {/* Left content */}
            <div className="relative z-10">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 text-sm text-indigo-300 mb-8 backdrop-blur">
                <Zap className="w-4 h-4 text-yellow-400" />
                <span>AI-Powered Incident Intelligence</span>
              </div>

              <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.05] mb-8">
                <span className="text-white">See Through</span>
                <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 animate-gradient">
                  Alert Chaos
                </span>
              </h1>

              <p className="text-xl text-white/40 max-w-lg mb-12 leading-relaxed">
                OpsMesh clusters duplicates, scores severity in real-time,
                and delivers AI root cause analysis—so your team resolves faster.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/dashboard"
                  className="group flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-8 py-4 rounded-2xl font-semibold hover:opacity-90 transition shadow-2xl shadow-purple-500/25"
                >
                  Launch Dashboard
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
                <a
                  href="https://github.com/saifhaque18/opsmesh"
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-center gap-2 px-8 py-4 rounded-2xl font-semibold border border-white/10 bg-white/5 hover:bg-white/10 transition backdrop-blur-xl"
                >
                  <GithubIcon className="w-5 h-5" />
                  Star on GitHub
                </a>
              </div>

              {/* Stats */}
              <div className="mt-16 flex items-center gap-8">
                {[
                  { value: "90%", label: "Less Noise" },
                  { value: "10x", label: "Faster MTTR" },
                  { value: "24/7", label: "AI Analysis" },
                ].map((stat, i) => (
                  <div key={i} className="relative">
                    <div className="text-3xl font-bold bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">{stat.value}</div>
                    <div className="text-sm text-white/30">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Floating Dashboard */}
            <div className="relative lg:pl-8">
              <FloatingDashboard />
            </div>
          </div>
        </div>
      </section>

      {/* Features Vortex Section */}
      <section id="features" className="relative py-32 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-6xl font-bold mb-6">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                Intelligence Pipeline
              </span>
            </h2>
            <p className="text-xl text-white/40 max-w-2xl mx-auto">
              Every alert flows through our AI-powered pipeline, transforming chaos into clarity.
            </p>
          </div>

          <FeatureVortex />
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-6">
        <div className="max-w-4xl mx-auto">
          <LiquidGlassCard glowColor="purple" delay={0} hoverScale={false}>
            <div className="p-12 md:p-16 text-center relative overflow-hidden">
              {/* Background decoration */}
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 via-purple-500/5 to-pink-500/5" />
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[100px]" />

              <div className="relative z-10">
                <h2 className="text-4xl md:text-5xl font-bold mb-6">
                  Ready to clear the noise?
                </h2>
                <p className="text-lg text-white/40 mb-10 max-w-lg mx-auto">
                  Deploy OpsMesh in minutes. Open-source, self-hosted, and built for modern SRE teams.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                  <Link
                    href="/dashboard"
                    className="flex items-center gap-2 bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-8 py-4 rounded-2xl font-semibold hover:opacity-90 transition shadow-2xl shadow-purple-500/25"
                  >
                    Get Started Free <ArrowRight className="w-5 h-5" />
                  </Link>
                  <a
                    href="https://github.com/saifhaque18/opsmesh"
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-2 px-8 py-4 rounded-2xl font-semibold border border-white/10 hover:bg-white/5 transition"
                  >
                    <GithubIcon className="w-5 h-5" /> View Source
                  </a>
                </div>
              </div>
            </div>
          </LiquidGlassCard>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-12 px-6 bg-black/20 backdrop-blur">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
              <Network className="w-3 h-3 text-white" />
            </div>
            <span className="text-sm text-white/30">© 2025 OpsMesh. Built by Saiful Haque.</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-white/30">
            <a href="https://github.com/saifhaque18/opsmesh" target="_blank" rel="noreferrer" className="hover:text-white transition">GitHub</a>
            <a href="#" className="hover:text-white transition">Docs</a>
          </div>
        </div>
      </footer>

      {/* CSS for gradient animation */}
      <style jsx global>{`
        @keyframes gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        .animate-gradient {
          background-size: 200% 200%;
          animation: gradient 3s ease infinite;
        }
      `}</style>
    </div>
  );
}

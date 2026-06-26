import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ChevronRight,
  Cpu,
  Check,
  ChevronDown,
  Info,
  Server,
  Layers,
  HelpCircle,
  MapPin,
  Clock,
  Coins,
  BrainCircuit,
  Database,
  Workflow,
  Sliders,
  Circle,
} from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { fadeInUp, stagger } from '../utils/animations'

const NAV_ITEMS = [
  { label: 'Overview', id: 'overview' },
  { label: 'Why RouteMind', id: 'why-routemind' },
  { label: 'How Routing Works', id: 'how-routing-works' },
  { label: 'Supported Models', id: 'supported-models' },
  { label: 'Decision Factors', id: 'decision-factors' },
  { label: 'Architecture', id: 'architecture' },
  { label: 'FAQ', id: 'faq' },
  { label: 'Future Roadmap', id: 'roadmap' },
]

const Documentation = () => {
  const [activeSection, setActiveSection] = useState('overview')
  const [expandedFaq, setExpandedFaq] = useState(null)
  const observerRef = useRef(null)

  // IntersectionObserver: auto-update active section on scroll
  useEffect(() => {
    const sectionEls = NAV_ITEMS.map(({ id }) => document.getElementById(id)).filter(Boolean)

    observerRef.current = new IntersectionObserver(
      (entries) => {
        // Find the topmost visible section
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible.length > 0) {
          setActiveSection(visible[0].target.id)
        }
      },
      { rootMargin: '-80px 0px -60% 0px', threshold: 0 }
    )

    sectionEls.forEach((el) => observerRef.current.observe(el))

    return () => {
      if (observerRef.current) observerRef.current.disconnect()
    }
  }, [])

  const toggleFaq = (idx) => {
    setExpandedFaq(expandedFaq === idx ? null : idx)
  }

  const handleNavClick = (id) => {
    setActiveSection(id)
    const element = document.getElementById(id)
    if (element) {
      const offset = 100
      const bodyRect = document.body.getBoundingClientRect().top
      const elementRect = element.getBoundingClientRect().top
      const elementPosition = elementRect - bodyRect
      const offsetPosition = elementPosition - offset
      window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
    }
  }

  return (
    <div className="min-h-screen bg-app-bg text-primary flex flex-col font-sans selection:bg-blue-600/30 selection:text-white relative overflow-x-hidden">
      <Navbar />

      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-blue-600/5 blur-[120px] rounded-full pointer-events-none -z-10"></div>

      <div className="max-w-[1100px] w-full mx-auto px-6 py-12 md:py-20 flex-1 flex flex-col md:flex-row gap-12 relative items-start">
        {/* Sticky Sidebar Navigation (Desktop) */}
        <aside
          className="w-full md:w-[220px] shrink-0 sticky top-28 hidden md:block select-none"
          aria-label="Documentation sections"
        >
          <div className="space-y-6">
            <div>
              <span className="text-[10px] font-mono text-secondary font-semibold tracking-wider uppercase block mb-3">
                Product Docs
              </span>
              <nav className="flex flex-col space-y-1.5 border-l border-border-app/40 pl-3">
                {NAV_ITEMS.map((item) => {
                  const isActive = activeSection === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => handleNavClick(item.id)}
                      className={`text-left text-xs transition-colors duration-150 py-1 cursor-pointer focus:outline-none focus-visible:text-primary ${
                        isActive
                          ? 'text-blue-600 dark:text-blue-400 font-semibold border-l-2 border-blue-500 -ml-[14px] pl-3'
                          : 'text-secondary hover:text-primary'
                      }`}
                    >
                      {item.label}
                    </button>
                  )
                })}
              </nav>
            </div>
          </div>
        </aside>

        {/* Mobile jump bar — fixed text-xs (was text-[11px], below 12px a11y floor) */}
        <div className="w-full md:hidden py-2 px-1 border-b border-border-app bg-card-bg/60 backdrop-blur-md sticky top-[76px] z-20 overflow-x-auto scrollbar-none flex gap-2 shrink-0 select-none">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`px-3 py-1 rounded-full text-xs font-mono whitespace-nowrap border shrink-0 transition-colors ${
                activeSection === item.id
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-card-bg border-border-app text-secondary'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        {/* Main Content */}
        <main className="flex-1 space-y-24 md:space-y-32 max-w-[800px] w-full min-w-0">
          {/* SECTION 1: Overview */}
          <motion.section
            id="overview"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-4 text-left ScrollTarget"
          >
            <motion.div
              variants={fadeInUp}
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
            >
              <Info size={11} /> Overview
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
            >
              What is RouteMind?
            </motion.h2>
            <motion.div
              variants={fadeInUp}
              className="space-y-4 text-sm sm:text-[15px] text-secondary leading-relaxed font-medium"
            >
              <p>
                RouteMind is an AI model routing platform that automatically selects the best AI
                model for a user's task.
              </p>
              <p>
                Instead of manually choosing between Gemini, Groq, NVIDIA NIM, or OpenRouter, users
                simply ask their question and RouteMind handles the decision-making process. The
                goal is to simplify AI usage while improving quality, transparency, and efficiency.
              </p>
            </motion.div>
          </motion.section>

          {/* SECTION 2: Why RouteMind — The Problem */}
          <motion.section
            id="why-routemind"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-4 text-left ScrollTarget"
          >
            <motion.div
              variants={fadeInUp}
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
            >
              <Layers size={11} /> Context Analysis
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
            >
              The Problem
            </motion.h2>

            <motion.div
              variants={fadeInUp}
              className="space-y-4 text-sm sm:text-[15px] text-secondary leading-relaxed font-medium"
            >
              <p>
                Different AI models excel at different tasks. Groq delivers low-latency coding
                responses, Gemini handles million-token document contexts, and NVIDIA NIM provides
                precision reasoning. OpenRouter aggregates free frontier models for cost-sensitive
                tasks.
              </p>
              <p>
                Currently, users must manually decide which model to use before writing a prompt.
                This workflow creates:
              </p>
            </motion.div>

            <motion.ul
              variants={fadeInUp}
              className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs text-primary font-mono select-none"
            >
              {[
                'Decision fatigue',
                'Fragmented workflows',
                'Unnecessary compute cost',
                'Complex user experiences',
              ].map((label) => (
                <li
                  key={label}
                  className="flex items-center gap-2 bg-card-bg border border-border-app p-3 rounded-lg"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500 shrink-0 animate-pulse"></span>
                  <span>{label}</span>
                </li>
              ))}
            </motion.ul>

            <motion.p variants={fadeInUp} className="text-xs text-secondary leading-normal pt-2">
              RouteMind removes this burden by serving as an intelligent middleware layer that
              intercepts prompt intent and routes dynamically.
            </motion.p>
          </motion.section>

          {/* SECTION 3: How Routing Works */}
          <motion.section
            id="how-routing-works"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-6 text-left ScrollTarget"
          >
            <div className="space-y-2">
              <motion.div
                variants={fadeInUp}
                className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
              >
                <Workflow size={11} /> Operations Flow
              </motion.div>
              <motion.h2
                variants={fadeInUp}
                className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
              >
                The Routing Process
              </motion.h2>
            </div>

            {/* Updated: 6 steps matching actual code pipeline */}
            <motion.div
              variants={fadeInUp}
              className="grid grid-cols-2 sm:grid-cols-6 gap-2 bg-card-bg border border-border-app p-4 rounded-xl text-center select-none font-mono text-[10px]"
            >
              {[
                { step: '01', title: 'Query' },
                { step: '02', title: 'Intent' },
                { step: '03', title: 'Complexity' },
                { step: '04', title: 'Policy' },
                { step: '05', title: 'Provider' },
                { step: '06', title: 'Response' },
              ].map((item, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-2 bg-sidebar-bg/60 border border-border-app/40 rounded-lg"
                >
                  <div className="flex flex-col items-center flex-1">
                    <span className="text-blue-600 dark:text-blue-500 font-bold">{item.step}</span>
                    <span className="text-primary mt-1 text-[9px] uppercase font-semibold">
                      {item.title}
                    </span>
                  </div>
                  {idx < 5 && (
                    <div className="hidden sm:flex items-center text-secondary self-center">
                      <ChevronRight size={12} />
                    </div>
                  )}
                </div>
              ))}
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className="space-y-4 font-mono text-xs text-secondary pt-2"
            >
              <div className="flex gap-4">
                <span className="text-blue-600 dark:text-blue-400 font-bold shrink-0">
                  1. Intent Analysis:
                </span>
                <span>
                  Keyword-based classification maps the prompt to a task type (e.g. coding,
                  research, reasoning, document).
                </span>
              </div>
              <div className="flex gap-4">
                <span className="text-blue-600 dark:text-blue-400 font-bold shrink-0">
                  2. Complexity Detection:
                </span>
                <span>
                  Prompt length and keyword signals determine simple / medium / complex tier, which
                  upgrades or downgrades the routing policy automatically.
                </span>
              </div>
              <div className="flex gap-4">
                <span className="text-blue-600 dark:text-blue-400 font-bold shrink-0">
                  3. Policy Application:
                </span>
                <span>
                  User-selected policy (balanced / speed / cost / quality) is combined with
                  complexity to derive the effective routing strategy.
                </span>
              </div>
              <div className="flex gap-4">
                <span className="text-blue-600 dark:text-blue-400 font-bold shrink-0">
                  4. Multi-Factor Scoring:
                </span>
                <span>
                  Each healthy provider is scored: 35% specialization capability + 20% latency + 15%
                  cost + 15% health + 15% historical success rate.
                </span>
              </div>
              <div className="flex gap-4">
                <span className="text-blue-600 dark:text-blue-400 font-bold shrink-0">
                  5. Response &amp; Explanation:
                </span>
                <span>
                  Delivers output alongside routing metadata: provider, model, confidence score, and
                  reason.
                </span>
              </div>
            </motion.div>
          </motion.section>

          {/* SECTION 4: Supported Models — updated to match router.py exactly */}
          <motion.section
            id="supported-models"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-4 text-left ScrollTarget"
          >
            <motion.div
              variants={fadeInUp}
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
            >
              <Cpu size={11} /> Model Ecosystem
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
            >
              Current Model Ecosystem
            </motion.h2>
            <motion.p variants={fadeInUp} className="text-secondary text-sm leading-relaxed">
              RouteMind is completely provider-agnostic. Models are assigned per routing policy
              (balanced / speed / cost / quality) and selected dynamically based on health and
              scoring.
            </motion.p>

            <motion.div
              variants={fadeInUp}
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 font-mono text-xs select-none"
            >
              {/* Gemini */}
              <div className="p-4 bg-card-bg border border-border-app rounded-xl space-y-2">
                <span className="text-secondary uppercase tracking-wider text-[9px]">
                  Google Gemini
                </span>
                <ul className="space-y-1 text-primary">
                  {[
                    { model: 'gemini-2.5-pro', policy: 'quality' },
                    { model: 'gemini-2.5-flash', policy: 'balanced' },
                    { model: 'gemini-2.5-flash-lite', policy: 'speed / cost' },
                  ].map(({ model, policy }) => (
                    <li key={model} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0"></span>
                        <span>{model}</span>
                      </span>
                      <span className="text-[9px] text-secondary">{policy}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Groq */}
              <div className="p-4 bg-card-bg border border-border-app rounded-xl space-y-2">
                <span className="text-secondary uppercase tracking-wider text-[9px]">Groq</span>
                <ul className="space-y-1 text-primary">
                  {[
                    { model: 'llama-3.3-70b-versatile', policy: 'balanced / quality' },
                    { model: 'llama-3.1-8b-instant', policy: 'speed / cost' },
                  ].map(({ model, policy }) => (
                    <li key={model} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-orange-500 shrink-0"></span>
                        <span>{model}</span>
                      </span>
                      <span className="text-[9px] text-secondary">{policy}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* NVIDIA NIM */}
              <div className="p-4 bg-card-bg border border-border-app rounded-xl space-y-2">
                <span className="text-secondary uppercase tracking-wider text-[9px]">
                  NVIDIA NIM
                </span>
                <ul className="space-y-1 text-primary">
                  {[
                    { model: 'meta/llama-3.1-70b-instruct', policy: 'balanced / quality' },
                    { model: 'meta/llama-3.1-8b-instruct', policy: 'speed / cost' },
                  ].map(({ model, policy }) => (
                    <li key={model} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-green-500 shrink-0"></span>
                        <span>{model}</span>
                      </span>
                      <span className="text-[9px] text-secondary">{policy}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* OpenRouter */}
              <div className="p-4 bg-card-bg border border-border-app rounded-xl space-y-2">
                <span className="text-secondary uppercase tracking-wider text-[9px]">
                  OpenRouter (Free tier)
                </span>
                <ul className="space-y-1 text-primary">
                  {[
                    { model: 'deepseek/deepseek-r1-0528:free', policy: 'quality' },
                    { model: 'qwen/qwen3-coder:free', policy: 'balanced' },
                    { model: 'cohere/north-mini-code:free', policy: 'speed / cost' },
                  ].map(({ model, policy }) => (
                    <li key={model} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-1.5 rounded-full bg-purple-500 shrink-0"></span>
                        <span className="break-all">{model}</span>
                      </span>
                      <span className="text-[9px] text-secondary shrink-0">{policy}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </motion.section>

          {/* SECTION 5: Decision Factors */}
          <motion.section
            id="decision-factors"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-4 text-left ScrollTarget"
          >
            <motion.div
              variants={fadeInUp}
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
            >
              <Sliders size={11} /> Decision Engine
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
            >
              How RouteMind Chooses Models
            </motion.h2>
            <motion.p variants={fadeInUp} className="text-secondary text-sm leading-relaxed">
              Every routing decision is a composite score across five weighted factors:
            </motion.p>

            <motion.div
              variants={fadeInUp}
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 font-mono text-xs select-none"
            >
              <div className="p-3 bg-card-bg border border-border-app rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                  <BrainCircuit size={13} />
                  <span className="font-semibold text-primary">Specialization (35%)</span>
                </div>
                <p className="text-[10px] text-secondary leading-normal">
                  Per-intent capability weights — e.g. Groq scores 100 for coding, Gemini scores 100
                  for research.
                </p>
              </div>
              <div className="p-3 bg-card-bg border border-border-app rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400">
                  <Clock size={13} />
                  <span className="font-semibold text-primary">Latency Score (20%)</span>
                </div>
                <p className="text-[10px] text-secondary leading-normal">
                  Derived from live health-monitor latency readings. 100 = fastest, 0 = slowest.
                </p>
              </div>
              <div className="p-3 bg-card-bg border border-border-app rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                  <Coins size={13} />
                  <span className="font-semibold text-primary">Cost Score (15%)</span>
                </div>
                <p className="text-[10px] text-secondary leading-normal">
                  Free models score 100, premium frontier models score lower. Balances quality vs
                  spend.
                </p>
              </div>
              <div className="p-3 bg-card-bg border border-border-app rounded-xl space-y-1.5">
                <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
                  <Database size={13} />
                  <span className="font-semibold text-primary">Health + Success (30%)</span>
                </div>
                <p className="text-[10px] text-secondary leading-normal">
                  Live health-check status (15%) and historical request success rate (15%) prevent
                  routing to flaky providers.
                </p>
              </div>
            </motion.div>
          </motion.section>

          {/* SECTION 6: Architecture — expanded to match actual backend */}
          <motion.section
            id="architecture"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-6 text-left ScrollTarget"
          >
            <div className="space-y-2">
              <motion.div
                variants={fadeInUp}
                className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
              >
                <Server size={11} /> Topology Diagram
              </motion.div>
              <motion.h2
                variants={fadeInUp}
                className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
              >
                System Architecture
              </motion.h2>
            </div>

            {/* Updated: shows actual pipeline steps from backend code */}
            <motion.div
              variants={fadeInUp}
              className="p-5 bg-card-bg border border-border-app rounded-xl space-y-4 select-none font-mono text-[10px] text-center overflow-x-auto"
            >
              <div className="grid grid-cols-2 sm:grid-cols-7 gap-2 items-center min-w-[560px]">
                <div className="p-2 bg-sidebar-bg border border-border-app rounded font-semibold text-secondary">
                  User
                </div>
                <div className="text-secondary text-center">──&gt;</div>
                <div className="p-2 bg-blue-100 dark:bg-blue-950/20 border border-blue-300 dark:border-blue-500/20 text-blue-700 dark:text-blue-400 rounded font-semibold">
                  Intent Classifier
                </div>
                <div className="text-secondary text-center">──&gt;</div>
                <div className="p-2 bg-purple-100 dark:bg-purple-950/20 border border-purple-300 dark:border-purple-500/20 text-purple-700 dark:text-purple-400 rounded font-semibold">
                  Policy Router
                </div>
                <div className="text-secondary text-center">──&gt;</div>
                <div className="p-2 bg-green-100 dark:bg-green-950/20 border border-green-300 dark:border-green-500/20 text-green-700 dark:text-green-400 rounded font-semibold">
                  Provider API
                </div>
              </div>
              <div className="text-[9px] text-secondary grid grid-cols-2 sm:grid-cols-7 gap-2 min-w-[560px]">
                <span></span>
                <span></span>
                <span>keyword scoring → task type</span>
                <span></span>
                <span>multi-factor scoring → best model</span>
                <span></span>
                <span>raw tokens + metadata</span>
              </div>
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className="space-y-4 text-sm sm:text-[15px] text-secondary leading-relaxed font-medium"
            >
              <p>
                A query enters the FastAPI backend and is processed by the{' '}
                <strong className="text-primary">Intent Classifier</strong>, which uses keyword
                heuristics to assign a task type (coding, research, reasoning, etc.) and a
                complexity tier (simple / medium / complex). The{' '}
                <strong className="text-primary">Policy Router</strong> then runs multi-factor
                scoring across all healthy providers — weighting specialization, latency, cost, and
                historical reliability — to select the optimal provider and model. The raw response
                is wrapped with routing metadata and returned to the frontend.
              </p>
            </motion.div>
          </motion.section>

          {/* SECTION 7: FAQ — corrected accuracy claim and routing description */}
          <motion.section
            id="faq"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-6 text-left ScrollTarget"
          >
            <div className="space-y-2">
              <motion.div
                variants={fadeInUp}
                className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
              >
                <HelpCircle size={11} /> Knowledge Base
              </motion.div>
              <motion.h2
                variants={fadeInUp}
                className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
              >
                Frequently Asked Questions
              </motion.h2>
            </div>

            <motion.div variants={fadeInUp} className="space-y-3 select-none">
              {[
                {
                  q: 'Why not use Gemini directly?',
                  a: "Gemini is a single model ecosystem. If you need low-latency coding, Groq's Llama 3.3 is often superior. If you need reasoning depth, NVIDIA NIM's Llama 3.1 70b wins. OpenRouter gives you powerful free-tier models for cost-sensitive tasks. RouteMind gives you all specialists under one workflow without managing multiple billing accounts.",
                },
                {
                  q: 'Why not use OpenRouter directly?',
                  a: 'OpenRouter requires you to manually select the target model for every request. RouteMind uses keyword-based intent classification and multi-factor scoring to automate that selection — routing to Groq, Gemini, NVIDIA NIM, or OpenRouter depending on what your task needs.',
                },
                {
                  q: 'How does routing work?',
                  a: 'RouteMind uses a keyword heuristic classifier to detect task type and complexity, then runs a weighted scoring algorithm (specialization + latency + cost + health) across all healthy providers to pick the best model for your request.',
                },
                {
                  q: 'Can I choose a model manually?',
                  a: 'Yes. While RouteMind operates automatically by default, users can adjust preferences or lock models directly from the workspace settings drawer.',
                },
                {
                  q: 'Does RouteMind store my data?',
                  a: 'No. All prompt packages are proxied securely using ephemeral APIs. We do not store, view, or parse user conversation logs for training.',
                },
                {
                  q: 'Will more models be added?',
                  a: 'Yes. We continuously benchmark new frontier open-source and proprietary models and update endpoints as soon as they pass verification. Upcoming additions include self-learning routing and domain-specific provider tuning.',
                },
              ].map((faq, idx) => {
                const isOpen = expandedFaq === idx
                return (
                  <div
                    key={idx}
                    className="bg-card-bg border border-border-app rounded-xl overflow-hidden"
                  >
                    <button
                      onClick={() => toggleFaq(idx)}
                      className="w-full px-5 py-4 flex items-center justify-between text-left text-xs font-semibold text-primary hover:bg-sidebar-bg/40 focus:outline-none focus-visible:bg-sidebar-bg/60 transition-colors cursor-pointer"
                      aria-expanded={isOpen}
                    >
                      <span className="text-primary">{faq.q}</span>
                      <ChevronDown
                        size={14}
                        className={`text-secondary transition-transform duration-200 ${isOpen ? 'rotate-180 text-blue-500' : ''}`}
                      />
                    </button>
                    {isOpen && (
                      <div className="px-5 pb-4 pt-1 text-xs text-secondary leading-relaxed border-t border-border-app/20 bg-sidebar-bg/25">
                        {faq.a}
                      </div>
                    )}
                  </div>
                )
              })}
            </motion.div>
          </motion.section>

          {/* SECTION 8: Future Roadmap — Clock/Circle icons, not Check */}
          <motion.section
            id="roadmap"
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="space-y-4 text-left ScrollTarget"
          >
            <motion.div
              variants={fadeInUp}
              className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 font-mono text-[10px] uppercase font-semibold"
            >
              <MapPin size={11} /> Milestones
            </motion.div>
            <motion.h2
              variants={fadeInUp}
              className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
            >
              What's Next
            </motion.h2>
            <motion.p variants={fadeInUp} className="text-secondary text-sm leading-relaxed">
              We are constantly refining the orchestration tier. Here is our product expansion plan:
            </motion.p>

            <motion.ul
              variants={fadeInUp}
              className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs text-primary font-mono select-none"
            >
              {[
                { title: 'Self-learning routing', status: 'In development', statusColor: 'blue' },
                {
                  title: 'User feedback optimization',
                  status: 'Planning',
                  statusColor: 'secondary',
                },
                { title: 'Domain-specific routing', status: 'Planning', statusColor: 'secondary' },
                { title: 'Enterprise analytics API', status: 'Backlog', statusColor: 'secondary' },
                { title: 'Browser extension package', status: 'Backlog', statusColor: 'secondary' },
                { title: 'Multi-agent workflows', status: 'In development', statusColor: 'blue' },
                { title: 'Custom routing tuning', status: 'Planning', statusColor: 'secondary' },
              ].map((item, idx) => (
                <li
                  key={idx}
                  className="flex items-center justify-between bg-card-bg border border-border-app p-3 rounded-lg"
                >
                  <div className="flex items-center gap-2">
                    {/* Clock for in-development, Circle for planned — not Check (implies done) */}
                    {item.statusColor === 'blue' ? (
                      <Clock size={11} className="text-blue-600 dark:text-blue-400" />
                    ) : (
                      <Circle size={11} className="text-secondary" />
                    )}
                    <span>{item.title}</span>
                  </div>
                  <span
                    className={`text-[8px] px-1.5 py-0.5 rounded border font-semibold uppercase ${
                      item.statusColor === 'blue'
                        ? 'bg-blue-100 dark:bg-blue-950/40 border-blue-300 dark:border-blue-500/20 text-blue-700 dark:text-blue-400'
                        : 'bg-card-bg border-border-app text-secondary'
                    }`}
                  >
                    {item.status}
                  </span>
                </li>
              ))}
            </motion.ul>
          </motion.section>

          {/* FINAL CTA */}
          <motion.section
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: '-100px' }}
            variants={stagger}
            className="text-center max-w-2xl mx-auto space-y-6 py-12 select-none border border-border-app/40 bg-card-bg/30 rounded-2xl p-8 relative"
          >
            <div className="absolute inset-0 bg-blue-500/5 blur-2xl pointer-events-none rounded-2xl"></div>
            <div className="space-y-3">
              <motion.h2
                variants={fadeInUp}
                className="text-2xl sm:text-3xl font-bold tracking-tight text-primary"
              >
                The Future of AI Interaction
              </motion.h2>
              <motion.p variants={fadeInUp} className="text-secondary text-sm leading-relaxed">
                The future is not a single AI model. The future is intelligent orchestration of many
                models working together. RouteMind aims to become the operating system that makes
                this possible.
              </motion.p>
            </div>
            <motion.div variants={fadeInUp} className="flex justify-center pt-2">
              <Link
                to="/chat"
                className="bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm px-6 py-3 rounded-lg border border-blue-500/30 flex items-center gap-1.5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              >
                <span>Start Routing</span>
                <ChevronRight size={15} />
              </Link>
            </motion.div>
          </motion.section>
        </main>
      </div>

      <Footer />
    </div>
  )
}

export default Documentation

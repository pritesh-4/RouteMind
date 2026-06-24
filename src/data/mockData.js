// ==============================
// Sidebar Chat History
// ==============================

export const chatHistory = [
  {
    id: 1,
    title: "Debug React Project",
    lastUpdated: "2 min ago",
  },
  {
    id: 2,
    title: "Research Paper Summary",
    lastUpdated: "15 min ago",
  },
  {
    id: 3,
    title: "System Design Interview",
    lastUpdated: "1 hour ago",
  },
  {
    id: 4,
    title: "RouteMind Architecture",
    lastUpdated: "3 hours ago",
  },
  {
    id: 5,
    title: "Startup Validation Notes",
    lastUpdated: "Yesterday",
  },
];

// ==============================
// Main Chat Messages
// ==============================

export const messages = [
  {
    id: 1,
    role: "user",
    content: "Debug my React useEffect issue",
    timestamp: "10:41 PM",
  },

  {
    id: 2,
    role: "assistant",
    content: `
The issue likely comes from a missing dependency inside your useEffect hook.

Try:

\`\`\`jsx
useEffect(() => {
  fetchData();
}, [userId]);
\`\`\`

This ensures the effect reruns whenever the userId changes.

You should also make sure that fetchData is stable and not recreated on every render.
    `,
    timestamp: "10:42 PM",

    model: "GPT-4o",

    confidence: 92,

    reason:
      "Selected because RouteMind detected a software development and debugging task.",

    showRoutingInfo: true,
  },

  {
    id: 3,
    role: "user",
    content: "Summarize this 120-page AI research paper",
    timestamp: "10:45 PM",
  },

  {
    id: 4,
    role: "assistant",
    content: `
### Research Paper Summary

This paper introduces a scalable architecture for training large multimodal models.

Key Contributions:

- Improved memory efficiency
- Faster training throughput
- Better reasoning performance
- Reduced inference costs

Overall, the paper focuses on making large AI systems more practical for production deployment.
    `,
    timestamp: "10:46 PM",

    model: "Gemini Flash",

    confidence: 95,

    reason:
      "Selected because the task required large-context document understanding.",

    showRoutingInfo: true,
  },
];

// ==============================
// Routing Card Mock Data
// ==============================

export const routingInfo = {
  selectedModel: "GPT-4o",

  confidence: 92,

  qualityScore: 95,

  latencyScore: 88,

  costEfficiency: 89,

  routingScore: 91,

  estimatedCost: "$0.003",

  estimatedSavings: "67%",

  provider: "OpenAI",

  intent: "Coding",

  fallbackModels: [
    "Claude Sonnet",
    "Gemini Flash",
  ],

  reason:
    "GPT-4o was selected because the query involved React debugging and code analysis. It provides the highest coding performance and reliability for this task.",
};

// ==============================
// Typing Indicator Stages
// ==============================

export const routingStages = [
  {
    id: 1,
    stage: "Analyzing Query Structure",
    status: "completed",
  },

  {
    id: 2,
    stage: "Comparing Available Models",
    status: "completed",
  },

  {
    id: 3,
    stage: "Calculating Routing Score",
    status: "active",
  },

  {
    id: 4,
    stage: "Selecting Optimal Provider",
    status: "pending",
  },

  {
    id: 5,
    stage: "Generating Response",
    status: "pending",
  },
];

// ==============================
// Home Page Terminal Demo
// ==============================

export const terminalQueries = [
  {
    id: 1,

    query: "Debug my React application",

    model: "GPT-4o",

    reason: "Best coding performance",

    provider: "OpenAI",
  },

  {
    id: 2,

    query: "Summarize this research paper",

    model: "Gemini Flash",

    reason: "Large context capabilities",

    provider: "Google",
  },

  {
    id: 3,

    query: "Write a product launch announcement",

    model: "Claude Sonnet",

    reason: "Creative writing optimization",

    provider: "Anthropic",
  },

  {
    id: 4,

    query: "Research latest AI developments",

    model: "Search Model",

    reason: "Real-time web access",

    provider: "Search",
  },
];

// ==============================
// Suggested Prompts
// ==============================

export const suggestedPrompts = [
  "Debug my React project",
  "Summarize this research paper",
  "Compare Next.js and Remix",
  "Explain transformers simply",
  "Design a scalable URL shortener",
  "Write a launch announcement",
];

// ==============================
// Today's Routing Stats
// ==============================

export const routingStats = {
  totalQueries: 11,

  models: {
    GPT: 5,
    Claude: 2,
    Gemini: 3,
    Search: 1,
  },
};

export const MODEL_CANDIDATES = ['GPT-4o', 'Claude 3.5 Sonnet', 'Gemini 1.5 Flash', 'DeepSeek Coder', 'Llama 3.1'];

export const ROUTING_STAGES = [
  { id: 'intent', label: 'Analyzing Query Structure' },
  { id: 'compare', label: 'Comparing Available Models' },
  { id: 'cost', label: 'Calculating Routing Score' },
  { id: 'provider', label: 'Selecting Optimal Provider' },
  { id: 'generate', label: 'Generating Response' }
];

export const TERMINAL_EXAMPLES = [
  {
    prompt: 'Debug my React state management synchronization error.',
    steps: ['Analyzing Intent Structures...', 'Comparing Inference Models...', 'Evaluating Memory & Costs...'],
    selectedModel: 'Claude 3.5 Sonnet',
    reason: 'Routed to Claude 3.5 Sonnet due to unmatched React 19 architecture reasoning and code repair accuracy.',
    cost: '$0.0048',
    savings: '62%'
  },
  {
    prompt: 'Summarize the attention mechanism in this 80-page transformers PDF.',
    steps: ['Analyzing Intent Structures...', 'Measuring Context Payload...', 'Evaluating Edge Node Latency...'],
    selectedModel: 'Gemini 1.5 Pro',
    reason: 'Routed to Gemini 1.5 Pro due to 2M token long-context payload capabilities and high semantic retrieval rates.',
    cost: '$0.0015',
    savings: '82%'
  },
  {
    prompt: 'Draft a short, punchy product update tweet for RouteMind v2 launch.',
    steps: ['Analyzing Intent Structures...', 'Comparing Inference Models...', 'Calculating Token Budget...'],
    selectedModel: 'GPT-4o',
    reason: 'Routed to GPT-4o for optimal speed, balanced creative copywriting syntax, and cost-efficient edge processing.',
    cost: '$0.0022',
    savings: '74%'
  }
];
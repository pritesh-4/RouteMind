// Centralized mock data consumed across RouteMind components

export const MODEL_CANDIDATES = [
  'Gemini 2.5 Flash',
  'Llama 3.3 (Groq)',
]

export const ROUTING_STAGES = [
  { id: 'intent', label: 'Analyzing Query Structure' },
  { id: 'compare', label: 'Comparing Available Models' },
  { id: 'cost', label: 'Calculating Routing Score' },
  { id: 'provider', label: 'Selecting Optimal Provider' },
  { id: 'generate', label: 'Generating Response' },
]

export const TERMINAL_EXAMPLES = [
  {
    prompt: 'Debug my React state management synchronization error.',
    steps: [
      'Analyzing Intent Structures...',
      'Comparing Inference Models...',
      'Evaluating Memory & Costs...',
    ],
    selectedModel: 'Llama 3.3 (Groq)',
    reason:
      'Routed to Llama 3.3 (Groq) due to superior code logic evaluation and sub-second generation speeds.',
    cost: '$0.00018',
    savings: '85%',
  },
  {
    prompt: 'Summarize the attention mechanism in this 80-page transformers PDF.',
    steps: [
      'Analyzing Intent Structures...',
      'Measuring Context Payload...',
      'Evaluating Edge Node Latency...',
    ],
    selectedModel: 'Gemini 2.5 Flash',
    reason:
      'Routed to Gemini 2.5 Flash due to high semantic document indexing and optimal cost efficiency.',
    cost: '$0.00006',
    savings: '97%',
  },
  {
    prompt: 'Draft a short, punchy product update tweet for RouteMind v2 launch.',
    steps: [
      'Analyzing Intent Structures...',
      'Comparing Inference Models...',
      'Calculating Token Budget...',
    ],
    selectedModel: 'Gemini 2.5 Flash',
    reason:
      'Routed to Gemini 2.5 Flash for rapid low-overhead creative copywriting and low-cost response packaging.',
    cost: '$0.00001',
    savings: '98%',
  },
]

export const defaultStats = {
  totalQueries: 0,
  savings: 0.0,
  models: {
    'gemini-2.5-flash': 0,
    'llama-3.3-70b-versatile': 0,
  },
}

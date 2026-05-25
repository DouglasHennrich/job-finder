import {
  defineSquad,
  defineTeam,
  defineAgent,
  defineRouting,
} from "@bradygaster/squad-sdk";

export default defineSquad({
  team: defineTeam({
    name: "job-finder",
    agents: [
      defineAgent({
        name: "python-engineer",
        role: "Python Pipeline Engineer",
        status: "active",
        model: "claude-sonnet-4.6",
        capabilities: [
          { name: "Python 3.11+", level: "expert" },
          { name: "pdfplumber", level: "expert" },
          { name: "pipeline orchestration", level: "expert" },
          { name: "python-dotenv", level: "expert" },
          { name: "asyncio", level: "proficient" },
          { name: "launchd", level: "basic" },
        ],
      }),
      defineAgent({
        name: "scraping-engineer",
        role: "Web Scraping Engineer",
        status: "active",
        model: "claude-sonnet-4.6",
        capabilities: [
          { name: "Playwright async", level: "expert" },
          { name: "playwright-stealth", level: "expert" },
          { name: "REST API integration", level: "expert" },
          { name: "Serper.dev", level: "proficient" },
          { name: "HTML DOM parsing", level: "proficient" },
          { name: "anti-bot evasion", level: "proficient" },
        ],
      }),
      defineAgent({
        name: "ai-engineer",
        role: "AI Integration Engineer",
        status: "active",
        model: "claude-sonnet-4.6",
        capabilities: [
          { name: "OpenAI SDK", level: "expert" },
          { name: "prompt engineering", level: "expert" },
          { name: "LLM provider abstraction", level: "expert" },
          { name: "Ollama", level: "proficient" },
          { name: "GitHub Models", level: "proficient" },
          { name: "JSON parsing with fallback", level: "proficient" },
        ],
      }),
      defineAgent({
        name: "obsidian-engineer",
        role: "Obsidian Storage Engineer",
        status: "active",
        model: "claude-haiku-4.5",
        capabilities: [
          { name: "Markdown templating", level: "expert" },
          { name: "Python file I/O", level: "expert" },
          { name: "Obsidian vault conventions", level: "proficient" },
          { name: "YAML frontmatter", level: "proficient" },
          { name: "python-slugify", level: "proficient" },
        ],
      }),
    ],
  }),

  routing: defineRouting({
    strategy: "capability-match",
    rules: [
      {
        pattern:
          /config|env|dotenv|setup|main\.py|pipeline|pdf|pdfplumber|resume|parser|requirements|launchd/i,
        agent: "python-engineer",
      },
      {
        pattern:
          /scraper|playwright|stealth|indeed|google.?jobs|himalayas|serper|scraping|bot|delay|humaniz|linkedin|solides/i,
        agent: "scraping-engineer",
      },
      {
        pattern:
          /llm|ollama|copilot|claude|openai|prompt|analyze|analyzer|score|fit|model|token|inference/i,
        agent: "ai-engineer",
      },
      {
        pattern:
          /obsidian|vault|markdown|note|template|index|slug|writer|frontmatter/i,
        agent: "obsidian-engineer",
      },
    ],
  }),
});

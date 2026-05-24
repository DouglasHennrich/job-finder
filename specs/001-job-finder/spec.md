# Feature Specification: Job Finder Automation

**Feature Branch**: `001-job-finder`

**Created**: 2026-05-24

**Status**: Draft

**Input**: Personal automation tool that searches LATAM/Brazil remote jobs, scores them against a PDF resume using AI, and saves matching opportunities as notes in an Obsidian vault.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Resume Profile Extraction (Priority: P1)

As a job seeker, I want the tool to read my PDF resume and build a structured professional profile so that job opportunities can be accurately evaluated against my background.

**Why this priority**: Without a parsed resume profile, no job evaluation is possible. This is the foundation of the entire pipeline and must work correctly before anything else.

**Independent Test**: Can be fully tested by pointing the tool at the PDF resume file and verifying it returns a structured profile with skills, experience summary, and role preferences — with no job searching or AI scoring involved.

**Acceptance Scenarios**:

1. **Given** a valid PDF resume file exists, **When** the tool starts, **Then** it successfully extracts a professional profile with relevant skills and experience
2. **Given** a corrupted or unreadable PDF file, **When** the tool starts, **Then** it fails with a clear, actionable error message before attempting any job search
3. **Given** the resume contains no extractable text (e.g., image-only PDF), **When** the tool starts, **Then** it reports the issue clearly rather than proceeding with an empty profile

---

### User Story 2 — Multi-Source Job Discovery (Priority: P2)

As a job seeker, I want the tool to automatically search for remote job opportunities in Brazil/LATAM across multiple independent sources so that I get broad coverage without manual searching.

**Why this priority**: Job discovery is the core value of the tool. Multiple sources increase coverage and reduce reliance on any single platform.

**Independent Test**: Can be fully tested by running the search step alone and verifying that job listings are returned from at least one source, containing title, company, location, description, and URL — regardless of scoring or saving.

**Acceptance Scenarios**:

1. **Given** a search is triggered, **When** all sources are reachable, **Then** the tool returns job listings from all 3 sources (Google Jobs, Indeed, Himalayas)
2. **Given** a search is triggered, **When** one source is temporarily unavailable, **Then** the tool continues with the remaining sources and reports which source failed
3. **Given** a search is triggered, **When** a source returns no results, **Then** the tool proceeds without error and notes the empty result
4. **Given** repeated searches, **When** the same job appears in multiple sources, **Then** it is treated as one candidate for scoring (not duplicated in output)

---

### User Story 3 — AI-Powered Job Fit Scoring (Priority: P3)

As a job seeker, I want each discovered job evaluated against my resume profile by an AI model so that I receive a numeric fit score and written justification in Brazilian Portuguese, allowing me to focus on the most relevant opportunities.

**Why this priority**: Automated scoring is what differentiates this tool from a simple job aggregator. It saves hours of manual filtering.

**Independent Test**: Can be fully tested by providing a sample job listing and resume profile to the scoring step and verifying it returns a score between 0–100, a tier label, and a non-empty Portuguese justification — with no vault writing involved.

**Acceptance Scenarios**:

1. **Given** a job listing and a resume profile, **When** the scoring step runs, **Then** it returns a numeric score (0–100), a tier classification (🔥/✅/🤔/❌), and a justification written in Brazilian Portuguese
2. **Given** the AI provider is set to "local", **When** the scoring step runs, **Then** it uses the locally available model without requiring internet access
3. **Given** the AI provider is set to "cloud", **When** the scoring step runs, **Then** it uses the cloud model with auto-detected authentication credentials
4. **Given** the AI provider is misconfigured, **When** the scoring step runs, **Then** the tool reports a clear configuration error and does not proceed to save

---

### User Story 4 — Obsidian Vault Note Creation (Priority: P4)

As a job seeker, I want job opportunities that meet my minimum score threshold saved as individual Markdown notes in my Obsidian vault so that I can review, annotate, and track them in my personal knowledge system.

**Why this priority**: Persisting results to Obsidian is the final deliverable of each run — without it, the analysis is lost.

**Independent Test**: Can be fully tested by providing a pre-scored job analysis and verifying that a correctly formatted `.md` note appears in the vault directory, with all required fields (score, tier, justification, title, company, URL, date).

**Acceptance Scenarios**:

1. **Given** a job scores at or above the minimum threshold, **When** the save step runs, **Then** a Markdown note is created in the vault with title, company, score, tier, justification (pt-BR), source URL, and date found
2. **Given** a job scores below the minimum threshold, **When** the save step runs, **Then** no note is created for that job
3. **Given** the vault directory does not exist, **When** the save step runs, **Then** the tool fails with a clear error message indicating the path issue
4. **Given** notes are saved, **When** the run completes, **Then** the vault's Index note is regenerated with an up-to-date summary table of all saved jobs grouped by tier

---

### User Story 5 — Deduplication Across Runs (Priority: P5)

As a job seeker, I want jobs I have already seen to be skipped in subsequent runs so that I do not waste time reviewing the same opportunities again.

**Why this priority**: Without deduplication, the vault fills with duplicate notes and scoring time is wasted on already-known jobs.

**Independent Test**: Can be fully tested by running the tool twice for the same search and verifying that the second run creates no new notes for jobs already present in the vault.

**Acceptance Scenarios**:

1. **Given** a job note already exists in the vault, **When** the same job is discovered in a new run, **Then** it is skipped entirely (no re-scoring, no re-saving)
2. **Given** a new run discovers 10 jobs, 3 of which are already in the vault, **When** processing completes, **Then** only 7 are evaluated for scoring
3. **Given** the vault is empty, **When** the first run completes, **Then** all qualifying jobs are saved without deduplication interference

---

### Edge Cases

- What happens if the resume PDF is missing or its path is incorrect at startup?
- What if the AI model returns a score outside the 0–100 range or malformed output?
- What if all 3 job sources return zero results for the current search query?
- What if the vault's Index note becomes corrupted or is manually deleted between runs?
- What if the minimum score threshold is set to 0 (save everything) or 100 (save nothing)?
- What if authentication credentials for the cloud AI provider expire mid-run?
- What if the job description is in a language other than English or Portuguese?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tool MUST extract a professional profile from a PDF resume file before any job searching begins
- **FR-002**: The tool MUST search for remote-friendly job opportunities targeting Brazil/LATAM from at least 3 independent sources in a single run
- **FR-003**: The tool MUST evaluate each discovered job against the resume profile and produce a numeric fit score from 0 to 100
- **FR-004**: Each scored job MUST include a tier classification: 🔥 Must Apply (≥80), ✅ Good Fit (60–79), 🤔 Maybe (40–59), or ❌ Skip (<40)
- **FR-005**: Each scored job MUST include a written justification explaining the fit assessment, written in Brazilian Portuguese
- **FR-006**: The tool MUST save job notes only for jobs meeting or exceeding the configured minimum score threshold
- **FR-007**: Job notes saved to the Obsidian vault MUST include: job title, company name, fit score, tier, justification (pt-BR), source URL, and date found
- **FR-008**: The tool MUST skip any job that already has a corresponding note in the vault (deduplication)
- **FR-009**: The tool MUST regenerate a summary Index note in the vault after each run, grouping all saved jobs by tier in a Markdown table
- **FR-010**: The minimum score threshold MUST be configurable via an environment variable without modifying source code
- **FR-011**: The AI provider (local or cloud) MUST be selectable via an environment variable without modifying source code
- **FR-012**: When using the cloud AI provider, the tool MUST auto-detect authentication credentials without requiring manual token input each run
- **FR-013**: The tool MUST continue processing remaining job sources if one source fails, reporting the failure without stopping the run
- **FR-014**: The tool MUST be executable on-demand from the command line and support periodic scheduled execution without modification

### Key Entities

- **Resume Profile**: The structured professional summary derived from the user's PDF resume — captures skills, experience history, and preferred role types; serves as the benchmark for all job fit evaluations
- **Job Posting**: A single job opportunity discovered from a source — contains title, company, remote/location indicator, full description text, source platform, and direct application URL
- **Job Analysis**: The result of comparing a Job Posting against the Resume Profile — contains numeric score (0–100), tier classification (🔥/✅/🤔/❌), and written Portuguese justification
- **Vault Note**: A Markdown document saved in the Obsidian vault representing one analyzed job posting; filename is a slug derived from job title and company
- **Index Note**: A Markdown summary document in the vault listing all saved jobs in a table, grouped by tier, regenerated fresh on each run

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A complete run (resume parsing → job search → scoring → saving) finishes within 10 minutes under normal network conditions
- **SC-002**: Zero duplicate notes are created for the same job posting across multiple consecutive runs
- **SC-003**: All notes saved to the vault open and render correctly in Obsidian with properly formatted content on first access
- **SC-004**: When manually reviewed, at least 80% of jobs scored ≥80 are genuinely relevant to the user's professional profile
- **SC-005**: The tool can be switched between local and cloud AI providers by changing a single configuration value, with no code modification required
- **SC-006**: The tool runs to completion without manual intervention once launched, including automatic credential resolution for the cloud AI provider
- **SC-007**: If one job source fails during a run, the tool completes successfully using the remaining sources and reports which source was unavailable

---

## Assumptions

- The user has exactly one PDF resume file that acts as the authoritative professional profile; it is updated manually when needed
- "Remote LATAM/Brazil" means positions that are either fully remote with Brazilian/LATAM eligibility, or explicitly based in Brazil
- The Obsidian vault is stored at a fixed local path on macOS, accessible to the running process
- Job justifications are written in Brazilian Portuguese for the user's personal reading comfort
- Score tiers: 🔥 Must Apply (≥80), ✅ Good Fit (60–79), 🤔 Maybe (40–59), ❌ Skip (<40)
- The default minimum score threshold is 60 — only Good and Excellent jobs are saved unless reconfigured
- The Index note is a plain Markdown table (no Obsidian plugins or Dataview queries required)
- The tool is single-user; no multi-user, authentication, or permission management is required
- Scheduled periodic execution will be set up and validated manually after the tool is confirmed to work correctly on-demand
- A local AI option must always be available as a fallback for offline or privacy-sensitive use
- The tool does not submit applications — it only discovers, scores, and saves job information for the user's review

"""
AI Workflow Orchestrator — 10 Built-In Pipeline Templates for Phase 12.7C.
Templates:
1. Research Pipeline
2. Discovery Pipeline
3. Lead Scoring Pipeline
4. Outreach Pipeline
5. Report Pipeline
6. RAG Pipeline
7. Summarization Pipeline
8. Planning Pipeline
9. Coding Pipeline
10. Vision Pipeline
"""
from typing import Dict, List, Any

BUILTIN_PIPELINE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "template_id": "tpl_research_pipeline",
        "name": "Enterprise Research Pipeline",
        "description": "Comprehensive company research: Prompt → Embedding → Search → Reasoning → Generation → Validation → Guardrail → Memory → Evaluation → Output",
        "category": "research",
        "workflow_spec": {
            "workflow_id": "wf_research_pipeline",
            "name": "Enterprise Research Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Research Prompt", "node_type": "PromptNode", "config": {"template": "Research target entity: {target_company}"}},
                {"node_id": "node_embed", "name": "Generate Vector Embeddings", "node_type": "EmbeddingNode"},
                {"node_id": "node_search", "name": "Execute Web & Intelligence Search", "node_type": "SearchNode"},
                {"node_id": "node_reasoning", "name": "Synthesize Insights", "node_type": "ReasoningNode"},
                {"node_id": "node_generation", "name": "Generate Research Report", "node_type": "GenerationNode", "config": {"capability": "research"}},
                {"node_id": "node_validation", "name": "Validate Report Integrity", "node_type": "ValidationNode"},
                {"node_id": "node_guardrail", "name": "Run Safety Guardrails", "node_type": "GuardrailNode"},
                {"node_id": "node_memory", "name": "Persist to AI Memory", "node_type": "MemoryNode", "config": {"artifact_type": "research_report"}},
                {"node_id": "node_eval", "name": "Score Output Quality", "node_type": "EvaluationNode"},
                {"node_id": "node_output", "name": "Finalize Output", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_embed"},
                {"from_node_id": "node_embed", "to_node_id": "node_search"},
                {"from_node_id": "node_search", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_generation"},
                {"from_node_id": "node_generation", "to_node_id": "node_validation"},
                {"from_node_id": "node_validation", "to_node_id": "node_guardrail"},
                {"from_node_id": "node_guardrail", "to_node_id": "node_memory"},
                {"from_node_id": "node_memory", "to_node_id": "node_eval"},
                {"from_node_id": "node_eval", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_discovery_pipeline",
        "name": "Lead Discovery Pipeline",
        "description": "Discover potential leads matching ICP criteria.",
        "category": "discovery",
        "workflow_spec": {
            "workflow_id": "wf_discovery_pipeline",
            "name": "Lead Discovery Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Discovery Prompt", "node_type": "PromptNode", "config": {"template": "Discover leads in industry: {industry} with ICP: {icp}"}},
                {"node_id": "node_search", "name": "Search Lead Registries", "node_type": "SearchNode"},
                {"node_id": "node_reasoning", "name": "Filter Candidates", "node_type": "ReasoningNode"},
                {"node_id": "node_output", "name": "Output Lead Set", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_search"},
                {"from_node_id": "node_search", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_scoring_pipeline",
        "name": "Lead Scoring Pipeline",
        "description": "Multi-dimensional lead qualification & scoring.",
        "category": "scoring",
        "workflow_spec": {
            "workflow_id": "wf_scoring_pipeline",
            "name": "Lead Scoring Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Scoring Input", "node_type": "PromptNode", "config": {"template": "Score lead: {lead_name} profile: {profile}"}},
                {"node_id": "node_reasoning", "name": "Evaluate Fit Criteria", "node_type": "ReasoningNode"},
                {"node_id": "node_gen", "name": "Format Score Card JSON", "node_type": "GenerationNode", "config": {"capability": "json_generation"}},
                {"node_id": "node_output", "name": "Output Score", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_outreach_pipeline",
        "name": "Personalized Outreach Pipeline",
        "description": "Generates personalized sales outreach sequences.",
        "category": "outreach",
        "workflow_spec": {
            "workflow_id": "wf_outreach_pipeline",
            "name": "Personalized Outreach Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Outreach Prompt", "node_type": "PromptNode", "config": {"template": "Draft outreach to: {lead_name} at {company}"}},
                {"node_id": "node_reasoning", "name": "Analyze Value Proposition", "node_type": "ReasoningNode"},
                {"node_id": "node_gen", "name": "Draft Email Sequence", "node_type": "GenerationNode", "config": {"capability": "chat"}},
                {"node_id": "node_guardrail", "name": "Check PII & Profanity", "node_type": "GuardrailNode"},
                {"node_id": "node_output", "name": "Final Sequence", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_guardrail"},
                {"from_node_id": "node_guardrail", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_report_pipeline",
        "name": "Executive Report Pipeline",
        "description": "Generates executive-ready sales intelligence summaries.",
        "category": "report",
        "workflow_spec": {
            "workflow_id": "wf_report_pipeline",
            "name": "Executive Report Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Report Topic", "node_type": "PromptNode", "config": {"template": "Executive report for: {topic}"}},
                {"node_id": "node_reasoning", "name": "Synthesize High-Level Trends", "node_type": "ReasoningNode"},
                {"node_id": "node_gen", "name": "Draft Markdown Report", "node_type": "GenerationNode", "config": {"capability": "summarization"}},
                {"node_id": "node_output", "name": "Final Report", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_rag_pipeline",
        "name": "Retrieval Augmented Generation (RAG) Pipeline",
        "description": "Dense vector retrieval + context-augmented generation.",
        "category": "rag",
        "workflow_spec": {
            "workflow_id": "wf_rag_pipeline",
            "name": "RAG Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render RAG Question", "node_type": "PromptNode", "config": {"template": "{question}"}},
                {"node_id": "node_embed", "name": "Embed Query", "node_type": "EmbeddingNode"},
                {"node_id": "node_retrieve", "name": "Retrieve Context Chunks", "node_type": "RetrievalNode"},
                {"node_id": "node_gen", "name": "Generate Contextual Answer", "node_type": "GenerationNode", "config": {"capability": "chat"}},
                {"node_id": "node_output", "name": "Output Answer", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_embed"},
                {"from_node_id": "node_embed", "to_node_id": "node_retrieve"},
                {"from_node_id": "node_retrieve", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_summarization_pipeline",
        "name": "Document Summarization Pipeline",
        "description": "Fast multi-page text condensation.",
        "category": "summarization",
        "workflow_spec": {
            "workflow_id": "wf_summarization_pipeline",
            "name": "Document Summarization Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Input Text", "node_type": "PromptNode", "config": {"template": "Summarize: {document_text}"}},
                {"node_id": "node_gen", "name": "Summarize Text", "node_type": "GenerationNode", "config": {"capability": "summarization"}},
                {"node_id": "node_output", "name": "Output Summary", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_planning_pipeline",
        "name": "Task Planning & Decomposition Pipeline",
        "description": "Decomposes complex goals into multi-step execution plans.",
        "category": "planning",
        "workflow_spec": {
            "workflow_id": "wf_planning_pipeline",
            "name": "Task Planning Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Goal", "node_type": "PromptNode", "config": {"template": "Create plan for goal: {goal}"}},
                {"node_id": "node_reasoning", "name": "Decompose Plan Steps", "node_type": "ReasoningNode"},
                {"node_id": "node_output", "name": "Output Plan", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_coding_pipeline",
        "name": "Code Generation & Review Pipeline",
        "description": "Generates, validates, and formats code.",
        "category": "coding",
        "workflow_spec": {
            "workflow_id": "wf_coding_pipeline",
            "name": "Code Generation Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Coding Spec", "node_type": "PromptNode", "config": {"template": "Write code for: {spec}"}},
                {"node_id": "node_reasoning", "name": "Generate Code & Review Syntax", "node_type": "ReasoningNode"},
                {"node_id": "node_output", "name": "Output Code", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_reasoning"},
                {"from_node_id": "node_reasoning", "to_node_id": "node_output"},
            ],
        },
    },
    {
        "template_id": "tpl_vision_pipeline",
        "name": "Visual Inspection & OCR Pipeline",
        "description": "Analyzes visual assets and extracts structured annotations.",
        "category": "vision",
        "workflow_spec": {
            "workflow_id": "wf_vision_pipeline",
            "name": "Visual Inspection Pipeline",
            "initial_node_id": "node_prompt",
            "nodes": [
                {"node_id": "node_prompt", "name": "Render Vision Input", "node_type": "PromptNode", "config": {"template": "Analyze visual asset: {image_url}"}},
                {"node_id": "node_gen", "name": "Analyze Visual Attributes", "node_type": "GenerationNode", "config": {"capability": "vision"}},
                {"node_id": "node_output", "name": "Output Analysis", "node_type": "OutputNode"},
            ],
            "edges": [
                {"from_node_id": "node_prompt", "to_node_id": "node_gen"},
                {"from_node_id": "node_gen", "to_node_id": "node_output"},
            ],
        },
    },
]

"""
Pre-packaged Workflow Templates for Phase 11 — Milestone 4: Autonomous Workflow Engine.
"""
from typing import Dict, List, Any


PREBUILT_WORKFLOW_TEMPLATES: List[Dict[str, Any]] = [
    {
        "template_id": "sales_discovery",
        "name": "Sales Discovery Workflow",
        "description": "Performs initial company research, vector memory lookup, firmographic intelligence extraction, and ICP fit scoring.",
        "category": "sales_discovery",
        "steps": [
            {
                "step_id": "step_01_research",
                "name": "Company Research",
                "step_type": "tool",
                "target": "research_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_02_intelligence",
                "name": "Firmographics Intelligence",
                "step_type": "tool",
                "target": "company_intelligence_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_03_scoring",
                "name": "Lead Fit Scoring",
                "step_type": "tool",
                "target": "lead_scoring_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
        ],
    },
    {
        "template_id": "lead_qualification",
        "name": "Lead Qualification & ICP Audit",
        "description": "Audits lead fit, queries vector memory RAG, and scores intent signals.",
        "category": "lead_qualification",
        "steps": [
            {
                "step_id": "step_01_memory",
                "name": "Memory & RAG Search",
                "step_type": "tool",
                "target": "memory_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_02_scoring",
                "name": "ICP Lead Scoring",
                "step_type": "tool",
                "target": "lead_scoring_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
        ],
    },
    {
        "template_id": "sales_intelligence",
        "name": "Comprehensive Sales Intelligence",
        "description": "Combines company intelligence, vector search, research synthesis, and executive sales reporting.",
        "category": "sales_intelligence",
        "steps": [
            {
                "step_id": "step_01_intel",
                "name": "Company Intelligence Data",
                "step_type": "tool",
                "target": "company_intelligence_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_02_research",
                "name": "Research Synthesis",
                "step_type": "tool",
                "target": "research_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_03_report",
                "name": "Executive Sales Report",
                "step_type": "tool",
                "target": "executive_report_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
        ],
    },
    {
        "template_id": "company_research",
        "name": "Deep Company Research Pipeline",
        "description": "Performs multi-query vector search and research synthesis.",
        "category": "research",
        "steps": [
            {
                "step_id": "step_01_vector",
                "name": "Multi-Query Vector Search",
                "step_type": "tool",
                "target": "vector_search_tool",
                "inputs": {"query": "{{company_name}} tech stack and funding"},
            },
            {
                "step_id": "step_02_research",
                "name": "Research Deep Dive",
                "step_type": "tool",
                "target": "research_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
        ],
    },
    {
        "template_id": "outreach_campaign",
        "name": "Cold Outreach Campaign Pipeline",
        "description": "Generates personalized cold emails, LinkedIn scripts, and posts message bus updates.",
        "category": "outreach",
        "steps": [
            {
                "step_id": "step_01_intel",
                "name": "Firmographics Intelligence",
                "step_type": "tool",
                "target": "company_intelligence_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_02_outreach",
                "name": "Cold Email & Sequence Generation",
                "step_type": "tool",
                "target": "outreach_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
        ],
    },
    {
        "template_id": "executive_report_gen",
        "name": "Executive Sales Report Generation",
        "description": "Consolidates all company intelligence into a downloadable Executive Sales Report document.",
        "category": "executive_report",
        "steps": [
            {
                "step_id": "step_01_report",
                "name": "Executive Report Synthesis",
                "step_type": "tool",
                "target": "executive_report_tool",
                "inputs": {"company_name": "{{company_name}}"},
            },
            {
                "step_id": "step_02_artifact",
                "name": "Persist Report Artifact",
                "step_type": "tool",
                "target": "artifact_tool",
                "inputs": {"action": "save", "artifact_type": "executive", "company_name": "{{company_name}}"},
            },
        ],
    },
]

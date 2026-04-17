"""
Shared agent factory — wraps LangChain create_tool_calling_agent + AgentExecutor.
"""
from __future__ import annotations

from typing import List

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

import config
from models.schemas import AgentFinding, Incident


SYSTEM_PREAMBLE = """You are a specialised manufacturing operations analysis agent.
You have access to a set of tools for querying live plant data and searching the
manufacturing knowledge base (KBAs, process standards, prior incident reports,
maintenance history, and supplier records).

When analysing an incident:
1. Use your tools to gather relevant data — do NOT skip tool calls.
2. Look for anomalies, threshold breaches, and patterns.
3. Cross-reference live data with historical incidents in the knowledge base.
4. Be specific: cite equipment IDs, metric values, thresholds, and document IDs.
5. List contributing factors — not just the most obvious one.
6. Structure your final answer as a JSON object matching AgentFinding schema.

INCIDENT CONTEXT:
  ID:          {incident_id}
  Description: {incident_description}
  Plant:       {plant_id}
  Line:        {line_id}
  Timestamp:   {timestamp}
"""


def make_agent_executor(
    domain_system_prompt: str,
    tools: List[BaseTool],
    agent_name: str,
) -> AgentExecutor:
    """Create a ReAct-style tool-calling agent for a domain."""
    llm = config.get_llm(temperature=0.0)
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PREAMBLE + "\n\n" + domain_system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=config.VERBOSE,
        max_iterations=config.MAX_AGENT_ITERATIONS,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )


def run_domain_agent(
    executor: AgentExecutor,
    incident: Incident,
    agent_name: str,
    domain: str,
    analysis_instruction: str,
) -> AgentFinding:
    """
    Run an agent executor and convert its output to an AgentFinding.
    Extracts tool names used as raw_tool_outputs for transparency.
    """
    input_vars = {
        "incident_id":          incident.id,
        "incident_description": incident.description,
        "plant_id":             incident.plant_id,
        "line_id":              incident.line_id or "UNKNOWN",
        "timestamp":            incident.timestamp or "NOW",
        "input":                analysis_instruction,
        "agent_scratchpad":     [],
    }

    result = executor.invoke(input_vars)
    output_text: str = result.get("output", "")

    # Collect tool names used
    tool_names = []
    for step in result.get("intermediate_steps", []):
        if hasattr(step[0], "tool"):
            tool_names.append(f"{step[0].tool}: {str(step[1])[:120]}...")

    # Best-effort parse — agents return free text so we keep it as-is
    return AgentFinding(
        agent_name=agent_name,
        domain=domain,
        analysis_summary=output_text,
        raw_tool_outputs=tool_names,
    )

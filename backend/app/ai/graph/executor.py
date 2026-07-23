"""
AI Graph Engine — GraphExecutor for asynchronous DAG execution with state propagation, retries, and metrics accumulation.
"""
import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.ai.graph.graph import DAGGraph
from app.ai.graph.node import NodeResult
from app.ai.graph.scheduler import graph_scheduler

logger = logging.getLogger("backend.ai.graph.executor")


class ExecutionResult:
    """Aggregated execution summary for an entire DAG run."""

    def __init__(self, run_id: str, workflow_id: str):
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.success: bool = True
        self.outputs: Dict[str, Any] = {}
        self.node_results: Dict[str, NodeResult] = {}
        self.completed_nodes: List[str] = []
        self.failed_nodes: List[str] = []
        self.total_latency_ms: float = 0.0
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.error: Optional[str] = None


class GraphExecutor:
    """Asynchronous DAG execution engine."""

    async def execute(
        self,
        graph: DAGGraph,
        inputs: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Executes a compiled DAGGraph.
        Nodes in the same topological stage are executed concurrently using asyncio.gather.
        """
        context = context or {}
        run_id = run_id or f"run_{graph.graph_id}_{int(time.time())}"
        res = ExecutionResult(run_id=run_id, workflow_id=graph.graph_id)

        start_t = time.time()
        pipeline_state: Dict[str, Any] = dict(inputs)

        # Obtain parallel execution stages
        stages = graph_scheduler.get_execution_stages(graph)

        for stage_idx, stage_nodes in enumerate(stages):
            logger.debug(f"GraphExecutor [{run_id}]: Executing stage {stage_idx + 1}/{len(stages)} ({stage_nodes})")

            # Execute all nodes in current stage concurrently
            async def run_single_node(n_id: str) -> NodeResult:
                node = graph.nodes[n_id]

                # Check incoming edges condition evaluation
                incoming = graph.get_incoming_edges(n_id)
                if incoming:
                    # Evaluate if any parent path permits execution
                    allowed = False
                    for edge in incoming:
                        parent_output = res.node_results.get(edge.from_node_id)
                        parent_data = parent_output.data if parent_output else {}
                        if edge.evaluate_condition(parent_data):
                            allowed = True
                            break
                    if not allowed:
                        logger.info(f"GraphExecutor: Node '{n_id}' skipped due to edge condition criteria.")
                        return NodeResult(node_id=n_id, node_type=node.node_type, success=True, data={"skipped": True})

                # Execute node
                return await node.execute(inputs=pipeline_state, context=context)

            stage_results = await asyncio.gather(*[run_single_node(n) for n in stage_nodes], return_exceptions=True)

            # Process stage node results
            for n_id, n_res in zip(stage_nodes, stage_results):
                if isinstance(n_res, Exception):
                    res.success = False
                    res.failed_nodes.append(n_id)
                    res.error = f"Node '{n_id}' raised exception: {str(n_res)}"
                    logger.error(f"GraphExecutor [{run_id}]: Node '{n_id}' failed: {n_res}")
                    break
                elif isinstance(n_res, NodeResult):
                    res.node_results[n_id] = n_res
                    res.total_tokens += (n_res.prompt_tokens + n_res.completion_tokens)
                    res.total_cost += n_res.estimated_cost

                    if n_res.success:
                        res.completed_nodes.append(n_id)
                        # Merge output into pipeline state for downstream nodes
                        if n_res.data:
                            pipeline_state.update(n_res.data)
                    else:
                        res.failed_nodes.append(n_id)
                        # Fallback node handling
                        node_obj = graph.nodes[n_id]
                        if node_obj.fallback_node_id and node_obj.fallback_node_id in graph.nodes:
                            fb_id = node_obj.fallback_node_id
                            logger.info(f"GraphExecutor: Node '{n_id}' failed. Executing fallback '{fb_id}'.")
                            fb_node = graph.nodes[fb_id]
                            fb_res = await fb_node.execute(inputs=pipeline_state, context=context)
                            res.node_results[fb_id] = fb_res
                            if fb_res.success:
                                res.completed_nodes.append(fb_id)
                                pipeline_state.update(fb_res.data)
                            else:
                                res.success = False
                                res.error = f"Node '{n_id}' and fallback '{fb_id}' both failed."
                        else:
                            res.success = False
                            res.error = n_res.error or f"Node '{n_id}' failed without fallback."

            if not res.success:
                logger.warning(f"GraphExecutor [{run_id}]: Pipeline aborted at stage {stage_idx + 1} due to node failure.")
                break

        res.total_latency_ms = round((time.time() - start_t) * 1000, 2)
        res.outputs = pipeline_state
        return res


graph_executor = GraphExecutor()

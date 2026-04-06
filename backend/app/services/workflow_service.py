"""
Сервис выполнения воркфлоу.
Топологическая сортировка → последовательный запуск инструментов → передача данных между шагами.
"""
import httpx
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models.workflow import Workflow, WorkflowRun
from ..models.agent import UserAgent
from ..models.agent_tool import AgentTool
from ..models.tool import Tool
from ..models.subscription import Subscription
from ..models.energy_transaction import EnergyTransaction

logger = logging.getLogger(__name__)


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[str]:
    """Топологическая сортировка узлов по зависимостям (edges)."""
    node_ids = [n["id"] for n in nodes]
    # Строим граф зависимостей: target зависит от source
    deps: dict[str, set] = {nid: set() for nid in node_ids}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src in deps and tgt in deps:
            deps[tgt].add(src)

    sorted_nodes = []
    visited = set()

    def visit(nid: str):
        if nid in visited:
            return
        visited.add(nid)
        for dep in deps.get(nid, []):
            visit(dep)
        sorted_nodes.append(nid)

    for nid in node_ids:
        visit(nid)

    return sorted_nodes


async def run_workflow(
    workflow_id: str,
    user_id: str,
    db: AsyncSession,
    trigger_type: str = "manual",
) -> WorkflowRun:
    """Запускаем воркфлоу: загружаем граф, сортируем, выполняем по цепочке."""

    # Загружаем воркфлоу
    wf_result = await db.execute(
        select(Workflow)
        .where(Workflow.id == workflow_id)
    )
    workflow = wf_result.scalar_one_or_none()
    if not workflow:
        raise ValueError(f"Воркфлоу {workflow_id} не найден")

    # Создаём запись о запуске
    run = WorkflowRun(
        workflow_id=workflow_id,
        user_id=user_id,
        trigger_type=trigger_type,
        status="running",
    )
    db.add(run)
    await db.flush()

    graph = workflow.graph_json or {"nodes": [], "edges": []}
    nodes_list = graph.get("nodes", [])
    edges_list = graph.get("edges", [])

    if not nodes_list:
        run.status = "success"
        run.result_json = {}
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        return run

    nodes_map = {n["id"]: n for n in nodes_list}
    order = _topological_sort(nodes_list, edges_list)

    # Храним выходные данные каждого узла: node_id → {field_name: value}
    node_outputs: dict[str, dict] = {}

    try:
        for node_id in order:
            node = nodes_map.get(node_id)
            if not node:
                continue

            tool_id = node.get("tool_id")
            if not tool_id:
                continue

            # Загружаем agent_tool для этого инструмента
            at_result = await db.execute(
                select(AgentTool)
                .where(
                    AgentTool.agent_id == workflow.agent_id,
                    AgentTool.tool_id == tool_id,
                )
                .options(selectinload(AgentTool.tool))
            )
            agent_tool = at_result.scalar_one_or_none()
            if not agent_tool:
                raise ValueError(f"Инструмент {tool_id} не добавлен агенту")

            # Проверяем энергию (берём стоимость из инструмента)
            energy_cost = agent_tool.tool.energy_cost
            sub_result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = sub_result.scalar_one_or_none()
            if not subscription or subscription.energy_left < energy_cost:
                raise ValueError(f"Недостаточно токенов для '{agent_tool.tool.name}'")

            upd = await db.execute(
                update(Subscription)
                .where(Subscription.id == subscription.id, Subscription.energy_left >= energy_cost)
                .values(energy_left=Subscription.energy_left - energy_cost)
            )
            if upd.rowcount == 0:
                raise ValueError("Недостаточно токенов (race condition)")

            db.add(EnergyTransaction(
                user_id=user_id,
                amount=-energy_cost,
                description=f"Воркфлоу: {agent_tool.tool.name}",
                agent_id=workflow.agent_id,
                tool_name=agent_tool.tool.name,
            ))

            # Собираем поля: base (из настроек агента) + manual (из узла) + edges (из предыдущих)
            fields: dict = {**(agent_tool.field_values or {})}
            fields.update(node.get("input_data") or {})

            for edge in edges_list:
                if edge.get("target") == node_id:
                    src_id = edge.get("source")
                    src_handle = edge.get("sourceHandle", "")
                    tgt_handle = edge.get("targetHandle", "")
                    if src_id in node_outputs and src_handle in node_outputs[src_id]:
                        fields[tgt_handle] = node_outputs[src_id][src_handle]

            # Вызываем webhook
            payload = {
                "fields": fields,
                "args": {},
                "agent_id": workflow.agent_id,
                "user_id": user_id,
                "workflow_run_id": str(run.id),
                "node_id": node_id,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(agent_tool.tool.webhook_url, json=payload)
                resp.raise_for_status()
                output = resp.json()

            node_outputs[node_id] = output if isinstance(output, dict) else {"result": output}

        run.status = "success"
        run.result_json = node_outputs
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()

    except Exception as e:
        run.status = "error"
        run.error = str(e)
        run.result_json = node_outputs  # сохраняем что успело выполниться
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        logger.error(f"Воркфлоу {workflow_id} ошибка: {e}")

    return run

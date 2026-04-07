"""
Сервис выполнения воркфлоу.
Топологическая сортировка → последовательный запуск инструментов → передача данных между шагами.
Поддерживает синхронные и асинхронные (callback) webhook-инструменты.
"""
import asyncio
import hashlib
import httpx
import logging
import os
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

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000/api")  # fallback only

# In-memory store for async callbacks (single-process)
_callback_events: dict[str, asyncio.Event] = {}
_callback_results: dict[str, dict] = {}

# In-memory live execution statuses: workflow_id → {run_id, nodes: {node_id → {status, output, error}}}
_run_statuses: dict[str, dict] = {}


def get_run_statuses(workflow_id: str) -> dict:
    return _run_statuses.get(str(workflow_id), {})


def _init_statuses(workflow_id: str, run_id: str, tool_node_ids: list[str]):
    _run_statuses[str(workflow_id)] = {
        "run_id": str(run_id),
        "nodes": {nid: {"status": "waiting"} for nid in tool_node_ids},
    }


def _set_node_status(workflow_id: str, node_id: str, status: str, output: dict = None, error: str = None):
    wf = _run_statuses.get(str(workflow_id))
    if wf:
        wf["nodes"][node_id] = {"status": status, "output": output, "error": error}

ACK_ONLY_KEYS = {'status', 'message', 'ok', 'success', 'started', 'queued', 'accepted',
                 'received', 'error', 'instanceid', 'instance_id', 'jobid', 'job_id',
                 'executionid', 'execution_id', 'taskid', 'task_id', 'requestid', 'request_id'}

ASYNC_STATUS_VALUES = {'started', 'queued', 'accepted', 'received', 'processing', 'pending', 'running'}


def _callback_token(run_id: str, node_id: str) -> str:
    return hashlib.sha256(f"{run_id}:{node_id}:wf_secret".encode()).hexdigest()[:20]


def _extract_output(response: dict) -> dict:
    """Извлекаем полезные данные из стандартного формата ответа {instanceId, status, data: {...}}."""
    if isinstance(response, dict) and isinstance(response.get("data"), dict):
        return response["data"]
    return response if isinstance(response, dict) else {"result": response}


def _is_ack_only(data: dict) -> bool:
    """True если ответ — подтверждение получения, без полезных данных. Ждём callback."""
    if not isinstance(data, dict) or not data:
        return True
    # Если status указывает на асинхронную обработку — это ack
    status_val = str(data.get('status', '')).lower()
    if status_val in ASYNC_STATUS_VALUES:
        return True
    # Если все ключи — служебные (id запроса, статус и т.д.) — это ack
    meaningful = {k for k in data if k.lower() not in ACK_ONLY_KEYS}
    return len(meaningful) == 0


def register_callback(run_id: str, node_id: str, base_url: str = None) -> str:
    """Регистрируем ожидание callback, возвращаем URL."""
    key = f"{run_id}:{node_id}"
    _callback_events[key] = asyncio.Event()
    token = _callback_token(run_id, node_id)
    url = base_url or APP_BASE_URL
    return f"{url}/workflows/runs/{run_id}/callback/{node_id}?token={token}"


def receive_callback(run_id: str, node_id: str, token: str, data: dict) -> bool:
    """Принимаем callback от инструмента. Возвращает True если принят."""
    expected = _callback_token(run_id, node_id)
    if token != expected:
        return False
    key = f"{run_id}:{node_id}"
    _callback_results[key] = data
    if key in _callback_events:
        _callback_events[key].set()
    return True


async def _wait_for_callback(run_id: str, node_id: str, timeout: float = 120.0) -> dict:
    key = f"{run_id}:{node_id}"
    event = _callback_events.get(key)
    if event:
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            raise ValueError(f"Timeout {int(timeout)}s: инструмент не ответил через callback")
        finally:
            _callback_events.pop(key, None)
    return _callback_results.pop(key, {})


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[str]:
    """Топологическая сортировка узлов по зависимостям."""
    node_ids = [n["id"] for n in nodes]
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
    base_url: str = None,
) -> WorkflowRun:
    effective_base_url = base_url or APP_BASE_URL
    """Запускаем воркфлоу: загружаем граф, сортируем, выполняем по цепочке."""

    wf_result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = wf_result.scalar_one_or_none()
    if not workflow:
        raise ValueError(f"Воркфлоу {workflow_id} не найден")

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
        await db.refresh(run)
        return run

    nodes_map = {n["id"]: n for n in nodes_list}
    order = _topological_sort(nodes_list, edges_list)

    # Инициализируем live-статусы для tool-нод
    tool_node_ids = [
        n["id"] for n in nodes_list
        if (n.get("node_type", "tool" if n.get("tool_id") else "skip")) == "tool"
    ]
    _init_statuses(str(workflow.id), str(run.id), tool_node_ids)

    # Выходные данные каждого узла
    node_outputs: dict[str, dict] = {}

    try:
        for node_id in order:
            node = nodes_map.get(node_id)
            if not node:
                continue

            node_type = node.get("node_type", "tool" if node.get("tool_id") else "trigger")

            # Trigger-ноды пропускаем — они только задают порядок
            if node_type == "trigger":
                continue

            # Output-нода: собираем входящие данные → финальный результат
            if node_type == "output":
                collected = {}
                for edge in edges_list:
                    if edge.get("target") == node_id and edge.get("targetHandle") not in ("__entry__", None, ""):
                        src_id = edge.get("source")
                        src_handle = edge.get("sourceHandle", "")
                        if src_id in node_outputs and src_handle in node_outputs[src_id]:
                            collected[src_handle] = node_outputs[src_id][src_handle]
                node_outputs[node_id] = collected
                continue

            tool_id = node.get("tool_id")
            if not tool_id:
                continue

            # Загружаем agent_tool
            at_result = await db.execute(
                select(AgentTool)
                .where(AgentTool.agent_id == workflow.agent_id, AgentTool.tool_id == tool_id)
                .options(selectinload(AgentTool.tool))
            )
            agent_tool = at_result.scalar_one_or_none()
            if not agent_tool:
                raise ValueError(f"Инструмент {tool_id} не добавлен агенту")

            # Энергия
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

            # Собираем поля: настройки агента + ручные данные ноды + данные из предыдущих нод
            fields: dict = {**(agent_tool.field_values or {})}
            fields.update(node.get("input_data") or {})

            for edge in edges_list:
                if edge.get("target") == node_id:
                    tgt_handle = edge.get("targetHandle", "")
                    if tgt_handle in ("__entry__", "", None):
                        continue  # только порядок, без данных
                    src_id = edge.get("source")
                    src_handle = edge.get("sourceHandle", "")
                    if src_id in node_outputs and src_handle in node_outputs[src_id]:
                        fields[tgt_handle] = node_outputs[src_id][src_handle]

            # Обновляем статус: нода запускается
            _set_node_status(str(workflow.id), node_id, "running")

            # Регистрируем callback до отправки webhook
            callback_url = register_callback(str(run.id), node_id, effective_base_url)

            payload = {
                **fields,           # плоская структура для совместимости
                "fields": fields,   # вложенная структура
                "callback_url": callback_url,
                "agent_id": str(workflow.agent_id),
                "user_id": str(user_id),
                "workflow_run_id": str(run.id),
                "node_id": node_id,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(agent_tool.tool.webhook_url, json=payload)
                resp.raise_for_status()
                direct_output = resp.json() if resp.content else {}

            if direct_output and not _is_ack_only(direct_output):
                # Синхронный инструмент — используем прямой ответ
                node_outputs[node_id] = _extract_output(direct_output)
                _callback_events.pop(f"{run.id}:{node_id}", None)
                _callback_results.pop(f"{run.id}:{node_id}", None)
            else:
                # Асинхронный инструмент — ждём callback
                logger.info(f"Ждём callback от '{agent_tool.tool.name}' (node {node_id})")
                cb_data = await _wait_for_callback(str(run.id), node_id, timeout=120.0)
                node_outputs[node_id] = _extract_output(cb_data)

            _set_node_status(str(workflow.id), node_id, "success", output=node_outputs[node_id])

        run.status = "success"
        run.result_json = node_outputs
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        _run_statuses.pop(str(workflow.id), None)

    except Exception as e:
        # Помечаем текущую running-ноду как error
        wf_st = _run_statuses.get(str(workflow.id), {})
        for nid, st in wf_st.get("nodes", {}).items():
            if st.get("status") == "running":
                _set_node_status(str(workflow.id), nid, "error", error=str(e))
        run.status = "error"
        run.error = str(e)
        run.result_json = node_outputs
        run.finished_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(run)
        logger.error(f"Воркфлоу {workflow_id} ошибка: {e}")

    return run

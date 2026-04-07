<template>
  <div class="flex flex-col h-screen">

    <!-- Top bar -->
    <div class="flex items-center gap-3 px-5 py-3 bg-white border-b border-gray-100 shrink-0 z-10">
      <button class="text-gray-400 hover:text-gray-600 text-lg" @click="router.push(`/cabinet/agents/${agentId}`)">←</button>

      <!-- Editable name -->
      <input
        v-model="workflowName"
        class="text-base font-semibold text-gray-900 border-0 outline-none bg-transparent hover:bg-gray-50 focus:bg-gray-50 rounded-lg px-2 py-1 transition-colors w-56"
        @blur="saveGraph"
      />

      <div class="ml-auto flex items-center gap-2">
        <!-- Run history badge -->
        <button
          v-if="lastRun"
          class="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border transition-colors"
          :class="lastRun.status === 'success' ? 'border-green-200 bg-green-50 text-green-700' : lastRun.status === 'error' ? 'border-red-200 bg-red-50 text-red-700' : 'border-gray-200 text-gray-500'"
          @click="showRunResult = true"
        >
          {{ lastRun.status === 'success' ? '✓' : lastRun.status === 'error' ? '✗' : '⟳' }}
          Последний запуск
        </button>
        <button class="btn-secondary text-sm" :disabled="saving" @click="saveGraph">
          {{ saving ? 'Сохраняю...' : '💾 Сохранить' }}
        </button>
        <button
          class="btn-primary text-sm flex items-center gap-1.5"
          :disabled="running || !nodes.length"
          @click="runWorkflow"
        >
          <span v-if="running" class="animate-spin">⟳</span>
          <span v-else>▶</span>
          {{ running ? 'Запускаю...' : 'Запустить' }}
        </button>
      </div>
    </div>

    <!-- Main area -->
    <div class="flex flex-1 overflow-hidden">

      <!-- Left sidebar: tool palette -->
      <aside class="w-56 bg-white border-r border-gray-100 flex flex-col shrink-0 overflow-y-auto">

        <!-- Триггеры -->
        <div class="px-4 pt-4 pb-2">
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Триггеры</div>
        </div>
        <div class="px-3 space-y-2 pb-3">
          <div
            v-for="trig in TRIGGER_TYPES"
            :key="trig.type"
            class="p-2.5 rounded-xl border border-emerald-200 bg-emerald-50 cursor-grab hover:border-emerald-400 hover:bg-emerald-100 transition-colors select-none flex items-center gap-2"
            draggable="true"
            @dragstart="onDragStartSpecial($event, { nodeType: 'trigger', triggerType: trig.type })"
          >
            <span class="text-base">{{ trig.icon }}</span>
            <div>
              <div class="text-xs font-medium text-emerald-800">{{ trig.label }}</div>
            </div>
          </div>
        </div>

        <!-- Точка выхода -->
        <div class="px-4 pb-2">
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Выход</div>
        </div>
        <div class="px-3 pb-3">
          <div
            class="p-2.5 rounded-xl border border-indigo-200 bg-indigo-50 cursor-grab hover:border-indigo-400 hover:bg-indigo-100 transition-colors select-none flex items-center gap-2"
            draggable="true"
            @dragstart="onDragStartSpecial($event, { nodeType: 'output' })"
          >
            <span class="text-base">🏁</span>
            <div class="text-xs font-medium text-indigo-800">Точка выхода</div>
          </div>
        </div>

        <!-- Инструменты -->
        <div class="px-4 pb-2 border-t border-gray-100 pt-3">
          <div class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Инструменты агента</div>
        </div>
        <div class="px-3 space-y-2 pb-4">
          <div
            v-for="at in agentTools"
            :key="at.tool_id"
            class="p-3 rounded-xl border border-gray-200 bg-gray-50 cursor-grab hover:border-primary-400 hover:bg-primary-50 transition-colors select-none"
            draggable="true"
            @dragstart="onDragStart($event, at)"
          >
            <div class="text-sm font-medium text-gray-800 leading-tight">{{ at.tool?.name }}</div>
            <div class="text-xs text-gray-400 mt-1 line-clamp-2">{{ at.tool?.description || 'Нет описания' }}</div>
            <div class="flex items-center gap-2 mt-1.5">
              <span class="text-xs text-gray-400">{{ at.tool?.fields?.length ?? 0 }} вх.</span>
              <span class="text-xs text-green-600">{{ at.tool?.output_fields?.length ?? 0 }} вых.</span>
            </div>
          </div>
          <div v-if="!agentTools.length" class="text-xs text-gray-400 text-center py-4">
            Добавьте инструменты агенту
          </div>
        </div>
      </aside>

      <!-- Canvas -->
      <div class="flex-1 relative" @drop="onDrop" @dragover.prevent>
        <VueFlow
          v-model:nodes="nodes"
          v-model:edges="edges"
          :node-types="nodeTypes"
          fit-view-on-init
          :default-edge-options="{ type: 'smoothstep', animated: true, style: { stroke: '#7c3aed', strokeWidth: 2 } }"
          @node-click="onNodeClick"
          @pane-click="selectedNodeId = null"
          @connect="onConnect"
        >
          <Background pattern-color="#e5e7eb" :gap="20" />
          <Controls />
          <MiniMap />
        </VueFlow>

        <!-- Empty state -->
        <div
          v-if="!nodes.length"
          class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
        >
          <div class="text-5xl mb-3 opacity-30">⟨⟩</div>
          <div class="text-gray-400 text-sm font-medium">Перетащите инструменты сюда</div>
          <div class="text-gray-300 text-xs mt-1">Соедините выходы одного с входами другого</div>
        </div>
      </div>

      <!-- Right panel: node config -->
      <Transition name="slide-right">
        <aside v-if="selectedNodeId" class="w-72 bg-white border-l border-gray-100 flex flex-col shrink-0">
          <NodeConfigPanel
            :node-id="selectedNodeId"
            :node-type="selectedNode?.type"
            :node-data="selectedNode?.data"
            :agent-tool="selectedAgentTool"
            :input-data="selectedNode?.data?.input_data ?? {}"
            @update="onNodeDataUpdate"
            @close="selectedNodeId = null"
            @delete="deleteSelectedNode"
          />
        </aside>
      </Transition>
    </div>

    <!-- Run result modal -->
    <Teleport to="body">
      <div v-if="showRunResult && lastRun" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" @click.self="showRunResult = false">
        <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
            <div>
              <h3 class="font-semibold text-gray-900">Результат запуска</h3>
              <p class="text-xs text-gray-400 mt-0.5">
                {{ lastRun.status === 'success' ? '✓ Успешно' : '✗ Ошибка' }}
                · {{ formatDate(lastRun.started_at) }}
              </p>
            </div>
            <button class="text-gray-400 hover:text-gray-600" @click="showRunResult = false">✕</button>
          </div>
          <div class="flex-1 overflow-y-auto px-6 py-4 space-y-3">
            <div v-if="lastRun.error" class="p-3 bg-red-50 rounded-lg text-sm text-red-700">{{ lastRun.error }}</div>
            <div v-for="(output, nodeId) in (lastRun.result_json || {})" :key="nodeId">
              <div class="text-xs font-medium text-gray-500 mb-1">{{ getNodeName(nodeId) }}</div>
              <pre class="text-xs bg-gray-50 rounded-lg p-3 overflow-x-auto">{{ JSON.stringify(output, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import ToolNode from '@/components/workflow/ToolNode.vue'
import TriggerNode from '@/components/workflow/TriggerNode.vue'
import OutputNode from '@/components/workflow/OutputNode.vue'
import NodeConfigPanel from '@/components/workflow/NodeConfigPanel.vue'
import { workflowApi } from '@/api/workflow'
import { agentsApi } from '@/api/agents'
import { useToastStore } from '@/stores/toast'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const workflowId = route.params.workflowId
const agentId = route.params.agentId

const nodeTypes = { tool: markRaw(ToolNode), trigger: markRaw(TriggerNode), output: markRaw(OutputNode) }

const TRIGGER_TYPES = [
  { type: 'manual', icon: '▶', label: 'Вручную' },
  { type: 'cron', icon: '🕐', label: 'По расписанию' },
]

const { screenToFlowCoordinate } = useVueFlow()

const nodes = ref([])
const edges = ref([])
const workflowName = ref('Новый воркфлоу')
const agentTools = ref([])
const saving = ref(false)
const running = ref(false)
const selectedNodeId = ref(null)
const lastRun = ref(null)
const showRunResult = ref(false)

const selectedNode = computed(() => nodes.value.find((n) => n.id === selectedNodeId.value))

const selectedAgentTool = computed(() => {
  if (!selectedNode.value) return null
  return agentTools.value.find((at) => at.tool_id === selectedNode.value.data.tool_id) ?? null
})

onMounted(async () => {
  // Загружаем агента для списка инструментов
  try {
    const agentRes = await agentsApi.get(agentId)
    agentTools.value = agentRes.data.agent_tools ?? []
  } catch {
    toast.error('Ошибка загрузки инструментов агента')
  }

  // Загружаем воркфлоу
  try {
    const res = await workflowApi.get(workflowId)
    workflowName.value = res.data.name
    loadGraph(res.data.graph_json)
  } catch {
    toast.error('Ошибка загрузки воркфлоу')
  }

  // Последний запуск
  try {
    const runsRes = await workflowApi.runs(workflowId)
    if (runsRes.data.length) lastRun.value = runsRes.data[0]
  } catch {}
})

function loadGraph(graph) {
  if (!graph) return
  nodes.value = (graph.nodes ?? []).map((n) => {
    const nodeType = n.node_type || (n.tool_id ? 'tool' : 'trigger')
    if (nodeType === 'trigger') {
      return { id: n.id, type: 'trigger', position: n.position, data: { triggerType: n.triggerType ?? 'manual', schedule: n.schedule ?? '', timezone: n.timezone ?? 'UTC', label: n.label ?? '' } }
    }
    if (nodeType === 'output') {
      return { id: n.id, type: 'output', position: n.position, data: { webhook_url: n.webhook_url ?? '', label: n.label ?? '' } }
    }
    return { id: n.id, type: 'tool', position: n.position, data: buildNodeData(n) }
  })
  edges.value = (graph.edges ?? []).map((e) => ({
    ...e,
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#7c3aed', strokeWidth: 2 },
  }))
}

function buildNodeData(node) {
  const at = agentTools.value.find((a) => a.tool_id === node.tool_id)
  return {
    tool_id: node.tool_id,
    toolName: at?.tool?.name ?? 'Инструмент',
    fields: at?.tool?.fields ?? [],
    outputFields: at?.tool?.output_fields ?? [],
    input_data: node.input_data ?? {},
  }
}

// Drag & drop from palette
let draggedTool = null
let draggedSpecial = null

function onDragStart(event, agentTool) {
  draggedTool = agentTool
  draggedSpecial = null
  event.dataTransfer.effectAllowed = 'move'
}

function onDragStartSpecial(event, spec) {
  draggedSpecial = spec
  draggedTool = null
  event.dataTransfer.effectAllowed = 'move'
}

function onDrop(event) {
  const position = screenToFlowCoordinate({ x: event.clientX, y: event.clientY })
  const nodeId = `node-${Date.now()}`

  if (draggedSpecial) {
    let newNode
    if (draggedSpecial.nodeType === 'trigger') {
      newNode = { id: nodeId, type: 'trigger', position, data: { triggerType: draggedSpecial.triggerType, schedule: '', timezone: 'UTC', label: '' } }
    } else if (draggedSpecial.nodeType === 'output') {
      newNode = { id: nodeId, type: 'output', position, data: { webhook_url: '', label: '' } }
    }
    if (newNode) {
      nodes.value = [...nodes.value, newNode]
      selectedNodeId.value = nodeId
    }
    draggedSpecial = null
    return
  }

  if (!draggedTool) return
  const newNode = {
    id: nodeId,
    type: 'tool',
    position,
    data: {
      tool_id: draggedTool.tool_id,
      toolName: draggedTool.tool?.name ?? 'Инструмент',
      fields: draggedTool.tool?.fields ?? [],
      outputFields: draggedTool.tool?.output_fields ?? [],
      input_data: {},
    },
  }
  nodes.value = [...nodes.value, newNode]
  selectedNodeId.value = nodeId
  draggedTool = null
}

function onConnect(params) {
  edges.value = [
    ...edges.value,
    {
      ...params,
      id: `edge-${Date.now()}`,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#7c3aed', strokeWidth: 2 },
    },
  ]
}

function onNodeClick({ node }) {
  selectedNodeId.value = node.id
}

function deleteSelectedNode() {
  if (!selectedNodeId.value) return
  nodes.value = nodes.value.filter((n) => n.id !== selectedNodeId.value)
  edges.value = edges.value.filter((e) => e.source !== selectedNodeId.value && e.target !== selectedNodeId.value)
  selectedNodeId.value = null
}

function onNodeDataUpdate(newData) {
  nodes.value = nodes.value.map((n) => {
    if (n.id !== selectedNodeId.value) return n
    // tool nodes: newData is input_data; trigger/output nodes: newData is full data merge
    if (n.type === 'tool') return { ...n, data: { ...n.data, input_data: newData } }
    return { ...n, data: { ...n.data, ...newData } }
  })
}

async function saveGraph() {
  saving.value = true
  const graph = {
    nodes: nodes.value.map((n) => {
      const base = { id: n.id, node_type: n.type, position: n.position }
      if (n.type === 'trigger') return { ...base, triggerType: n.data.triggerType, schedule: n.data.schedule, timezone: n.data.timezone, label: n.data.label }
      if (n.type === 'output') return { ...base, webhook_url: n.data.webhook_url, label: n.data.label }
      return { ...base, tool_id: n.data.tool_id, input_data: n.data.input_data ?? {} }
    }),
    edges: edges.value.map((e) => ({
      id: e.id,
      source: e.source,
      sourceHandle: e.sourceHandle,
      target: e.target,
      targetHandle: e.targetHandle,
    })),
  }
  try {
    await workflowApi.update(workflowId, { name: workflowName.value, graph_json: graph })
    toast.success('Воркфлоу сохранён')
  } catch {
    toast.error('Ошибка сохранения')
  } finally {
    saving.value = false
  }
}

let pollTimer = null

function applyNodeStatuses(statuses) {
  if (!statuses) return
  nodes.value = nodes.value.map((n) => {
    const s = statuses[n.id]
    if (!s) return n
    return { ...n, data: { ...n.data, runStatus: s.status } }
  })
}

function clearNodeStatuses() {
  nodes.value = nodes.value.map((n) => ({ ...n, data: { ...n.data, runStatus: null } }))
}

async function runWorkflow() {
  await saveGraph()
  running.value = true
  clearNodeStatuses()

  // Polling live статусов каждые 1.5 секунды
  pollTimer = setInterval(async () => {
    try {
      const res = await workflowApi.runningStatus(workflowId)
      if (res.data?.nodes) applyNodeStatuses(res.data.nodes)
    } catch { /* тихо */ }
  }, 1500)

  try {
    const res = await workflowApi.run(workflowId)
    lastRun.value = res.data
    // Финальные статусы из result_json
    if (res.data.result_json) {
      const finalStatuses = {}
      for (const nodeId of Object.keys(res.data.result_json)) {
        finalStatuses[nodeId] = { status: res.data.status === 'error' ? 'error' : 'success' }
      }
      applyNodeStatuses(finalStatuses)
    }
    if (res.data.status === 'success') {
      toast.success('Воркфлоу выполнен успешно')
    } else {
      toast.error(res.data.error || 'Ошибка выполнения')
    }
    showRunResult.value = true
  } catch (e) {
    toast.error(e.response?.data?.detail || 'Ошибка запуска')
  } finally {
    running.value = false
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function getNodeName(nodeId) {
  const node = nodes.value.find((n) => n.id === nodeId)
  return node?.data?.toolName ?? nodeId
}

function formatDate(d) {
  return new Date(d).toLocaleString('ru-RU')
}
</script>

<style>
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>

<script setup>
import { h, onMounted, onUnmounted, ref } from "vue";
import {
  NButton, NCard, NDataTable, NEmpty, NModal, NPopconfirm, NSelect, NSpace, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime, relative } from "../format";

const message = useMessage();
const tasks = ref([]);
const status = ref("");
const loading = ref(false);
const detailOpen = ref(false);
const current = ref(null);
const output = ref([]);
let timer = null;

const STATUSES = ["", "pending", "running", "done", "failed", "cancelled"].map((value) => ({
  label: value || "All statuses",
  value,
}));

async function load() {
  loading.value = true;
  try {
    tasks.value = await api("/tasks", { params: { limit: 200, status: status.value } });
  } finally {
    loading.value = false;
  }
}

async function open(row) {
  current.value = row;
  detailOpen.value = true;
  await loadOutput();
}

async function loadOutput() {
  const result = await api(`/tasks/${current.value.id}/output`, { params: { lines: 600 } });
  output.value = result.lines;
  current.value = await api(`/tasks/${current.value.id}`);
}

async function cancel(row) {
  const result = await api(`/tasks/${row.id}/cancel`, { method: "POST" });
  result.ok ? message.success("Cancelled") : message.info(result.message);
  await load();
}

async function prune() {
  const result = await api("/tasks/prune", { method: "POST", params: { keep: 50 } });
  message.success(result.message);
  await load();
}

const statusType = (value) =>
  ({ done: "success", failed: "error", running: "info", cancelled: "warning" })[value] || "default";

const columns = [
  { title: "#", key: "id", width: 70 },
  { title: "Task", key: "name", ellipsis: { tooltip: true } },
  { title: "Kind", key: "kind", width: 90 },
  {
    title: "Status",
    key: "status",
    width: 110,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: statusType(row.status) }, { default: () => row.status }),
  },
  { title: "Detail", key: "detail", ellipsis: { tooltip: true } },
  { title: "Started", key: "started_at", width: 110, render: (row) => relative(row.started_at) },
  { title: "Finished", key: "finished_at", width: 110, render: (row) => relative(row.finished_at) },
  {
    title: "Actions",
    key: "actions",
    width: 170,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => open(row) }, { default: () => "Output" }),
          ["pending", "running"].includes(row.status)
            ? h(NButton, { size: "tiny", type: "warning", secondary: true, onClick: () => cancel(row) }, { default: () => "Cancel" })
            : h(NButton, {
                size: "tiny", type: "error", secondary: true,
                onClick: async () => {
                  await api(`/tasks/${row.id}`, { method: "DELETE" });
                  await load();
                },
              }, { default: () => "Remove" }),
        ],
      }),
  },
];

onMounted(async () => {
  await load();
  timer = setInterval(async () => {
    await load();
    if (detailOpen.value && current.value) await loadOutput();
  }, 4000);
});

onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div>
    <div class="toolbar">
      <n-select v-model:value="status" :options="STATUSES" style="width: 170px" @update:value="load" />
      <n-popconfirm @positive-click="prune">
        <template #trigger><n-button secondary>Prune old tasks</n-button></template>
        The 50 newest tasks are kept; the rest and their logs are deleted.
      </n-popconfirm>
      <span class="spacer" />
      <span class="muted">refreshes every 4s</span>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="tasks" :bordered="false" size="small" :row-key="(row) => row.id" />
      <n-empty v-if="!tasks.length && !loading" style="padding: 30px 0"
        description="No background tasks. Installs, pulls and uploads show up here while they run." />
    </n-card>

    <n-modal v-model:show="detailOpen" preset="card" :title="current?.name" style="max-width: 800px">
      <dl v-if="current" class="kv" style="margin-bottom: 12px">
        <dt>Status</dt><dd>{{ current.status }}</dd>
        <dt>Command</dt><dd class="mono">{{ current.detail }}</dd>
        <dt>Started</dt><dd>{{ datetime(current.started_at) || "—" }}</dd>
        <dt>Finished</dt><dd>{{ datetime(current.finished_at) || "—" }}</dd>
      </dl>
      <n-card size="small" embedded>
        <pre class="log-pane mono">{{ output.join("\n") || "No output yet." }}</pre>
      </n-card>
      <template #footer>
        <n-space justify="end">
          <n-button size="small" @click="loadOutput">Refresh output</n-button>
          <n-button size="small" @click="detailOpen = false">Close</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NDynamicTags, NForm, NFormItem, NGi, NGrid,
  NInput, NModal, NPopconfirm, NSelect, NSpace, NStatistic, NTabPane, NTabs, NTag,
  useDialog, useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const dialog = useDialog();

const info = ref({ available: false });
const containers = ref([]);
const images = ref([]);
const networks = ref([]);
const volumes = ref([]);
const stats = ref([]);
const compose = ref([]);
const loading = ref(false);

const runOpen = ref(false);
const run = reactive({
  image: "", name: "", ports: [], volumes: [], env: [], network: "",
  restart: "unless-stopped", command: "",
});

const pullRef = ref("");
const composeDraft = reactive({ path: "/www/wwwroot/compose/docker-compose.yml", content: "" });

async function load() {
  loading.value = true;
  try {
    info.value = await api("/docker/info");
    if (!info.value.available) return;
    const [c, i, n, v, s, p] = await Promise.all([
      api("/docker/containers").catch(() => []),
      api("/docker/images").catch(() => []),
      api("/docker/networks").catch(() => []),
      api("/docker/volumes").catch(() => []),
      api("/docker/stats").catch(() => []),
      api("/docker/compose").catch(() => []),
    ]);
    containers.value = c;
    images.value = i;
    networks.value = n;
    volumes.value = v;
    stats.value = s;
    compose.value = p;
  } finally {
    loading.value = false;
  }
}

async function act(row, action) {
  try {
    const result = await api(`/docker/containers/${row.name || row.id}/${action}`, { method: "POST" });
    result.ok ? message.success(`${row.name} ${action}`) : message.error(result.message);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function showLogs(row) {
  const result = await api(`/docker/containers/${row.name || row.id}/logs`, { params: { lines: 300 } });
  dialog.info({
    title: `${row.name} logs`,
    style: { width: "760px" },
    content: () => h("pre", { class: "log-pane mono" }, result.lines.join("\n") || "No output."),
    positiveText: "Close",
  });
}

async function startContainer() {
  if (!run.image.trim()) return message.warning("An image is required");
  try {
    const task = await api("/docker/containers", { method: "POST", body: { ...run } });
    message.success(`Starting ${run.image} (task ${task.id})`);
    runOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function pull() {
  if (!pullRef.value.trim()) return;
  const task = await api("/docker/images/pull", { method: "POST", body: { reference: pullRef.value.trim() } });
  message.success(`Pulling ${pullRef.value} (task ${task.id})`);
  pullRef.value = "";
}

async function prune(target) {
  const result = await api(`/docker/prune/${target}`, { method: "POST" });
  message.success(result.output.split("\n").at(-1) || "Pruned");
  await load();
}

async function saveCompose() {
  await api("/docker/compose/write", { method: "POST", body: { ...composeDraft } });
  message.success("Compose file written");
}

async function composeAction(action) {
  const task = await api("/docker/compose", {
    method: "POST",
    body: { compose_file: composeDraft.path, action },
  });
  message.success(`compose ${action} started (task ${task.id})`);
}

const containerColumns = [
  { title: "Name", key: "name", ellipsis: { tooltip: true } },
  { title: "Image", key: "image", ellipsis: { tooltip: true } },
  {
    title: "State",
    key: "state",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.state === "running" ? "success" : "default" },
        { default: () => row.state }),
  },
  { title: "Status", key: "status", ellipsis: { tooltip: true } },
  { title: "Ports", key: "ports", ellipsis: { tooltip: true } },
  {
    title: "Actions",
    key: "actions",
    width: 280,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          ...["start", "restart", "stop"].map((action) =>
            h(NButton, { size: "tiny", secondary: true, onClick: () => act(row, action) }, { default: () => action })),
          h(NButton, { size: "tiny", secondary: true, onClick: () => showLogs(row) }, { default: () => "Logs" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => act(row, "rm") }, { default: () => "Remove" }),
        ],
      }),
  },
];

const imageColumns = [
  { title: "Repository", key: "repository", ellipsis: { tooltip: true } },
  { title: "Tag", key: "tag", width: 140 },
  { title: "Size", key: "size", width: 110 },
  { title: "Created", key: "created", width: 140 },
  {
    title: "",
    key: "actions",
    width: 100,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/docker/images/${encodeURIComponent(`${row.repository}:${row.tag}`)}`, {
            method: "DELETE", params: { force: true },
          });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const networkColumns = [
  { title: "Name", key: "name" },
  { title: "Driver", key: "driver", width: 120 },
  { title: "Scope", key: "scope", width: 120 },
  {
    title: "",
    key: "actions",
    width: 100,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        disabled: ["bridge", "host", "none"].includes(row.name),
        onClick: async () => {
          await api(`/docker/networks/${row.name}`, { method: "DELETE" });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const volumeColumns = [
  { title: "Name", key: "name", ellipsis: { tooltip: true } },
  { title: "Driver", key: "driver", width: 110 },
  { title: "Mountpoint", key: "mountpoint", ellipsis: { tooltip: true } },
  {
    title: "",
    key: "actions",
    width: 100,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/docker/volumes/${row.name}`, { method: "DELETE", params: { force: true } });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const statColumns = [
  { title: "Container", key: "name" },
  { title: "CPU", key: "cpu", width: 90 },
  { title: "Memory", key: "memory" },
  { title: "Mem %", key: "memory_percent", width: 90 },
  { title: "Net I/O", key: "net" },
  { title: "Block I/O", key: "block" },
  { title: "PIDs", key: "pids", width: 70 },
];

onMounted(load);
</script>

<template>
  <div>
    <n-alert v-if="!info.available" type="info" :bordered="false">
      Docker is not installed. Install it from the App store page, then reload this one.
    </n-alert>

    <template v-else>
      <n-grid cols="2 s:4" responsive="screen" :x-gap="12" :y-gap="12">
        <n-gi><n-card size="small"><n-statistic label="Version" :value="info.version || '—'" /></n-card></n-gi>
        <n-gi><n-card size="small"><n-statistic label="Running" :value="`${info.containers_running} / ${info.containers}`" /></n-card></n-gi>
        <n-gi><n-card size="small"><n-statistic label="Images" :value="info.images" /></n-card></n-gi>
        <n-gi><n-card size="small"><n-statistic label="Storage driver" :value="info.driver || '—'" /></n-card></n-gi>
      </n-grid>

      <div class="toolbar" style="margin-top: 14px">
        <n-button type="primary" @click="runOpen = true">Run container</n-button>
        <n-popconfirm @positive-click="() => prune('system')">
          <template #trigger><n-button secondary>Prune system</n-button></template>
          Stopped containers, dangling images, unused networks and the build cache are removed.
        </n-popconfirm>
        <span class="spacer" />
        <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
      </div>

      <n-tabs type="line" animated>
        <n-tab-pane name="containers" tab="Containers">
          <n-card size="small">
            <n-data-table :columns="containerColumns" :data="containers" :bordered="false" size="small"
              :row-key="(row) => row.id" />
          </n-card>
          <n-card v-if="stats.length" size="small" title="Live stats" style="margin-top: 14px">
            <n-data-table :columns="statColumns" :data="stats" :bordered="false" size="small"
              :row-key="(row) => row.name" />
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="images" tab="Images">
          <n-space style="margin-bottom: 12px">
            <n-input v-model:value="pullRef" placeholder="nginx:alpine" style="width: 240px" @keyup.enter="pull" />
            <n-button type="primary" size="small" @click="pull">Pull</n-button>
          </n-space>
          <n-card size="small">
            <n-data-table :columns="imageColumns" :data="images" :bordered="false" size="small"
              :row-key="(row) => row.id" />
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="networks" tab="Networks">
          <n-card size="small">
            <n-data-table :columns="networkColumns" :data="networks" :bordered="false" size="small"
              :row-key="(row) => row.id" />
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="volumes" tab="Volumes">
          <n-card size="small">
            <n-data-table :columns="volumeColumns" :data="volumes" :bordered="false" size="small"
              :row-key="(row) => row.name" />
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="compose" tab="Compose">
          <n-form label-placement="top" size="small">
            <n-form-item label="Compose file path"><n-input v-model:value="composeDraft.path" class="mono" /></n-form-item>
            <n-form-item label="Contents">
              <n-input v-model:value="composeDraft.content" type="textarea" :rows="16" class="mono"
                placeholder="services:&#10;  web:&#10;    image: nginx:alpine&#10;    ports: ['8080:80']" />
            </n-form-item>
            <n-space>
              <n-button size="small" @click="saveCompose">Save file</n-button>
              <n-button size="small" type="primary" @click="composeAction('up')">up -d</n-button>
              <n-button size="small" @click="composeAction('pull')">pull</n-button>
              <n-button size="small" @click="composeAction('restart')">restart</n-button>
              <n-button size="small" type="error" secondary @click="composeAction('down')">down</n-button>
            </n-space>
          </n-form>
          <n-card v-if="compose.length" size="small" title="Known projects" style="margin-top: 14px">
            <n-data-table size="small" :bordered="false" :data="compose" :row-key="(row) => row.name"
              :columns="[{ title: 'Project', key: 'name' }, { title: 'Status', key: 'status' }, { title: 'Files', key: 'config_files', ellipsis: { tooltip: true } }]" />
          </n-card>
        </n-tab-pane>
      </n-tabs>
    </template>

    <n-modal v-model:show="runOpen" preset="card" title="Run container" style="max-width: 560px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Image"><n-input v-model:value="run.image" placeholder="nginx:alpine" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Name"><n-input v-model:value="run.name" placeholder="optional" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item label="Port mappings (host:container)"><n-dynamic-tags v-model:value="run.ports" /></n-form-item>
        <n-form-item label="Volume mappings (host:container)"><n-dynamic-tags v-model:value="run.volumes" /></n-form-item>
        <n-form-item label="Environment (KEY=value)"><n-dynamic-tags v-model:value="run.env" /></n-form-item>
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Restart policy">
              <n-select v-model:value="run.restart"
                :options="['no', 'always', 'unless-stopped', 'on-failure'].map((v) => ({ label: v, value: v }))" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="Network">
              <n-select v-model:value="run.network" clearable
                :options="networks.map((n) => ({ label: n.name, value: n.name }))" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="Override command"><n-input v-model:value="run.command" class="mono" /></n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="runOpen = false">Cancel</n-button>
          <n-button type="primary" @click="startContainer">Run</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

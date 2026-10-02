<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput, NInputNumber,
  NModal, NSelect, NSpace, NSwitch, NTabPane, NTabs, NTag, useDialog, useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const dialog = useDialog();

const projects = ref([]);
const runtimes = ref([]);
const loading = ref(false);
const createOpen = ref(false);
const detailOpen = ref(false);
const current = ref(null);
const logs = ref([]);
const unit = ref({ path: "", content: "" });

const draft = reactive({
  name: "", runtime: "node", path: "", command: "", port: 3000,
  user: "root", env: "", autostart: true, note: "",
});

const runtimeOptions = computed(() =>
  runtimes.value.map((item) => ({
    label: item.available ? `${item.label} — ${item.version}` : `${item.label} (not installed)`,
    value: item.key,
    disabled: false,
  })),
);

async function load() {
  loading.value = true;
  try {
    const [rows, runtimeRows] = await Promise.all([api("/projects"), api("/projects/runtimes")]);
    projects.value = rows;
    runtimes.value = runtimeRows;
  } finally {
    loading.value = false;
  }
}

function pickRuntime(key) {
  const found = runtimes.value.find((item) => item.key === key);
  if (found && !draft.command) draft.command = found.default_command;
}

async function create() {
  if (!draft.name.trim()) return message.warning("A project name is required");
  try {
    await api("/projects", { method: "POST", body: { ...draft } });
    message.success(`${draft.name} created`);
    createOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function act(project, action) {
  try {
    const result = await api(`/projects/${project.id}/${action}`, { method: "POST" });
    result.ok ? message.success(`${project.name} ${action}ed`) : message.error(result.message);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function openDetail(project) {
  current.value = { ...project };
  detailOpen.value = true;
  await Promise.all([loadLogs(), loadUnit()]);
}

async function loadLogs() {
  const result = await api(`/projects/${current.value.id}/logs`, { params: { lines: 300 } });
  logs.value = result.lines;
}

async function loadUnit() {
  unit.value = await api(`/projects/${current.value.id}/unit`);
}

async function save() {
  try {
    const project = current.value;
    await api(`/projects/${project.id}`, {
      method: "PATCH",
      body: {
        runtime: project.runtime, path: project.path, command: project.command,
        port: project.port, user: project.user, env: project.env, note: project.note,
      },
    });
    message.success("Saved; restart the project to pick it up");
    await Promise.all([load(), loadUnit()]);
  } catch (error) {
    message.error(error.message);
  }
}

function remove(project) {
  dialog.warning({
    title: `Delete ${project.name}?`,
    content: "The systemd unit is stopped and removed. The project files stay on disk.",
    positiveText: "Delete",
    negativeText: "Cancel",
    onPositiveClick: async () => {
      await api(`/projects/${project.id}`, { method: "DELETE" });
      message.success(`${project.name} removed`);
      detailOpen.value = false;
      await load();
    },
  });
}

const columns = computed(() => [
  {
    title: "Project",
    key: "name",
    render: (row) =>
      h("div", {}, [
        h(NButton, { text: true, type: "primary", onClick: () => openDetail(row) }, { default: () => row.name }),
        h("div", { class: "muted mono" }, row.path),
      ]),
  },
  { title: "Runtime", key: "runtime", width: 100 },
  { title: "Port", key: "port", width: 80, render: (row) => row.port || "—" },
  { title: "Command", key: "command", ellipsis: { tooltip: true } },
  {
    title: "State",
    key: "state",
    width: 110,
    render: (row) =>
      h(NTag, {
        size: "small", bordered: false,
        type: row.state === "active" ? "success" : row.state === "failed" ? "error" : "default",
      }, { default: () => row.state }),
  },
  {
    title: "Autostart",
    key: "enabled",
    width: 100,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/projects/${row.id}/autostart/${value}`, { method: "POST" });
          await load();
        },
      }),
  },
  {
    title: "Actions",
    key: "actions",
    width: 250,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          ...["start", "restart", "stop"].map((action) =>
            h(NButton, { size: "tiny", secondary: true, onClick: () => act(row, action) },
              { default: () => action })),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => remove(row) },
            { default: () => "Delete" }),
        ],
      }),
  },
]);

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-button type="primary" @click="createOpen = true">Add project</n-button>
      <span class="spacer" />
      <n-space class="chip-list">
        <n-tag v-for="item in runtimes" :key="item.key" size="small" :bordered="false"
          :type="item.available ? 'success' : 'default'">
          {{ item.label }}{{ item.version ? ` ${item.version}` : "" }}
        </n-tag>
      </n-space>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-card size="small">
      <n-data-table :columns="columns" :data="projects" :loading="loading" :bordered="false"
        :row-key="(row) => row.id" size="small" />
      <n-empty v-if="!projects.length && !loading" style="padding: 30px 0"
        description="No projects yet. A project becomes a systemd unit the panel can start, stop and read logs from." />
    </n-card>

    <n-modal v-model:show="createOpen" preset="card" title="Add project" style="max-width: 580px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Name"><n-input v-model:value="draft.name" placeholder="my-api" /></n-form-item></n-gi>
          <n-gi>
            <n-form-item label="Runtime">
              <n-select v-model:value="draft.runtime" :options="runtimeOptions" @update:value="pickRuntime" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="Working directory">
          <n-input v-model:value="draft.path" placeholder="/www/wwwroot/my-api" />
        </n-form-item>
        <n-form-item label="Start command">
          <n-input v-model:value="draft.command" placeholder="npm start" class="mono" />
        </n-form-item>
        <n-grid cols="3" :x-gap="12">
          <n-gi><n-form-item label="Port"><n-input-number v-model:value="draft.port" :min="0" :max="65535" style="width: 100%" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Run as user"><n-input v-model:value="draft.user" /></n-form-item></n-gi>
          <n-gi>
            <n-form-item label="Autostart">
              <n-switch v-model:value="draft.autostart" />
            </n-form-item>
          </n-gi>
        </n-grid>
        <n-form-item label="Environment (KEY=value per line)">
          <n-input v-model:value="draft.env" type="textarea" :rows="3" class="mono" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="createOpen = false">Cancel</n-button>
          <n-button type="primary" @click="create">Create</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="detailOpen" preset="card" :title="current?.name" style="max-width: 760px">
      <n-tabs v-if="current" type="line" animated>
        <n-tab-pane name="settings" tab="Settings">
          <n-form label-placement="top" size="small">
            <n-grid cols="2" :x-gap="12">
              <n-gi><n-form-item label="Runtime"><n-select v-model:value="current.runtime" :options="runtimeOptions" /></n-form-item></n-gi>
              <n-gi><n-form-item label="Port"><n-input-number v-model:value="current.port" :min="0" :max="65535" style="width: 100%" /></n-form-item></n-gi>
            </n-grid>
            <n-form-item label="Working directory"><n-input v-model:value="current.path" /></n-form-item>
            <n-form-item label="Start command"><n-input v-model:value="current.command" class="mono" /></n-form-item>
            <n-form-item label="Run as user"><n-input v-model:value="current.user" /></n-form-item>
            <n-form-item label="Environment"><n-input v-model:value="current.env" type="textarea" :rows="4" class="mono" /></n-form-item>
            <n-form-item label="Note"><n-input v-model:value="current.note" /></n-form-item>
            <n-space>
              <n-button type="primary" size="small" @click="save">Save</n-button>
              <n-button size="small" @click="act(current, 'restart')">Restart</n-button>
            </n-space>
          </n-form>
        </n-tab-pane>
        <n-tab-pane name="logs" tab="Logs">
          <n-button size="small" style="margin-bottom: 10px" @click="loadLogs">Refresh</n-button>
          <n-card size="small" embedded>
            <pre class="log-pane mono">{{ logs.join("\n") || "No output yet." }}</pre>
          </n-card>
        </n-tab-pane>
        <n-tab-pane name="unit" tab="systemd unit">
          <p class="muted mono">{{ unit.path }}</p>
          <n-card size="small" embedded>
            <pre class="log-pane mono">{{ unit.content }}</pre>
          </n-card>
          <p class="muted" style="margin-top: 8px">Generated from the settings above; edits here would be overwritten.</p>
        </n-tab-pane>
      </n-tabs>
    </n-modal>
  </div>
</template>

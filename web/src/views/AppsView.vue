<script setup>
import { computed, onMounted, ref } from "vue";
import {
  NAlert, NButton, NCard, NEmpty, NGi, NGrid, NInput, NModal, NPopconfirm, NSpace,
  NTable, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const data = ref({ package_manager: "", apps: [] });
const loading = ref(false);
const filter = ref("");
const upgradable = ref([]);
const updateOpen = ref(false);

const CATEGORIES = [
  { key: "web", label: "Web servers" },
  { key: "database", label: "Databases" },
  { key: "runtime", label: "Runtimes" },
  { key: "container", label: "Containers" },
  { key: "security", label: "Security" },
  { key: "tool", label: "Tools" },
];

const grouped = computed(() => {
  const needle = filter.value.trim().toLowerCase();
  return CATEGORIES.map((category) => ({
    ...category,
    apps: data.value.apps.filter(
      (app) =>
        app.category === category.key &&
        (!needle || app.name.toLowerCase().includes(needle) || app.slug.includes(needle)),
    ),
  })).filter((category) => category.apps.length);
});

const installedCount = computed(() => data.value.apps.filter((app) => app.installed).length);

async function load() {
  loading.value = true;
  try {
    data.value = await api("/apps");
  } finally {
    loading.value = false;
  }
}

async function install(app) {
  try {
    const task = await api(`/apps/${app.slug}/install`, { method: "POST" });
    message.success(`Installing ${app.name} — follow it on the Tasks page (task ${task.id})`);
  } catch (error) {
    message.error(error.message);
  }
}

async function uninstall(app) {
  try {
    const task = await api(`/apps/${app.slug}/uninstall`, { method: "POST" });
    message.success(`Removing ${app.name} (task ${task.id})`);
  } catch (error) {
    message.error(error.message);
  }
}

async function serviceAction(app, action) {
  if (!app.service) return;
  const result = await api("/system/services", { method: "POST", body: { name: app.service, action } });
  result.ok ? message.success(`${app.service} ${action}`) : message.error(result.message);
  await load();
}

async function checkUpdates() {
  upgradable.value = await api("/apps/system/upgradable");
  updateOpen.value = true;
}

async function systemUpdate() {
  const task = await api("/apps/system/update", { method: "POST" });
  message.success(`System update started (task ${task.id})`);
  updateOpen.value = false;
}
onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-input v-model:value="filter" placeholder="Filter software" clearable style="width: 220px" />
      <n-button secondary @click="checkUpdates">Check for updates</n-button>
      <span class="spacer" />
      <n-tag size="small" :bordered="false">{{ installedCount }} installed</n-tag>
      <n-tag v-if="data.package_manager" size="small" :bordered="false" type="info">
        {{ data.package_manager }}
      </n-tag>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-alert v-if="!data.package_manager" type="warning" :bordered="false" style="margin-bottom: 12px">
      No supported package manager was found, so the panel can report what is installed but cannot install anything.
    </n-alert>

    <div v-for="category in grouped" :key="category.key" style="margin-bottom: 18px">
      <h3 style="margin: 0 0 10px; font-size: 14px">{{ category.label }}</h3>
      <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14" :y-gap="14">
        <n-gi v-for="app in category.apps" :key="app.slug">
          <n-card size="small" :title="app.name">
            <template #header-extra>
              <n-tag size="small" :bordered="false" :type="app.installed ? 'success' : 'default'">
                {{ app.installed ? app.version || "installed" : "not installed" }}
              </n-tag>
            </template>
            <p class="muted" style="margin: 0 0 10px; min-height: 36px">{{ app.description }}</p>
            <n-space align="center" :size="6">
              <n-button v-if="!app.installed" size="tiny" type="primary" :disabled="!app.installable"
                @click="install(app)">Install</n-button>
              <template v-else>
                <n-tag v-if="app.state" size="small" :bordered="false"
                  :type="app.state === 'active' ? 'success' : 'default'">{{ app.state }}</n-tag>
                <n-button v-if="app.service" size="tiny" secondary @click="serviceAction(app, 'restart')">Restart</n-button>
                <n-button v-if="app.service" size="tiny" secondary @click="serviceAction(app, app.state === 'active' ? 'stop' : 'start')">
                  {{ app.state === "active" ? "Stop" : "Start" }}
                </n-button>
                <n-popconfirm @positive-click="() => uninstall(app)">
                  <template #trigger><n-button size="tiny" type="error" secondary>Remove</n-button></template>
                  The package manager removes {{ app.name }}. Data directories are left alone.
                </n-popconfirm>
              </template>
            </n-space>
            <p v-if="app.package" class="muted mono" style="margin: 10px 0 0">{{ app.package }}</p>
          </n-card>
        </n-gi>
      </n-grid>
    </div>

    <n-empty v-if="!grouped.length && !loading" description="Nothing matches that filter." />

    <n-modal v-model:show="updateOpen" preset="card" title="System updates" style="max-width: 640px">
      <n-empty v-if="!upgradable.length" description="Everything is up to date." />
      <n-table v-else size="small" :bordered="false" striped>
        <thead><tr><th>Package</th><th>Candidate</th></tr></thead>
        <tbody>
          <tr v-for="row in upgradable" :key="row.name">
            <td class="mono">{{ row.name }}</td>
            <td class="mono">{{ row.candidate }}</td>
          </tr>
        </tbody>
      </n-table>
      <template #footer>
        <n-space justify="end">
          <n-button @click="updateOpen = false">Close</n-button>
          <n-button type="primary" :disabled="!upgradable.length" @click="systemUpdate">
            Update {{ upgradable.length }} packages
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

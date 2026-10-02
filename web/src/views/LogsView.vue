<script setup>
import { h, onMounted, ref } from "vue";
import { NButton, NCard, NDataTable, NSelect, NSpace, NTabPane, NTabs, NTag } from "naive-ui";
import { api } from "../api";
import { datetime } from "../format";

const operations = ref([]);
const logins = ref([]);
const sites = ref([]);
const selectedSite = ref(null);
const kind = ref("access");
const siteLines = ref([]);

const kindOptions = [
  { label: "access", value: "access" },
  { label: "error", value: "error" },
];

async function loadSiteLog() {
  if (!selectedSite.value) return;
  const data = await api(`/logs/site/${selectedSite.value}`, { params: { kind: kind.value, lines: 300 } });
  siteLines.value = data.lines;
}

const operationColumns = [
  { title: "When", key: "created_at", width: 170, render: (row) => datetime(row.created_at) },
  { title: "User", key: "username", width: 120 },
  { title: "Action", key: "action", width: 180 },
  { title: "Target", key: "target", ellipsis: { tooltip: true } },
  {
    title: "Result",
    key: "success",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.success ? "success" : "error" }, {
        default: () => (row.success ? "ok" : "failed"),
      }),
  },
];

const loginColumns = [
  { title: "When", key: "created_at", width: 170, render: (row) => datetime(row.created_at) },
  { title: "User", key: "username", width: 140 },
  { title: "IP", key: "ip", width: 160 },
  {
    title: "Result",
    key: "success",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.success ? "success" : "error" }, {
        default: () => (row.success ? "ok" : "failed"),
      }),
  },
  { title: "Detail", key: "detail" },
];

onMounted(async () => {
  [operations.value, logins.value, sites.value] = await Promise.all([
    api("/logs/operations"),
    api("/auth/login-logs"),
    api("/sites"),
  ]);
});
</script>

<template>
  <n-tabs type="line" animated>
    <n-tab-pane name="operations" tab="Operations">
      <n-card size="small">
        <n-data-table :columns="operationColumns" :data="operations" :bordered="false" size="small" />
      </n-card>
    </n-tab-pane>

    <n-tab-pane name="logins" tab="Logins">
      <n-card size="small">
        <n-data-table :columns="loginColumns" :data="logins" :bordered="false" size="small" />
      </n-card>
    </n-tab-pane>

    <n-tab-pane name="site" tab="Site logs">
      <div class="toolbar">
        <n-select
          v-model:value="selectedSite"
          :options="sites.map((site) => ({ label: site.name, value: site.id }))"
          placeholder="pick a site"
          style="width: 240px"
          @update:value="loadSiteLog"
        />
        <n-select v-model:value="kind" :options="kindOptions" style="width: 130px" @update:value="loadSiteLog" />
        <n-button secondary @click="loadSiteLog">Refresh</n-button>
      </div>
      <n-card size="small">
        <pre class="mono log-pane">{{ siteLines.join("\n") || "No log lines yet." }}</pre>
      </n-card>
    </n-tab-pane>
  </n-tabs>
</template>

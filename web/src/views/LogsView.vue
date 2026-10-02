<script setup>
import { computed, h, onMounted, ref } from "vue";
import {
  NButton, NCard, NDataTable, NEmpty, NGi, NGrid, NPopconfirm, NSelect,
  NStatistic, NTabPane, NTabs, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes, datetime, number } from "../format";
import UsageChart from "../components/UsageChart.vue";

const message = useMessage();

const sites = ref([]);
const siteChoice = ref(null);
const kind = ref("access");
const lines = ref([]);
const analysis = ref(null);
const errors = ref(null);
const sizes = ref([]);
const operations = ref([]);
const logins = ref([]);
const loading = ref(false);

const siteOptions = computed(() => sites.value.map((site) => ({ label: site.name, value: site.id })));

const hourlySeries = computed(() => [
  {
    key: "cpu",
    label: "Requests per hour",
    points: (analysis.value?.hourly || []).map((row) => row.count),
  },
]);

async function load() {
  loading.value = true;
  try {
    const [siteRows, sizeRows, operationRows, loginRows] = await Promise.all([
      api("/sites").catch(() => []),
      api("/logs/sizes").catch(() => []),
      api("/logs/operations", { params: { limit: 200 } }).catch(() => []),
      api("/logs/logins", { params: { limit: 200 } }).catch(() => []),
    ]);
    sites.value = siteRows;
    sizes.value = sizeRows;
    operations.value = operationRows;
    logins.value = loginRows;
    if (!siteChoice.value && siteRows.length) siteChoice.value = siteRows[0].id;
  } finally {
    loading.value = false;
  }
}

async function loadTail() {
  if (!siteChoice.value) return;
  const result = await api(`/logs/site/${siteChoice.value}`, { params: { kind: kind.value, lines: 400 } });
  lines.value = result.lines;
}

async function loadAnalysis() {
  if (!siteChoice.value) return;
  try {
    analysis.value = await api(`/logs/site/${siteChoice.value}/analysis`, {
      params: { max_lines: 50000, top: 20 },
    });
  } catch (error) {
    analysis.value = null;
    message.warning(error.message);
  }
}

async function loadErrors() {
  if (!siteChoice.value) return;
  errors.value = await api(`/logs/site/${siteChoice.value}/errors`, { params: { lines: 300 } })
    .catch(() => ({ entries: [], lines: [] }));
}

async function rotate() {
  const result = await api(`/logs/site/${siteChoice.value}/rotate`, { method: "POST", params: { kind: kind.value } });
  message.success(`Rotated ${bytes(result.bytes)} into ${result.archive}`);
  await Promise.all([loadTail(), load()]);
}

async function truncate() {
  const result = await api(`/logs/site/${siteChoice.value}/truncate`, { method: "POST", params: { kind: kind.value } });
  message.success(result.message);
  await Promise.all([loadTail(), load()]);
}

const sizeColumns = [
  { title: "Site", key: "site" },
  { title: "Access log", key: "access", width: 130, render: (row) => bytes(row.access) },
  { title: "Error log", key: "error", width: 130, render: (row) => bytes(row.error) },
  { title: "Total", key: "total", width: 130, render: (row) => bytes(row.total) },
];

const operationColumns = [
  { title: "When", key: "created_at", width: 160, render: (row) => datetime(row.created_at) },
  { title: "User", key: "username", width: 120 },
  { title: "Action", key: "action", width: 180 },
  { title: "Target", key: "target", ellipsis: { tooltip: true } },
  {
    title: "OK",
    key: "success",
    width: 70,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.success ? "success" : "error" },
        { default: () => (row.success ? "yes" : "no") }),
  },
  { title: "Detail", key: "detail", ellipsis: { tooltip: true } },
];

const loginColumns = [
  { title: "When", key: "created_at", width: 160, render: (row) => datetime(row.created_at) },
  { title: "User", key: "username", width: 140 },
  { title: "From", key: "ip", width: 150 },
  {
    title: "Result",
    key: "success",
    width: 100,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.success ? "success" : "error" },
        { default: () => (row.success ? "ok" : "failed") }),
  },
  { title: "Detail", key: "detail" },
];

onMounted(async () => {
  await load();
  await loadTail();
});
</script>

<template>
  <div>
    <n-tabs type="line" animated>
      <n-tab-pane name="site" tab="Site logs">
        <div class="toolbar">
          <n-select v-model:value="siteChoice" :options="siteOptions" style="width: 220px" @update:value="loadTail" />
          <n-select v-model:value="kind" style="width: 130px" @update:value="loadTail"
            :options="[{ label: 'Access', value: 'access' }, { label: 'Error', value: 'error' }]" />
          <n-button secondary @click="loadTail">Refresh</n-button>
          <n-popconfirm @positive-click="rotate">
            <template #trigger><n-button secondary>Rotate</n-button></template>
            The current log is copied beside itself with a timestamp, then emptied.
          </n-popconfirm>
          <n-popconfirm @positive-click="truncate">
            <template #trigger><n-button secondary type="error">Empty</n-button></template>
            The log is emptied without keeping a copy.
          </n-popconfirm>
        </div>
        <n-card size="small" embedded>
          <pre class="log-pane mono">{{ lines.join("\n") || "No log lines." }}</pre>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="analysis" tab="Traffic report" @vue:mounted="loadAnalysis">
        <div class="toolbar">
          <n-select v-model:value="siteChoice" :options="siteOptions" style="width: 220px" @update:value="loadAnalysis" />
          <n-button secondary @click="loadAnalysis">Analyse</n-button>
          <span class="spacer" />
          <span v-if="analysis" class="muted">
            {{ number(analysis.parsed) }} requests parsed from {{ number(analysis.lines_read) }} lines
          </span>
        </div>

        <template v-if="analysis">
          <n-grid cols="2 s:3 l:5" responsive="screen" :x-gap="12" :y-gap="12">
            <n-gi><n-card size="small"><n-statistic label="Requests" :value="number(analysis.parsed)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Unique visitors" :value="number(analysis.unique_visitors)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Bandwidth" :value="bytes(analysis.total_bytes)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Error rate" :value="`${analysis.error_rate}%`" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Spiders" :value="analysis.spiders.length" /></n-card></n-gi>
          </n-grid>

          <n-card v-if="analysis.hourly.length" size="small" title="Requests per hour" style="margin-top: 14px">
            <usage-chart :series="hourlySeries" :capacity="analysis.hourly.length" :height="170"
              :max="0" :format="(v) => number(Math.round(v))"
              :span-text="analysis.hourly[0]?.hour || ''" />
          </n-card>

          <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
            <n-gi>
              <n-card size="small" title="Top addresses">
                <n-data-table size="small" :bordered="false" :max-height="280" :data="analysis.top_ips"
                  :row-key="(row) => row.ip"
                  :columns="[{ title: 'Address', key: 'ip' }, { title: 'Requests', key: 'count', width: 110 }]" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Top paths">
                <n-data-table size="small" :bordered="false" :max-height="280" :data="analysis.top_paths"
                  :row-key="(row) => row.path"
                  :columns="[{ title: 'Path', key: 'path', ellipsis: { tooltip: true } }, { title: 'Hits', key: 'count', width: 90 }]" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Status codes">
                <n-data-table size="small" :bordered="false" :max-height="260" :data="analysis.statuses"
                  :row-key="(row) => row.status"
                  :columns="[{ title: 'Status', key: 'status', width: 100 }, { title: 'Count', key: 'count' }]" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Heaviest paths by bandwidth">
                <n-data-table size="small" :bordered="false" :max-height="260" :data="analysis.heaviest_paths"
                  :row-key="(row) => row.path"
                  :columns="[
                    { title: 'Path', key: 'path', ellipsis: { tooltip: true } },
                    { title: 'Bytes', key: 'bytes', width: 110, render: (row) => bytes(row.bytes) },
                  ]" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Crawlers">
                <n-data-table size="small" :bordered="false" :max-height="240" :data="analysis.spiders"
                  :row-key="(row) => row.spider"
                  :columns="[{ title: 'Crawler', key: 'spider' }, { title: 'Requests', key: 'count', width: 110 }]" />
                <n-empty v-if="!analysis.spiders.length" size="small" description="No known crawler in this window." />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Referers">
                <n-data-table size="small" :bordered="false" :max-height="240" :data="analysis.top_referers"
                  :row-key="(row) => row.referer"
                  :columns="[{ title: 'Referer', key: 'referer', ellipsis: { tooltip: true } }, { title: 'Hits', key: 'count', width: 90 }]" />
                <n-empty v-if="!analysis.top_referers.length" size="small" description="No referers recorded." />
              </n-card>
            </n-gi>
          </n-grid>
        </template>
        <n-empty v-else description="Pick a site and analyse its access log." style="margin-top: 50px" />
      </n-tab-pane>

      <n-tab-pane name="errors" tab="Errors" @vue:mounted="loadErrors">
        <div class="toolbar">
          <n-select v-model:value="siteChoice" :options="siteOptions" style="width: 220px" @update:value="loadErrors" />
          <n-button secondary @click="loadErrors">Refresh</n-button>
        </div>
        <template v-if="errors">
          <n-card size="small" title="Grouped messages">
            <n-data-table size="small" :bordered="false" :max-height="300" :data="errors.entries"
              :row-key="(row) => row.message"
              :columns="[
                { title: 'Message', key: 'message', ellipsis: { tooltip: true } },
                { title: 'Count', key: 'count', width: 90 },
              ]" />
            <n-empty v-if="!errors.entries.length" style="padding: 24px 0" description="No errors logged." />
          </n-card>
          <n-card size="small" title="Raw tail" style="margin-top: 14px" embedded>
            <pre class="log-pane mono">{{ errors.lines.join("\n") || "Nothing logged." }}</pre>
          </n-card>
        </template>
      </n-tab-pane>

      <n-tab-pane name="sizes" tab="Disk footprint">
        <n-card size="small">
          <n-data-table :columns="sizeColumns" :data="sizes" :bordered="false" size="small"
            :row-key="(row) => row.id" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="operations" tab="Panel actions">
        <div class="toolbar">
          <span class="spacer" />
          <n-popconfirm @positive-click="async () => { const r = await api('/logs/operations', { method: 'DELETE', params: { keep: 500 } }); message.success(r.message); await load(); }">
            <template #trigger><n-button secondary type="error">Trim to 500</n-button></template>
            Older operation log entries are deleted.
          </n-popconfirm>
          <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
        </div>
        <n-card size="small">
          <n-data-table :columns="operationColumns" :data="operations" :bordered="false" size="small"
            :row-key="(row) => row.id" :max-height="560" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="logins" tab="Logins">
        <n-card size="small">
          <n-data-table :columns="loginColumns" :data="logins" :bordered="false" size="small"
            :row-key="(row) => row.id" :max-height="560" />
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

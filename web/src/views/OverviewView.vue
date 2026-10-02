<script setup>
import { computed, h, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  NButton,
  NCard,
  NDataTable,
  NEmpty,
  NGi,
  NGrid,
  NIcon,
  NProgress,
  NSpace,
  NStatistic,
  NTag,
  useMessage,
} from "naive-ui";
import {
  CubeOutline,
  GlobeOutline,
  RocketOutline,
  ServerOutline,
  ShieldCheckmarkOutline,
} from "@vicons/ionicons5";
import { api } from "../api";
import { bytes, duration, number } from "../format";
import Gauge from "../components/Gauge.vue";
import UsageChart from "../components/UsageChart.vue";

const CAPACITY = 60;
const message = useMessage();
const router = useRouter();

const info = ref(null);
const services = ref([]);
const counts = ref({ sites: 0, databases: 0, projects: 0, containers: 0 });
const audit = ref(null);
const cpuHistory = ref([]);
const memoryHistory = ref([]);
let timer = null;

const chartSeries = computed(() => [
  { key: "cpu", label: "CPU", points: cpuHistory.value },
  { key: "memory", label: "Memory", points: memoryHistory.value },
]);

const rootDisk = computed(
  () => info.value?.disks?.find((disk) => disk.mountpoint === "/") || info.value?.disks?.[0] || null,
);

const loadPercent = computed(() => {
  if (!info.value) return 0;
  return Math.min(100, (info.value.load["1m"] / Math.max(1, info.value.cpu.cores)) * 100);
});

function push(target, value) {
  target.value = [...target.value, value].slice(-CAPACITY);
}

async function refresh() {
  try {
    const data = await api("/system/overview");
    info.value = data;
    push(cpuHistory, data.cpu.percent);
    push(memoryHistory, data.memory.percent);
  } catch {
    /* a dropped poll is not worth a toast */
  }
}

async function loadStatic() {
  const [serviceRows, sites, databases, projects, report] = await Promise.all([
    api("/system/services").catch(() => []),
    api("/sites").catch(() => []),
    api("/databases").catch(() => []),
    api("/projects").catch(() => []),
    api("/security/audit").catch(() => null),
  ]);
  services.value = serviceRows;
  audit.value = report;
  const docker = await api("/docker/info").catch(() => ({ containers_running: 0 }));
  counts.value = {
    sites: sites.length,
    databases: databases.length,
    projects: projects.length,
    containers: docker.containers_running || 0,
  };
}

async function serviceAction(name, action) {
  const result = await api("/system/services", { method: "POST", body: { name, action } });
  result.ok ? message.success(`${name} ${action}`) : message.error(result.message || "Failed");
  services.value = await api("/system/services");
}

const diskColumns = [
  { title: "Mount", key: "mountpoint", ellipsis: { tooltip: true } },
  { title: "Type", key: "fstype", width: 90 },
  { title: "Used", key: "used", width: 100, render: (row) => bytes(row.used) },
  { title: "Total", key: "total", width: 100, render: (row) => bytes(row.total) },
  {
    title: "Usage",
    key: "percent",
    width: 160,
    render: (row) =>
      h(NProgress, {
        percentage: row.percent,
        indicatorPlacement: "inside",
        height: 14,
        status: row.percent >= 90 ? "error" : row.percent >= 75 ? "warning" : "success",
      }),
  },
];

const serviceColumns = [
  { title: "Service", key: "name" },
  {
    title: "State",
    key: "state",
    width: 110,
    render: (row) =>
      h(
        NTag,
        {
          type: row.state === "active" ? "success" : row.state === "inactive" ? "default" : "warning",
          size: "small",
          bordered: false,
        },
        { default: () => row.state || "unknown" },
      ),
  },
  {
    title: "Actions",
    key: "actions",
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () =>
          ["restart", "reload", "stop", "start"].map((action) =>
            h(
              NButton,
              { size: "tiny", secondary: true, onClick: () => serviceAction(row.name, action) },
              { default: () => action },
            ),
          ),
      }),
  },
];

const shortcuts = [
  { label: "Websites", icon: GlobeOutline, path: "/sites", key: "sites" },
  { label: "Databases", icon: ServerOutline, path: "/databases", key: "databases" },
  { label: "Projects", icon: RocketOutline, path: "/projects", key: "projects" },
  { label: "Containers", icon: CubeOutline, path: "/docker", key: "containers" },
];

onMounted(async () => {
  await Promise.all([refresh(), loadStatic()]);
  timer = setInterval(refresh, 3000);
});

onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div v-if="info">
    <div class="gauge-row">
      <gauge
        label="CPU"
        :percent="info.cpu.percent"
        :detail="`${info.cpu.cores} cores`"
        :caption="info.os"
      />
      <gauge
        label="Memory"
        :percent="info.memory.percent"
        :detail="`${bytes(info.memory.used)} / ${bytes(info.memory.total)}`"
        :caption="`${bytes(info.memory.available)} available`"
      />
      <gauge
        v-if="rootDisk"
        label="Disk"
        :percent="rootDisk.percent"
        :detail="`${bytes(rootDisk.used)} / ${bytes(rootDisk.total)}`"
        :caption="rootDisk.mountpoint"
      />
      <gauge
        label="Load"
        :percent="loadPercent"
        :display="String(info.load['1m'].toFixed(2))"
        unit=""
        :detail="`5m ${info.load['5m'].toFixed(2)} · 15m ${info.load['15m'].toFixed(2)}`"
        :caption="`pressure ${info.load.pressure}`"
      />
      <gauge
        v-if="info.swap.total"
        label="Swap"
        :percent="info.swap.percent"
        :detail="`${bytes(info.swap.used)} / ${bytes(info.swap.total)}`"
      />
    </div>

    <n-grid cols="1 l:3" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
      <n-gi span="1 l:2">
        <n-card size="small" title="CPU and memory">
          <template #header-extra>
            <span class="muted">{{ info.hostname }} · up {{ duration(info.uptime_seconds) }}</span>
          </template>
          <usage-chart :series="chartSeries" :capacity="CAPACITY" :interval="3" :height="200" />
        </n-card>
      </n-gi>

      <n-gi>
        <n-card size="small" title="At a glance">
          <n-grid cols="2" :x-gap="12" :y-gap="14">
            <n-gi v-for="item in shortcuts" :key="item.key">
              <div class="shortcut" @click="router.push(item.path)">
                <n-icon size="20" :component="item.icon" />
                <n-statistic :label="item.label" :value="counts[item.key]" />
              </div>
            </n-gi>
          </n-grid>

          <div v-if="audit" class="score-ring" style="margin-top: 16px">
            <n-progress
              type="circle"
              :percentage="audit.score"
              :stroke-width="8"
              style="width: 62px"
              :status="audit.score >= 75 ? 'success' : audit.score >= 50 ? 'warning' : 'error'"
            />
            <div>
              <strong>Security score</strong>
              <p class="muted" style="margin: 2px 0 6px">
                {{ audit.passed }} of {{ audit.total }} checks pass
              </p>
              <n-button size="tiny" secondary @click="router.push('/security')">
                <template #icon><n-icon :component="ShieldCheckmarkOutline" /></template>
                Review
              </n-button>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
      <n-gi>
        <n-card size="small" title="Disks">
          <n-data-table
            :columns="diskColumns"
            :data="info.disks"
            :bordered="false"
            size="small"
            :row-key="(row) => row.mountpoint"
          />
        </n-card>
      </n-gi>

      <n-gi>
        <n-card size="small" title="Services">
          <n-data-table
            :columns="serviceColumns"
            :data="services"
            :bordered="false"
            size="small"
            :max-height="260"
            :row-key="(row) => row.name"
          />
        </n-card>
      </n-gi>
    </n-grid>

    <n-card size="small" title="Network" style="margin-top: 14px">
      <n-grid cols="2 s:4" responsive="screen" :x-gap="16" :y-gap="12">
        <n-gi><n-statistic label="Sent" :value="bytes(info.network.bytes_sent)" /></n-gi>
        <n-gi><n-statistic label="Received" :value="bytes(info.network.bytes_recv)" /></n-gi>
        <n-gi><n-statistic label="Packets out" :value="number(info.network.packets_sent)" /></n-gi>
        <n-gi><n-statistic label="Packets in" :value="number(info.network.packets_recv)" /></n-gi>
      </n-grid>
    </n-card>
  </div>

  <n-empty v-else description="Loading the dashboard…" style="margin-top: 80px" />
</template>

<style scoped>
.shortcut {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  border-radius: 6px;
  padding: 4px;
  transition: background 0.15s;
}

.shortcut:hover {
  background: rgba(130, 140, 155, 0.12);
}
</style>

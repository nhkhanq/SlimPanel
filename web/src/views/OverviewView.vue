<script setup>
import { computed, h, onMounted, onUnmounted, ref } from "vue";
import { NButton, NCard, NDataTable, NGi, NGrid, NSpace, NTag, useMessage } from "naive-ui";
import { api } from "../api";
import { bytes, duration, percent } from "../format";
import StatCard from "../components/StatCard.vue";
import UsageChart from "../components/UsageChart.vue";

const CAPACITY = 60;
const message = useMessage();

const info = ref(null);
const services = ref([]);
const cpuHistory = ref([]);
const memoryHistory = ref([]);
let timer = null;

const chartSeries = computed(() => [
  { key: "cpu", label: "CPU", points: cpuHistory.value },
  { key: "memory", label: "Memory", points: memoryHistory.value },
]);

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
    /* transient poll failure */
  }
}

async function loadServices() {
  services.value = await api("/system/services");
}

async function serviceAction(name, action) {
  const result = await api("/system/services", { method: "POST", body: { name, action } });
  result.ok ? message.success(`${name} ${action}`) : message.error(result.message || "Failed");
  await loadServices();
}

const diskColumns = [
  { title: "Mount", key: "mountpoint" },
  { title: "Type", key: "fstype" },
  { title: "Used", key: "used", render: (row) => bytes(row.used) },
  { title: "Total", key: "total", render: (row) => bytes(row.total) },
  { title: "Usage", key: "percent", render: (row) => `${row.percent}%` },
];

const serviceColumns = [
  { title: "Service", key: "name" },
  {
    title: "State",
    key: "state",
    render: (row) =>
      h(NTag, { type: row.state === "active" ? "success" : "default", size: "small", bordered: false }, {
        default: () => row.state || "unknown",
      }),
  },
  {
    title: "Actions",
    key: "actions",
    render: (row) =>
      h(NSpace, { size: 6 }, {
        default: () =>
          ["restart", "reload", "stop", "start"].map((action) =>
            h(NButton, { size: "tiny", secondary: true, onClick: () => serviceAction(row.name, action) }, {
              default: () => action,
            }),
          ),
      }),
  },
];

onMounted(async () => {
  await Promise.all([refresh(), loadServices()]);
  timer = setInterval(refresh, 3000);
});

onUnmounted(() => clearInterval(timer));
</script>

<template>
  <div v-if="info">
    <n-grid cols="2 s:2 m:4" responsive="screen" :x-gap="12" :y-gap="12">
      <n-gi>
        <stat-card
          label="CPU"
          :value="percent(info.cpu.percent)"
          :note="`${info.cpu.cores} cores`"
          :percent="info.cpu.percent"
        />
      </n-gi>
      <n-gi>
        <stat-card
          label="Memory"
          :value="percent(info.memory.percent)"
          :note="`${bytes(info.memory.used)} / ${bytes(info.memory.total)}`"
          :percent="info.memory.percent"
        />
      </n-gi>
      <n-gi>
        <stat-card
          label="Load average"
          :value="info.load['1m'].toFixed(2)"
          :note="`5m ${info.load['5m'].toFixed(2)} · 15m ${info.load['15m'].toFixed(2)}`"
          :percent="Math.min(info.load.pressure * 100, 100)"
          :status="info.load.pressure > 1 ? 'warning' : 'default'"
        />
      </n-gi>
      <n-gi>
        <stat-card
          label="Uptime"
          :value="duration(info.uptime_seconds)"
          :note="`${info.hostname} · ${info.os}`"
        />
      </n-gi>
    </n-grid>

    <n-card title="Last 3 minutes" size="small" style="margin-top: 12px">
      <usage-chart :series="chartSeries" :capacity="CAPACITY" />
    </n-card>

    <n-grid cols="1 l:2" responsive="screen" :x-gap="12" :y-gap="12" style="margin-top: 12px">
      <n-gi>
        <n-card title="Disks" size="small">
          <n-data-table :columns="diskColumns" :data="info.disks" :bordered="false" size="small" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="Services" size="small">
          <n-data-table :columns="serviceColumns" :data="services" :bordered="false" size="small" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

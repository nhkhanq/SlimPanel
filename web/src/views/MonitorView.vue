<script setup>
import { computed, onMounted, ref } from "vue";
import {
  NButton, NCard, NEmpty, NGi, NGrid, NPopconfirm, NSelect, NStatistic, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes, number, rate } from "../format";
import UsageChart from "../components/UsageChart.vue";

const message = useMessage();
const status = ref(null);
const hours = ref(6);
const history = ref({ samples: [] });
const summary = ref(null);
const loading = ref(false);

const RANGES = [1, 6, 12, 24, 72, 168].map((value) => ({
  label: value < 24 ? `${value}h` : `${value / 24}d`,
  value,
}));

const points = (field) => history.value.samples.map((row) => row[field] ?? 0);

const cpuSeries = computed(() => [
  { key: "cpu", label: "CPU", points: points("cpu") },
  { key: "memory", label: "Memory", points: points("memory") },
  { key: "swap", label: "Swap", points: points("swap") },
]);

const loadSeries = computed(() => [{ key: "load", label: "Load 1m", points: points("load1") }]);
const netSeries = computed(() => [
  { key: "net_down", label: "Download", points: points("net_down") },
  { key: "net_up", label: "Upload", points: points("net_up") },
]);
const diskSeries = computed(() => [
  { key: "net_down", label: "Read", points: points("disk_read") },
  { key: "net_up", label: "Write", points: points("disk_write") },
]);

const spanText = computed(() => `${hours.value}h ago`);

async function load() {
  loading.value = true;
  try {
    const [statusRow, historyRow, summaryRow] = await Promise.all([
      api("/monitor/status"),
      api("/monitor/history", { params: { hours: hours.value, points: 360 } }),
      api("/monitor/summary", { params: { hours: hours.value } }),
    ]);
    status.value = statusRow;
    history.value = historyRow;
    summary.value = summaryRow;
  } finally {
    loading.value = false;
  }
}

async function sampleNow() {
  await api("/monitor/sample", { method: "POST" });
  message.success("Sample taken");
  await load();
}

async function clearHistory() {
  const result = await api("/monitor", { method: "DELETE" });
  message.success(result.message);
  await load();
}
onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <n-select v-model:value="hours" :options="RANGES" style="width: 110px" @update:value="load" />
      <n-button secondary @click="sampleNow">Sample now</n-button>
      <n-popconfirm @positive-click="clearHistory">
        <template #trigger><n-button secondary type="error">Clear history</n-button></template>
        Every stored sample is deleted. Sampling continues.
      </n-popconfirm>
      <span class="spacer" />
      <n-tag v-if="status" size="small" :bordered="false" :type="status.running ? 'success' : 'warning'">
        {{ status.running ? `sampling every ${status.interval}s` : "sampler stopped" }}
      </n-tag>
      <n-tag v-if="status" size="small" :bordered="false">keeps {{ status.retention_days }}d</n-tag>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-grid v-if="summary && summary.count" cols="2 s:3 l:6" responsive="screen" :x-gap="12" :y-gap="12">
      <n-gi><n-card size="small"><n-statistic label="CPU avg" :value="`${summary.cpu.avg}%`" /><span class="muted">peak {{ summary.cpu.max }}%</span></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Memory avg" :value="`${summary.memory.avg}%`" /><span class="muted">peak {{ summary.memory.max }}%</span></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Load avg" :value="summary.load1.avg" /><span class="muted">peak {{ summary.load1.max }}</span></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Disk" :value="`${summary.disk.avg}%`" /><span class="muted">peak {{ summary.disk.max }}%</span></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Downloaded" :value="bytes(summary.traffic_recv)" /><span class="muted">in {{ summary.hours }}h</span></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Uploaded" :value="bytes(summary.traffic_sent)" /><span class="muted">{{ number(summary.count) }} samples</span></n-card></n-gi>
    </n-grid>

    <n-empty v-if="!history.samples.length" style="margin: 60px 0"
      description="No samples in this window yet. The sampler writes one row a minute." />

    <template v-else>
      <n-card size="small" title="CPU, memory and swap" style="margin-top: 14px">
        <usage-chart :series="cpuSeries" :capacity="history.samples.length" :height="200" :span-text="spanText" />
      </n-card>

      <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
        <n-gi>
          <n-card size="small" title="Network throughput">
            <usage-chart :series="netSeries" :capacity="history.samples.length" :height="180"
              :max="0" :format="rate" :span-text="spanText" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card size="small" title="Disk throughput">
            <usage-chart :series="diskSeries" :capacity="history.samples.length" :height="180"
              :max="0" :format="rate" :span-text="spanText" />
          </n-card>
        </n-gi>
      </n-grid>

      <n-card size="small" title="Load average" style="margin-top: 14px">
        <usage-chart :series="loadSeries" :capacity="history.samples.length" :height="160"
          :max="0" :format="(v) => Number(v).toFixed(2)" :span-text="spanText" />
      </n-card>
    </template>
  </div>
</template>

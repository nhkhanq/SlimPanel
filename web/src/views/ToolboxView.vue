<script setup>
import { onMounted, reactive, ref } from "vue";
import {
  NButton, NCard, NDataTable, NForm, NFormItem, NGi, NGrid, NInput, NInputNumber,
  NPopconfirm, NSelect, NSpace, NStatistic, NTabPane, NTabs, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes } from "../format";

const message = useMessage();
const info = ref(null);
const timezones = ref([]);
const swap = ref(null);
const sysctl = ref([]);
const sysctlDraft = ref({});
const ports = ref([]);
const loading = ref(false);

const hostname = ref("");
const timezone = ref("");
const dns = ref("");
const resolveHost = ref("example.com");
const resolveResult = ref(null);
const swapDraft = reactive({ size_mb: 2048, path: "/swapfile" });

async function load() {
  loading.value = true;
  try {
    const [infoRow, zones, swapRow, sysctlRows, portRows] = await Promise.all([
      api("/toolbox"),
      api("/toolbox/timezones").catch(() => []),
      api("/toolbox/swap").catch(() => null),
      api("/toolbox/sysctl").catch(() => []),
      api("/toolbox/ports").catch(() => []),
    ]);
    info.value = infoRow;
    timezones.value = zones;
    swap.value = swapRow;
    sysctl.value = sysctlRows;
    sysctlDraft.value = Object.fromEntries(sysctlRows.map((row) => [row.key, row.value]));
    ports.value = portRows;
    hostname.value = infoRow.hostname;
    timezone.value = infoRow.timezone;
    dns.value = infoRow.dns.join(", ");
  } finally {
    loading.value = false;
  }
}

async function run(label, fn) {
  try {
    const result = await fn();
    message.success(result?.message || `${label} done`);
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

const setHostname = () =>
  run("Hostname", () => api("/toolbox/hostname", { method: "POST", body: { name: hostname.value } }));
const setTimezone = () =>
  run("Timezone", () => api("/toolbox/timezone", { method: "POST", body: { name: timezone.value } }));
const setDns = () =>
  run("DNS", () => api("/toolbox/dns", { method: "POST", body: { servers: dns.value.split(",").map((s) => s.trim()) } }));
const createSwap = () =>
  run("Swap", () => api("/toolbox/swap", { method: "POST", body: { ...swapDraft } }));
const removeSwap = () =>
  run("Swap", () => api("/toolbox/swap", { method: "DELETE", params: { path: swapDraft.path } }));
const saveSysctl = () =>
  run("Kernel", () => api("/toolbox/sysctl", { method: "POST", body: { values: sysctlDraft.value } }));

async function releaseMemory() {
  const result = await api("/toolbox/release-memory", { method: "POST" });
  message.success(`Freed ${bytes(result.freed)}`);
  await load();
}

async function resolve() {
  resolveResult.value = await api("/toolbox/resolve", { params: { host: resolveHost.value } });
}

async function reboot() {
  await api("/toolbox/reboot", { method: "POST", params: { confirm: "reboot" } });
  message.warning("Reboot requested; the panel will go away for a moment.");
}

const portColumns = [
  { title: "Port", key: "port", width: 90 },
  { title: "Address", key: "address", width: 150 },
  { title: "Process", key: "process" },
  { title: "PID", key: "pid", width: 90 },
];

onMounted(load);
</script>

<template>
  <div v-if="info">
    <n-grid cols="2 s:4" responsive="screen" :x-gap="12" :y-gap="12">
      <n-gi><n-card size="small"><n-statistic label="Hostname" :value="info.hostname" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Timezone" :value="info.timezone || '—'" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Kernel" :value="info.kernel" /></n-card></n-gi>
      <n-gi><n-card size="small"><n-statistic label="Packages" :value="info.package_manager || '—'" /></n-card></n-gi>
    </n-grid>

    <n-tabs type="line" animated style="margin-top: 14px">
      <n-tab-pane name="system" tab="System">
        <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14">
          <n-gi>
            <n-card size="small" title="Identity">
              <n-form label-placement="top" size="small">
                <n-form-item label="Hostname">
                  <n-space>
                    <n-input v-model:value="hostname" style="width: 240px" />
                    <n-button size="small" @click="setHostname">Set</n-button>
                  </n-space>
                </n-form-item>
                <n-form-item label="Timezone">
                  <n-space>
                    <n-select v-model:value="timezone" filterable style="width: 240px"
                      :options="timezones.map((z) => ({ label: z, value: z }))" />
                    <n-button size="small" @click="setTimezone">Set</n-button>
                  </n-space>
                </n-form-item>
                <n-form-item label="DNS servers (comma separated)">
                  <n-space>
                    <n-input v-model:value="dns" style="width: 240px" />
                    <n-button size="small" @click="setDns">Set</n-button>
                  </n-space>
                </n-form-item>
              </n-form>
            </n-card>
          </n-gi>

          <n-gi>
            <n-card size="small" title="Maintenance">
              <n-space vertical :size="12">
                <n-space align="center">
                  <n-button size="small" @click="releaseMemory">Release memory</n-button>
                  <span class="muted">sync, then drop the page cache</span>
                </n-space>
                <n-space align="center">
                  <n-input v-model:value="resolveHost" style="width: 180px" />
                  <n-button size="small" @click="resolve">DNS lookup</n-button>
                </n-space>
                <pre v-if="resolveResult" class="log-pane mono" style="max-height: 150px">{{ resolveResult.output }}</pre>
                <n-popconfirm @positive-click="reboot">
                  <template #trigger><n-button size="small" type="error" secondary>Reboot server</n-button></template>
                  Every service on this host restarts. Make sure nothing is mid-write.
                </n-popconfirm>
              </n-space>
            </n-card>
          </n-gi>
        </n-grid>
      </n-tab-pane>

      <n-tab-pane name="swap" tab="Swap">
        <n-card size="small">
          <n-grid cols="3" :x-gap="12" style="margin-bottom: 14px">
            <n-gi><n-statistic label="Total" :value="bytes(swap?.total || 0)" /></n-gi>
            <n-gi><n-statistic label="Used" :value="bytes(swap?.used || 0)" /></n-gi>
            <n-gi><n-statistic label="Usage" :value="`${swap?.percent || 0}%`" /></n-gi>
          </n-grid>
          <n-space v-if="swap?.entries?.length" class="chip-list" style="margin-bottom: 14px">
            <n-tag v-for="entry in swap.entries" :key="entry.name" size="small" :bordered="false">
              {{ entry.name }} · {{ bytes(entry.size_kb * 1024) }} ({{ entry.type }})
            </n-tag>
          </n-space>
          <n-form inline label-placement="top" size="small">
            <n-form-item label="Size (MB)">
              <n-input-number v-model:value="swapDraft.size_mb" :min="64" :max="65536" style="width: 140px" />
            </n-form-item>
            <n-form-item label="Path"><n-input v-model:value="swapDraft.path" style="width: 200px" class="mono" /></n-form-item>
            <n-form-item label=" ">
              <n-space>
                <n-button size="small" type="primary" @click="createSwap">Create</n-button>
                <n-popconfirm @positive-click="removeSwap">
                  <template #trigger><n-button size="small" type="error" secondary>Remove</n-button></template>
                  The swap file is switched off, deleted and removed from /etc/fstab.
                </n-popconfirm>
              </n-space>
            </n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="kernel" tab="Kernel">
        <n-card size="small">
          <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14">
            <n-gi v-for="row in sysctl" :key="row.key">
              <n-form-item :label="row.key" label-placement="top" size="small">
                <n-input v-model:value="sysctlDraft[row.key]" class="mono" />
              </n-form-item>
            </n-gi>
          </n-grid>
          <n-button type="primary" size="small" @click="saveSysctl">Apply and persist</n-button>
          <p class="muted" style="margin-top: 8px">
            Written to <code>/etc/sysctl.d/99-slimpanel.conf</code> so the values survive a reboot.
          </p>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="ports" tab="Open ports">
        <n-card size="small">
          <n-data-table :columns="portColumns" :data="ports" :bordered="false" size="small"
            :row-key="(row) => `${row.port}-${row.address}`" :max-height="480" />
        </n-card>
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

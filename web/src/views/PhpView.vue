<script setup>
import { computed, onMounted, ref, watch } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput,
  NSelect, NSpace, NTabPane, NTabs, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";

const message = useMessage();
const versions = ref([]);
const selected = ref("");
const ini = ref({ path: "", content: "", values: {}, tunable: [] });
const extensions = ref([]);
const fpm = ref(null);
const fpmConf = ref({ path: "", content: "" });
const slow = ref({ path: "", lines: [] });
const loading = ref(false);
const draftValues = ref({});

const current = computed(() => versions.value.find((item) => item.version === selected.value));
const options = computed(() =>
  versions.value.map((item) => ({
    label: item.installed ? item.label : `${item.label} (incomplete)`,
    value: item.version,
  })),
);

async function load() {
  loading.value = true;
  try {
    versions.value = await api("/php");
    if (!selected.value && versions.value.length) {
      selected.value = (versions.value.find((v) => v.installed) || versions.value[0]).version;
    }
  } finally {
    loading.value = false;
  }
}

async function loadVersion() {
  if (!selected.value) return;
  ini.value = await api(`/php/${selected.value}/ini`).catch(() => ({ path: "", content: "", values: {}, tunable: [] }));
  draftValues.value = { ...ini.value.values };
  extensions.value = await api(`/php/${selected.value}/extensions`).catch(() => []);
  fpm.value = await api(`/php/${selected.value}/fpm`).catch(() => null);
  fpmConf.value = await api(`/php/${selected.value}/fpm/config`).catch(() => ({ path: "", content: "" }));
  slow.value = await api(`/php/${selected.value}/slow-log`).catch(() => ({ path: "", lines: [] }));
}

watch(selected, loadVersion);

async function saveValues() {
  try {
    ini.value = await api(`/php/${selected.value}/ini/values`, {
      method: "POST",
      body: { values: draftValues.value },
    });
    draftValues.value = { ...ini.value.values };
    message.success("php.ini updated — restart PHP-FPM to apply it");
  } catch (error) {
    message.error(error.message);
  }
}

async function saveRaw() {
  try {
    await api(`/php/${selected.value}/ini`, { method: "POST", body: { content: ini.value.content } });
    message.success("php.ini written (a .bak copy was kept)");
    await loadVersion();
  } catch (error) {
    message.error(error.message);
  }
}

async function saveFpm() {
  try {
    await api(`/php/${selected.value}/fpm/config`, { method: "POST", body: { content: fpmConf.value.content } });
    message.success("Pool config written");
  } catch (error) {
    message.error(error.message);
  }
}

async function serviceAction(action) {
  try {
    const result = await api(`/php/${selected.value}/service/${action}`, { method: "POST" });
    result.ok ? message.success(`PHP-FPM ${action}ed`) : message.error(result.message);
    await Promise.all([load(), loadVersion()]);
  } catch (error) {
    message.error(error.message);
  }
}

const extensionColumns = [
  { title: "Extension", key: "name" },
  {
    title: "Loaded",
    key: "loaded",
    width: 110,
    render: (row) => (row.loaded ? "yes" : "no"),
  },
];

onMounted(async () => {
  await load();
  await loadVersion();
});
</script>

<template>
  <div>
    <div class="toolbar">
      <n-select v-model:value="selected" :options="options" style="width: 200px" />
      <n-button v-for="action in ['restart', 'reload', 'start', 'stop']" :key="action" secondary
        :disabled="!current?.installed" @click="serviceAction(action)">{{ action }}</n-button>
      <span class="spacer" />
      <n-tag v-if="current" size="small" :bordered="false" :type="current.running ? 'success' : 'default'">
        {{ current.service }}: {{ current.running ? "running" : "stopped" }}
      </n-tag>
      <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
    </div>

    <n-empty v-if="!versions.length" description="No PHP installation found. Install PHP-FPM from the App store page." />

    <template v-else-if="current">
      <n-alert v-if="!current.installed" type="warning" :bordered="false" style="margin-bottom: 12px">
        {{ current.path }} exists but has no binary or php.ini, so this build looks half-installed.
      </n-alert>

      <n-card size="small" style="margin-bottom: 14px">
        <dl class="kv">
          <dt>Path</dt><dd class="mono">{{ current.path || "—" }}</dd>
          <dt>Binary</dt><dd class="mono">{{ current.binary || "—" }}</dd>
          <dt>php.ini</dt><dd class="mono">{{ current.ini || "—" }}</dd>
          <dt>FPM socket</dt><dd class="mono">{{ current.socket }}</dd>
        </dl>
      </n-card>

      <n-tabs type="line" animated>
        <n-tab-pane name="settings" tab="Settings">
          <n-card size="small">
            <n-grid cols="1 s:2 l:3" responsive="screen" :x-gap="14">
              <n-gi v-for="key in ini.tunable" :key="key">
                <n-form-item :label="key" label-placement="top" size="small">
                  <n-input v-model:value="draftValues[key]" :placeholder="ini.values[key] || 'not set'" class="mono" />
                </n-form-item>
              </n-gi>
            </n-grid>
            <n-space>
              <n-button type="primary" size="small" @click="saveValues">Save</n-button>
              <n-button size="small" @click="serviceAction('reload')">Reload FPM</n-button>
            </n-space>
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="ini" tab="php.ini">
          <p class="muted mono">{{ ini.path }}</p>
          <n-input v-model:value="ini.content" type="textarea" :rows="24" class="mono" />
          <n-button type="primary" size="small" style="margin-top: 10px" @click="saveRaw">Save file</n-button>
        </n-tab-pane>

        <n-tab-pane name="extensions" tab="Extensions">
          <n-card size="small">
            <n-data-table :columns="extensionColumns" :data="extensions" size="small" :bordered="false"
              :max-height="460" :row-key="(row) => row.name" />
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="fpm" tab="FPM pool">
          <p class="muted mono">{{ fpmConf.path || "no pool config found" }}</p>
          <n-input v-model:value="fpmConf.content" type="textarea" :rows="22" class="mono" />
          <n-button type="primary" size="small" style="margin-top: 10px" :disabled="!fpmConf.path" @click="saveFpm">
            Save pool config
          </n-button>
        </n-tab-pane>

        <n-tab-pane name="status" tab="Service">
          <n-card v-if="fpm" size="small">
            <pre class="log-pane mono">{{ fpm.status }}</pre>
          </n-card>
        </n-tab-pane>

        <n-tab-pane name="slow" tab="Slow log">
          <p class="muted mono">{{ slow.path || "no slow log configured" }}</p>
          <n-card size="small" embedded>
            <pre class="log-pane mono">{{ slow.lines.join("\n") || "Nothing logged." }}</pre>
          </n-card>
        </n-tab-pane>
      </n-tabs>
    </template>
  </div>
</template>

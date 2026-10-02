<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NAlert, NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput,
  NInputNumber, NModal, NPopconfirm, NSelect, NSpace, NStatistic, NTabPane, NTabs, NTag,
  useDialog, useMessage,
} from "naive-ui";
import { api } from "../api";
import { bytes, datetime, duration, number } from "../format";

const message = useMessage();
const dialog = useDialog();

const tab = ref("mysql");
const engines = ref([]);
const loading = ref(false);

const mysqlRows = ref([]);
const mysqlStatus = ref({ available: false, server_databases: [] });
const createOpen = ref(false);
const draft = reactive({ name: "", username: "", password: "", charset: "utf8mb4", note: "" });

const pg = ref({ available: false, databases: [] });
const pgDraft = reactive({ name: "", username: "", password: "" });

const mongo = ref({ available: false, databases: [] });
const redis = ref({ available: false });
const redisConfig = ref([]);
const redisKeys = ref([]);
const redisPattern = ref("*");

const servers = ref([]);
const serverOpen = ref(false);
const serverDraft = reactive({
  name: "", engine: "mysql", host: "127.0.0.1", port: 3306, username: "", password: "", note: "",
});

const engineOptions = computed(() =>
  engines.value.map((item) => ({ label: item.label, value: item.key })),
);

async function load() {
  loading.value = true;
  try {
    engines.value = await api("/databases/engines");
    const [rows, status] = await Promise.all([
      api("/databases"),
      api("/databases/status").catch(() => ({ available: false, server_databases: [] })),
    ]);
    mysqlRows.value = rows;
    mysqlStatus.value = status;
    servers.value = await api("/databases/servers").catch(() => []);
  } finally {
    loading.value = false;
  }
}

async function loadPg() {
  pg.value = await api("/databases/postgres").catch(() => ({ available: false, databases: [] }));
}
async function loadMongo() {
  mongo.value = await api("/databases/mongodb").catch(() => ({ available: false, databases: [] }));
}
async function loadRedis() {
  redis.value = await api("/databases/redis").catch(() => ({ available: false }));
  if (redis.value.available) {
    redisConfig.value = await api("/databases/redis/config").catch(() => []);
    await loadRedisKeys();
  }
}
async function loadRedisKeys() {
  redisKeys.value = await api("/databases/redis/keys", {
    params: { pattern: redisPattern.value, limit: 200 },
  }).catch(() => []);
}

async function createMysql() {
  if (!draft.name.trim()) return message.warning("A database name is required");
  try {
    await api("/databases", { method: "POST", body: { ...draft } });
    message.success(`${draft.name} created`);
    createOpen.value = false;
    Object.assign(draft, { name: "", username: "", password: "", note: "" });
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function showCredentials(row) {
  const data = await api(`/databases/${row.id}/credentials`);
  dialog.info({
    title: `${data.name} credentials`,
    content: () =>
      h("dl", { class: "kv" }, [
        h("dt", {}, "Database"), h("dd", { class: "mono" }, data.name),
        h("dt", {}, "User"), h("dd", { class: "mono" }, data.username),
        h("dt", {}, "Password"), h("dd", { class: "mono" }, data.password),
      ]),
    positiveText: "Close",
  });
}

async function resetPassword(row) {
  const result = await api(`/databases/${row.id}/password`, { method: "POST", body: { password: "" } });
  message.success(`New password set for ${result.name}`);
  await showCredentials(row);
}

async function backupMysql(row) {
  const record = await api(`/databases/${row.id}/backup`, { method: "POST" });
  message.success(`Dumped ${bytes(record.size)} to ${record.filename}`);
}

function dropMysql(row) {
  dialog.error({
    title: `Drop ${row.name}?`,
    content: "The database and its user are dropped. This cannot be undone.",
    positiveText: "Drop",
    negativeText: "Cancel",
    onPositiveClick: async () => {
      await api(`/databases/${row.id}`, { method: "DELETE" });
      message.success(`${row.name} dropped`);
      await load();
    },
  });
}

async function createPg() {
  try {
    const result = await api("/databases/postgres", { method: "POST", body: { ...pgDraft } });
    message.success(`${result.name} created with password ${result.password}`);
    await loadPg();
  } catch (error) {
    message.error(error.message);
  }
}

async function createServer() {
  try {
    await api("/databases/servers", { method: "POST", body: { ...serverDraft } });
    message.success("Server added");
    serverOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function testServer(row) {
  const result = await api(`/databases/servers/${row.id}/test`, { method: "POST" });
  result.ok ? message.success("Connected") : message.error(result.output.slice(0, 200));
}

const mysqlColumns = computed(() => [
  { title: "Database", key: "name" },
  { title: "User", key: "username", width: 150 },
  { title: "Charset", key: "charset", width: 100 },
  { title: "Note", key: "note", ellipsis: { tooltip: true } },
  { title: "Created", key: "created_at", width: 150, render: (row) => datetime(row.created_at) },
  {
    title: "Actions",
    key: "actions",
    width: 300,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => showCredentials(row) }, { default: () => "Credentials" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => resetPassword(row) }, { default: () => "New password" }),
          h(NButton, { size: "tiny", secondary: true, onClick: () => backupMysql(row) }, { default: () => "Backup" }),
          h(NButton, { size: "tiny", type: "error", secondary: true, onClick: () => dropMysql(row) }, { default: () => "Drop" }),
        ],
      }),
  },
]);

const pgColumns = [
  { title: "Database", key: "name" },
  { title: "Owner", key: "owner", width: 160 },
  { title: "Size", key: "size", width: 120, render: (row) => bytes(row.size) },
  {
    title: "Actions",
    key: "actions",
    width: 220,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, {
            size: "tiny", secondary: true,
            onClick: async () => {
              const result = await api(`/databases/postgres/${row.name}/password`, { method: "POST", body: { password: "" } });
              message.success(`New password: ${result.password}`);
            },
          }, { default: () => "New password" }),
          h(NButton, {
            size: "tiny", secondary: true,
            onClick: async () => {
              const record = await api(`/databases/postgres/${row.name}/backup`, { method: "POST" });
              message.success(`Dumped ${bytes(record.size)}`);
            },
          }, { default: () => "Backup" }),
          h(NButton, {
            size: "tiny", type: "error", secondary: true,
            onClick: async () => {
              await api(`/databases/postgres/${row.name}`, { method: "DELETE" });
              message.success(`${row.name} dropped`);
              await loadPg();
            },
          }, { default: () => "Drop" }),
        ],
      }),
  },
];

const mongoColumns = [
  { title: "Database", key: "name" },
  { title: "Size on disk", key: "size", width: 150, render: (row) => bytes(row.size) },
  {
    title: "Actions",
    key: "actions",
    width: 120,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/databases/mongodb/${row.name}`, { method: "DELETE" });
          message.success(`${row.name} dropped`);
          await loadMongo();
        },
      }, { default: () => "Drop" }),
  },
];

const redisKeyColumns = [
  { title: "Key", key: "key", ellipsis: { tooltip: true } },
  { title: "Type", key: "type", width: 100 },
  { title: "TTL", key: "ttl", width: 100, render: (row) => (row.ttl < 0 ? "none" : `${row.ttl}s`) },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/databases/redis/keys/${encodeURIComponent(row.key)}`, { method: "DELETE" });
          await loadRedisKeys();
        },
      }, { default: () => "Delete" }),
  },
];

const serverColumns = [
  { title: "Name", key: "name" },
  { title: "Engine", key: "engine", width: 110 },
  { title: "Host", key: "host" },
  { title: "Port", key: "port", width: 80 },
  { title: "User", key: "username", width: 130 },
  {
    title: "Actions",
    key: "actions",
    width: 170,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => testServer(row) }, { default: () => "Test" }),
          h(NButton, {
            size: "tiny", type: "error", secondary: true,
            onClick: async () => {
              await api(`/databases/servers/${row.id}`, { method: "DELETE" });
              await load();
            },
          }, { default: () => "Remove" }),
        ],
      }),
  },
];

const unmanaged = computed(() => {
  const known = new Set(mysqlRows.value.map((row) => row.name));
  return mysqlStatus.value.server_databases.filter((name) => !known.has(name));
});

onMounted(load);
</script>

<template>
  <div>
    <n-tabs v-model:value="tab" type="line" animated>
      <n-tab-pane name="mysql" tab="MySQL">
        <div class="toolbar">
          <n-button type="primary" :disabled="!mysqlStatus.available" @click="createOpen = true">
            Add database
          </n-button>
          <span class="spacer" />
          <n-tag size="small" :bordered="false" :type="mysqlStatus.available ? 'success' : 'error'">
            {{ mysqlStatus.available ? "server reachable" : "server unreachable" }}
          </n-tag>
          <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
        </div>

        <n-alert v-if="!mysqlStatus.available" type="warning" :bordered="false" style="margin-bottom: 12px">
          The panel cannot reach MySQL. Install it from the App store page, or set
          <code>mysql_user</code> and <code>mysql_password</code> under Settings.
        </n-alert>

        <n-card size="small">
          <n-data-table :columns="mysqlColumns" :data="mysqlRows" :loading="loading" :bordered="false"
            :row-key="(row) => row.id" size="small" />
        </n-card>

        <n-card v-if="unmanaged.length" size="small" title="On the server but not in the panel" style="margin-top: 14px">
          <n-space class="chip-list">
            <n-tag v-for="name in unmanaged" :key="name" size="small" :bordered="false">{{ name }}</n-tag>
          </n-space>
          <p class="muted" style="margin-top: 8px">
            These exist in MySQL but have no panel record, so the panel leaves them alone.
          </p>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="postgres" tab="PostgreSQL" @vue:mounted="loadPg">
        <n-alert v-if="!pg.available" type="info" :bordered="false" style="margin-bottom: 12px">
          PostgreSQL is not reachable. Install it from the App store page.
        </n-alert>
        <template v-else>
          <n-form inline label-placement="top" size="small" style="margin-bottom: 12px">
            <n-form-item label="Database"><n-input v-model:value="pgDraft.name" style="width: 160px" /></n-form-item>
            <n-form-item label="Role"><n-input v-model:value="pgDraft.username" placeholder="same as database" style="width: 160px" /></n-form-item>
            <n-form-item label="Password"><n-input v-model:value="pgDraft.password" placeholder="generated" style="width: 160px" /></n-form-item>
            <n-form-item label=" "><n-button size="small" type="primary" @click="createPg">Create</n-button></n-form-item>
          </n-form>
          <n-card size="small">
            <n-data-table :columns="pgColumns" :data="pg.databases" :bordered="false" size="small"
              :row-key="(row) => row.name" />
          </n-card>
        </template>
      </n-tab-pane>

      <n-tab-pane name="mongodb" tab="MongoDB" @vue:mounted="loadMongo">
        <n-alert v-if="!mongo.available" type="info" :bordered="false">
          MongoDB is not reachable. Install it from the App store page.
        </n-alert>
        <n-card v-else size="small">
          <n-data-table :columns="mongoColumns" :data="mongo.databases" :bordered="false" size="small"
            :row-key="(row) => row.name" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="redis" tab="Redis" @vue:mounted="loadRedis">
        <n-alert v-if="!redis.available" type="info" :bordered="false">
          Redis is not reachable. Install it from the App store page.
        </n-alert>
        <template v-else>
          <n-grid cols="2 s:4" responsive="screen" :x-gap="12" :y-gap="12">
            <n-gi><n-card size="small"><n-statistic label="Version" :value="redis.version" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Memory" :value="redis.used_memory_human" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Clients" :value="redis.connected_clients" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Uptime" :value="duration(redis.uptime_seconds)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Hits" :value="number(redis.hits)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Misses" :value="number(redis.misses)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Evicted" :value="number(redis.evicted)" /></n-card></n-gi>
            <n-gi><n-card size="small"><n-statistic label="Policy" :value="redis.maxmemory_policy || '—'" /></n-card></n-gi>
          </n-grid>

          <n-grid cols="1 l:2" responsive="screen" :x-gap="14" :y-gap="14" style="margin-top: 14px">
            <n-gi>
              <n-card size="small" title="Keys">
                <n-space style="margin-bottom: 10px">
                  <n-input v-model:value="redisPattern" placeholder="*" style="width: 160px" @keyup.enter="loadRedisKeys" />
                  <n-button size="small" @click="loadRedisKeys">Scan</n-button>
                  <n-popconfirm @positive-click="async () => { await api('/databases/redis/flush', { method: 'POST' }); message.success('Flushed'); await loadRedis(); }">
                    <template #trigger><n-button size="small" type="error" secondary>Flush all</n-button></template>
                    Every key in every database is deleted.
                  </n-popconfirm>
                </n-space>
                <n-data-table :columns="redisKeyColumns" :data="redisKeys" :bordered="false" size="small"
                  :max-height="300" :row-key="(row) => row.key" />
              </n-card>
            </n-gi>
            <n-gi>
              <n-card size="small" title="Configuration">
                <n-data-table size="small" :bordered="false" :data="redisConfig"
                  :row-key="(row) => row.key"
                  :columns="[{ title: 'Key', key: 'key' }, { title: 'Value', key: 'value', ellipsis: { tooltip: true } }]" />
                <n-space v-if="redis.keyspace?.length" class="chip-list" style="margin-top: 10px">
                  <n-tag v-for="entry in redis.keyspace" :key="entry.db" size="small" :bordered="false">
                    {{ entry.db }}: {{ number(entry.keys) }} keys
                  </n-tag>
                </n-space>
              </n-card>
            </n-gi>
          </n-grid>
        </template>
      </n-tab-pane>

      <n-tab-pane name="servers" tab="Remote servers">
        <div class="toolbar">
          <n-button type="primary" @click="serverOpen = true">Add server</n-button>
          <span class="spacer" />
          <n-button quaternary @click="load">Refresh</n-button>
        </div>
        <n-card size="small">
          <n-data-table :columns="serverColumns" :data="servers" :bordered="false" size="small"
            :row-key="(row) => row.id" />
          <n-empty v-if="!servers.length" style="padding: 26px 0"
            description="No extra servers. Add one to keep its connection details beside the panel." />
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="createOpen" preset="card" title="Add MySQL database" style="max-width: 500px">
      <n-form label-placement="top" size="small">
        <n-form-item label="Database name"><n-input v-model:value="draft.name" placeholder="my_app" /></n-form-item>
        <n-form-item label="User"><n-input v-model:value="draft.username" placeholder="same as the database" /></n-form-item>
        <n-form-item label="Password"><n-input v-model:value="draft.password" placeholder="generated if blank" /></n-form-item>
        <n-grid cols="2" :x-gap="12">
          <n-gi>
            <n-form-item label="Charset">
              <n-select v-model:value="draft.charset"
                :options="['utf8mb4', 'utf8', 'latin1'].map((c) => ({ label: c, value: c }))" />
            </n-form-item>
          </n-gi>
          <n-gi><n-form-item label="Note"><n-input v-model:value="draft.note" /></n-form-item></n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="createOpen = false">Cancel</n-button>
          <n-button type="primary" @click="createMysql">Create</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="serverOpen" preset="card" title="Add database server" style="max-width: 500px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Name"><n-input v-model:value="serverDraft.name" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Engine"><n-select v-model:value="serverDraft.engine" :options="engineOptions" /></n-form-item></n-gi>
        </n-grid>
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Host"><n-input v-model:value="serverDraft.host" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Port"><n-input-number v-model:value="serverDraft.port" :min="1" :max="65535" style="width: 100%" /></n-form-item></n-gi>
        </n-grid>
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="User"><n-input v-model:value="serverDraft.username" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Password"><n-input v-model:value="serverDraft.password" type="password" show-password-on="click" /></n-form-item></n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="serverOpen = false">Cancel</n-button>
          <n-button type="primary" @click="createServer">Add</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

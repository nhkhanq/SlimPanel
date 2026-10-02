<script setup>
import { computed, h, onMounted, reactive, ref } from "vue";
import {
  NButton, NCard, NDataTable, NEmpty, NForm, NFormItem, NGi, NGrid, NInput, NInputNumber,
  NModal, NSelect, NSpace, NSwitch, NTabPane, NTabs, NTag, useMessage,
} from "naive-ui";
import { api } from "../api";
import { datetime } from "../format";

const message = useMessage();
const channels = ref([]);
const rules = ref([]);
const events = ref([]);
const metrics = ref([]);
const loading = ref(false);

const channelOpen = ref(false);
const channelDraft = reactive({ name: "", kind: "webhook", config: {} });

const ruleDraft = reactive({
  name: "", metric: "cpu", operator: ">", threshold: 90, target: "",
  channel_id: null, cooldown_minutes: 60,
});

const testDraft = reactive({ title: "Hello from SlimPanel", body: "Testing the alert pipeline.", channel_id: null });

const KIND_FIELDS = {
  webhook: [["url", "https://example.com/hook"]],
  slack: [["url", "https://hooks.slack.com/services/…"]],
  dingtalk: [["url", "https://oapi.dingtalk.com/robot/send?access_token=…"]],
  wecom: [["url", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=…"]],
  telegram: [["token", "bot token"], ["chat_id", "chat id"]],
  email: [
    ["host", "smtp.example.com"], ["port", "587"], ["username", "panel@example.com"],
    ["password", "app password"], ["to", "you@example.com"], ["from", "optional"],
  ],
};

const kindOptions = Object.keys(KIND_FIELDS).map((key) => ({ label: key, value: key }));
const fields = computed(() => KIND_FIELDS[channelDraft.kind] || []);
const metricOptions = computed(() => metrics.value.map((m) => ({ label: m.label, value: m.key })));
const channelOptions = computed(() => channels.value.map((c) => ({ label: `${c.name} (${c.kind})`, value: c.id })));

async function load() {
  loading.value = true;
  try {
    const [channelRows, ruleRows, eventRows, metricRows] = await Promise.all([
      api("/notify/channels"),
      api("/notify/rules"),
      api("/notify/events", { params: { limit: 100 } }),
      api("/notify/metrics"),
    ]);
    channels.value = channelRows;
    rules.value = ruleRows;
    events.value = eventRows;
    metrics.value = metricRows;
  } finally {
    loading.value = false;
  }
}

function openChannel() {
  channelDraft.config = {};
  channelOpen.value = true;
}

async function createChannel() {
  try {
    await api("/notify/channels", { method: "POST", body: { ...channelDraft } });
    message.success("Channel added");
    channelOpen.value = false;
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function testChannel(row) {
  try {
    const result = await api(`/notify/channels/${row.id}/test`, { method: "POST" });
    message.success(result.detail || "Delivered");
  } catch (error) {
    message.error(error.message);
  }
}

async function createRule() {
  try {
    await api("/notify/rules", { method: "POST", body: { ...ruleDraft } });
    message.success("Rule added");
    await load();
  } catch (error) {
    message.error(error.message);
  }
}

async function evaluate() {
  const result = await api("/notify/evaluate", { method: "POST" });
  message.success(result.fired ? `${result.fired} alert(s) fired` : "No rule matched");
  await load();
}

async function sendTest() {
  await api("/notify/send", { method: "POST", body: { ...testDraft } });
  message.success("Sent");
  await load();
}

const channelColumns = [
  { title: "Name", key: "name" },
  { title: "Kind", key: "kind", width: 110 },
  {
    title: "Config",
    key: "config",
    render: (row) =>
      h("span", { class: "mono muted" },
        Object.entries(row.config).map(([k, v]) => `${k}=${v}`).join("  ")),
  },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/notify/channels/${row.id}`, { method: "PATCH", body: { enabled: value } });
          await load();
        },
      }),
  },
  {
    title: "Actions",
    key: "actions",
    width: 160,
    render: (row) =>
      h(NSpace, { size: 4 }, {
        default: () => [
          h(NButton, { size: "tiny", secondary: true, onClick: () => testChannel(row) }, { default: () => "Test" }),
          h(NButton, {
            size: "tiny", type: "error", secondary: true,
            onClick: async () => {
              await api(`/notify/channels/${row.id}`, { method: "DELETE" });
              await load();
            },
          }, { default: () => "Remove" }),
        ],
      }),
  },
];

const ruleColumns = [
  { title: "Rule", key: "name" },
  {
    title: "Condition",
    key: "metric",
    render: (row) => `${row.metric} ${row.operator} ${row.threshold}${row.target ? ` (${row.target})` : ""}`,
  },
  {
    title: "Channel",
    key: "channel_id",
    width: 150,
    render: (row) => channels.value.find((c) => c.id === row.channel_id)?.name || "all enabled",
  },
  { title: "Cooldown", key: "cooldown_minutes", width: 100, render: (row) => `${row.cooldown_minutes}m` },
  { title: "Last fired", key: "last_fired_at", width: 160, render: (row) => datetime(row.last_fired_at) || "never" },
  {
    title: "Enabled",
    key: "enabled",
    width: 90,
    render: (row) =>
      h(NSwitch, {
        value: row.enabled, size: "small",
        "onUpdate:value": async (value) => {
          await api(`/notify/rules/${row.id}`, { method: "PATCH", body: { enabled: value } });
          await load();
        },
      }),
  },
  {
    title: "",
    key: "actions",
    width: 90,
    render: (row) =>
      h(NButton, {
        size: "tiny", type: "error", secondary: true,
        onClick: async () => {
          await api(`/notify/rules/${row.id}`, { method: "DELETE" });
          await load();
        },
      }, { default: () => "Remove" }),
  },
];

const eventColumns = [
  { title: "When", key: "created_at", width: 160, render: (row) => datetime(row.created_at) },
  { title: "Title", key: "title" },
  { title: "Body", key: "body", ellipsis: { tooltip: true } },
  {
    title: "Delivered",
    key: "delivered",
    width: 110,
    render: (row) =>
      h(NTag, { size: "small", bordered: false, type: row.delivered ? "success" : "warning" },
        { default: () => (row.delivered ? "yes" : "no") }),
  },
  { title: "Detail", key: "detail", ellipsis: { tooltip: true } },
];

onMounted(load);
</script>

<template>
  <div>
    <n-tabs type="line" animated>
      <n-tab-pane name="channels" tab="Channels">
        <div class="toolbar">
          <n-button type="primary" @click="openChannel">Add channel</n-button>
          <span class="spacer" />
          <n-button quaternary :loading="loading" @click="load">Refresh</n-button>
        </div>
        <n-card size="small">
          <n-data-table :columns="channelColumns" :data="channels" :bordered="false" size="small"
            :row-key="(row) => row.id" />
          <n-empty v-if="!channels.length" style="padding: 26px 0"
            description="No channels. Add a webhook, Telegram bot or SMTP account to get alerts." />
        </n-card>

        <n-card size="small" title="Send a test message" style="margin-top: 14px">
          <n-form inline label-placement="top" size="small">
            <n-form-item label="Title"><n-input v-model:value="testDraft.title" style="width: 220px" /></n-form-item>
            <n-form-item label="Body"><n-input v-model:value="testDraft.body" style="width: 280px" /></n-form-item>
            <n-form-item label="Channel">
              <n-select v-model:value="testDraft.channel_id" :options="channelOptions" clearable
                placeholder="all enabled" style="width: 180px" />
            </n-form-item>
            <n-form-item label=" "><n-button size="small" type="primary" @click="sendTest">Send</n-button></n-form-item>
          </n-form>
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="rules" tab="Rules">
        <n-card size="small" title="New rule">
          <n-form label-placement="top" size="small">
            <n-grid cols="2 l:4" responsive="screen" :x-gap="12">
              <n-gi><n-form-item label="Name"><n-input v-model:value="ruleDraft.name" placeholder="CPU too high" /></n-form-item></n-gi>
              <n-gi><n-form-item label="Metric"><n-select v-model:value="ruleDraft.metric" :options="metricOptions" /></n-form-item></n-gi>
              <n-gi>
                <n-form-item label="Operator">
                  <n-select v-model:value="ruleDraft.operator"
                    :options="['>', '>=', '<', '<=', '=='].map((v) => ({ label: v, value: v }))" />
                </n-form-item>
              </n-gi>
              <n-gi><n-form-item label="Threshold"><n-input-number v-model:value="ruleDraft.threshold" style="width: 100%" /></n-form-item></n-gi>
            </n-grid>
            <n-grid cols="2 l:3" responsive="screen" :x-gap="12">
              <n-gi>
                <n-form-item label="Target (service or domain, where it applies)">
                  <n-input v-model:value="ruleDraft.target" placeholder="nginx" />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="Channel">
                  <n-select v-model:value="ruleDraft.channel_id" :options="channelOptions" clearable
                    placeholder="all enabled" />
                </n-form-item>
              </n-gi>
              <n-gi>
                <n-form-item label="Cooldown (minutes)">
                  <n-input-number v-model:value="ruleDraft.cooldown_minutes" :min="1" style="width: 100%" />
                </n-form-item>
              </n-gi>
            </n-grid>
            <n-space>
              <n-button type="primary" size="small" @click="createRule">Add rule</n-button>
              <n-button size="small" @click="evaluate">Evaluate now</n-button>
            </n-space>
          </n-form>
        </n-card>

        <n-card size="small" style="margin-top: 14px">
          <n-data-table :columns="ruleColumns" :data="rules" :bordered="false" size="small"
            :row-key="(row) => row.id" />
        </n-card>
      </n-tab-pane>

      <n-tab-pane name="events" tab="History">
        <n-card size="small">
          <n-data-table :columns="eventColumns" :data="events" :bordered="false" size="small"
            :row-key="(row) => row.id" />
          <n-empty v-if="!events.length" style="padding: 26px 0" description="No alerts have fired." />
        </n-card>
      </n-tab-pane>
    </n-tabs>

    <n-modal v-model:show="channelOpen" preset="card" title="Add notification channel" style="max-width: 500px">
      <n-form label-placement="top" size="small">
        <n-grid cols="2" :x-gap="12">
          <n-gi><n-form-item label="Name"><n-input v-model:value="channelDraft.name" /></n-form-item></n-gi>
          <n-gi><n-form-item label="Kind"><n-select v-model:value="channelDraft.kind" :options="kindOptions" /></n-form-item></n-gi>
        </n-grid>
        <n-form-item v-for="[key, hint] in fields" :key="key" :label="key">
          <n-input v-model:value="channelDraft.config[key]" :placeholder="hint"
            :type="key === 'password' ? 'password' : 'text'" show-password-on="click" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="channelOpen = false">Cancel</n-button>
          <n-button type="primary" @click="createChannel">Add</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

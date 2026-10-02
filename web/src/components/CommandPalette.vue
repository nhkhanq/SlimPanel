<script setup>
/* Ctrl/Cmd-K jump list over every page, so a 24-item sidebar stays usable. */
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { NIcon, NInput, NModal, NScrollbar } from "naive-ui";
import { menu } from "../router";

const props = defineProps({ show: Boolean });
const emit = defineEmits(["update:show"]);

const router = useRouter();
const query = ref("");
const active = ref(0);

const entries = menu.flatMap((group) =>
  group.children.map((item) => ({ ...item, group: group.label })),
);

const results = computed(() => {
  const needle = query.value.trim().toLowerCase();
  if (!needle) return entries;
  return entries.filter(
    (item) =>
      item.name.toLowerCase().includes(needle) ||
      item.group.toLowerCase().includes(needle) ||
      item.path.includes(needle),
  );
});

watch(results, () => {
  active.value = 0;
});

watch(
  () => props.show,
  (open) => {
    if (open) {
      query.value = "";
      active.value = 0;
    }
  },
);

function go(item) {
  if (!item) return;
  router.push(item.path);
  emit("update:show", false);
}

function onKeydown(event) {
  if (event.key === "ArrowDown") {
    event.preventDefault();
    active.value = Math.min(active.value + 1, results.value.length - 1);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    active.value = Math.max(active.value - 1, 0);
  } else if (event.key === "Enter") {
    go(results.value[active.value]);
  }
}
</script>

<template>
  <n-modal
    :show="props.show"
    preset="card"
    style="max-width: 520px"
    title="Go to"
    @update:show="(value) => emit('update:show', value)"
  >
    <n-input
      v-model:value="query"
      autofocus
      clearable
      placeholder="Search pages…"
      @keydown="onKeydown"
    />
    <n-scrollbar style="max-height: 50vh; margin-top: 12px">
      <div
        v-for="(item, index) in results"
        :key="item.path"
        class="row"
        :class="{ active: index === active }"
        @click="go(item)"
        @mouseenter="active = index"
      >
        <n-icon size="17" :component="item.icon" />
        <span class="name">{{ item.name }}</span>
        <span class="group">{{ item.group }}</span>
      </div>
      <p v-if="!results.length" class="muted" style="padding: 10px 4px">No page matches that.</p>
    </n-scrollbar>
  </n-modal>
</template>

<style scoped>
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
}

.row.active {
  background: rgba(32, 165, 58, 0.14);
}

.name {
  flex: 1;
  font-weight: 500;
}

.group {
  font-size: 12px;
  opacity: 0.6;
}
</style>

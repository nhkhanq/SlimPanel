<script setup>
/* The ring aaPanel puts across the top of its dashboard. */
import { computed } from "vue";
import { NCard, NProgress } from "naive-ui";
import { gaugeColors } from "../theme";

const props = defineProps({
  label: { type: String, required: true },
  percent: { type: Number, default: 0 },
  detail: { type: String, default: "" },
  caption: { type: String, default: "" },
  unit: { type: String, default: "%" },
  display: { type: String, default: "" },
});

const value = computed(() => Math.min(100, Math.max(0, Number(props.percent) || 0)));
const colour = computed(() => gaugeColors(value.value));
</script>

<template>
  <n-card size="small" :bordered="true">
    <div class="gauge">
      <n-progress
        type="circle"
        :stroke-width="8"
        :percentage="value"
        :color="colour"
        :rail-color="'rgba(130,140,155,0.18)'"
        :style="{ width: '92px' }"
      >
        <span class="reading">{{ display || `${value.toFixed(1)}${unit}` }}</span>
      </n-progress>
      <div class="meta">
        <strong>{{ label }}</strong>
        <span v-if="detail" class="muted">{{ detail }}</span>
        <span v-if="caption" class="muted">{{ caption }}</span>
      </div>
    </div>
  </n-card>
</template>

<style scoped>
.gauge {
  display: flex;
  align-items: center;
  gap: 14px;
}

.reading {
  font-size: 15px;
  font-weight: 600;
}

.meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
</style>

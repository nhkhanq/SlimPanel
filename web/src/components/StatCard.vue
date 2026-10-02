<script setup>
import { NCard, NProgress } from "naive-ui";

defineProps({
  label: { type: String, required: true },
  value: { type: String, required: true },
  note: { type: String, default: "" },
  percent: { type: Number, default: null },
  status: { type: String, default: "default" },
});
</script>

<template>
  <n-card size="small">
    <div class="label">{{ label }}</div>
    <div class="value">{{ value }}</div>
    <div class="note">{{ note }}</div>
    <n-progress
      v-if="percent !== null"
      type="line"
      :percentage="Math.min(percent, 100)"
      :status="status"
      :show-indicator="false"
      :height="6"
      style="margin-top: 10px"
    />
  </n-card>
</template>

<style scoped>
.label {
  font-size: 12px;
  opacity: 0.65;
}

.value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.25;
}

.note {
  font-size: 12px;
  opacity: 0.65;
  min-height: 18px;
}
</style>

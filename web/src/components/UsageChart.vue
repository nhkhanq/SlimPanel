<script setup>
import { computed, ref } from "vue";
import { state } from "../store";
import { seriesColors } from "../theme";

const props = defineProps({
  series: { type: Array, required: true },
  height: { type: Number, default: 180 },
  capacity: { type: Number, default: 60 },
  interval: { type: Number, default: 3 },
});

const WIDTH = 760;
const PAD = { top: 14, right: 56, bottom: 22, left: 36 };

const palette = computed(() => seriesColors[state.theme] || seriesColors.dark);
const plotWidth = computed(() => WIDTH - PAD.left - PAD.right);
const plotHeight = computed(() => props.height - PAD.top - PAD.bottom);

const hover = ref(null);

const xAt = (index) =>
  PAD.left + (props.capacity <= 1 ? 0 : (index / (props.capacity - 1)) * plotWidth.value);
const yAt = (value) => PAD.top + plotHeight.value * (1 - Math.min(Math.max(value, 0), 100) / 100);

const pointCount = computed(() => Math.max(...props.series.map((s) => s.points.length), 0));
const offset = computed(() => Math.max(props.capacity - pointCount.value, 0));
const spanLabel = computed(() => `${Math.round((props.capacity * props.interval) / 60)} min ago`);

const lines = computed(() =>
  props.series.map((entry) => ({
    ...entry,
    color: palette.value[entry.key] || palette.value.cpu,
    last: entry.points.at(-1) ?? 0,
    path: entry.points
      .map(
        (value, index) =>
          `${index ? "L" : "M"}${xAt(index + offset.value).toFixed(1)} ${yAt(value).toFixed(1)}`,
      )
      .join(" "),
  })),
);

const ticks = [0, 25, 50, 75, 100];
function onMove(event) {
  if (!pointCount.value) return;
  const box = event.currentTarget.getBoundingClientRect();
  const x = ((event.clientX - box.left) / box.width) * WIDTH;
  const slot = Math.round(((x - PAD.left) / plotWidth.value) * (props.capacity - 1));
  hover.value = Math.min(Math.max(slot - offset.value, 0), pointCount.value - 1);
}
</script>

<template>
  <div class="chart" :style="{ '--grid': palette.grid, '--ink': palette.text }">
    <div class="legend">
      <span v-for="line in lines" :key="line.key" class="legend-item">
        <i :style="{ background: line.color }" />
        {{ line.label }}
      </span>
    </div>

    <svg
      :viewBox="`0 0 ${WIDTH} ${height}`"
      preserveAspectRatio="none"
      role="img"
      :aria-label="`${series.map((s) => s.label).join(' and ')} usage over time`"
      @mousemove="onMove"
      @mouseleave="hover = null"
    >
      <g class="grid">
        <template v-for="tick in ticks" :key="tick">
          <line :x1="PAD.left" :x2="WIDTH - PAD.right" :y1="yAt(tick)" :y2="yAt(tick)" />
          <text :x="PAD.left - 8" :y="yAt(tick) + 4" text-anchor="end">{{ tick }}</text>
        </template>
        <text :x="PAD.left" :y="height - 6">{{ spanLabel }}</text>
        <text :x="WIDTH - PAD.right" :y="height - 6" text-anchor="end">now</text>
      </g>

      <path
        v-for="line in lines"
        :key="line.key"
        :d="line.path"
        fill="none"
        :stroke="line.color"
        stroke-width="2"
        stroke-linejoin="round"
        stroke-linecap="round"
      />

      <template v-for="line in lines" :key="`${line.key}-end`">
        <circle
          v-if="line.points.length"
          :cx="xAt(line.points.length - 1 + offset)"
          :cy="yAt(line.last)"
          r="3.5"
          :fill="line.color"
          :stroke="palette.surface"
          stroke-width="2"
        />
        <text
          v-if="line.points.length"
          class="value"
          :x="xAt(line.points.length - 1 + offset) + 9"
          :y="yAt(line.last) + 4"
        >
          {{ line.last.toFixed(0) }}%
        </text>
      </template>

      <g v-if="hover !== null && pointCount">
        <line class="crosshair" :x1="xAt(hover + offset)" :x2="xAt(hover + offset)" :y1="PAD.top" :y2="height - PAD.bottom" />
        <circle
          v-for="line in lines"
          :key="`${line.key}-hover`"
          :cx="xAt(hover + offset)"
          :cy="yAt(line.points[hover] ?? 0)"
          r="4"
          :fill="line.color"
          :stroke="palette.surface"
          stroke-width="2"
        />
      </g>
    </svg>

    <div v-if="hover !== null && pointCount" class="tooltip">
      <span v-for="line in lines" :key="`${line.key}-tip`">
        <i :style="{ background: line.color }" />
        {{ line.label }} {{ (line.points[hover] ?? 0).toFixed(1) }}%
      </span>
    </div>
  </div>
</template>

<style scoped>
.chart {
  position: relative;
}

svg {
  width: 100%;
  display: block;
}

.grid line {
  stroke: var(--grid);
  stroke-width: 1;
}

.grid text,
.value {
  fill: var(--ink);
  font-size: 11px;
  font-family: ui-sans-serif, system-ui, sans-serif;
}

.crosshair {
  stroke: var(--ink);
  stroke-width: 1;
  stroke-dasharray: 3 3;
  opacity: 0.6;
}

.legend,
.tooltip {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 12.5px;
  color: var(--ink);
}

.legend {
  margin-bottom: 4px;
}

.tooltip {
  margin-top: 2px;
  min-height: 19px;
}

.legend i,
.tooltip i {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 2px;
  margin-right: 6px;
}
</style>

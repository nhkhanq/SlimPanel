<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { NAlert, NCard } from "naive-ui";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import { wsUrl } from "../api";
import { state } from "../store";

const host = ref(null);
const closed = ref(false);
let term = null;
let socket = null;
let fit = null;
let onResize = null;

const themes = {
  dark: { background: "#171a21", foreground: "#e6e8ee", cursor: "#3987e5" },
  light: { background: "#ffffff", foreground: "#1a1d23", cursor: "#2a78d6" },
};

onMounted(() => {
  term = new Terminal({
    fontSize: 13,
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
    cursorBlink: true,
    theme: themes[state.theme] || themes.dark,
  });
  fit = new FitAddon();
  term.loadAddon(fit);
  term.open(host.value);
  fit.fit();

  socket = new WebSocket(wsUrl("/ws/terminal"));
  socket.onopen = () => send({ type: "resize", rows: term.rows, cols: term.cols });
  socket.onmessage = (event) => term.write(event.data);
  socket.onclose = () => {
    closed.value = true;
    term.write("\r\n\x1b[31m[connection closed]\x1b[0m\r\n");
  };

  term.onData((data) => send({ type: "input", data }));

  onResize = () => {
    fit.fit();
    send({ type: "resize", rows: term.rows, cols: term.cols });
  };
  window.addEventListener("resize", onResize);
});

function send(payload) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
}

onUnmounted(() => {
  window.removeEventListener("resize", onResize);
  socket?.close();
  term?.dispose();
});
</script>

<template>
  <div>
    <n-alert v-if="closed" type="warning" :bordered="false" style="margin-bottom: 12px">
      The shell session ended. Reload the page to start a new one.
    </n-alert>
    <n-card size="small" content-style="padding: 0">
      <div ref="host" class="terminal-host" />
    </n-card>
  </div>
</template>

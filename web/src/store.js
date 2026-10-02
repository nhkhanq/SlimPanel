import { reactive } from "vue";

const THEME_KEY = "slimpanel-theme";

function storedTheme() {
  try {
    return localStorage.getItem(THEME_KEY) || "dark";
  } catch {
    return "dark";
  }
}

export const state = reactive({
  user: null,
  theme: storedTheme(),
  ready: false,
});

export function setUser(user) {
  state.user = user;
}

export function toggleTheme() {
  state.theme = state.theme === "dark" ? "light" : "dark";
  try {
    localStorage.setItem(THEME_KEY, state.theme);
  } catch {
    /* private mode */
  }
}

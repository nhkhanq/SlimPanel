const root = location.pathname.replace(/\/index\.html$/, "").replace(/\/$/, "");

export const API = `${root}/api`;

export function wsUrl(path) {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${location.host}${root}${path}`;
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

let onUnauthorized = () => {};

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export async function api(path, { method = "GET", body, params } = {}) {
  const url = new URL(`${API}${path}`, location.origin);
  for (const [key, value] of Object.entries(params || {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  }

  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    onUnauthorized();
    throw new ApiError("Not authenticated", 401);
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(payload.detail || `${response.status} ${response.statusText}`, response.status);
  }
  if (response.status === 204) return null;
  return response.json();
}

export function downloadUrl(path, params = {}) {
  const url = new URL(`${API}${path}`, location.origin);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  return url.toString();
}

export async function uploadFile(path, file) {
  const form = new FormData();
  form.append("path", path);
  form.append("upload_file", file);
  const response = await fetch(`${API}/files/upload`, { method: "POST", body: form });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(payload.detail || "Upload failed", response.status);
  }
  return response.json();
}

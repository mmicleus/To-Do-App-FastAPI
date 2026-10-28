const TOKEN_KEY = "dailyTodos_access_token";
const LEGACY_TOKEN_KEY = "daymark_access_token";
const PAGE_SIZE = 100;

const authView = document.querySelector("#auth-view");
const appView = document.querySelector("#app-view");
const authForm = document.querySelector("#auth-form");
const authError = document.querySelector("#auth-error");
const signupFields = document.querySelector("#signup-fields");
const emailInput = document.querySelector("#email");
const passwordInput = document.querySelector("#password");
const passwordHint = document.querySelector("#password-hint");
const authSubmit = document.querySelector("#auth-submit");
const taskDialog = document.querySelector("#task-dialog");
const taskForm = document.querySelector("#task-form");
const taskList = document.querySelector("#task-list");
const toast = document.querySelector("#toast");

let token = localStorage.getItem(TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);
if (token && !localStorage.getItem(TOKEN_KEY)) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.removeItem(LEGACY_TOKEN_KEY);
}
let tasks = [];
let currentFilter = "all";
let currentUrgency = "all";
let editingTaskId = null;
let toastTimer;
let signupMode = false;

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function errorMessage(payload, fallback) {
  if (typeof payload?.detail === "string") return payload.detail;
  if (Array.isArray(payload?.detail)) {
    return payload.detail.map((item) => item.msg || "Invalid input").join(" ");
  }
  return fallback;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    throw new ApiError(errorMessage(payload, `Request failed (${response.status})`), response.status);
  }
  return payload;
}

function showAuthError(message = "") {
  authError.textContent = message;
  authError.hidden = !message;
}

function setAuthMode(createAccount) {
  signupMode = createAccount;
  document.querySelector("#login-tab").classList.toggle("is-active", !createAccount);
  document.querySelector("#signup-tab").classList.toggle("is-active", createAccount);
  document.querySelector("#login-tab").setAttribute("aria-selected", String(!createAccount));
  document.querySelector("#signup-tab").setAttribute("aria-selected", String(createAccount));
  signupFields.hidden = !createAccount;
  emailInput.required = createAccount;
  emailInput.disabled = !createAccount;
  passwordInput.autocomplete = createAccount ? "new-password" : "current-password";
  passwordHint.hidden = !createAccount;
  authSubmit.innerHTML = createAccount
    ? 'Create account <span aria-hidden="true">→</span>'
    : 'Sign in <span aria-hidden="true">→</span>';
  showAuthError();
}

function showApp() {
  authView.hidden = true;
  appView.hidden = false;
}

function showAuth(message = "") {
  appView.hidden = true;
  authView.hidden = false;
  showAuthError(message);
}

function setUser(user) {
  const username = user.username || "Your account";
  document.querySelector("#profile-name").textContent = username;
  document.querySelector("#profile-avatar").textContent = username.slice(0, 1).toUpperCase();
  document.querySelector("#greeting-name").textContent = username === "Your account" ? "" : `, ${username}`;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  document.querySelector(".welcome-row h1").firstChild.textContent = greeting;
  document.querySelector("#today-date").textContent = new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date());
}

async function startApp() {
  if (!token) {
    showAuth();
    return;
  }

  showApp();
  try {
    const user = await request("/users/me/");
    setUser(user);
    await loadTasks();
  } catch (error) {
    if (error.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      token = null;
      showAuth("Your session has expired. Please sign in again.");
      return;
    }
    showToast(error.message || "Couldn't connect to the app.", true);
  }
}

async function loadTasks() {
  const loaded = [];
  for (let skip = 0; ; skip += PAGE_SIZE) {
    const page = await request(`/todos/?limit=${PAGE_SIZE}&skip=${skip}`);
    loaded.push(...page);
    if (page.length < PAGE_SIZE) break;
  }

  tasks = loaded.sort((first, second) => second.id - first.id);
  renderTasks();
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function createTaskCard(task) {
  const card = makeElement("article", `task-card${task.completed ? " is-completed" : ""}`);
  const checkbox = makeElement("input", "task-checkbox");
  checkbox.type = "checkbox";
  checkbox.checked = task.completed;
  checkbox.setAttribute("aria-label", `${task.completed ? "Mark as incomplete" : "Complete"}: ${task.title}`);
  checkbox.addEventListener("change", () => updateTask(task.id, { completed: checkbox.checked }));

  const copy = makeElement("div", "task-copy");
  copy.append(makeElement("h3", "task-title", task.title));
  if (task.description) copy.append(makeElement("p", "task-description", task.description));

  const meta = makeElement("div", "task-meta");
  const badge = makeElement("span", "priority-badge");
  badge.append(makeElement("span", `priority-dot priority-${task.urgency}`));
  badge.append(document.createTextNode(task.urgency));
  meta.append(badge);

  const actions = makeElement("div", "task-actions");
  const editButton = makeElement("button", "icon-button", "✎");
  editButton.type = "button";
  editButton.setAttribute("aria-label", `Edit ${task.title}`);
  editButton.title = "Edit task";
  editButton.addEventListener("click", () => openTaskDialog(task));

  const deleteButton = makeElement("button", "icon-button delete-task", "×");
  deleteButton.type = "button";
  deleteButton.setAttribute("aria-label", `Delete ${task.title}`);
  deleteButton.title = "Delete task";
  deleteButton.addEventListener("click", () => deleteTask(task));
  actions.append(editButton, deleteButton);
  meta.append(actions);
  card.append(checkbox, copy, meta);
  return card;
}

function visibleTasks() {
  const search = document.querySelector("#task-search").value.trim().toLocaleLowerCase();
  return tasks.filter((task) => {
    if (currentFilter === "active" && task.completed) return false;
    if (currentFilter === "completed" && !task.completed) return false;
    if (currentUrgency !== "all" && task.urgency !== currentUrgency) return false;
    const content = `${task.title} ${task.description || ""}`.toLocaleLowerCase();
    return !search || content.includes(search);
  });
}

function renderTasks() {
  const openCount = tasks.filter((task) => !task.completed).length;
  const doneCount = tasks.length - openCount;
  document.querySelector("#total-count").textContent = tasks.length;
  document.querySelector("#open-count").textContent = openCount;
  document.querySelector("#done-count").textContent = doneCount;
  document.querySelector("#nav-all-count").textContent = tasks.length;
  document.querySelector("#nav-active-count").textContent = openCount;

  const labels = { all: "All tasks", active: "In progress", completed: "Completed" };
  document.querySelector("#list-title").firstChild.textContent = labels[currentFilter];

  const results = visibleTasks();
  document.querySelector("#list-count").textContent = results.length;
  taskList.replaceChildren(...results.map(createTaskCard));
  const empty = results.length === 0;
  document.querySelector("#empty-state").hidden = !empty;
  document.querySelector("#load-more-note").hidden = true;

  const hasTasks = tasks.length > 0;
  document.querySelector("#empty-title").textContent = hasTasks ? "Nothing matches." : "A fresh start.";
  document.querySelector("#empty-copy").textContent = hasTasks
    ? "Try a different search or filter to find what you’re looking for."
    : "Nothing on your list just yet. Add a task and make it yours.";
  document.querySelector("#empty-add-button").hidden = hasTasks;
}

function showToast(message, isError = false) {
  window.clearTimeout(toastTimer);
  toast.textContent = message;
  toast.classList.toggle("is-error", isError);
  toast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 3000);
}

function updateCounts() {
  document.querySelector("#title-count").textContent = document.querySelector("#task-title").value.length;
  document.querySelector("#description-count").textContent = document.querySelector("#task-description").value.length;
}

function openTaskDialog(task = null) {
  editingTaskId = task?.id ?? null;
  document.querySelector("#dialog-title").textContent = task ? "Edit your task" : "Add a task";
  document.querySelector("#save-task").innerHTML = task
    ? 'Save changes <span aria-hidden="true">→</span>'
    : 'Add task <span aria-hidden="true">→</span>';
  document.querySelector("#task-title").value = task?.title || "";
  document.querySelector("#task-description").value = task?.description || "";
  document.querySelector("#task-urgency").value = task?.urgency || "low";
  document.querySelector("#task-form-error").hidden = true;
  updateCounts();
  taskDialog.showModal();
  document.querySelector("#task-title").focus();
}

async function saveTask(event) {
  event.preventDefault();
  const error = document.querySelector("#task-form-error");
  error.hidden = true;
  const payload = {
    title: document.querySelector("#task-title").value.trim(),
    description: document.querySelector("#task-description").value.trim() || null,
    urgency: document.querySelector("#task-urgency").value,
  };

  try {
    if (editingTaskId === null) {
      await request("/todos/", { method: "POST", body: JSON.stringify(payload) });
      showToast("Task added. One step closer.");
    } else {
      await request(`/todos/${editingTaskId}`, { method: "PATCH", body: JSON.stringify(payload) });
      showToast("Your changes are saved.");
    }
    taskDialog.close();
    await loadTasks();
  } catch (requestError) {
    error.textContent = requestError.message || "Couldn't save this task.";
    error.hidden = false;
  }
}

async function updateTask(id, changes) {
  try {
    await request(`/todos/${id}`, { method: "PATCH", body: JSON.stringify(changes) });
    await loadTasks();
    showToast(changes.completed ? "Nicely done. Keep that momentum." : "Task moved back to your list.");
  } catch (error) {
    showToast(error.message || "Couldn't update this task.", true);
    await loadTasks();
  }
}

async function deleteTask(task) {
  if (!window.confirm(`Remove "${task.title}" from your list?`)) return;
  try {
    await request(`/todos/${task.id}`, { method: "DELETE" });
    await loadTasks();
    showToast("Task removed.");
  } catch (error) {
    showToast(error.message || "Couldn't remove this task.", true);
  }
}

async function submitAuth(event) {
  event.preventDefault();
  showAuthError();
  authSubmit.disabled = true;
  authSubmit.textContent = signupMode ? "Creating account..." : "Signing in...";

  try {
    if (signupMode) {
      await request("/sign-up", {
        method: "POST",
        body: JSON.stringify({
          username: document.querySelector("#username").value.trim(),
          email: emailInput.value.trim(),
          password: passwordInput.value,
        }),
      });
      setAuthMode(false);
      passwordInput.value = "";
      showAuthError("Account created. Sign in to get started.");
      return;
    }

    const formData = new URLSearchParams();
    formData.set("username", document.querySelector("#username").value.trim());
    formData.set("password", passwordInput.value);
    const response = await fetch("/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) throw new ApiError(errorMessage(payload, "Couldn't sign in."), response.status);

    token = payload.access_token;
    localStorage.setItem(TOKEN_KEY, token);
    passwordInput.value = "";
    await startApp();
  } catch (error) {
    showAuthError(error.message || "Couldn't connect to the app. Please try again.");
  } finally {
    authSubmit.disabled = false;
    authSubmit.innerHTML = signupMode
      ? 'Create account <span aria-hidden="true">→</span>'
      : 'Sign in <span aria-hidden="true">→</span>';
  }
}

document.querySelector("#login-tab").addEventListener("click", () => setAuthMode(false));
document.querySelector("#signup-tab").addEventListener("click", () => setAuthMode(true));
authForm.addEventListener("submit", submitAuth);
document.querySelector("#logout-button").addEventListener("click", () => {
  localStorage.removeItem(TOKEN_KEY);
  token = null;
  tasks = [];
  authForm.reset();
  setAuthMode(false);
  showAuth();
});

document.querySelector("#add-task-button").addEventListener("click", () => openTaskDialog());
document.querySelector("#empty-add-button").addEventListener("click", () => openTaskDialog());
document.querySelector("#cancel-task").addEventListener("click", () => taskDialog.close());
document.querySelector("#dialog-close").addEventListener("click", () => taskDialog.close());
taskForm.addEventListener("submit", saveTask);
document.querySelector("#task-title").addEventListener("input", updateCounts);
document.querySelector("#task-description").addEventListener("input", updateCounts);
document.querySelector("#task-search").addEventListener("input", renderTasks);

document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => {
    currentFilter = button.dataset.filter;
    document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("is-active", item === button));
    renderTasks();
  });
});

document.querySelectorAll(".filter-chip").forEach((button) => {
  button.addEventListener("click", () => {
    currentUrgency = button.dataset.urgency;
    document.querySelectorAll(".filter-chip").forEach((item) => item.classList.toggle("is-selected", item === button));
    renderTasks();
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !taskDialog.open && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    document.querySelector("#task-search").focus();
  }
});

startApp();

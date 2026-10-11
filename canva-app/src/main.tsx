import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import styles from "./index.css?inline";

// Inject styles directly so the JS bundle is 100% self-contained
if (typeof document !== "undefined") {
  const styleEl = document.createElement("style");
  styleEl.setAttribute("data-app", "canva-sinhala-caption");
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);
}

// Safely mount to existing #root or create it for Canva iframe
let rootEl = document.getElementById("root");
if (!rootEl && typeof document !== "undefined") {
  rootEl = document.createElement("div");
  rootEl.id = "root";
  document.body.appendChild(rootEl);
}

if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

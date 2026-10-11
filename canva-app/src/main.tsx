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

function renderApp() {
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
}

// Register Canva Design Editor intent if inside Canva, or render directly
async function bootstrap() {
  try {
    const { prepareDesignEditor } = await import("@canva/intents/design");
    prepareDesignEditor({
      render: async () => {
        renderApp();
      },
    });
  } catch (e) {
    console.log("Running app standalone:", e);
    renderApp();
  }
}

bootstrap();

// Uses relative paths since FastAPI serves both static files and API endpoints
const API_BASE_URL = "";

document.addEventListener("DOMContentLoaded", () => {
  initTabNavigation();
  initDiagnosisForm();
  initShowroomsButton();
  loadDashboardMetrics();
  loadAssessmentHistory();
});

/* -------------------------------------------------------------
 * 1. TAB SWITCHING SYSTEM
 * ------------------------------------------------------------- */
function initTabNavigation() {
  const navButtons = document.querySelectorAll(".nav-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  navButtons.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();

      const targetTabId = btn.getAttribute("data-tab");

      // Deactivate all buttons & hide all tabs
      navButtons.forEach((b) => b.classList.remove("active"));
      tabContents.forEach((tab) => (tab.style.display = "none"));

      // Activate clicked button & show target tab
      btn.classList.add("active");
      const activeTab = document.getElementById(targetTabId);
      if (activeTab) {
        activeTab.style.display = "block";
      }

      // Context-aware tab triggers
      if (targetTabId === "showrooms-tab") {
        fetchNearbyShowrooms();
      } else if (targetTabId === "sustainability-tab") {
        loadDashboardMetrics();
      } else if (targetTabId === "assessments-tab") {
        loadAssessmentHistory();
      }
    });
  });
}

/* -------------------------------------------------------------
 * 2. DIAGNOSTIC FORM SUBMISSION
 * ------------------------------------------------------------- */
function initDiagnosisForm() {
  const form = document.getElementById("diagnosis-form");
  const resultsContainer = document.getElementById("results-container");

  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault(); // STOP FORM PAGE REFRESH

    const fileInput = document.getElementById("image-upload");
    const descInput = document.getElementById("fault-description");

    if (!fileInput.files || fileInput.files.length === 0) {
      alert("Please upload an image of the item first.");
      return;
    }

    const formData = new FormData();
    formData.append("image", fileInput.files[0]);
    formData.append("description", descInput.value || "");

    // Set UI Loading State
    resultsContainer.style.display = "block";
    resultsContainer.innerHTML = "<p>⏳ Analyzing item with Gemini Vision AI...</p>";

    try {
      const response = await fetch(`${API_BASE_URL}/api/diagnose`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server returned status code ${response.status}`);
      }

      const data = await response.json();
      renderDiagnosticResults(data);
      loadDashboardMetrics(); // Refresh aggregate stats
    } catch (error) {
      console.error("Diagnostic Error:", error);
      resultsContainer.innerHTML = `<p style="color: red;">Failed to analyze image: ${error.message}. Ensure backend server is running.</p>`;
    }
  });
}

function renderDiagnosticResults(data) {
  const container = document.getElementById("results-container");
  const fiveR = data.five_r || {};

  container.innerHTML = `
    <h2>Assessment Result: ${data.item_name || "Hardware Device"}</h2>
    <p><strong>Identified Fault:</strong> ${data.fault || "N/A"}</p>
    <p><strong>AI Confidence Score:</strong> ${((data.confidence || 0) * 100).toFixed(0)}%</p>
    <hr>
    <h3>${data.recommendation_title || "RECOMMENDATION"}</h3>
    <p>${data.recommendation_text || ""}</p>
    
    <div style="margin: 15px 0; padding: 10px; background: rgba(0,0,0,0.03); border-radius: 6px;">
      <p><strong>Est. Repair Cost:</strong> ${data.estimated_repair_cost || "N/A"}</p>
      <p><strong>Est. Replacement Cost:</strong> ${data.estimated_replacement_cost || "N/A"}</p>
      <p><strong>Financial Savings:</strong> ${data.money_saved || "₹0"}</p>
      <p><strong>Prevented E-Waste:</strong> ${data.ewaste_saved || 0} kg</p>
      <p><strong>Carbon Prevented:</strong> ${data.carbon_prevented || 0} kg CO2e</p>
    </div>

    <h4>Actionable 5-R Path</h4>
    <ul>
      <li><strong>Repair:</strong> ${fiveR.repair || "N/A"}</li>
      <li><strong>Reuse:</strong> ${fiveR.reuse || "N/A"}</li>
      <li><strong>Resell:</strong> ${fiveR.resell || "N/A"}</li>
      <li><strong>Recycle:</strong> ${fiveR.recycle || "N/A"}</li>
      <li><strong>Replace:</strong> ${fiveR.replace || "N/A"}</li>
    </ul>
  `;
}

/* -------------------------------------------------------------
 * 3. GEOLOCATION & OPENSTREETMAP SHOWROOMS
 * ------------------------------------------------------------- */
function initShowroomsButton() {
  const btn = document.getElementById("get-location-btn");
  if (btn) {
    btn.addEventListener("click", () => fetchNearbyShowrooms());
  }
}

function fetchNearbyShowrooms() {
  const container = document.getElementById("showrooms-container");
  if (!container) return;

  if (!navigator.geolocation) {
    container.innerHTML = "<p>Geolocation is not supported by your browser.</p>";
    return;
  }

  container.innerHTML = "<p>Requesting location permission...</p>";

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      container.innerHTML = `<p>Searching OpenStreetMap for repair centers near coordinates (${lat.toFixed(3)}, ${lng.toFixed(3)})...</p>`;

      try {
        const response = await fetch(`${API_BASE_URL}/api/shops?lat=${lat}&lng=${lng}`);
        if (!response.ok) throw new Error("Failed to load nearby shops.");

        const shops = await response.json();
        renderShowrooms(shops);
      } catch (error) {
        console.error("Showrooms Fetch Error:", error);
        container.innerHTML = `<p style="color: red;">Error fetching nearby repair centers.</p>`;
      }
    },
    (error) => {
      console.warn("Geolocation denied or unavailable. Fetching default center list.");
      container.innerHTML = "<p style='color: orange;'>Location access was denied or unavailable. Showing default service centers:</p>";
      
      fetch(`${API_BASE_URL}/api/shops`)
        .then((res) => res.json())
        .then((shops) => renderShowrooms(shops))
        .catch(() => {
          container.innerHTML = "<p>Unable to load default repair centers.</p>";
        });
    }
  );
}

function renderShowrooms(shops) {
  const container = document.getElementById("showrooms-container");

  if (!shops || shops.length === 0) {
    container.innerHTML = "<p>No nearby repair shops found in your immediate radius.</p>";
    return;
  }

  container.innerHTML = shops
    .map(
      (shop) => `
    <div class="card" style="margin-bottom: 12px; border-left: 4px solid #10b981;">
      <h4>📍 ${shop.name}</h4>
      <p><strong>Location:</strong> ${shop.location}</p>
      <p><strong>Distance:</strong> ${shop.distance} | <strong>Rating:</strong> ⭐ ${shop.rating}</p>
      <p><strong>Est. Service Cost:</strong> ${shop.price_est}</p>
    </div>
  `
    )
    .join("");
}

/* -------------------------------------------------------------
 * 4. DASHBOARD METRICS & ASSESSMENT HISTORY FETCHERS
 * ------------------------------------------------------------- */
async function loadDashboardMetrics() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/dashboard`);
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById("stat-money").innerText = data.money_saved || "₹0";
    document.getElementById("stat-carbon").innerText = data.carbon_prevented || "0.0 kg CO2e";
    document.getElementById("stat-ewaste").innerText = data.ewaste_saved || "0.0 kg";
  } catch (err) {
    console.error("Failed to update dashboard stats:", err);
  }
}

async function loadAssessmentHistory() {
  const historyList = document.getElementById("history-list");
  if (!historyList) return;

  try {
    const res = await fetch(`${API_BASE_URL}/api/history`);
    if (!res.ok) return;

    const history = await res.json();
    if (!history || history.length === 0) {
      historyList.innerHTML = "<p>No previous assessments recorded yet.</p>";
      return;
    }

    historyList.innerHTML = history
      .map(
        (item) => `
      <div style="padding: 10px; border-bottom: 1px solid #eee;">
        <p><strong>ID:</strong> ${item.id} — <strong>${item.item_name}</strong></p>
        <p><strong>Issue:</strong> ${item.fault}</p>
      </div>
    `
      )
      .join("");
  } catch (err) {
    console.error("Failed to load history:", err);
  }
}
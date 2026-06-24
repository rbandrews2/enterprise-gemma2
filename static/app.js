const functionGrid = document.querySelector("#function-grid");
const form = document.querySelector("#ops-form");
const result = document.querySelector("#result");
const button = document.querySelector("#generate-button");
const sampleButton = document.querySelector("#sample-button");
const sessionStatus = document.querySelector("#session-status");
const activeFunctionTitle = document.querySelector("#active-function-title");
const endpointLabel = document.querySelector("#endpoint-label");

const functions = [
  {
    id: "plan",
    number: "01",
    title: "Draft Plan",
    endpoint: "/work-zone-plan",
    copy: "Generate the first field-ready traffic control plan from intake notes.",
    buildPayload: values => ({
      job_type: values.workType,
      road_type: values.roadType,
      location: values.location,
      speed_limit: values.speedLimit,
      crew_notes: values.notes
    })
  },
  {
    id: "checklist",
    number: "02",
    title: "Crew Checklist",
    endpoint: "/document",
    copy: "Create a supervisor checklist, daily plan, or customer-facing note.",
    buildPayload: values => ({
      document_type: "checklist",
      topic: `${values.workType} on ${values.roadType}`,
      details: `${values.location}. ${values.notes}`,
      tone: "professional"
    })
  },
  {
    id: "compliance",
    number: "03",
    title: "Compliance Package",
    endpoint: "/compliance-package-json",
    copy: "Build structured forms, review flags, and regulatory summary blocks.",
    buildPayload: buildPackagePayload
  },
  {
    id: "visual",
    number: "04",
    title: "Visual Prompt",
    endpoint: "/package-image-prompt",
    copy: "Prepare an AI-ready visual brief for work-zone diagrams and customer review.",
    buildPayload: buildPackagePayload
  },
  {
    id: "manifest",
    number: "05",
    title: "Package Manifest",
    endpoint: "/package-manifest",
    copy: "Generate the package index that helps teams track assets and approvals.",
    buildPayload: buildPackagePayload
  },
  {
    id: "email",
    number: "06",
    title: "Email Preview",
    endpoint: "/package-email-preview",
    copy: "Draft a customer update using the selected work-zone package details.",
    buildPayload: values => ({
      customer_name: "Customer",
      customer_email: values.customerEmail,
      customer_company: "Customer Company",
      package_request: buildPackagePayload(values)
    })
  },
  {
    id: "saved",
    number: "07",
    title: "Saved Package",
    endpoint: "/complete-package-saved-v13",
    copy: "Create the saved package record with map, Street View, PDF, and manifest paths.",
    buildPayload: buildPackagePayload
  },
  {
    id: "delivery",
    number: "08",
    title: "Delivery Record",
    endpoint: "/deliver-package",
    copy: "Prepare the delivery workflow and customer handoff record.",
    buildPayload: values => ({
      customer_name: "Customer",
      customer_email: values.customerEmail,
      customer_company: "Customer Company",
      package_request: buildPackagePayload(values)
    })
  }
];

let activeFunction = functions[0];

function buildPackagePayload(values) {
  return {
    location: {
      address: values.location,
      state: "VA"
    },
    work: {
      work_type: values.workType,
      work_zone_type: values.workZoneType,
      road_type: values.roadType,
      speed_limit: values.speedLimit,
      time_of_day: "night",
      duration: "single shift",
      lane_count: 2,
      shoulder_present: true,
      traffic_volume: "moderate"
    },
    site_conditions: {
      curves: false,
      hills: false,
      intersections: true,
      pedestrians: true,
      school_zone: false,
      weather_notes: "Confirm field conditions before deployment."
    },
    user_notes: values.notes,
    requested_outputs: [
      "forms",
      "checklists",
      "regulatory_summary",
      "diagram_spec"
    ]
  };
}

function readValues() {
  return {
    location: document.querySelector("#location").value.trim(),
    roadType: document.querySelector("#road-type").value.trim(),
    workType: document.querySelector("#work-type").value.trim(),
    workZoneType: document.querySelector("#work-zone-type").value.trim(),
    speedLimit: document.querySelector("#speed-limit").value.trim(),
    customerEmail: document.querySelector("#customer-email").value.trim(),
    notes: document.querySelector("#crew-notes").value.trim()
  };
}

function renderCards() {
  functionGrid.innerHTML = "";

  functions.forEach(item => {
    const card = document.createElement("button");
    card.className = `function-card${item.id === activeFunction.id ? " active" : ""}`;
    card.type = "button";
    card.setAttribute("aria-pressed", String(item.id === activeFunction.id));
    card.innerHTML = `
      <span>${item.number} / ${item.endpoint}</span>
      <h2>${item.title}</h2>
      <p>${item.copy}</p>
    `;
    card.addEventListener("click", () => selectFunction(item.id));
    functionGrid.append(card);
  });
}

function selectFunction(id) {
  activeFunction = functions.find(item => item.id === id) || functions[0];
  activeFunctionTitle.textContent = activeFunction.title;
  endpointLabel.textContent = activeFunction.endpoint;
  result.textContent = `${activeFunction.title} selected. Run the function when the job details are ready.`;
  renderCards();
}

async function loadSession() {
  if (!sessionStatus) return;

  try {
    const response = await fetch("/api/session");
    const session = await response.json();

    if (session.verified_user) {
      sessionStatus.textContent = `Signed in as ${session.verified_user}`;
      return;
    }

    sessionStatus.textContent = `Protected for ${session.allowed_domain}`;
  } catch {
    sessionStatus.textContent = "Sign in with your workzoneos.org account.";
  }
}

function formatOutput(data) {
  if (typeof data === "string") return data;
  if (data.text) return data.text;
  if (data.email_preview) return data.email_preview;
  if (data.package_id) {
    return JSON.stringify({
      package_id: data.package_id,
      package_uri: data.package_uri,
      manifest_uri: data.manifest_uri,
      delivery_uri: data.delivery_uri,
      assets: data.assets
    }, null, 2);
  }
  return JSON.stringify(data, null, 2);
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  button.disabled = true;
  result.textContent = `Running ${activeFunction.title}...`;

  try {
    const payload = activeFunction.buildPayload(readValues());
    const response = await fetch(activeFunction.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `${activeFunction.title} failed.`);
    }

    result.textContent = formatOutput(data);
  } catch (error) {
    result.textContent = `Unable to run ${activeFunction.title}: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});

sampleButton.addEventListener("click", () => {
  document.querySelector("#location").value = "Richmond, VA shoulder closure";
  document.querySelector("#road-type").value = "Urban arterial";
  document.querySelector("#work-type").value = "Line striping and traffic control";
  document.querySelector("#work-zone-type").value = "Shoulder closure";
  document.querySelector("#speed-limit").value = "35 mph";
  document.querySelector("#customer-email").value = "customer@example.com";
  document.querySelector("#crew-notes").value = "Night work, moderate traffic, supervisor review required, maintain pedestrian access.";
  result.textContent = "Sample job details restored.";
});

renderCards();
selectFunction(activeFunction.id);
loadSession();

const API_BASE = "/api/v1";

const uploadForm = document.getElementById("uploadForm");
const processButton = document.getElementById("processButton");
const message = document.getElementById("message");
const healthStatus = document.getElementById("healthStatus");
const documentsTableBody = document.getElementById("documentsTableBody");
const refreshButton = document.getElementById("refreshButton");


// -----------------------------
// API Health Check
// -----------------------------

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);

        if (!response.ok) {
            throw new Error("API is not healthy");
        }

        healthStatus.textContent = "API Online";
        healthStatus.style.background = "#dcfce7";
        healthStatus.style.color = "#166534";

    } catch (error) {

        healthStatus.textContent = "API Offline";
        healthStatus.style.background = "#fee2e2";
        healthStatus.style.color = "#991b1b";
    }
}


// -----------------------------
// Show Message
// -----------------------------

function showMessage(text, type) {

    message.textContent = text;
    message.className = `message ${type}`;
}


// -----------------------------
// Load Documents
// -----------------------------

async function loadDocuments() {

    documentsTableBody.innerHTML = `
        <tr>
            <td colspan="6">Loading documents...</td>
        </tr>
    `;

    try {

        const response = await fetch(`${API_BASE}/documents`);

        if (!response.ok) {
            throw new Error("Failed to load documents");
        }

        const documents = await response.json();

        if (documents.length === 0) {

            documentsTableBody.innerHTML = `
                <tr>
                    <td colspan="6">No documents processed yet.</td>
                </tr>
            `;

            return;
        }


        documentsTableBody.innerHTML = documents.map(document => `

            <tr>

                <td>${document.id}</td>

                <td>${escapeHtml(document.document_name)}</td>

                <td>${escapeHtml(document.document_type)}</td>

                <td>${escapeHtml(document.status)}</td>

                <td>${formatDate(document.created_at)}</td>

                <td>
                    <button
                        class="view-button"
                        onclick="viewDocument('${encodeURIComponent(document.document_name)}')">
                        View
                    </button>
                </td>

            </tr>

        `).join("");


    } catch (error) {

        documentsTableBody.innerHTML = `
            <tr>
                <td colspan="6">
                    Unable to load documents.
                </td>
            </tr>
        `;
    }
}


// -----------------------------
// View Document
// -----------------------------

function viewDocument(documentName) {

    window.location.href =
        `/document-result.html?document=${documentName}`;
}


// -----------------------------
// Process Document
// -----------------------------

uploadForm.addEventListener("submit", async function(event) {

    event.preventDefault();

    const documentType =
        document.getElementById("documentType").value;

    const fileInput =
        document.getElementById("file");

    if (!documentType) {
        showMessage("Please select a document type.", "error");
        return;
    }

    if (!fileInput.files.length) {
        showMessage("Please select a document.", "error");
        return;
    }


    const formData = new FormData();

    formData.append("document_type", documentType);
    formData.append("file", fileInput.files[0]);


    processButton.disabled = true;
    processButton.textContent = "Processing...";

    showMessage(
        "Document is being processed. This may take some time.",
        "success"
    );


    try {

        const response = await fetch(
            `${API_BASE}/documents/process`,
            {
                method: "POST",
                body: formData
            }
        );


        const data = await response.json();


        if (!response.ok) {

            const errorMessage =
                data.detail || "Document processing failed.";

            throw new Error(errorMessage);
        }


        showMessage(
            "Document processed successfully!",
            "success"
        );


        uploadForm.reset();

        await loadDocuments();


    } catch (error) {

        showMessage(
            error.message || "Something went wrong.",
            "error"
        );

    } finally {

        processButton.disabled = false;
        processButton.textContent = "Process Document";
    }

});


// -----------------------------
// Refresh Button
// -----------------------------

refreshButton.addEventListener("click", loadDocuments);


// -----------------------------
// Utility Functions
// -----------------------------

function formatDate(dateString) {

    if (!dateString) {
        return "-";
    }

    const date = new Date(dateString);

    if (isNaN(date.getTime())) {
        return dateString;
    }

    return date.toLocaleString();
}


function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// -----------------------------
// Initial Load
// -----------------------------

checkHealth();
loadDocuments();
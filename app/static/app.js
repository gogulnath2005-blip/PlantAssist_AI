const chatForm = document.getElementById("chatForm");
const questionInput = document.getElementById("questionInput");
const sendButton = document.getElementById("sendButton");

const messages = document.getElementById("messages");
const chatSection = document.getElementById("chatSection");
const welcomeSection = document.getElementById("welcomeSection");

const connectionStatus = document.getElementById("connectionStatus");
const clearChatButton = document.getElementById("clearChat");


// Check whether FastAPI is running
async function checkConnection() {
    const dot = document.querySelector(".connection-dot");

    try {
        const response = await fetch("/api/health");

        if (!response.ok) {
            throw new Error("API unavailable");
        }

        const data = await response.json();

        connectionStatus.textContent = "API connected";
        dot.classList.remove("offline");

        return data;

    } catch (error) {
        connectionStatus.textContent = "API disconnected";
        dot.classList.add("offline");

        return null;
    }
}


// Create an HTML element safely
function createElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = String(text);
    }

    return element;
}


// Show a message in the conversation
function addMessage(role, text) {

    welcomeSection.style.display = "none";
    chatSection.classList.add("visible");

    const message = createElement("div", `message ${role}`);

    const avatar = createElement(
        "div",
        "message-avatar",
        role === "assistant" ? "P" : "Y"
    );

    const content = createElement("div", "message-content");

    const name = createElement(
        "div",
        "message-name",
        role === "assistant" ? "PlantAssist AI" : "You"
    );

    const messageText = createElement("div", "message-text", text);

    content.appendChild(name);
    content.appendChild(messageText);

    message.appendChild(avatar);
    message.appendChild(content);

    messages.appendChild(message);

    scrollToBottom();

    return content;
}


// Display evidence sources
function displaySources(content, sources) {

    if (!Array.isArray(sources) || sources.length === 0) {
        return;
    }

    const heading = createElement(
        "div",
        "evidence-heading",
        `DOCUMENT EVIDENCE · ${sources.length} SOURCE(S)`
    );

    content.appendChild(heading);

    sources.forEach((source) => {

        const card = createElement("div", "source-card");

        const title = createElement(
            "div",
            "source-title",
            source.title || "Untitled document"
        );

        const metadata = createElement("div", "source-meta");

        const fields = [
            `Document: ${source.document_number || "Unknown"}`,
            `Revision: ${source.revision || "Unknown"}`,
            `Page: ${source.page ?? "Unknown"}`,
            `Effective: ${source.effective_date || "Unknown"}`,
            `Status: ${source.revision_status || "Unknown"}`
        ];

        fields.forEach((field) => {
            metadata.appendChild(
                createElement("span", "", field)
            );
        });

        const excerpt = createElement(
            "div",
            "source-excerpt",
            source.excerpt || "No excerpt available."
        );

        card.appendChild(title);
        card.appendChild(metadata);
        card.appendChild(excerpt);

        content.appendChild(card);
    });
}


// Display a clear abstention notice
function displayAbstention(content, response) {

    const notice = createElement(
        "div",
        "abstain-notice",
        response.answer ||
        "I could not find sufficient supporting evidence in the supplied documents. Please consult the approved plant procedure or responsible supervisor."
    );

    content.appendChild(notice);
}


// Show an API error
function displayError(message) {

    const content = addMessage(
        "assistant",
        "I could not complete your request."
    );

    content.appendChild(
        createElement("div", "error-notice", message)
    );
}


// Scroll to the latest message
function scrollToBottom() {
    chatSection.scrollTop = chatSection.scrollHeight;
}


// Ask the FastAPI backend
async function askPlantAssist(question) {

    if (!question.trim()) {
        return;
    }

    addMessage("user", question);

    questionInput.value = "";
    questionInput.style.height = "auto";

    sendButton.disabled = true;
    sendButton.querySelector("span:first-child").textContent = "Wait";

    const loadingMessage = addMessage(
        "assistant",
        "Searching the plant documents..."
    );

    loadingMessage.classList.add("typing");

    try {

        const response = await fetch("/api/ask", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },

            body: JSON.stringify({
                question: question
            })
        });

        const data = await response.json();

        loadingMessage.parentElement.remove();

        if (!response.ok) {
            throw new Error(
                data.detail
                    ? JSON.stringify(data.detail)
                    : `API request failed: ${response.status}`
            );
        }

        const answerContent = addMessage(
            "assistant",
            "PlantAssist response"
        );

        // If the backend abstains, show no evidence as an answer.
        if (data.status === "abstained" || !data.sources?.length) {

            displayAbstention(answerContent, data);

        } else {

            // This version retrieves evidence only.
            // It does not generate operational instructions.
            const explanation = createElement(
                "div",
                "message-text",
                data.answer || "Matching document evidence was retrieved."
            );

            answerContent.appendChild(explanation);

            displaySources(answerContent, data.sources);
        }

        if (data.note) {
            answerContent.appendChild(
                createElement("div", "message-text", data.note)
            );
        }

        scrollToBottom();

    } catch (error) {

        loadingMessage.parentElement?.remove();

        displayError(
            error.message || "Check whether the FastAPI server is running."
        );

    } finally {

        sendButton.disabled = false;
        sendButton.querySelector("span:first-child").textContent = "Send";

        questionInput.focus();
    }
}


// Submit a question
chatForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    await askPlantAssist(question);
});


// Suggested questions
document.querySelectorAll(".suggestion-card").forEach((button) => {

    button.addEventListener("click", async () => {

        const question = button.dataset.question;

        if (question) {
            await askPlantAssist(question);
        }
    });
});


// Clear conversation
clearChatButton.addEventListener("click", () => {

    messages.innerHTML = "";

    chatSection.classList.remove("visible");
    welcomeSection.style.display = "";

    questionInput.value = "";
    questionInput.focus();
});


// Automatically increase textarea height
questionInput.addEventListener("input", () => {

    questionInput.style.height = "auto";

    questionInput.style.height =
        Math.min(questionInput.scrollHeight, 130) + "px";
});


// Enter sends; Shift + Enter creates a new line
questionInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        chatForm.requestSubmit();
    }
});


// Initial connection check
checkConnection();

setInterval(checkConnection, 30000);
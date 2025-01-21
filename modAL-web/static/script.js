// Variables globales
const currentImage = document.getElementById("digit-to-label");
const labelInput = document.getElementById("label-input");
const submitButton = document.getElementById("submit-button");
const historyContainer = document.getElementById("history-container");
const performanceChartCanvas = document.getElementById("performance-chart");

// Función para cargar la imagen actual desde el backend
async function loadCurrentImage() {
    try {
        const response = await fetch("/api/current-image");
        if (!response.ok) throw new Error("Failed to load current image.");
        const data = await response.json();
        currentImage.src = `data:image/png;base64,${data.image}`;
    } catch (error) {
        console.error(error);
        alert("Error loading the current image.");
    }
}

// Función para enviar la etiqueta al backend
async function submitLabel() {
    const label = labelInput.value.trim();
    if (!label || isNaN(label) || label < 0 || label > 9) {
        alert("Please enter a valid label (0-9).");
        return;
    }

    try {
        const response = await fetch("/api/submit-label", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ label })
        });

        if (!response.ok) throw new Error("Failed to submit label.");
        const data = await response.json();
        alert(data.message);

        // Actualizar datos después de enviar la etiqueta
        labelInput.value = "";
        loadCurrentImage();
        loadHistory();
        loadPerformanceChart();
    } catch (error) {
        console.error(error);
        alert("Error submitting the label.");
    }
}

// Función para cargar el historial de las últimas 5 imágenes etiquetadas
async function loadHistory() {
    try {
        const response = await fetch("/api/history");
        if (!response.ok) throw new Error("Failed to load history.");
        const data = await response.json();

        // Actualizar historial en el frontend
        historyContainer.innerHTML = ""; // Limpiar historial anterior
        data.forEach(item => {
            const historyItem = document.createElement("div");
            historyItem.className = "history-item";
            historyItem.innerHTML = `
                <img src="data:image/png;base64,${item.image}" alt="Labeled digit">
                <span>Label: ${item.label}</span>
            `;
            historyContainer.appendChild(historyItem);
        });
    } catch (error) {
        console.error(error);
        alert("Error loading history.");
    }
}


// Función para cargar la gráfica de rendimiento
let performanceChart; // Variable global para manejar el gráfico

async function loadPerformanceChart() {
    try {
        const response = await fetch("/api/accuracy-scores");
        if (!response.ok) throw new Error("Failed to load performance scores.");
        const scores = await response.json();

        // Configurar o actualizar el gráfico
        if (!performanceChart) {
            performanceChart = new Chart(performanceChartCanvas, {
                type: "line",
                data: {
                    labels: scores.map((_, index) => `Query ${index + 1}`),
                    datasets: [{
                        label: "Accuracy",
                        data: scores,
                        borderColor: "rgba(75, 192, 192, 1)",
                        tension: 0.1,
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: { beginAtZero: true, max: 1 }
                    }
                }
            });
        } else {
            performanceChart.data.labels = scores.map((_, index) => `Query ${index + 1}`);
            performanceChart.data.datasets[0].data = scores;
            performanceChart.update();
        }
    } catch (error) {
        console.error(error);
        alert("Error loading performance chart.");
    }
}

// Asignar eventos y cargar datos iniciales
submitButton.addEventListener("click", submitLabel);
window.onload = () => {
    loadCurrentImage();
    loadHistory();
    loadPerformanceChart();
};

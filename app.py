from flask import Flask, jsonify, render_template_string

# Cria a instância da aplicação Flask
app = Flask(__name__)

# Dados simulados do projeto
project_data = {
    "sprintAtual": 1,
    "totalSprints": 4,
    "sprintDurationDays": 10,
    "sprint1": {
        "totalSP": 8,
        "stories": [
            { "id": 'H1', "title": 'Cadastrar novo projeto de construção', "sp": 3, "status": 'Concluído' },
            { "id": 'H8', "title": 'Definir orçamento inicial para projeto', "sp": 1, "status": 'Concluído' },
            { "id": 'H2', "title": 'Visualizar todos os projetos em lista', "sp": 2, "status": 'Em Andamento' },
            { "id": 'H3', "title": 'Editar informações básicas de um projeto', "sp": 2, "status": 'A Fazer' },
        ],
        "dailyProgressSP": [8, 8, 7, 6, 4, 4, 3, 2, 1, 0]
    },
    "velocityHistory": [
        { "sprint": 0, "planned": 10, "completed": 0 },
        { "sprint": 1, "planned": 8, "completed": 4 },
        { "sprint": 2, "planned": 9, "completed": 0 },
        { "sprint": 3, "planned": 10, "completed": 0 },
    ]
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard de Acompanhamento - AutoU</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .card-shadow { box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); }
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
            position: absolute;
            top: 50%;
            left: 50%;
            margin-left: -20px;
            margin-top: -20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .hidden { display: none; }
    </style>
</head>
<body class="bg-gray-50 text-gray-800">

    <div id="loader" class="loader"></div>

    <div id="dashboard-content" class="container mx-auto p-4 md:p-8 hidden">
        <!-- Cabeçalho -->
        <header class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900">Dashboard de Acompanhamento</h1>
            <p class="text-gray-600 mt-1">Projeto: Plataforma de Gestão de Obras AutoU</p>
        </header>

        <!-- Seção de KPIs Principais -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-white p-6 rounded-lg card-shadow">
                <h3 class="text-sm font-medium text-gray-500">Sprint Atual</h3>
                <p class="text-3xl font-semibold text-gray-900" id="sprint-atual"></p>
            </div>
            <div class="bg-white p-6 rounded-lg card-shadow">
                <h3 class="text-sm font-medium text-gray-500">Progresso da Sprint</h3>
                <p class="text-3xl font-semibold text-gray-900" id="sprint-progress"></p>
            </div>
            <div class="bg-white p-6 rounded-lg card-shadow">
                <h3 class="text-sm font-medium text-gray-500">Velocity (Média)</h3>
                <p class="text-3xl font-semibold text-gray-900" id="velocity-media"></p>
            </div>
            <div class="bg-white p-6 rounded-lg card-shadow">
                <h3 class="text-sm font-medium text-gray-500">Total de Sprints (V1)</h3>
                <p class="text-3xl font-semibold text-gray-900" id="total-sprints"></p>
            </div>
        </div>

        <!-- Seção de Gráficos -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div class="bg-white p-6 rounded-lg card-shadow"><h3 class="text-lg font-semibold mb-4">Sprint 1 - Burndown Chart</h3><canvas id="burndownChart"></canvas></div>
            <div class="bg-white p-6 rounded-lg card-shadow"><h3 class="text-lg font-semibold mb-4">Velocity do Time (Histórico)</h3><canvas id="velocityChart"></canvas></div>
        </div>

        <!-- Status das Histórias da Sprint -->
        <div class="bg-white p-6 rounded-lg card-shadow">
            <h3 class="text-lg font-semibold mb-4">Status das Histórias - Sprint 1</h3>
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">História</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Story Points</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        </tr>
                    </thead>
                    <tbody id="sprint-stories-table" class="bg-white divide-y divide-gray-200"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // --- LÓGICA DO DASHBOARD (AGORA DINÂMICO) ---
        document.addEventListener('DOMContentLoaded', async () => {
            try {
                // Busca os dados da nossa API Flask
                const response = await fetch('/api/data');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const projectData = await response.json();

                // Esconde o loader e mostra o conteúdo
                document.getElementById('loader').classList.add('hidden');
                document.getElementById('dashboard-content').classList.remove('hidden');

                // Renderiza o dashboard com os dados recebidos
                updateKPIs(projectData);
                renderStoriesTable(projectData);
                renderBurndownChart(projectData);
                renderVelocityChart(projectData);

            } catch (error) {
                console.error("Falha ao carregar dados do projeto:", error);
                document.getElementById('loader').textContent = "Erro ao carregar dados.";
            }
        });

        function updateKPIs(data) {
            document.getElementById('sprint-atual').textContent = data.sprintAtual;
            document.getElementById('total-sprints').textContent = data.totalSprints;

            const sprintData = data.sprint1;
            const completedSP = sprintData.stories
                .filter(s => s.status === 'Concluído')
                .reduce((acc, story) => acc + story.sp, 0);
            
            const progress = (completedSP / sprintData.totalSP) * 100;
            document.getElementById('sprint-progress').textContent = `${Math.round(progress)}%`;
            
            const completedVelocities = data.velocityHistory
                .filter(v => v.sprint > 0 && v.completed > 0)
                .map(v => v.completed);
            
            const avgVelocity = completedVelocities.length > 0 
                ? (completedVelocities.reduce((a, b) => a + b, 0) / completedVelocities.length)
                : data.sprint1.totalSP;

            document.getElementById('velocity-media').textContent = `${Math.round(avgVelocity)} SP`;
        }

        function getStatusBadge(status) {
            const badges = {
                'Concluído': 'bg-green-100 text-green-800',
                'Em Andamento': 'bg-yellow-100 text-yellow-800',
                'A Fazer': 'bg-gray-100 text-gray-800'
            };
            const classes = badges[status] || 'bg-gray-100 text-gray-800';
            return `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${classes}">${status}</span>`;
        }

        function renderStoriesTable(data) {
            const tableBody = document.getElementById('sprint-stories-table');
            let tableHTML = '';
            data.sprint1.stories.forEach(story => {
                tableHTML += `
                    <tr>
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${story.id}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${story.title}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${story.sp}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${getStatusBadge(story.status)}</td>
                    </tr>`;
            });
            tableBody.innerHTML = tableHTML;
        }

        function renderBurndownChart(data) {
            const ctx = document.getElementById('burndownChart').getContext('2d');
            const sprintData = data.sprint1;
            
            const labels = Array.from({ length: data.sprintDurationDays + 1 }, (_, i) => `Dia ${i}`);
            const idealLine = Array.from({ length: data.sprintDurationDays + 1 }, (_, i) => 
                sprintData.totalSP - (sprintData.totalSP / data.sprintDurationDays) * i
            );
            
            const diaAtual = 5;
            const realProgress = sprintData.dailyProgressSP.slice(0, diaAtual + 1);

            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Ideal (SP Restantes)',
                        data: idealLine,
                        borderColor: 'rgba(200, 200, 200, 1)',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        fill: false,
                        tension: 0.1
                    }, {
                        label: 'Real (SP Restantes)',
                        data: realProgress,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true, title: { display: true, text: 'Story Points' }}, x: { title: { display: true, text: 'Dias da Sprint' }}}}
            });
        }

        function renderVelocityChart(data) {
            const ctx = document.getElementById('velocityChart').getContext('2d');
            const history = data.velocityHistory.filter(v => v.sprint > 0);
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: history.map(v => `Sprint ${v.sprint}`),
                    datasets: [{
                        label: 'Planejado (SP)',
                        data: history.map(v => v.planned),
                        backgroundColor: 'rgba(200, 200, 200, 0.6)',
                        borderWidth: 1
                    }, {
                        label: 'Concluído (SP)',
                        data: history.map(v => v.completed),
                        backgroundColor: 'rgba(22, 163, 74, 0.6)',
                        borderWidth: 1
                    }]
                },
                options: { responsive: true, scales: { y: { beginAtZero: true, title: { display: true, text: 'Story Points' }}}}
            });
        }
    </script>
</body>
</html>
"""

#ROTAS DA API 
@app.route('/api/data')
def get_project_data():
    return jsonify(project_data)


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
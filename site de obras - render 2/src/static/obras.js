document.addEventListener('DOMContentLoaded', fetchObras);

async function fetchObras() {
    try {
        const response = await fetch(`${API_BASE_URL}/obras`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const obras = await response.json();
        const obrasListDiv = document.getElementById('obras-list');
        obrasListDiv.innerHTML = ''; // Clear previous content

        if (obras.length === 0) {
            obrasListDiv.innerHTML = '<p class="text-gray-400">Nenhuma obra encontrada. Adicione uma nova obra para começar!</p>';
            return;
        }

        obras.forEach(obra => {
            const obraCard = `
                <div class="bg-gray-800 glassmorphism rounded-lg shadow-lg p-6 flex flex-col justify-between hover:shadow-xl transition-all duration-300 ease-in-out transform hover:-translate-y-1">
                    <div>
                        <h2 class="text-xl font-semibold text-white mb-2">${obra.nome}</h2>
                        <p class="text-gray-400 mb-1"><i class="fas fa-map-marker-alt mr-2"></i>${obra.localizacao}</p>
                        <p class="text-gray-400 mb-1"><i class="fas fa-dollar-sign mr-2"></i>Valor: R$ ${obra.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                        <p class="text-gray-400 mb-4"><i class="fas fa-info-circle mr-2"></i>Status: ${obra.status}</p>
                        
                        <div class="w-full bg-gray-700 rounded-full h-2.5 mb-4">
                            <div class="bg-blue-600 h-2.5 rounded-full obra-progress-bar" style="width: ${obra.progresso}%;"></div>
                        </div>
                        <p class="text-gray-400 text-sm">Progresso: ${obra.progresso}%</p>
                    </div>
                    <div class="mt-4 flex justify-end space-x-2">
                        <button onclick="navigate('obra-detalhes', ${obra.id})" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
                            Ver Detalhes
                        </button>
                    </div>
                </div>
            `;
            obrasListDiv.innerHTML += obraCard;
        });
    } catch (error) {
        console.error('Erro ao buscar obras:', error);
        showToast('Erro ao carregar obras. Tente novamente.', 'error');
        document.getElementById('obras-list').innerHTML = '<p class="text-red-400">Não foi possível carregar as obras. Verifique sua conexão ou tente novamente mais tarde.</p>';
    }
}

function showCreateObraModal() {
    const body = `
        <div class="space-y-4">
            <div>
                <label for="obra-nome" class="block text-gray-300 text-sm font-bold mb-2">Nome da Obra:</label>
                <input type="text" id="obra-nome" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Nome da Obra">
            </div>
            <div>
                <label for="obra-localizacao" class="block text-gray-300 text-sm font-bold mb-2">Localização:</label>
                <input type="text" id="obra-localizacao" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Localização">
            </div>
            <div>
                <label for="obra-valor" class="block text-gray-300 text-sm font-bold mb-2">Valor:</label>
                <input type="number" id="obra-valor" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Valor" step="0.01">
            </div>
            <div>
                <label for="obra-status" class="block text-gray-300 text-sm font-bold mb-2">Status:</label>
                <select id="obra-status" class="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
                    <option value="Planejada">Planejada</option>
                    <option value="Em Andamento">Em Andamento</option>
                    <option value="Concluída">Concluída</option>
                    <option value="Pausada">Pausada</option>
                </select>
            </div>
            <div>
                <label for="obra-data-inicio" class="block text-gray-300 text-sm font-bold mb-2">Data de Início:</label>
                <input type="date" id="obra-data-inicio" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
            </div>
        </div>
    `;

    const footer = `
        <button onclick="closeModal()" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">Cancelar</button>
        <button onclick="createObra()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">Criar Obra</button>
    `;

    showModal('Criar Nova Obra', body, footer);
}

async function createObra() {
    const nome = document.getElementById('obra-nome').value;
    const localizacao = document.getElementById('obra-localizacao').value;
    const valor = parseFloat(document.getElementById('obra-valor').value);
    const status = document.getElementById('obra-status').value;
    const dataInicio = document.getElementById('obra-data-inicio').value;

    if (!nome || !localizacao || isNaN(valor) || !status || !dataInicio) {
        showToast('Por favor, preencha todos os campos.', 'warning');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/obras`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nome,
                localizacao,
                valor,
                status,
                dataInicio
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const newObra = await response.json();
        showToast('Obra criada com sucesso!', 'success');
        closeModal();
        fetchObras(); // Refresh the list
    } catch (error) {
        console.error('Erro ao criar obra:', error);
        showToast('Erro ao criar obra. Tente novamente.', 'error');
    }
}



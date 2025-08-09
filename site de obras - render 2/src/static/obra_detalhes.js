async function loadView() {
    const contentDiv = document.getElementById("content");
    contentDiv.innerHTML = `
        <button onclick="navigate(\'obras\')" class="mb-4 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">
            <i class="fas fa-arrow-left mr-2"></i>Voltar para Obras
        </button>
        <h1 class="text-3xl font-bold text-white mb-6" id="obra-detalhes-titulo"></h1>
        <div id="obra-info" class="bg-gray-800 glassmorphism rounded-lg shadow-lg p-6 mb-6"></div>
        
        <h2 class="text-2xl font-bold text-white mb-4">Etapas da Obra</h2>
        <div id="etapas-list" class="space-y-4 mb-6"></div>
        <button onclick="showCreateEtapaModal()" class="mb-6 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
            <i class="fas fa-plus-circle mr-2"></i>Adicionar Etapa
        </button>

        <h2 class="text-2xl font-bold text-white mb-4">Mobiliário</h2>
        <div id="mobiliario-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6"></div>
        <button onclick="showCreateMobiliarioModal()" class="mb-6 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg shadow-lg transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">
            <i class="fas fa-plus-circle mr-2"></i>Adicionar Mobiliário
        </button>
    `;

    fetchObraDetalhes(currentObraId);
    fetchEtapas(currentObraId);
    fetchMobiliario(currentObraId);
}

async function fetchObraDetalhes(obraId) {
    try {
        const response = await fetch(`${API_BASE_URL}/obras/${obraId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const obra = await response.json();
        document.getElementById("obra-detalhes-titulo").textContent = obra.nome;
        document.getElementById("obra-info").innerHTML = `
            <p class="text-gray-300 mb-2"><i class="fas fa-map-marker-alt mr-2"></i>Localização: ${obra.localizacao}</p>
            <p class="text-gray-300 mb-2"><i class="fas fa-dollar-sign mr-2"></i>Valor: R$ ${obra.valor.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
            <p class="text-gray-300 mb-2"><i class="fas fa-info-circle mr-2"></i>Status: ${obra.status}</p>
            <p class="text-gray-300 mb-2"><i class="fas fa-calendar-alt mr-2"></i>Início: ${new Date(obra.dataInicio).toLocaleDateString("pt-BR")}</p>
            <div class="w-full bg-gray-700 rounded-full h-2.5 mb-2">
                <div class="bg-blue-600 h-2.5 rounded-full obra-progress-bar" style="width: ${obra.progresso}%;"></div>
            </div>
            <p class="text-gray-300 text-sm">Progresso: ${obra.progresso}%</p>
        `;
    } catch (error) {
        console.error("Erro ao buscar detalhes da obra:", error);
        showToast("Erro ao carregar detalhes da obra.", "error");
    }
}

async function fetchEtapas(obraId) {
    try {
        const response = await fetch(`${API_BASE_URL}/obras/${obraId}/etapas`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const etapas = await response.json();
        const etapasListDiv = document.getElementById("etapas-list");
        etapasListDiv.innerHTML = "";

        if (etapas.length === 0) {
            etapasListDiv.innerHTML = 
                `<p class="text-gray-400">Nenhuma etapa encontrada para esta obra. Adicione uma nova etapa!</p>`;
            return;
        }

        etapas.forEach(etapa => {
            const fotosHtml = etapa.fotos.map(fotoUrl => `
                <img src="${fotoUrl}" alt="Foto da Etapa" class="w-24 h-24 object-cover rounded-lg cursor-pointer" onclick="showImageModal(\'${fotoUrl}\')">
            `).join("");

            const etapaCard = `
                <div class="bg-gray-800 glassmorphism rounded-lg shadow-lg p-4">
                    <h3 class="text-xl font-semibold text-white mb-2">${etapa.titulo}</h3>
                    <p class="text-gray-400 mb-2">${etapa.descricao}</p>
                    <p class="text-gray-400 text-sm mb-2"><i class="fas fa-calendar-check mr-2"></i>Data: ${new Date(etapa.dataEtapa).toLocaleDateString("pt-BR")}</p>
                    <div class="flex flex-wrap gap-2 mb-4">
                        ${fotosHtml}
                    </div>
                    <div class="flex justify-end space-x-2">
                        <button onclick="showEditEtapaModal(${etapa.id})" class="bg-yellow-600 hover:bg-yellow-700 text-white font-bold py-1 px-3 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-opacity-50">
                            Editar
                        </button>
                        <button onclick="softDeleteEtapa(${etapa.id})" class="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-3 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50">
                            Excluir
                        </button>
                    </div>
                </div>
            `;
            etapasListDiv.innerHTML += etapaCard;
        });
    } catch (error) {
        console.error("Erro ao buscar etapas:", error);
        showToast("Erro ao carregar etapas.", "error");
    }
}

function showCreateEtapaModal() {
    const body = `
        <div class="space-y-4">
            <div>
                <label for="etapa-titulo" class="block text-gray-300 text-sm font-bold mb-2">Título:</label>
                <input type="text" id="etapa-titulo" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Título da Etapa">
            </div>
            <div>
                <label for="etapa-descricao" class="block text-gray-300 text-sm font-bold mb-2">Descrição:</label>
                <textarea id="etapa-descricao" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Descrição da Etapa"></textarea>
            </div>
            <div>
                <label for="etapa-data" class="block text-gray-300 text-sm font-bold mb-2">Data:</label>
                <input type="date" id="etapa-data" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
            </div>
            <div>
                <label for="etapa-fotos-file" class="block text-gray-300 text-sm font-bold mb-2">Upload de Fotos:</label>
                <input type="file" id="etapa-fotos-file" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" multiple accept="image/*">
            </div>
            <div>
                <label for="etapa-fotos-url" class="block text-gray-300 text-sm font-bold mb-2">Ou URLs das Fotos (separadas por vírgula):</label>
                <input type="text" id="etapa-fotos-url" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="URL1, URL2, URL3">
            </div>
        </div>
    `;

    const footer = `
        <button onclick="closeModal()" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">Cancelar</button>
        <button onclick="createEtapa()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">Criar Etapa</button>
    `;

    showModal("Criar Nova Etapa", body, footer);
}

async function createEtapa() {
    const titulo = document.getElementById("etapa-titulo").value;
    const descricao = document.getElementById("etapa-descricao").value;
    const dataEtapa = document.getElementById("etapa-data").value;
    const fotosFile = document.getElementById("etapa-fotos-file").files;
    const fotosUrlInput = document.getElementById("etapa-fotos-url").value;
    let fotos = fotosUrlInput ? fotosUrlInput.split(",").map(url => url.trim()) : [];

    if (!titulo || !dataEtapa) {
        showToast("Por favor, preencha o título e a data da etapa.", "warning");
        return;
    }

    try {
        // Upload de arquivos se existirem
        if (fotosFile.length > 0) {
            const formData = new FormData();
            for (let i = 0; i < fotosFile.length; i++) {
                formData.append("file", fotosFile[i]);
            }
            const uploadResponse = await fetch(`${API_BASE_URL}/upload-foto`, {
                method: "POST",
                body: formData,
            });

            if (!uploadResponse.ok) {
                throw new Error(`HTTP error! status: ${uploadResponse.status}`);
            }
            const uploadResult = await uploadResponse.json();
            fotos.push(uploadResult.url);
        }

        const response = await fetch(`${API_BASE_URL}/obras/${currentObraId}/etapas`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                titulo,
                descricao,
                dataEtapa,
                fotos
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast("Etapa criada com sucesso!", "success");
        closeModal();
        fetchEtapas(currentObraId); // Refresh the list
    } catch (error) {
        console.error("Erro ao criar etapa:", error);
        showToast("Erro ao criar etapa. Tente novamente.", "error");
    }
}

async function showEditEtapaModal(etapaId) {
    try {
        const response = await fetch(`${API_BASE_URL}/etapas/${etapaId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const etapa = await response.json();

        const body = `
            <div class="space-y-4">
                <div>
                    <label for="edit-etapa-titulo" class="block text-gray-300 text-sm font-bold mb-2">Título:</label>
                    <input type="text" id="edit-etapa-titulo" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" value="${etapa.titulo}">
                </div>
                <div>
                    <label for="edit-etapa-descricao" class="block text-gray-300 text-sm font-bold mb-2">Descrição:</label>
                    <textarea id="edit-etapa-descricao" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">${etapa.descricao || ""}</textarea>
                </div>
                <div>
                    <label for="edit-etapa-data" class="block text-gray-300 text-sm font-bold mb-2">Data:</label>
                    <input type="date" id="edit-etapa-data" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" value="${etapa.dataEtapa}">
                </div>
                <div>
                    <label for="edit-etapa-fotos-file" class="block text-gray-300 text-sm font-bold mb-2">Upload de Fotos:</label>
                    <input type="file" id="edit-etapa-fotos-file" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" multiple accept="image/*">
                </div>
                <div>
                    <label for="edit-etapa-fotos-url" class="block text-gray-300 text-sm font-bold mb-2">Ou URLs das Fotos (separadas por vírgula):</label>
                    <input type="text" id="edit-etapa-fotos-url" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" value="${etapa.fotos.join(", ")}">
                </div>
            </div>
        `;

        const footer = `
            <button onclick="closeModal()" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">Cancelar</button>
            <button onclick="updateEtapa(${etapa.id})" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">Salvar Alterações</button>
        `;

        showModal("Editar Etapa", body, footer);
    } catch (error) {
        console.error("Erro ao carregar etapa para edição:", error);
        showToast("Erro ao carregar etapa para edição.", "error");
    }
}

async function updateEtapa(etapaId) {
    const titulo = document.getElementById("edit-etapa-titulo").value;
    const descricao = document.getElementById("edit-etapa-descricao").value;
    const dataEtapa = document.getElementById("edit-etapa-data").value;
    const fotosFile = document.getElementById("edit-etapa-fotos-file").files;
    const fotosUrlInput = document.getElementById("edit-etapa-fotos-url").value;
    let fotos = fotosUrlInput ? fotosUrlInput.split(",").map(url => url.trim()) : [];

    if (!titulo || !dataEtapa) {
        showToast("Por favor, preencha o título e a data da etapa.", "warning");
        return;
    }

    try {
        // Upload de arquivos se existirem
        if (fotosFile.length > 0) {
            const formData = new FormData();
            for (let i = 0; i < fotosFile.length; i++) {
                formData.append("file", fotosFile[i]);
            }
            const uploadResponse = await fetch(`${API_BASE_URL}/upload-foto`, {
                method: "POST",
                body: formData,
            });

            if (!uploadResponse.ok) {
                throw new Error(`HTTP error! status: ${uploadResponse.status}`);
            }
            const uploadResult = await uploadResponse.json();
            fotos.push(uploadResult.url);
        }

        const response = await fetch(`${API_BASE_URL}/etapas/${etapaId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                titulo,
                descricao,
                dataEtapa,
                fotos
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast("Etapa atualizada com sucesso!", "success");
        closeModal();
        fetchEtapas(currentObraId); // Refresh the list
    } catch (error) {
        console.error("Erro ao atualizar etapa:", error);
        showToast("Erro ao atualizar etapa. Tente novamente.", "error");
    }
}

async function softDeleteEtapa(etapaId) {
    if (!confirm("Tem certeza que deseja mover esta etapa para a lixeira?")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/etapas/${etapaId}/soft-delete`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ usuario: "Admin" }) // Pode ser dinâmico com usuário logado
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast("Etapa movida para a lixeira!", "success");
        fetchEtapas(currentObraId); // Refresh the list
    } catch (error) {
        console.error("Erro ao mover etapa para lixeira:", error);
        showToast("Erro ao mover etapa para lixeira. Tente novamente.", "error");
    }
}

async function fetchMobiliario(obraId) {
    try {
        const response = await fetch(`${API_BASE_URL}/obras/${obraId}/mobiliario`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const mobiliario = await response.json();
        const mobiliarioListDiv = document.getElementById("mobiliario-list");
        mobiliarioListDiv.innerHTML = "";

        if (mobiliario.length === 0) {
            mobiliarioListDiv.innerHTML = 
                `<p class="text-gray-400">Nenhum mobiliário encontrado para esta obra. Adicione um novo mobiliário!</p>`;
            return;
        }

        mobiliario.forEach(mob => {
            const mobiliarioCard = `
                <div class="bg-gray-800 glassmorphism rounded-lg shadow-lg p-4">
                    <h3 class="text-xl font-semibold text-white mb-2">${mob.type} - ${mob.room}</h3>
                    <p class="text-gray-400 mb-2">Status: ${mob.status}</p>
                    <div class="flex justify-end space-x-2">
                        <button onclick="deleteMobiliario(${mob.id})" class="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-3 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50">
                            Excluir
                        </button>
                    </div>
                </div>
            `;
            mobiliarioListDiv.innerHTML += mobiliarioCard;
        });
    } catch (error) {
        console.error("Erro ao buscar mobiliário:", error);
        showToast("Erro ao carregar mobiliário.", "error");
    }
}

function showCreateMobiliarioModal() {
    const body = `
        <div class="space-y-4">
            <div>
                <label for="mobiliario-tipo" class="block text-gray-300 text-sm font-bold mb-2">Tipo:</label>
                <input type="text" id="mobiliario-tipo" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Ex: Cadeira, Mesa">
            </div>
            <div>
                <label for="mobiliario-comodo" class="block text-gray-300 text-sm font-bold mb-2">Cômodo:</label>
                <input type="text" id="mobiliario-comodo" class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white" placeholder="Ex: Sala, Cozinha">
            </div>
            <div>
                <label for="mobiliario-status" class="block text-gray-300 text-sm font-bold mb-2">Status:</label>
                <select id="mobiliario-status" class="shadow border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-gray-700 border-gray-600 text-white">
                    <option value="existente">Existente</option>
                    <option value="novo">Novo</option>
                </select>
            </div>
        </div>
    `;

    const footer = `
        <button onclick="closeModal()" class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-opacity-50">Cancelar</button>
        <button onclick="createMobiliario()" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50">Adicionar Mobiliário</button>
    `;

    showModal("Adicionar Novo Mobiliário", body, footer);
}

async function createMobiliario() {
    const tipo = document.getElementById("mobiliario-tipo").value;
    const comodo = document.getElementById("mobiliario-comodo").value;
    const status = document.getElementById("mobiliario-status").value;

    if (!tipo || !comodo || !status) {
        showToast("Por favor, preencha todos os campos do mobiliário.", "warning");
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/obras/${currentObraId}/mobiliario`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                type: tipo,
                room: comodo,
                status: status
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast("Mobiliário adicionado com sucesso!", "success");
        closeModal();
        fetchMobiliario(currentObraId); // Refresh the list
    } catch (error) {
        console.error("Erro ao adicionar mobiliário:", error);
        showToast("Erro ao adicionar mobiliário. Tente novamente.", "error");
    }
}

async function deleteMobiliario(mobiliarioId) {
    if (!confirm("Tem certeza que deseja excluir este mobiliário?")) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/mobiliario/${mobiliarioId}`, {
            method: "DELETE",
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        showToast("Mobiliário excluído com sucesso!", "success");
        fetchMobiliario(currentObraId); // Refresh the list
    } catch (error) {
        console.error("Erro ao excluir mobiliário:", error);
        showToast("Erro ao excluir mobiliário. Tente novamente.", "error");
    }
}



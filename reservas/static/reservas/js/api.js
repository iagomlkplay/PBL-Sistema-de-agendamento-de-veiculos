// Funções utilitárias para chamar a API do backend

const API_BASE = '/api';

/**
 * Cria uma reserva.
 * @param {Object} dados - Dados da reserva.
 * @returns {Promise<Object>} Resposta em JSON.
 */
async function criarReserva(dados) {
    const resp = await fetch(`${API_BASE}/reservas/criar/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    });
    const json = await resp.json();
    if (!resp.ok) {
        throw new Error(formatarErro(json));
    }
    return json;
}

/**
 * Lista todas as reservas confirmadas.
 * @returns {Promise<Array>}
 */
async function listarReservas() {
    const resp = await fetch(`${API_BASE}/reservas/`);
    if (!resp.ok) {
        throw new Error('Erro ao listar reservas.');
    }
    return resp.json();
}

/**
 * Extrai uma mensagem de erro legível do JSON de resposta.
 */
function formatarErro(json) {
    if (!json) return 'Erro desconhecido.';
    if (typeof json.erro === 'string') return json.erro;
    if (Array.isArray(json.erro)) return json.erro.join(' ');
    return JSON.stringify(json);
}
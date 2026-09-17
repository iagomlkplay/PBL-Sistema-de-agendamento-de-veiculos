document.addEventListener('DOMContentLoaded', () => {
    
    // Define o "min" do datetime-local para agora
    const agora = new Date();
    agora.setMinutes(agora.getMinutes() - agora.getTimezoneOffset());
    const agoraISO = agora.toISOString().slice(0, 16); // YYYY-MM-DDTHH:MM

    const inputInicio = document.getElementById('data_inicio');
    const inputFim = document.getElementById('data_fim');
    inputInicio.min = agoraISO;
    inputFim.min = agoraISO;

    // Quando o usuário escolher a data de início, força a data fim a ser no mesmo dia
    inputInicio.addEventListener('change', () => {
        if (inputInicio.value) {
            const dia = inputInicio.value.split('T')[0];
            inputFim.min = `${dia}T08:00`;
            inputFim.max = `${dia}T17:00`;
        }
    });

    // Quando o usuário escolher a data de fim, força a data início a ser no mesmo dia
    inputFim.addEventListener('change', () => {
        if (inputFim.value) {
            const dia = inputFim.value.split('T')[0];
            inputInicio.min = `${dia}T08:00`;
            inputInicio.max = `${dia}T17:00`;
        }
    });

    const form = document.getElementById('form-reserva');
    const mensagem = document.getElementById('mensagem');
    const resultado = document.getElementById('resultado');
    const btn = document.getElementById('btn-enviar');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Limpa mensagens anteriores
        mensagem.className = 'mensagem';
        mensagem.textContent = '';
        resultado.classList.add('escondido');
        btn.disabled = true;
        btn.textContent = 'Enviando...';

        // Monta o objeto com os dados
        const dados = {
            origem: document.getElementById('origem').value.trim(),
            destino: document.getElementById('destino').value.trim(),
            num_passageiros: parseInt(document.getElementById('num_passageiros').value, 10),
            motivo: document.getElementById('motivo').value.trim(),
            data_inicio: document.getElementById('data_inicio').value + ':00',
            data_fim: document.getElementById('data_fim').value + ':00'
        };

        try {
            const resp = await criarReserva(dados);

            // Sucesso: mostra o protocolo
            document.getElementById('protocolo').textContent = resp.protocolo;
            document.getElementById('veiculo').textContent = resp.veiculo;
            document.getElementById('motorista').textContent = resp.motorista;
            document.getElementById('periodo').textContent =
                `${formatarData(resp.data_inicio)} até ${formatarData(resp.data_fim)}`;
            resultado.classList.remove('escondido');

            mensagem.className = 'mensagem sucesso';
            mensagem.textContent = 'Reserva criada com sucesso!';

            form.reset();
        } catch (err) {
            mensagem.className = 'mensagem erro';
            mensagem.textContent = 'Erro: ' + err.message;
        } finally {
            btn.disabled = false;
            btn.textContent = 'Solicitar Reserva';
        }
    });

    function formatarData(iso) {
        const d = new Date(iso);
        return d.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
    }
});
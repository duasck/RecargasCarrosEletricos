import socket
import logging
import json
import os
from random import uniform
from .models import PontoRecarga

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(container_id)s] %(message)s"
)

HOST = "0.0.0.0"
BASE_PORT = int(os.getenv('BASE_PORT', 6000))

# Obtém o ID do container
container_id = os.getenv('HOSTNAME', 'ponto_1').split('_')[-1]
try:
    PORT = BASE_PORT + int(container_id)
except ValueError:
    PORT = BASE_PORT + 1  # Fallback se não conseguir converter para número

class PontoRecargaService:
    def __init__(self):
        self.ponto = PontoRecarga(
            id_ponto=f"P{container_id}",
            localizacao={
                "lat": -23.5505 + (int(container_id) * 0.01,
                "lon": -46.6333 + (int(container_id) * 0.01
            }
        )

    def handle_request(self, mensagem):
        if mensagem["acao"] == "reservar":
            return self.ponto.reservar(mensagem["id_veiculo"])
        elif mensagem["acao"] == "iniciar_recarga":
            return self.ponto.iniciar_recarga(mensagem.get("taxa_recarga", 10.0))
        elif mensagem["acao"] == "liberar":
            return self.ponto.liberar()
        return {"status": "acao_nao_reconhecida"}

# Configuração do logging com container_id
old_factory = logging.getLogRecordFactory()
def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    record.container_id = f"PONTO-{container_id}"
    return record
logging.setLogRecordFactory(record_factory)

service = PontoRecargaService()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

logging.info(f"Servidor do Ponto de Recarga {service.ponto.id_ponto} rodando na porta {PORT}...")
logging.info(f"Localização: {service.ponto.localizacao}")

while True:
    conn, addr = s.accept()
    logging.info(f"Conexão recebida de {addr}")

    try:
        data = conn.recv(1024)
        if data:
            mensagem = json.loads(data.decode())
            logging.info(f"Mensagem recebida: {mensagem}")
            
            resposta = service.handle_request(mensagem)
            conn.sendall(json.dumps(resposta).encode())
            logging.info(f"Resposta enviada: {resposta}")

    except Exception as e:
        logging.error(f"Erro ao processar requisição: {e}")
        conn.sendall(json.dumps({"status": "
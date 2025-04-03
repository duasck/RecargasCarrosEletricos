import socket
import logging
import json
import os
import random
import time
from .client_models import Cliente
from shared.random_info import listaClientes

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CLIENTE-%(client_id)s] %(message)s"
)

HOST = "nuvem" if os.getenv('IN_DOCKER') else "localhost"
PORT = 5000

class ClienteService:
    def __init__(self):
        client_id = os.getenv('HOSTNAME', 'cliente_1').split('_')[-1]
        try:
            cliente_info = random.choice(listaClientes)
        except IndexError:
            cliente_info = type('', (), {
                'id': f'cliente_{client_id}', 
                'coordenadas': [
                    random.uniform(-23.56, -23.54), 
                    random.uniform(-46.66, -46.62)
                ]
            })()
        
        self.cliente = Cliente(
            id_veiculo=cliente_info.id,
            bateria=random.randint(10, 30),
            localizacao={
                "lat": cliente_info.coordenadas[0],
                "lon": cliente_info.coordenadas[1]
            }
        )
        
        # Configuração do logging com client_id
        old_factory = logging.getLogRecordFactory()
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.client_id = client_id
            return record
        logging.setLogRecordFactory(record_factory)

    def send_request(self, mensagem):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.settimeout(5.0)
                client_socket.connect((HOST, PORT))
                client_socket.sendall(json.dumps(mensagem).encode())
                resposta = client_socket.recv(1024)
                return json.loads(resposta.decode())
        except Exception as e:
            logging.error(f"Erro na comunicação: {e}")
            return {"status": "erro", "mensagem": str(e)}

    def run(self):
        while True:
            try:
                # Lista pontos próximos
                pontos = self.send_request({
                    "acao": "listar_pontos",
                    "id_veiculo": self.cliente.id_veiculo,
                    "localizacao": self.cliente.localizacao
                })
                
                if pontos and random.random() > 0.3:
                    # Tenta fazer uma reserva
                    reserva = self.send_request({
                        "acao": "solicitar_reserva",
                        "id_veiculo": self.cliente.id_veiculo,
                        "localizacao": self.cliente.localizacao
                    })
                    
                    if reserva.get("status") == "reservado":
                        self.cliente.ponto_reservado = reserva.get("id_ponto")
                        time.sleep(2)
                        
                        if random.random() > 0.5:
                            time.sleep(3)
                            self.send_request({
                                "acao": "liberar_ponto",
                                "id_ponto": self.cliente.ponto_reservado,
                                "id_veiculo": self.cliente.id_veiculo
                            })
                            self.cliente.ponto_reservado = None
                
                if random.random() > 0.8:
                    self.send_request({
                        "acao": "solicitar_historico",
                        "id_veiculo": self.cliente.id_veiculo
                    })
                
                time.sleep(random.randint(2, 5))
                
            except KeyboardInterrupt:
                if self.cliente.ponto_reservado:
                    self.send_request({
                        "acao": "liberar_ponto",
                        "id_ponto": self.cliente.ponto_reservado,
                        "id_veiculo": self.cliente.id_veiculo
                    })
                break
            except Exception as e:
                logging.error(f"Erro no loop principal: {e}")
                time.sleep(5)

if __name__ == "__main__":
    ClienteService().run()
import socket
import threading
import logging
import json
import os
from random import uniform

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [NUVEM] %(message)s")

HOST = "0.0.0.0"
PORT = 5000

class NuvemService:
    def __init__(self):
        self.num_pontos = int(os.getenv('NUM_PONTOS', 3))
        self.pontos_recarga = self.gerar_pontos_recarga()
        
    def gerar_pontos_recarga(self):
        pontos = {}
        base_lat = -23.5505
        base_lon = -46.6333
        
        for i in range(1, self.num_pontos + 1):
            pontos[f"P{i}"] = {
                "ip": "localhost",
                "porta": 6000 + i,
                "localizacao": {
                    "lat": base_lat + (i * 0.01),
                    "lon": base_lon + (i * 0.01)
                },
                "status": "disponivel"
            }
        return pontos

    def calcular_distancia(self, local1, local2):
        return ((local1["lat"] - local2["lat"])**2 + (local1["lon"] - local2["lon"])**2)**0.5

    def calcular_pontos_proximos(self, localizacao_cliente):
        pontos_proximos = []
        for id_ponto, info in self.pontos_recarga.items():
            distancia = self.calcular_distancia(localizacao_cliente, info["localizacao"])
            pontos_proximos.append({
                "id_ponto": id_ponto,
                "distancia": distancia,
                "status": info["status"],
                "localizacao": info["localizacao"]
            })
        pontos_proximos.sort(key=lambda x: x["distancia"])
        return pontos_proximos[:5]

    def atualizar_status_ponto(self, id_ponto, status):
        if id_ponto in self.pontos_recarga:
            self.pontos_recarga[id_ponto]["status"] = status
            return True
        return False

    def handle_client(self, client_socket, addr):
        logging.info(f"Cliente {addr} conectado.")
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    logging.info(f"Cliente {addr} desconectou.")
                    break

                mensagem = json.loads(data.decode())
                logging.info(f"Mensagem recebida do cliente: {mensagem}")

                if mensagem["acao"] == "listar_pontos":
                    resposta = self.calcular_pontos_proximos(mensagem["localizacao"])
                elif mensagem["acao"] == "solicitar_reserva":
                    resposta = self.processar_reserva(mensagem)
                elif mensagem["acao"] == "liberar_ponto":
                    resposta = {"status": "liberado"} if self.atualizar_status_ponto(
                        mensagem["id_ponto"], "disponivel") else {"status": "erro"}
                elif mensagem["acao"] == "solicitar_historico":
                    resposta = self.gerar_historico()
                else:
                    resposta = {"status": "acao_nao_reconhecida"}

                client_socket.sendall(json.dumps(resposta).encode())

        except Exception as e:
            logging.error(f"Erro ao processar cliente {addr}: {e}")
            client_socket.sendall(json.dumps(
                {"status": "erro", "mensagem": str(e)}).encode())
        finally:
            client_socket.close()
            logging.info(f"Conexão com {addr} encerrada.")

    def processar_reserva(self, mensagem):
        pontos_proximos = self.calcular_pontos_proximos(mensagem["localizacao"])
        id_ponto = next((p["id_ponto"] for p in pontos_proximos 
                        if p["status"] == "disponivel"), None)
        
        if not id_ponto:
            return {"status": "indisponivel", "mensagem": "Nenhum ponto disponível"}

        try:
            ponto_info = self.pontos_recarga[id_ponto]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as ponto_socket:
                ponto_socket.connect((ponto_info["ip"], ponto_info["porta"]))
                ponto_socket.sendall(json.dumps({
                    "acao": "reservar",
                    "id_veiculo": mensagem["id_veiculo"]
                }).encode())
                resposta = ponto_socket.recv(1024)
            
            if json.loads(resposta.decode())["status"] == "reservado":
                self.atualizar_status_ponto(id_ponto, "ocupado")
            
            return json.loads(resposta.decode())
        except Exception as e:
            logging.error(f"Erro ao conectar com ponto {id_ponto}: {e}")
            return {"status": "erro", "mensagem": str(e)}

    def gerar_historico(self):
        return [{
            "data": "2023-10-01",
            "valor": 50.0,
            "ponto": "P1"
        }, {
            "data": "2023-10-05",
            "valor": 30.0,
            "ponto": "P2"
        }]

    def run(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        # Verifica se o servidor está pronto
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
        
        logging.info(f"Servidor rodando na porta {PORT}...")

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(
                target=self.handle_client, 
                args=(client_socket, addr)
            ).start()

if __name__ == "__main__":
    NuvemService().run()
class Cliente:
    def __init__(self, id_veiculo, bateria, localizacao):
        self.id_veiculo = id_veiculo
        self.bateria = bateria
        self.localizacao = localizacao
        self.historico = []
        self.ponto_reservado = None
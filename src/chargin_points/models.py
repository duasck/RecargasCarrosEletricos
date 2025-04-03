class PontoRecarga:
    def __init__(self, id_ponto, localizacao):
        self.id_ponto = id_ponto
        self.localizacao = localizacao
        self.status = "disponivel"
        self.fila = []
        self.veiculo_atual = None
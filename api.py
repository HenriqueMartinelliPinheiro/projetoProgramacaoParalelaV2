from flask import Flask, request, jsonify
import threading
import queue
import time
import random

app = Flask(__name__)


class Ingresso:
    def __init__(self, id_ingresso):
        self.id_ingresso = id_ingresso
        self.idUsuarioReserva = None
        self.idComprador = None


class RequisicaoCompra:
    def __init__(self, id_usuario):
        self.id_usuario = id_usuario


class ResultadoCompra:
    def __init__(self, id_usuario, id_ingresso):
        self.id_usuario = id_usuario
        self.id_ingresso = id_ingresso


class SistemaVendaIngressos:
    def __init__(self):
        self.ingressos = [Ingresso(i) for i in range(1000)]
        self.filaEntrada = queue.Queue()
        self.filasProcessamento = [queue.Queue() for _ in range(3)]
        self.resultados_processados = {}

    def despachante(self):
        while True:
            requisicao = self.filaEntrada.get()  # Obtém a requisição da fila
            ingresso_reservado = None

            # Verifica se há ingressos disponíveis (não vendidos e não reservados)
            ingressos_disponiveis = [
                ingresso for ingresso in self.ingressos if ingresso.idComprador is None and ingresso.idUsuarioReserva is None]

            if ingressos_disponiveis:
                # Se houver ingressos disponíveis, tenta reservar
                ingresso_reservado = ingressos_disponiveis[0]
                ingresso_reservado.idUsuarioReserva = requisicao.id_usuario
                print(
                    f"Despachante: Ingresso {ingresso_reservado.id_ingresso} reservado pelo usuário {requisicao.id_usuario}.")
                fila_processamento = min(
                    self.filasProcessamento, key=lambda x: x.qsize())
                fila_processamento.put((requisicao, ingresso_reservado))
            else:
                # Se todos os ingressos estão vendidos, coloca o resultado no dicionário
                print(
                    f"Despachante: Todos os ingressos vendidos. Usuário {requisicao.id_usuario} não conseguiu comprar.")
                self.resultados_processados[requisicao.id_usuario] = -1

            self.filaEntrada.task_done()

    def processador(self, fila_processamento, nome_thread):
        while True:
            time.sleep(random.uniform(2, 5.0))
            requisicao, ingresso = fila_processamento.get()

            # Verifica se o ingresso já foi comprado antes de continuar o processamento
            if ingresso.idComprador is not None:
                print(
                    f"{nome_thread}: Ingresso {ingresso.id_ingresso} já foi comprado, ignorando.")
                fila_processamento.task_done()
                continue

            # Marca o ingresso como comprado pelo usuário
            ingresso.idComprador = requisicao.id_usuario

            resultado = ResultadoCompra(
                requisicao.id_usuario, ingresso.id_ingresso)
            self.resultados_processados[requisicao.id_usuario] = resultado.id_ingresso
            print(
                f"{nome_thread}: Usuário {requisicao.id_usuario} comprou o ingresso {ingresso.id_ingresso}.")
            fila_processamento.task_done()


sistema_venda = SistemaVendaIngressos()


@app.route('/compra', methods=['POST'])
def receber_requisicao():
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    requisicao = RequisicaoCompra(id_usuario)
    sistema_venda.filaEntrada.put(requisicao)
    return jsonify({"status": "Requisição recebida", "id_usuario": id_usuario})


@app.route('/resultado/<int:id_usuario>', methods=['GET'])
def resultado_usuario(id_usuario):
    # Busca pelo resultado específico de um usuário
    if id_usuario in sistema_venda.resultados_processados:
        id_ingresso = sistema_venda.resultados_processados[id_usuario]
        print(
            f"Resultado encontrado para usuário {id_usuario}: Ingresso {id_ingresso}")
        return jsonify({"id_usuario": id_usuario, "id_ingresso": id_ingresso})
    return jsonify({"status": "Aguardando processamento"})


if __name__ == '__main__':
    # Inicia a thread do despachante
    threading.Thread(target=sistema_venda.despachante, daemon=True).start()

    # Inicia as threads dos processadores
    for i, fila in enumerate(sistema_venda.filasProcessamento, start=1):
        threading.Thread(target=sistema_venda.processador, args=(
            fila, f"Processador {i}"), daemon=True).start()

    # Executa o servidor Flask
    app.run(port=5000, debug=True)

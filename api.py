import threading
import queue
import time
import random
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

num_processadores = 4
num_ingressos = 100


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
        self.ingressos = [Ingresso(i) for i in range(num_ingressos)]
        self.filaEntrada = queue.Queue()
        self.filasProcessamento = [queue.Queue()
                                   for _ in range(num_processadores)]
        self.resultados_processados = {}

    def despachante(self):
        while True:
            ingressos_disponiveis = [
                ingresso for ingresso in self.ingressos if ingresso.idComprador is None and ingresso.idUsuarioReserva is None
            ]

            if not ingressos_disponiveis:
                todos_vendidos = all(
                    ingresso.idComprador is not None for ingresso in self.ingressos)
                if todos_vendidos:
                    while not self.filaEntrada.empty():
                        requisicao = self.filaEntrada.get()
                        self.resultados_processados[requisicao.id_usuario] = -1
                        self.filaEntrada.task_done()
                        print(
                            f"Despachante: Todos os ingressos vendidos. Usuário {requisicao.id_usuario} não conseguiu comprar.", flush=True)

                    time.sleep(1)
                else:
                    print(
                        "Despachante: Todos os ingressos estão reservados no momento. Aguardando 5 segundos antes de tentar novamente.", flush=True)
                    time.sleep(5)
                    continue

            requisicao = self.filaEntrada.get()

            ingresso_disponivel_para_reserva = next(
                (ingresso for ingresso in self.ingressos if ingresso.idComprador is None and ingresso.idUsuarioReserva is None), None
            )

            if ingresso_disponivel_para_reserva:
                ingresso_reservado = ingresso_disponivel_para_reserva
                ingresso_reservado.idUsuarioReserva = requisicao.id_usuario
                print(
                    f"Despachante: Ingresso {ingresso_reservado.id_ingresso} reservado pelo usuário {requisicao.id_usuario}.", flush=True
                )
                fila_processamento = min(
                    self.filasProcessamento, key=lambda x: x.qsize())
                fila_processamento.put((requisicao, ingresso_reservado))
            else:
                self.filaEntrada.put(requisicao)
                print(
                    f"Despachante: Todos os ingressos estão reservados no momento. Usuário {requisicao.id_usuario} aguardará.", flush=True
                )

            self.filaEntrada.task_done()

    def processador(self, fila_processamento, nome_thread):
        while True:
            time.sleep(random.uniform(2, 5.0))
            requisicao, ingresso = fila_processamento.get()

            if ingresso.idComprador is not None:
                print(
                    f"{nome_thread}: Ingresso {ingresso.id_ingresso} já foi comprado, ignorando.", flush=True
                )
                fila_processamento.task_done()
                continue

            # Compra do ingresso
            ingresso.idComprador = requisicao.id_usuario
            resultado = ResultadoCompra(
                requisicao.id_usuario, ingresso.id_ingresso)
            self.resultados_processados[requisicao.id_usuario] = resultado.id_ingresso
            print(
                f"{nome_thread}: Usuário {requisicao.id_usuario} comprou o ingresso {ingresso.id_ingresso}.", flush=True
            )
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
    if id_usuario in sistema_venda.resultados_processados:
        id_ingresso = sistema_venda.resultados_processados[id_usuario]
        return jsonify({"id_usuario": id_usuario, "id_ingresso": id_ingresso})
    return jsonify({"status": "Aguardando processamento"})


if __name__ == '__main__':
    threading.Thread(target=sistema_venda.despachante, daemon=True).start()

    for i, fila in enumerate(sistema_venda.filasProcessamento, start=1):
        threading.Thread(target=sistema_venda.processador, args=(
            fila, f"Processador {i}"), daemon=True).start()

    app.run(port=5000, debug=True)

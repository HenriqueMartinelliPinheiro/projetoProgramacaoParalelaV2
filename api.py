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

ingressos = [Ingresso(i) for i in range(50)]

class RequisicaoCompra:
    def __init__(self, id_usuario):
        self.id_usuario = id_usuario

class ResultadoCompra:
    def __init__(self, id_usuario, id_ingresso):
        self.id_usuario = id_usuario
        self.id_ingresso = id_ingresso

filaEntrada = queue.Queue()
filaProcessamento1 = queue.Queue()
filaProcessamento2 = queue.Queue()
filaProcessamento3 = queue.Queue()
filaProcessamento = [filaProcessamento1, filaProcessamento2, filaProcessamento3]
filaSaida = queue.Queue()

@app.route('/compra', methods=['POST'])
def receber_requisicao():
    data = request.get_json()
    id_usuario = data.get('id_usuario')
    requisicao = RequisicaoCompra(id_usuario)
    filaEntrada.put(requisicao)
    return jsonify({"status": "Requisição recebida", "id_usuario": id_usuario})

def despachante():
    while True:
        requisicao = filaEntrada.get() 
        ingresso_reservado = None

        for ingresso in ingressos:
            if ingresso.idUsuarioReserva is None:
                ingresso.idUsuarioReserva = requisicao.id_usuario
                ingresso_reservado = ingresso
                print(f"Despachante: Ingresso {ingresso.id_ingresso} reservado pelo usuário {requisicao.id_usuario}.")
                break

        if ingresso_reservado:
            fila_processamento = min(filaProcessamento, key=lambda x: x.qsize())
            fila_processamento.put((requisicao, ingresso_reservado))
            print(f"Despachante: Requisição do usuário {requisicao.id_usuario} enviada para {fila_processamento}.")
        else:
            print(f"Despachante: Todos os ingressos reservados. Requisição do usuário {requisicao.id_usuario} retornada à fila.")
            filaEntrada.put(requisicao)

        filaEntrada.task_done() 

def processador(fila_processamento, nome_thread):
    while True:
        requisicao, ingresso = fila_processamento.get()
        time.sleep(random.uniform(2, 5.0))
        ingresso.idComprador = requisicao.id_usuario    
        resultado = ResultadoCompra(requisicao.id_usuario, ingresso.id_ingresso)
        filaSaida.put(resultado)
        print(f"{nome_thread}: Usuário {requisicao.id_usuario} comprou o ingresso {ingresso.id_ingresso}.")
        fila_processamento.task_done()

@app.route('/resultados', methods=['GET'])
def obter_resultados():
    resultados = []
    while not filaSaida.empty():
        resultado = filaSaida.get()
        resultados.append({
            "id_usuario": resultado.id_usuario,
            "id_ingresso": resultado.id_ingresso
        })
    return jsonify(resultados)

if __name__ == '__main__':
    threading.Thread(target=despachante, daemon=True).start()
    threading.Thread(target=processador, args=(filaProcessamento1, "Processador 1"), daemon=True).start()
    threading.Thread(target=processador, args=(filaProcessamento2, "Processador 2"), daemon=True).start()
    threading.Thread(target=processador, args=(filaProcessamento3, "Processador 3"), daemon=True).start()

    app.run(port=5000, debug=True)

import requests
import time
import threading

usuarios_pendentes = []

resultados_processados = {}

num_requisicoes = 200


def produtor(n_requisicoes):
    url = 'http://localhost:5000/compra'
    for i in range(1, n_requisicoes + 1):
        id_usuario = i
        response = requests.post(url, json={"id_usuario": id_usuario})
        if response.status_code == 200:
            print(
                f"Produtor: Requisição do usuário {id_usuario} enviada. Status: {response.status_code}")
            usuarios_pendentes.append(id_usuario)
        else:
            print(
                f"Produtor: Falha ao enviar requisição do usuário {id_usuario}. Status: {response.status_code}")


def buscar_resultado():
    while True:
        if usuarios_pendentes:
            id_usuario = usuarios_pendentes.pop(0)
            url = f'http://localhost:5000/resultado/{id_usuario}'
            while True:
                response = requests.get(url)
                if response.status_code == 200:
                    resultado = response.json()
                    if resultado.get("id_ingresso") is not None:
                        if resultado["id_ingresso"] == -1:
                            print(
                                f"Usuário {id_usuario}: Todos os ingressos vendidos.")
                        else:
                            print(
                                f"Usuário {id_usuario}: Compra do ingresso {resultado['id_ingresso']} confirmada.")
                        break
                    else:
                        print(
                            f"Usuário {id_usuario}: Aguardando processamento...")
                else:
                    print(
                        f"Erro ao buscar resultado para o usuário {id_usuario}. Status: {response.status_code}")

                time.sleep(2)
        else:
            time.sleep(1)


if __name__ == "__main__":
    thread_produtor = threading.Thread(
        target=produtor, args=(num_requisicoes,))

    thread_busca = threading.Thread(target=buscar_resultado)

    thread_produtor.start()
    thread_busca.start()

    thread_produtor.join()
    thread_busca.join()

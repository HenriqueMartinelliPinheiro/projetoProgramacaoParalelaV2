import requests
import time
import threading

# Lista compartilhada entre threads para armazenar IDs dos usuários que fizeram requisição
usuarios_pendentes = []

# Novo dicionário para armazenar os resultados processados
resultados_processados = {}


def produtor(n_requisicoes):
    url = 'http://localhost:5000/compra'
    # IDs dos usuários serão de 1 a n_requisicoes, de forma sequencial
    for i in range(1, n_requisicoes + 1):
        id_usuario = i
        response = requests.post(url, json={"id_usuario": id_usuario})
        if response.status_code == 200:
            print(
                f"Produtor: Requisição do usuário {id_usuario} enviada. Status: {response.status_code}")
            # Adiciona o ID do usuário para buscar o resultado depois
            usuarios_pendentes.append(id_usuario)
        else:
            print(
                f"Produtor: Falha ao enviar requisição do usuário {id_usuario}. Status: {response.status_code}")


def buscar_resultado():
    while True:
        if usuarios_pendentes:  # Verifica se há usuários na lista de pendentes
            # Remove o primeiro usuário da lista
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
                        break  # Sai do loop ao receber uma resposta final
                    else:
                        print(
                            f"Usuário {id_usuario}: Aguardando processamento...")
                else:
                    print(
                        f"Erro ao buscar resultado para o usuário {id_usuario}. Status: {response.status_code}")

                time.sleep(2)  # Espera 2 segundos antes de tentar novamente
        else:
            # Se não houver usuários pendentes, espera 1 segundo antes de checar novamente
            time.sleep(1)


if __name__ == "__main__":
    # Cria thread para fazer as requisições de compra
    thread_produtor = threading.Thread(target=produtor, args=(10000,))

    # Cria thread para buscar resultados
    thread_busca = threading.Thread(target=buscar_resultado)

    # Inicia as threads
    thread_produtor.start()
    thread_busca.start()

    # Aguarda que ambas as threads terminem
    thread_produtor.join()
    thread_busca.join()

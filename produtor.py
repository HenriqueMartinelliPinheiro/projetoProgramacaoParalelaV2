import requests
import random
import time

def produtor(n_requisicoes):
    url = 'http://localhost:5000/compra'
    for i in range(n_requisicoes):
        id_usuario = random.randint(1, 1000)
        response = requests.post(url, json={"id_usuario": id_usuario})
        print(f"Produtor: Requisição do usuário {id_usuario} enviada. Status: {response.status_code}")

if __name__ == "__main__":
    produtor(100)

import socket
import threading
import random
from enum import Enum

lista_pokemons = Enum("Pokemons", {
    "Pikachu": {"tipo": "Elétrico", "vida": 100, "fraqueza": "Terra", "vantagem": "Água", "ataques": [{"Choque do trovão": 10}, {"Cauda de ferro": 15}]},
    "Charmander": {"tipo": "Fogo", "vida": 100, "fraqueza": "Água", "vantagem": "Planta", "ataques": [{"Brasa": 10}, {"Lança-chamas": 15}]},
    "Squirtle": {"tipo": "Água", "vida": 100, "fraqueza": "Elétrico", "vantagem": "Fogo", "ataques": [{"Bolha": 10}, {"Hidro bomba": 15}]},
    "Bulbasaur": {"tipo": "Planta", "vida": 100, "fraqueza": "Fogo", "vantagem": "Água", "ataques": [{"Folha navalha": 10}, {"Raio solar": 15}]}
})


SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 4242
ADDR = (SERVER_IP, SERVER_PORT)
FORMAT = "utf-8"

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.bind(ADDR)
servidor.listen(2)


class Jogador:
    def __init__(self, socket):
        self.nome = None
        self.socket = socket
        self.socket_adversario = None
        self.pokemons = []
        self.turno_atual = False

    def set_nome(self, nome):
        self.nome = nome

    def define_pokemons(self):
        self.socket.send("status|escolha_pokemons".encode(FORMAT))

        pokemons_msg = self.socket.recv(1024).decode(FORMAT)
        pokemons = pokemons_msg.split("|")[1].split(",")

        print(f"Pokémons escolhidos por {self.nome}: {pokemons}")
        for pokemon in pokemons:
            self.instancia_pokemon(pokemon)

        self.socket.send("status|aguarde".encode(FORMAT))

    def instancia_pokemon(self, nome_pokemon):
        pokemon_info = lista_pokemons.__getitem__(nome_pokemon).value
        pokemon = Pokemon(
            nome=nome_pokemon,
            tipo=pokemon_info["tipo"],
            vida=pokemon_info["vida"],
            fraqueza=pokemon_info["fraqueza"],
            vantagem=pokemon_info["vantagem"],
            ataques=pokemon_info["ataques"],
        )
        self.pokemons.append(pokemon)


# Criando a classe Pokémon e seus métodos
class Pokemon:
    def __init__(self, nome, tipo, vida, fraqueza, vantagem, ataques):
        self.nome = nome
        self.tipo = tipo
        self._vida = vida
        self.fraqueza = fraqueza
        self.vantagem = vantagem
        self.ataques = ataques

    def vida(self, valor):
        if valor < 0:
            self._vida = 0
        else:
            self._vida = valor

    def perderVida(self, valor):
        self._vida = self._vida - valor
        if self._vida < 0:
            self._vida = 0

    # Método para verificar se o Pokémon está morto
    def morrer(self):
        if self._vida <= 0:
            print(f"{self.nome} morreu!")
        else:
            print(f"{self.nome} ainda está vivo com {self._vida} de vida.")

    def __str__(self):
        return (f"Nome: {self.nome}, Tipo: {self.tipo}, Vida: {self.vida}, "
                f"Fraqueza: {self.fraqueza}, Vantagem: {self.vantagem}")


def get_jogador_info(jogador):
    nome_msg = jogador.socket.recv(1024).decode(FORMAT)
    nome = nome_msg.split("|")[1]
    jogador.set_nome(nome)
    print(f"Jogador conectado: {jogador.nome}")
    jogador.define_pokemons()


def envia_mensagem_simultanea(jogador1, jogador2, mensagem):
    jogador1.socket.send(mensagem.encode(FORMAT))
    jogador2.socket.send(mensagem.encode(FORMAT))


def gerenciar_turnos(jogador, adversario, turno_condicao):
    while True:
        with turno_condicao:
            while not jogador.turno_atual:
                turno_condicao.wait()

            jogador.socket.send("status|sua_vez".encode(FORMAT))
            # Aqui você pode adicionar a lógica do turno do jogador
            data = jogador.socket.recv(1024).decode(FORMAT)

            if data:
                tipo_mensagem, mensagem = data.split("|", 1)
                if tipo_mensagem == "acao_escolhida":
                    if mensagem == "Atacar":
                        # Lógica de ataque
                        pass

            # Troca de turno
            jogador.turno_atual = False
            adversario.turno_atual = True
            turno_condicao.notify_all()


def main():
    print(f"Servidor rodando em {SERVER_IP}:{SERVER_PORT}")
    num_conexoes = 0

    while num_conexoes < 2:
        socket_cliente, endereco_cliente = servidor.accept()
        num_conexoes += 1

        if num_conexoes == 1:
            jogador1 = Jogador(socket_cliente)
            jogador1_thread = threading.Thread(target=get_jogador_info(
                jogador1), args=(jogador1, socket_cliente))
            jogador1_thread.start()

        else:
            jogador2 = Jogador(socket_cliente)
            jogador2_thread = threading.Thread(target=get_jogador_info(
                jogador2), args=(jogador2, socket_cliente))
            jogador2_thread.start()

            jogador1_thread.join()
            jogador2_thread.join()

            envia_mensagem_simultanea(jogador1, jogador2, "status|jogo_pronto")

            j1_pronto = jogador1.socket.recv(1024).decode(FORMAT).split("|")[1]
            j2_pronto = jogador2.socket.recv(1024).decode(FORMAT).split("|")[1]

            if j1_pronto != "pronto" and j2_pronto != "pronto":
                print("Erro inesperado!")
                exit()

            envia_mensagem_simultanea(
                jogador1, jogador2, "status|batalha_iniciada")

    if random.randint(0, 1) == 0:
        jogador1.turno_atual = True
        jogador2.turno_atual = False
    else:
        jogador1.turno_atual = False
        jogador2.turno_atual = True

    turno_condicao = threading.Condition()

    # Iniciar as threads de gerenciamento de turnos
    threading.Thread(target=gerenciar_turnos,
                     args=(jogador1, jogador2, turno_condicao)).start()
    threading.Thread(target=gerenciar_turnos,
                     args=(jogador2, jogador1, turno_condicao)).start()


if __name__ == "__main__":
    print("[INICIANDO] Servidor está iniciando...")
    main()

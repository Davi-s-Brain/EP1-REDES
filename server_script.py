import socket
import threading
import sys
import time
from lista_pokemons import lista_pokemons

# Configurações do servidor
SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 4242
ADDR = (SERVER_IP, SERVER_PORT)
FORMAT = "utf-8"
fim_de_jogo = False

# Criação do socket do servidor
servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(ADDR)
servidor.listen(2)


# Classe que representa um jogador


class Jogador:
    def __init__(self, socket):
        self.nome = None
        self.socket = socket
        self.socket_adversario = None
        self.pokemons = []

    # Define o nome do jogador
    def set_nome(self, nome):
        self.nome = nome

    # Recebe e define os pokémons escolhidos pelo jogador
    def define_pokemons(self):
        self.socket.send("status|escolha_pokemons\n".encode(FORMAT))

        pokemons_msg = self.socket.recv(1024).decode(FORMAT)
        pokemons = pokemons_msg.split("|")[1].split(",")

        print(f"Pokémons escolhidos por {self.nome}: {pokemons}")
        for pokemon in pokemons:
            self.instancia_pokemon(pokemon)

        self.socket.send("status|jogo_pronto\n".encode(FORMAT))

    # Instancia um pokémon com base nas informações da lista de pokémons
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


# Classe que representa um Pokémon


class Pokemon:
    def __init__(self, nome, tipo, vida, fraqueza, vantagem, ataques):
        self.nome = nome
        self.tipo = tipo
        self._vida = vida
        self.fraqueza = fraqueza
        self.vantagem = vantagem
        self.ataques = ataques

    # Define a vida do Pokémon
    def vida(self, valor):
        if valor < 0:
            self._vida = 0
        else:
            self._vida = int(valor)

    # Retorna a vida atual do Pokemón
    def get_vida(self):
        return self._vida

    # Reduz a vida do Pokémon
    def perderVida(self, valor):
        self._vida = self._vida - int(valor)
        if self._vida < 0:
            self._vida = 0

    # Verifica se o Pokémon está morto
    def morrer(self):
        if self._vida <= 0:
            print(f"{self.nome} morreu!")
        else:
            print(f"{self.nome} ainda está vivo com {self._vida} de vida.")

    def __str__(self):
        return (f"Nome: {self.nome}, Tipo: {self.tipo}, Vida: {self._vida}, "
                f"Fraqueza: {self.fraqueza}, Vantagem: {self.vantagem}")


# Função para obter informações do jogador


def get_jogador_info(jogador):
    nome_msg = jogador.socket.recv(1024).decode(FORMAT)
    nome = nome_msg.split("|")[1].split("\n")[0]
    jogador.set_nome(nome)
    print(f"Jogador conectado: {jogador.nome}")
    jogador.define_pokemons()


# Envia uma mensagem simultaneamente para dois jogadores


def envia_mensagem_simultanea(jogador1, jogador2, mensagem):
    mensagem_bytes = f"{mensagem}\n".encode(FORMAT)
    jogador1.socket.send(mensagem_bytes)
    jogador2.socket.send(mensagem_bytes)


# Gerencia os turnos dos jogadores


def gerenciar_turnos(jogador, adversario):
    global fim_de_jogo
    turno = [jogador, adversario]

    while not fim_de_jogo:
        jogador_atual = turno[0]
        adversario_atual = turno[1]

        jogador_atual.socket.send("status|sua_vez\n".encode(FORMAT))
        adversario_atual.socket.send("status|aguarde\n".encode(FORMAT))

        data = jogador_atual.socket.recv(1024).decode(FORMAT)

        if data:
            tipo_mensagem, mensagem = data.split("|", 1)

            if tipo_mensagem == "ataque":
                pokemon_atacante = mensagem.split("|")[0].split(".")[1]
                ataque = mensagem.split("|")[1]
                dano = int(mensagem.split("|")[2])

                # Encontra o Pokémon defensor
                # Supondo que o primeiro Pokémon é o que está batalhando
                pokemon_defensor = adversario_atual.pokemons[0]

                # Aplica a lógica de fraqueza
                if pokemon_defensor.tipo in jogador_atual.pokemons[0].vantagem:
                    dano *= 2
                elif pokemon_defensor.tipo in jogador_atual.pokemons[0].fraqueza:
                    dano //= 2

                # Subtrai os pontos de vida do Pokémon defensor
                pokemon_defensor.perderVida(dano)
                print(f"{pokemon_defensor.nome} agora tem {pokemon_defensor._vida} de vida.")
                
                mensagem_ataque = f"{jogador_atual.nome} atacou com {pokemon_atacante}, {ataque}. Causou {dano} de dano.\nSeu pokemon tem {adversario_atual.pokemons[0].get_vida()} de vida.\n{jogador_atual.nome} tem {jogador_atual.pokemons[0].get_vida()} de vida."

                time.sleep(0.1)
                adversario_atual.socket.send(
                    f"ataque_recebido|{mensagem_ataque}\n".encode(FORMAT))
                time.sleep(0.1)

                # Verifica se o Pokémon defensor morreu
                if pokemon_defensor.get_vida() <= 0:
                    adversario_atual.pokemons.pop(0)
                    time.sleep(0.1)
                    adversario_atual.socket.send(
                        f"morte|{pokemon_defensor.nome}\n".encode(FORMAT))
                    print(f"{pokemon_defensor.nome} morreu!")
                    time.sleep(0.1)

                    # Verifica se o adversário ainda tem pokémons
                    if not adversario_atual.pokemons:
                        jogador_atual.socket.send(
                            "status|vitoria\n".encode(FORMAT))
                        adversario_atual.socket.send(
                            "status|derrota\n".encode(FORMAT))
                        fim_de_jogo = True

            if tipo_mensagem == "item":
                pokemon_nome = mensagem.split("|")[0].strip()  # Remove espaços em branco e divide corretamente
                pokemon = next((p for p in jogador_atual.pokemons if p.nome == pokemon_nome), None)

                if pokemon is None:
                    print(f"Pokémon {pokemon_nome} não encontrado no time de {jogador_atual.nome}.")
                    jogador_atual.socket.send(f"erro|Pokémon {pokemon_nome} não encontrado.\n".encode(FORMAT))
                else:
                    # Supondo que o item cura 20 pontos de vida, sem exceder o máximo de vida
                    vida_atual = pokemon.get_vida()
                    vida_maxima = lista_pokemons.__getitem__(pokemon_nome).value["vida"]  # Pega o valor máximo de vida

                    nova_vida = min(vida_atual + 20, vida_maxima)  # Não deixa a vida ultrapassar o máximo
                    pokemon.vida(nova_vida)  # Define a nova vida

                    print(
                        f"{jogador_atual.nome} usou uma poção no {pokemon.nome}, que agora tem {nova_vida} de vida.")

                    time.sleep(0.1)
                    jogador_atual.socket.send(
                        f"info|{pokemon.nome}|{nova_vida}".encode(FORMAT)
                    )
                    time.sleep(0.1)

                # Alterna os turnos após usar um item
                turno = [adversario_atual, jogador_atual]

            # verifica se o jogador fugiu
            if tipo_mensagem == "fugiu":
                print(f"Um jogador fugiu da batalha!")

                # Enviar mensagem para ambos os jogadores
                jogador_atual.socket.send(
                    f"status|derrota\n".encode(FORMAT))
                adversario_atual.socket.send(
                    f"status|vitoria\n".encode(FORMAT))
                fim_de_jogo = True

        # Alterna os turnos
        turno = [adversario_atual, jogador_atual]

    jogador.socket.close()
    adversario.socket.close()


# Função principal que inicia o servidor e gerencia as conexões


def main():
    print(f"Servidor rodando em {SERVER_IP}:{SERVER_PORT}")
    num_conexoes = 0

    while num_conexoes < 2:
        socket_cliente, endereco_cliente = servidor.accept()
        num_conexoes += 1

        if num_conexoes == 1:
            jogador1 = Jogador(socket_cliente)
            jogador1_thread = threading.Thread(
                target=get_jogador_info, args=(jogador1,))
            jogador1_thread.start()

        else:
            jogador2 = Jogador(socket_cliente)
            jogador2_thread = threading.Thread(
                target=get_jogador_info, args=(jogador2,))
            jogador2_thread.start()

            jogador1_thread.join()
            jogador2_thread.join()

            envia_mensagem_simultanea(jogador1, jogador2, "status|jogo_pronto")

            j1_pronto = jogador1.socket.recv(1024).decode(FORMAT).split("|")[1]
            j2_pronto = jogador2.socket.recv(1024).decode(FORMAT).split("|")[1]

            if j1_pronto != "pronto\n" and j2_pronto != "pronto\n":
                print("Erro inesperado!")
                exit()

    try:
        gerenciar_turnos(jogador1, jogador2)

    except KeyboardInterrupt:
        print("\nInterrupção via teclado recebida. Fechando o servidor...")
        servidor.close()
        sys.exit(0)


# Ponto de entrada do script
if __name__ == "__main__":
    print("[INICIANDO] Servidor está iniciando...")
    main()

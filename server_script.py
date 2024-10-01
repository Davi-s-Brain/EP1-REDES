import socket
import threading

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
        self.pokemons = None

    def set_nome(self, nome):
        self.nome = nome

    def define_pokemons(self):
        self.socket.send("status|escolha_pokemons".encode(FORMAT))
        pokemons_msg = self.socket.recv(1024).decode(FORMAT)
        pokemons = pokemons_msg.split("|")[1]
        print(f"Pokémons escolhidos por {self.nome}: {pokemons}")
        self.pokemons = pokemons
        self.socket.send("status|aguarde".encode(FORMAT))

    def gerenciar_turnos(self):
        while True:
            pass


def get_jogador_info(jogador):
    nome_msg = jogador.socket.recv(1024).decode(FORMAT)
    nome = nome_msg.split("|")[1]
    jogador.set_nome(nome)
    print(f"Jogador conectado: {jogador.nome}")
    jogador.define_pokemons()


def envia_mensagem_simultanea(jogador1, jogador2, mensagem):
    jogador1.socket.send(mensagem.encode(FORMAT))
    jogador2.socket.send(mensagem.encode(FORMAT))


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

    threading.Thread(target=jogador1.gerenciar_turnos()).start()
    threading.Thread(target=jogador2.gerenciar_turnos()).start()


if __name__ == "__main__":
    print("[INICIANDO] Servidor está iniciando...")
    main()

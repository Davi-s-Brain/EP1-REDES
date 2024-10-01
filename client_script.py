import socket
import inquirer
import typer
from inquirer.themes import BlueComposure

PORT = 4242
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)


# Definindo os Pokémons
pokemons = ["Charmander", "Bulbasaur", "Squirtle", "Pikachu"]


def escolher_pokemons(cliente):
    pokemons_prompt = [
        inquirer.Checkbox(
            "pokemons", message="Escolha seus pokémons (max 2)", choices=pokemons, default=[])
    ]

    pokemons_escolhidos = inquirer.prompt(
        pokemons_prompt, theme=BlueComposure())

    # Convertendo nomes dos Pokémon selecionados para objetos Pokemon
    pokemons_selecionados = pokemons_escolhidos['pokemons']

    pokemons_str = ','.join(
        [pokemon for pokemon in pokemons_selecionados])

    cliente.send(f"pokemons_escolhidos|{pokemons_str}".encode("utf-8"))


def escolher_acao(cliente):
    acoes = [
        inquirer.List("acao", message="O que será feito?", choices=[
            "Atacar", "Itens", "Fugir"
        ], default="Atacar")
    ]

    acao_escolhida = inquirer.prompt(acoes, theme=BlueComposure())
    cliente.send(f"acao_escolhida|{acao_escolhida['acao']}".encode("utf-8"))

    return acao_escolhida['acao']


if __name__ == "__main__":
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(ADDR)
    except Exception as e:
        typer.echo(f"Erro ao conectar ao servidor: {e}")
        exit()

    typer.echo("Bem-vindo à batalha Pokémon!")

    nome = typer.prompt("Digite seu nome: ")
    cliente.send(f"nome|{nome}".encode("utf-8"))
    print("Conectado ao servidor!")

    while True:
        mensagem = cliente.recv(1024).decode("utf-8")

        print(mensagem)

        tipo_mensagem, mensagem = mensagem.split("|", 1)

        if tipo_mensagem == "status":
            if mensagem == "escolha_pokemons":
                escolher_pokemons(cliente)
                cliente.send("status|pronto".encode("utf-8"))

            if mensagem == "aguarde":
                print("Aguardando o outro jogador escolher os pokémons...")
                while mensagem == "aguarde":
                    mensagem = cliente.recv(1024).decode("utf-8")

            if mensagem == "batalha_iniciada":
                print("A batalha está prestes a começar!")

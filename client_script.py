import socket
import inquirer
import typer
from lista_pokemons import lista_pokemons
from inquirer.themes import BlueComposure

PORT = 4242
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "utf-8"


# Definindo os Pokémons
nomes_pokemons = [pokemon.name for pokemon in lista_pokemons]
pokemons_jogador = []


def escolher_pokemons(cliente):
    pokemons_prompt = [
        inquirer.Checkbox(
            "pokemons", message="Escolha seus pokémons (max 2)", choices=nomes_pokemons, default=[])
    ]

    pokemons_escolhidos = inquirer.prompt(
        pokemons_prompt, theme=BlueComposure())

    # Convertendo nomes dos Pokémon selecionados para objetos Pokemon
    pokemons_selecionados = pokemons_escolhidos['pokemons']
    pokemons_jogador.extend(pokemons_selecionados)

    pokemons_str = ','.join(
        [pokemon for pokemon in pokemons_selecionados])

    cliente.send(f"pokemons_escolhidos|{pokemons_str}".encode(FORMAT))

    return pokemons_selecionados


def escolher_acao(cliente, pokemons_jogador):
    acoes = [
        inquirer.List("acao", message="O que será feito?", choices=[
            "Atacar", "Itens", "Fugir"
        ], default="Atacar")
    ]

    acao_escolhida = inquirer.prompt(acoes, theme=BlueComposure())

    if acao_escolhida["acao"] == "Atacar":
        atacar(cliente, pokemons_jogador)

    elif acao_escolhida["acao"] == "Itens":
        pass

    elif acao_escolhida["acao"] == "Fugir":
        pass


def atacar(cliente, pokemons_escolhidos):
    pokemon_atual = lista_pokemons[pokemons_escolhidos[0]]
    ataques_disponiveis = pokemon_atual.value["ataques"]
    
    ataques = [
        inquirer.List("ataque", message="Escolha um ataque", choices=[
            ataques_disponiveis[0], ataques_disponiveis[1]
        ], default="Ataque 1")
    ]

    ataque_escolhido = inquirer.prompt(ataques, theme=BlueComposure())

    cliente.send(f"ataque|{pokemon_atual}|{ataque_escolhido['ataque']}".encode(FORMAT))



if __name__ == "__main__":
    try:
        cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cliente.connect(ADDR)
    except Exception as e:
        typer.echo(f"Erro ao conectar ao servidor: {e}")
        exit()

    typer.echo("Bem-vindo à batalha Pokémon!")

    nome = typer.prompt("Digite seu nome")
    cliente.send(f"nome|{nome}\n".encode(FORMAT))
    print("Conectado ao servidor!")

    buffer = ""

    while True:
        buffer += cliente.recv(1024).decode(FORMAT)
        mensagens = buffer.split("\n")

        for mensagem in mensagens[:-1]:
            if not buffer:
                continue

            tipo_mensagem, buffer = buffer.split("|", 1)
            tipo_mensagem = tipo_mensagem.strip()
            buffer = buffer.strip()

            if tipo_mensagem == "status":
                if buffer == "escolha_pokemons":
                    pokemons_jogador = escolher_pokemons(cliente)

                elif buffer == "jogo_pronto":
                    cliente.send("status|pronto\n".encode(FORMAT))
                    typer.echo("Aguardando o outro jogador para começær...")

                elif buffer == "sua_vez":
                    print("É a sua vez de jogar!")
                    acao = escolher_acao(cliente, pokemons_jogador)

                elif buffer == "aguarde":
                    print("Aguarde o outro jogador realizar sua ação...")

            buffer = mensagens[-1]

import re
import sys
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
        usar_item(cliente, pokemons_jogador)

    elif acao_escolhida["acao"] == "Fugir":
        fugir(cliente, nome)

def usar_item(cliente, pokemons_jogador):
    # Supomos que o item cura o primeiro Pokémon
    pokemon = pokemons_jogador[0]  # O primeiro Pokémon do jogador
    
    # Enviar a mensagem de uso de item para o servidor
    cliente.send(f"item|{pokemon}\n".encode(FORMAT))
    print(f"Você usou uma poção em {pokemon}!")
    
def fugir(cliente, nome_jogador):
    cliente.send(f"fugiu|{nome_jogador}".encode(FORMAT))
    print(f"{nome} decidiu fugir da batalha!")
    sys.exit(0)  # Encerra o jogo localmente

def atacar(cliente, pokemons_escolhidos):
    pokemon_atual = lista_pokemons[pokemons_escolhidos[0]]
    ataques_disponiveis = pokemon_atual.value["ataques"]
    lista_ataques = []
    dano_ataque = 0

    for ataque, dano in ataques_disponiveis.items():
        lista_ataques.append(f"{ataque} (Dano: {dano})")

    ataques = [
        inquirer.List("ataque", message="Escolha um ataque", choices=[
            lista_ataques[0], lista_ataques[1]
        ], default="")
    ]

    ataque_escolhido = inquirer.prompt(ataques, theme=BlueComposure())

    match = re.search(r'\(Dano: (\d+)\)', ataque_escolhido["ataque"])
    if match:
        dano_ataque = int(match.group(1))

    nome_ataque = ataque_escolhido["ataque"].split(" (")[0]

    cliente.send(
        f"ataque|{pokemon_atual}|{nome_ataque}|{dano_ataque}".encode(FORMAT))


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
            if not mensagem:
                continue

            if buffer:
                tipo_mensagem, conteudo_mensagem = buffer.split("|", 1)
                tipo_mensagem = tipo_mensagem.strip()
                conteudo_mensagem = conteudo_mensagem.strip()
            else:
                # buffer = ""
                continue

            # print(f"{tipo_mensagem} - {conteudo_mensagem}")

            if tipo_mensagem == "status":
                if conteudo_mensagem == "escolha_pokemons":
                    pokemons_jogador = escolher_pokemons(cliente)

                elif conteudo_mensagem == "jogo_pronto":
                    cliente.send("status|pronto\n".encode(FORMAT))
                    typer.echo("Aguardando o outro jogador para começær...")

                elif conteudo_mensagem == "sua_vez":
                    print("É a sua vez de jogar!")
                    acao = escolher_acao(cliente, pokemons_jogador)

                elif conteudo_mensagem == "aguarde":
                    print("Aguarde o outro jogador realizar sua ação...")

                elif conteudo_mensagem == "vitoria":
                    print("VOCÊ VENCEU! PARABÉNS!")
                    sys.exit(0)

                elif conteudo_mensagem == "derrota":
                    print("VOCÊ PERDEU! BOA SORTE NA PRÓXIMA")
                    sys.exit(0)

            if tipo_mensagem == "fugiu":
                print(f"O jogador {nome} fugiu")

            if tipo_mensagem == "ataque_recebido":
                print(f"Ataque recebido! {conteudo_mensagem}")

            if tipo_mensagem == "morte":
                print(f"O pokemon {conteudo_mensagem} morreu!")

            buffer = mensagens[-1]

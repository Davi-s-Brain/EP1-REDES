import re
import sys
import socket
import inquirer
import typer
from lista_pokemons import lista_pokemons
from inquirer.themes import BlueComposure

PORT = 4242
SERVER = str(input("Insira o IP do servidor: "))
ADDR = (SERVER, PORT)
FORMAT = "utf-8"

# Definindo os Pokémons
nomes_pokemons = [pokemon.name for pokemon in lista_pokemons]
pokemons_jogador = []


def escolher_pokemons(cliente):
    pokemons_prompt = [
        inquirer.Checkbox(
            "pokemons", message="Escolha seus pokémons (max 1) Aperte espaço para selecionar e Enter para confirmar", choices=nomes_pokemons, default=[])
    ]

    # Exibir a lista de pokémons disponíveis para escolha
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

    # Exibe as ações disponíveis para o jogador
    acao_escolhida = inquirer.prompt(acoes, theme=BlueComposure())

    if acao_escolhida["acao"] == "Atacar":
        atacar(cliente, pokemons_jogador)

    elif acao_escolhida["acao"] == "Itens":
        usar_item(cliente, pokemons_jogador)

    elif acao_escolhida["acao"] == "Fugir":
        fugir(cliente, nome)


def usar_item(cliente, pokemons_jogador):
    # O primeiro Pokémon do jogador será curado
    pokemon = pokemons_jogador[0]  # O primeiro Pokémon escolhido
    item = [
        inquirer.List("item", message="Escolha um item", choices=[
            "potion"
        ], default="")
    ]

    item_escolhido = inquirer.prompt(item, theme=BlueComposure())

    if item_escolhido["item"] == "potion":
        cliente.send(f"item|{pokemon}|potion".encode(FORMAT))
        print(f"Você usou uma {item_escolhido['item']} em {pokemon}!")

    # Enviar a mensagem de uso de item para o servidor
    cliente.send(f"item|{pokemon}\n".encode(FORMAT))


def fugir(cliente, nome_jogador):
    cliente.send(f"fugiu|{nome_jogador}".encode(FORMAT))
    print(f"{nome} decidiu fugir da batalha!")
    sys.exit(0)  # Encerra o jogo localmente


def atacar(cliente, pokemons_escolhidos):
    # Seleciona o primeiro Pokémon escolhido pelo jogador
    pokemon_atual = lista_pokemons[pokemons_escolhidos[0]]
    ataques_disponiveis = pokemon_atual.value["ataques"]
    lista_ataques = []
    dano_ataque = 0

    for ataque, dano in ataques_disponiveis.items():
        lista_ataques.append(f"{ataque} (Dano: {dano})")

    # Prompt para o jogador escolher um ataque
    ataques = [
        inquirer.List("ataque", message="Escolha um ataque", choices=[
            lista_ataques[0], lista_ataques[1]
        ], default="")
    ]

    ataque_escolhido = inquirer.prompt(ataques, theme=BlueComposure())

    # Extrai o dano do ataque escolhido usando regex
    match = re.search(r'\(Dano: (\d+)\)', ataque_escolhido["ataque"])
    if match:
        dano_ataque = int(match.group(1))

    nome_ataque = ataque_escolhido["ataque"].split(" (")[0]

    # Envia a informação do ataque escolhido para o servidor
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

    mensagem = ""

    while True:
        mensagem = cliente.recv(1024).decode(FORMAT)

        tipo_mensagem, conteudo_mensagem = mensagem.split("|", 1)
        tipo_mensagem = tipo_mensagem.strip()
        conteudo_mensagem = conteudo_mensagem.strip()


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

        if tipo_mensagem == "erro":
            print(f"Erro: {conteudo_mensagem}")

        if tipo_mensagem == "info":
            pokemon_nome, pokemon_vida = conteudo_mensagem.split("|")
            print(f"O Pokémon {pokemon_nome} foi curado para {pokemon_vida} pontos de vida!")


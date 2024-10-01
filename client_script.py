import socket
import inquirer
import typer
from inquirer.themes import BlueComposure

PORT = 4242
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)

# Criando a classe Pokémon e seus métodos
class Pokemon:
    def __init__(self, nome, tipo, vida, fraqueza, vantagem):
        self.nome = nome
        self.tipo = tipo
        self._vida = vida
        self.fraqueza = fraqueza
        self.vantagem = vantagem

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


# Definindo Pokémon com atributos específicos
pokemons = [
    Pokemon(nome="Charmander", tipo="Fogo", vida=100,
            fraqueza="Água", vantagem="Planta"),
    Pokemon(nome="Bulbasaur", tipo="Planta", vida=100,
            fraqueza="Fogo", vantagem="Água"),
    Pokemon(nome="Squirtle", tipo="Água", vida=100,
            fraqueza="Elétrico", vantagem="Fogo"),
    Pokemon(nome="Pikachu", tipo="Elétrico", vida=100,
            fraqueza="Terra", vantagem="Água")
]


def escolher_pokemons(cliente):
    choices = [str(pokemon.nome) for pokemon in pokemons]
    pokemons_prompt = [
        inquirer.Checkbox(
            "pokemons", message="Escolha seus pokémons (max 2)", choices=choices, default=[])
    ]

    pokemons_escolhidos = inquirer.prompt(
        pokemons_prompt, theme=BlueComposure())

    # Convertendo nomes dos Pokémon selecionados para objetos Pokemon
    nomes_escolhidos = pokemons_escolhidos['pokemons']
    pokemons_selecionados = [
        pokemon for pokemon in pokemons if pokemon.nome in nomes_escolhidos]

    pokemons_str = ','.join(
        [pokemon.nome for pokemon in pokemons_selecionados])

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

from enum import Enum

lista_pokemons = Enum("Pokemons", {
    "Pikachu": {"tipo": "Elétrico", "vida": 100, "fraqueza": "Terra", "vantagem": "Água", "ataques": [{"Choque do trovão": 10}, {"Cauda de ferro": 15}]},
    "Charmander": {"tipo": "Fogo", "vida": 100, "fraqueza": "Água", "vantagem": "Planta", "ataques": [{"Brasa": 10}, {"Lança-chamas": 15}]},
    "Squirtle": {"tipo": "Água", "vida": 100, "fraqueza": "Elétrico", "vantagem": "Fogo", "ataques": [{"Bolha": 10}, {"Hidro bomba": 15}]},
    "Bulbasaur": {"tipo": "Planta", "vida": 100, "fraqueza": "Fogo", "vantagem": "Água", "ataques": [{"Folha navalha": 10}, {"Raio solar": 15}]}
})

import random

from settings import (
    PENALIZACION_FALLO,
    PRECIO_CUARTO,
    PRECIO_ENTERO,
    PRECIO_MAIZ,
    PRECIO_MEDIO,
)

TIPOS_PLATO = {
    "cuarto": PRECIO_CUARTO,
    "medio": PRECIO_MEDIO,
    "entero": PRECIO_ENTERO,
}

NOMBRES_PLATO = {
    "cuarto": "1/4 de humano",
    "medio": "1/2 humano",
    "entero": "Humano entero",
}


def _secuencia_minijuegos(tipo: str, con_maiz: bool) -> list[str]:
    if tipo == "cuarto":
        secuencia = ["horno"]
    elif tipo == "medio":
        secuencia = ["horno", "corte"]
    else:
        secuencia = ["horno", "corte", "horno"]

    if con_maiz:
        secuencia.append("maiz")

    return secuencia


class Pedido:
    def __init__(self, tipo: str, con_maiz: bool = False):
        self.tipo = tipo
        self.con_maiz = con_maiz
        self.precio_base = TIPOS_PLATO[tipo] + (PRECIO_MAIZ if con_maiz else 0)
        self.precio_actual = self.precio_base
        self.minijuegos = _secuencia_minijuegos(tipo, con_maiz)
        self.cancelado = False
        self.fallos = 0

    @property
    def nombre(self) -> str:
        nombre = NOMBRES_PLATO[self.tipo]
        if self.con_maiz:
            nombre += " + maíz"
        return nombre

    def aplicar_penalizacion(self) -> None:
        self.fallos += 1
        self.precio_actual -= PENALIZACION_FALLO
        # El pedido se cancela si el jugador falló TODOS los minijuegos
        if self.fallos >= len(self.minijuegos):
            self.cancelado = True

    @classmethod
    def generar_aleatorio(cls, nivel: int = 1) -> "Pedido":
        # Distribución ponderada por nivel (§10.6)
        # Nivel 1: mayoría cuartos y medios; nivel 3+: mayoría enteros
        if nivel <= 1:
            pesos = [6, 3, 1]   # cuarto 60%, medio 30%, entero 10%
        elif nivel == 2:
            pesos = [3, 4, 3]   # cuarto 30%, medio 40%, entero 30%
        else:
            pesos = [1, 3, 6]   # cuarto 10%, medio 30%, entero 60%

        tipo = random.choices(list(TIPOS_PLATO.keys()), weights=pesos, k=1)[0]
        con_maiz = random.choice([True, False])
        return cls(tipo, con_maiz)


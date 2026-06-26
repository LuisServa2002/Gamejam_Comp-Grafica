import pygame

from entities.pedido import Pedido
from minijuegos.corte import Corte
from minijuegos.horno import Horno
from minijuegos.maiz import Maiz
from settings import AMARILLO, ANCHO, BLANCO, HUD_ALTO, META_DINERO, NARANJA
from entities.cliente import (
    AnimacionClientePedido,
    AnimacionHumanoHorno,
    AnimacionResultadoCliente,
)
from utils.assets import get_asset_manager

def _formatear_tiempo(segundos: float) -> str:
    total = max(0, int(segundos))
    minutos = total // 60
    resto = total % 60
    return f"{minutos:02d}:{resto:02d}"


class ScreenJuego:
    MINIJUEGOS_REGISTRO = {
        "horno": Horno,
        "corte": Corte,
        "maiz": Maiz,
    }

    def __init__(self, gm):
        self.gm = gm
        self.fuente_hud = pygame.font.SysFont("Arial", 28, bold=True)
        self.fuente_pedido = pygame.font.SysFont("Arial", 20)
        self.fuente_boton = pygame.font.SysFont("Arial", 18, bold=True)
        self._botones_pedido: list[tuple[pygame.Rect, Pedido]] = []
        self.assets = get_asset_manager()
        self.anim_cliente = AnimacionClientePedido("")
        self.anim_horno = AnimacionHumanoHorno()
        self.anim_resultado = AnimacionResultadoCliente()
        self._fase_anterior: str | None = None

    def manejar_eventos(self, eventos):
        if self.gm.estado == "juego" and self.gm.fase_pedido is None:
            for evento in eventos:
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for rect, pedido in self._botones_pedido:
                        if rect.collidepoint(evento.pos):
                            if self.gm.seleccionar_pedido(pedido):
                                self.anim_cliente.reiniciar(pedido.nombre)
                            break
        elif self.gm.estado == "minijuego" and self.gm.minijuego_actual is not None:
            self.gm.minijuego_actual.manejar_eventos(eventos)

    def actualizar(self, dt):
        self.gm.actualizar_timer(dt)

        if self.gm.estado == "juego" and self.gm.fase_pedido == "anim_cliente":
            self.anim_cliente.actualizar(dt)
            if self.anim_cliente.terminada:
                self.gm.avanzar_fase_pedido()
                if self.gm.fase_pedido == "anim_horno":
                    self.anim_horno.reiniciar()
            self._fase_anterior = self.gm.fase_pedido
            return

        if self.gm.estado == "juego" and self.gm.fase_pedido == "anim_horno":
            self.anim_horno.actualizar(dt)
            if self.anim_horno.terminada:
                self.gm.avanzar_fase_pedido()
            self._fase_anterior = self.gm.fase_pedido
            return

        if self.gm.estado == "juego" and self.gm.fase_pedido == "anim_resultado":
            if self._fase_anterior != "anim_resultado":
                self.anim_resultado.reiniciar(bool(self.gm._ultimo_pedido_exitoso))
            self.anim_resultado.actualizar(dt)
            if self.anim_resultado.terminada:
                self.gm.finalizar_resultado_pedido()
            self._fase_anterior = self.gm.fase_pedido
            return

        if self.gm.estado != "minijuego":
            self._fase_anterior = self.gm.fase_pedido
            return

        if self.gm.minijuego_actual is not None:
            self.gm.minijuego_actual.actualizar(dt)
            resultado = self.gm.minijuego_actual.get_resultado()
            if resultado is not None:
                self.gm.registrar_resultado_minijuego(resultado)
                self.gm.minijuego_actual = None
        elif self.gm.pedido_activo is not None:
            self._iniciar_minijuego_actual()

    def dibujar(self, pantalla):
        self._dibujar_fondo(pantalla)
        self._botones_pedido.clear()

        if self.gm.estado == "juego" and self.gm.fase_pedido == "anim_cliente":
            self.anim_cliente.dibujar(pantalla)
        elif self.gm.estado == "juego" and self.gm.fase_pedido == "anim_horno":
            self.anim_horno.dibujar(pantalla)
        elif self.gm.estado == "juego" and self.gm.fase_pedido == "anim_resultado":
            self.anim_resultado.dibujar(pantalla)
        elif self.gm.estado == "juego":
            self._dibujar_cola_pedidos(pantalla)
        elif self.gm.estado == "minijuego" and self.gm.minijuego_actual is not None:
            self.gm.minijuego_actual.dibujar(pantalla)

        if self.gm.estado in ("juego", "minijuego"):
            self._dibujar_hud(pantalla)

    def _dibujar_fondo(self, pantalla):
        if (self.gm.estado == "juego" and self.gm.fase_pedido == "anim_horno") or self.gm.estado == "minijuego":
            fondo = self.assets.get("fondo_cocina")
        else:
            fondo = self.assets.get("fondo_restaurante")

        if fondo is not None:
            pantalla.blit(fondo, (0, 0))
        else:
            if self.gm.estado == "minijuego" or (self.gm.estado == "juego" and self.gm.fase_pedido == "anim_horno"):
                pantalla.fill((30, 25, 25))
            else:
                pantalla.fill((40, 30, 25))

    def _iniciar_minijuego_actual(self) -> None:
        id_minijuego = self.gm.get_minijuego_actual_id()
        if id_minijuego not in self.MINIJUEGOS_REGISTRO:
            return
        cls = self.MINIJUEGOS_REGISTRO[id_minijuego]
        if id_minijuego == "horno" and self.gm.indice_minijuego == 2:
            self.gm.minijuego_actual = cls(velocidad_extra=1.0)
        else:
            self.gm.minijuego_actual = cls()

    def _dibujar_hud(self, pantalla):
        tiempo = _formatear_tiempo(self.gm.tiempo_restante)
        texto_tiempo = self.fuente_hud.render(f"Tiempo: {tiempo}", True, BLANCO)
        texto_dinero = self.fuente_hud.render(
            f"Total: ${self.gm.dinero_acumulado} / ${META_DINERO}", True, AMARILLO
        )
        pygame.draw.rect(pantalla, (40, 30, 25), (0, 0, ANCHO, HUD_ALTO))
        pantalla.blit(texto_tiempo, (20, 20))
        pantalla.blit(texto_dinero, (480, 20))
        pygame.draw.line(pantalla, NARANJA, (0, HUD_ALTO), (ANCHO, HUD_ALTO), 2)

    def _dibujar_cola_pedidos(self, pantalla):
        inicio_x = 50
        ancho = 220
        separacion = 30

        for i, pedido in enumerate(self.gm.pedidos_disponibles):
            x = inicio_x + i * (ancho + separacion)
            y = 100
            rect = pygame.Rect(x, y, ancho, 160)
            self._botones_pedido.append((rect, pedido))

            pygame.draw.rect(pantalla, (60, 45, 35), rect, border_radius=8)
            pygame.draw.rect(pantalla, NARANJA, rect, width=2, border_radius=8)

            nombre = self.fuente_pedido.render(pedido.nombre, True, BLANCO)
            precio = self.fuente_pedido.render(f"${pedido.precio_actual}", True, AMARILLO)
            boton_rect = pygame.Rect(x + 40, y + 110, 140, 36)
            boton = self.fuente_boton.render("TOMAR", True, (0, 0, 0))

            pantalla.blit(nombre, nombre.get_rect(center=(x + ancho // 2, y + 45)))
            pantalla.blit(precio, precio.get_rect(center=(x + ancho // 2, y + 80)))
            pygame.draw.rect(pantalla, AMARILLO, boton_rect, border_radius=6)
            pantalla.blit(boton, boton.get_rect(center=boton_rect.center))

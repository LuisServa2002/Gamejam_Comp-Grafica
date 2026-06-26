import pygame

from entities.pedido import Pedido
from minijuegos.corte import Corte
from minijuegos.horno import Horno
from minijuegos.maiz import Maiz
from settings import AMARILLO, ANCHO, ALTO, BLANCO, HUD_ALTO, NARANJA, TIEMPO_BONUS_EXITO, TIEMPO_PENALIZACION, TIEMPO_BONUS_PEDIDO
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


# ─────────────────────────────────────────────────────────────────────────────
# Texto flotante que sube y se desvanece
# ─────────────────────────────────────────────────────────────────────────────
class _FloatingText:
    """Un texto que flota hacia arriba y se desvanece en 'duracion' segundos."""

    DURACION = 3   # segundos en pantalla
    VELOCIDAD_Y = 30  # px por segundo hacia arriba

    def __init__(self, texto: str, color: tuple, x: int, y: int):
        self.texto = texto
        self.color = color
        self.x = float(x)
        self.y = float(y)
        self.tiempo_vida = self.DURACION
        self.vivo = True
        self._fuente = pygame.font.SysFont("Arial", 26, bold=True)

    def actualizar(self, dt: float) -> None:
        self.y -= self.VELOCIDAD_Y * dt
        self.tiempo_vida -= dt
        if self.tiempo_vida <= 0:
            self.vivo = False

    def dibujar(self, pantalla: pygame.Surface) -> None:
        if not self.vivo:
            return
        # Alfa proporcional al tiempo restante (desaparece suavemente)
        alpha = int(255 * max(0.0, self.tiempo_vida / self.DURACION))

        sup = self._fuente.render(self.texto, True, self.color)
        sup.set_alpha(alpha)

        # Sombra para legibilidad
        sombra = self._fuente.render(self.texto, True, (0, 0, 0))
        sombra.set_alpha(alpha)
        pantalla.blit(sombra, (int(self.x) + 2, int(self.y) + 2))
        pantalla.blit(sup, (int(self.x), int(self.y)))


# ─────────────────────────────────────────────────────────────────────────────
# ScreenJuego
# ─────────────────────────────────────────────────────────────────────────────
class ScreenJuego:
    MINIJUEGOS_REGISTRO = {
        "horno": Horno,
        "corte": Corte,
        "maiz": Maiz,
    }

    # Posiciones fijas donde aparece cada tipo de notificación en HUD
    _POS_TIEMPO = (190, 10)   # junto al contador de tiempo (izquierda)
    _POS_DINERO = (ANCHO - 80, 10)   # junto al contador de dinero (derecha)

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

        # Lista de textos flotantes activos
        self._flotantes: list[_FloatingText] = []

    # ── helpers de notificaciones ────────────────────────────────────────── #

    def _spawn_flotante(self, texto: str, color: tuple, pos: tuple) -> None:
        """Crea un texto flotante en la posición indicada del HUD."""
        self._flotantes.append(_FloatingText(texto, color, pos[0], pos[1]))

    def _notificar_resultado_minijuego(self, exito: bool) -> None:
        """Genera los textos de penalización o bonificación según resultado."""
        nivel_clave = min(self.gm.nivel, 4)
        if exito:
            # Bonus de tiempo (nivel 2+)
            bonus_t = TIEMPO_BONUS_EXITO.get(nivel_clave, 0)
            if bonus_t > 0:
                self._spawn_flotante(f"+{int(bonus_t)}s ⏱", (80, 220, 100), self._POS_TIEMPO)
        else:
            # Penalización de tiempo (nivel 2+)
            pen_t = TIEMPO_PENALIZACION.get(nivel_clave, 0)
            if pen_t > 0:
                self._spawn_flotante(f"-{int(pen_t)}s ⏱", (220, 60, 60), self._POS_TIEMPO)

            # Penalización de precio (siempre que haya pedido activo)
            if self.gm.pedido_activo is not None:
                from settings import PENALIZACION_FALLO
                self._spawn_flotante(f"-${PENALIZACION_FALLO} 💰", (220, 60, 60), self._POS_DINERO)

    def _notificar_pedido_perfecto(self) -> None:
        """Bonus de tiempo por completar un pedido sin errores."""
        nivel_clave = min(self.gm.nivel, 4)
        bonus_p = TIEMPO_BONUS_PEDIDO.get(nivel_clave, 0)
        if bonus_p > 0:
            self._spawn_flotante(f"+{int(bonus_p)}s ⏱ ¡Perfecto!", (80, 220, 100), self._POS_TIEMPO)

    # ── eventos ──────────────────────────────────────────────────────────── #

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

    # ── actualizar ───────────────────────────────────────────────────────── #

    def actualizar(self, dt):
        self.gm.actualizar_timer(dt)

        # Actualizar textos flotantes
        self._flotantes = [f for f in self._flotantes if f.vivo]
        for f in self._flotantes:
            f.actualizar(dt)

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
                # ► Notificar ANTES de que game_manager modifique el estado
                self._notificar_resultado_minijuego(resultado)

                # Si el pedido quedará perfecto (sin fallos previos y éxito), notificar bonus pedido
                if resultado and self.gm._fallos_pedido_actual == 0:
                    ultimo_minijuego = (
                        self.gm.indice_minijuego + 1
                        >= len(self.gm.pedido_activo.minijuegos)
                    ) if self.gm.pedido_activo else False
                    if ultimo_minijuego:
                        self._notificar_pedido_perfecto()

                self.gm.registrar_resultado_minijuego(resultado)
                self.gm.minijuego_actual = None
        elif self.gm.pedido_activo is not None:
            self._iniciar_minijuego_actual()

    # ── dibujar ──────────────────────────────────────────────────────────── #

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
            # Textos flotantes siempre encima del HUD
            for f in self._flotantes:
                f.dibujar(pantalla)

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
            self.gm.minijuego_actual = cls(velocidad_extra=1.0, nivel=self.gm.nivel)
        else:
            self.gm.minijuego_actual = cls(nivel=self.gm.nivel)

    def _dibujar_hud(self, pantalla):
        tiempo = _formatear_tiempo(self.gm.tiempo_restante)
        meta = self.gm.get_meta_actual() if hasattr(self.gm, "get_meta_actual") else self.gm.get_meta_dinero()
        texto_tiempo = self.fuente_hud.render(f"Tiempo: {tiempo}", True, BLANCO)
        texto_dinero = self.fuente_hud.render(
            f"Total: ${self.gm.dinero_acumulado} / ${meta}", True, AMARILLO
        )
        texto_nivel = self.fuente_hud.render(f"Nivel {self.gm.nivel}", True, NARANJA)
        pygame.draw.rect(pantalla, (40, 30, 25), (0, 0, ANCHO, HUD_ALTO))
        pantalla.blit(texto_tiempo, (20, 20))
        pantalla.blit(texto_nivel, (texto_nivel.get_rect(centerx=ANCHO // 2).x, 20))
        pantalla.blit(texto_dinero, (ANCHO - texto_dinero.get_width() - 20, 20))
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

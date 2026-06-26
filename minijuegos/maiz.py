from __future__ import annotations

import math
import random

import pygame

from minijuegos.minijuego_base import MinijuegoBase
import settings


# ─────────────────────────────────────────────────────────────────────────────
# Partícula de grano de maíz
# ─────────────────────────────────────────────────────────────────────────────
class _GranoParticula:
    GRAVEDAD = 420  # px/s²

    def __init__(self, x: float, y: float):
        angulo = random.uniform(math.pi * 0.6, math.pi * 1.4)  # vuela hacia arriba/lados
        velocidad = random.uniform(120, 280)
        self.x = x
        self.y = y
        self.vx = math.cos(angulo) * velocidad
        self.vy = math.sin(angulo) * velocidad  # negativo → sube
        self.radio = random.randint(4, 7)
        self.vivo = True
        self.alpha = 255
        self.color = random.choice([
            (255, 210, 30),   # amarillo maíz
            (255, 185, 10),   # dorado
            (240, 200, 50),   # amarillo pálido
        ])

    def actualizar(self, dt: float) -> None:
        self.vy += self.GRAVEDAD * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Desaparecer al salir de pantalla
        if self.y > settings.ALTO + 20:
            self.vivo = False

    def dibujar(self, pantalla: pygame.Surface) -> None:
        if not self.vivo:
            return
        pygame.draw.circle(pantalla, self.color, (int(self.x), int(self.y)), self.radio)
        # Brillo interno
        if self.radio >= 5:
            pygame.draw.circle(pantalla, (255, 240, 160),
                               (int(self.x) - 1, int(self.y) - 1), max(1, self.radio - 3))


# ─────────────────────────────────────────────────────────────────────────────
# Minijuego Maíz
# ─────────────────────────────────────────────────────────────────────────────
class Maiz(MinijuegoBase):
    # Layout de la mazorca (columnas × filas de granos)
    COLS = 6
    FILAS = 12
    TOTAL_GRANOS = COLS * FILAS   # 72 granos

    def __init__(self, nivel: int = 1) -> None:
        super().__init__()

        # Dificultad según nivel
        clave = min(nivel, max(settings.MAIZ_DESCARGA_POR_NIVEL.keys()))
        self.velocidad_descarga = settings.MAIZ_DESCARGA_POR_NIVEL[clave]
        self.tiempo_restante    = settings.MAIZ_TIEMPO_POR_NIVEL[clave]
        self._tiempo_total      = self.tiempo_restante

        # Barra de progreso (0.0 – 100.0)
        self.progreso = 0.0
        self.fuerza_pulsacion = 8.0  # cuánto sube por cada ESPACIO

        # Partículas de granos volando
        self._particulas: list[_GranoParticula] = []

        # Mazorca: posición central
        self._cx = settings.ANCHO // 2
        self._cy = settings.HUD_ALTO + 310

        # Granos activos (True = aún en la mazorca, False = ya salió)
        self._granos_activos = [True] * self.TOTAL_GRANOS

        # Tazón acumulador
        #self._nivel_tazón = 0.0   # 0.0–1.0

        # Fuentes
        self._fuente_titulo = pygame.font.SysFont("Arial", 26, bold=True)
        self._fuente_ui     = pygame.font.SysFont("Arial", 20)

    # ------------------------------------------------------------------ #
    # Propiedades de la mazorca                                            #
    # ------------------------------------------------------------------ #

    @property
    def _ancho_mazorca(self) -> int:
        return self.COLS * 14 + 4   # ancho total de los granos

    @property
    def _alto_mazorca(self) -> int:
        return self.FILAS * 14 + 4

    # ------------------------------------------------------------------ #
    # Eventos                                                              #
    # ------------------------------------------------------------------ #

    def manejar_eventos(self, eventos) -> None:
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                self.progreso = min(100.0, self.progreso + self.fuerza_pulsacion)

                # Disparar 4–5 granos al presionar ESPACIO
                n_granos = random.randint(4, 5)
                for _ in range(n_granos):
                    # Posición aleatoria en la parte superior de la mazorca
                    ox = random.randint(-self._ancho_mazorca // 2, self._ancho_mazorca // 2)
                    oy = random.randint(-self._alto_mazorca // 2, 0)
                    self._particulas.append(
                        _GranoParticula(self._cx + ox, self._cy + oy)
                    )

                if self.progreso >= 100.0:
                    self.resultado = True

    # ------------------------------------------------------------------ #
    # Actualizar                                                           #
    # ------------------------------------------------------------------ #

    def actualizar(self, dt: float) -> None:
        self.tiempo_restante -= dt

        # Descarga pasiva
        if self.progreso > 0 and self.resultado is None:
            self.progreso = max(0.0, self.progreso - self.velocidad_descarga * dt)

        # Sincronizar granos activos con progreso
        granos_a_eliminar = int((self.progreso / 100.0) * self.TOTAL_GRANOS)
        for i in range(self.TOTAL_GRANOS):
            # Se eliminan de arriba hacia abajo
            self._granos_activos[i] = (i >= granos_a_eliminar)

        # Actualizar tazón
        #self._nivel_tazón = min(1.0, self.progreso / 100.0)

        # Actualizar partículas
        self._particulas = [p for p in self._particulas if p.vivo]
        for p in self._particulas:
            p.actualizar(dt)

        # Condición de fallo
        if self.tiempo_restante <= 0 and self.resultado is None:
            self.resultado = False

    # ------------------------------------------------------------------ #
    # Dibujar                                                              #
    # ------------------------------------------------------------------ #

    def dibujar(self, pantalla: pygame.Surface) -> None:
        # Overlay semitransparente sobre el fondo de cocina
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        pantalla.blit(overlay, (0, 0))

        self._dibujar_hud_minijuego(pantalla)
        self._dibujar_mazorca(pantalla)
        #self._dibujar_tazon(pantalla)
        self._dibujar_barra_progreso(pantalla)

        # Partículas (encima de todo)
        for p in self._particulas:
            p.dibujar(pantalla)

    # ------------------------------------------------------------------ #
    # Sub-renders                                                          #
    # ------------------------------------------------------------------ #

    def _dibujar_hud_minijuego(self, pantalla: pygame.Surface) -> None:
        titulo = self._fuente_titulo.render(
            "¡DESGRANA EL MAÍZ! — Pulsa ESPACIO rápido", True, settings.AMARILLO
        )
        pantalla.blit(titulo, titulo.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 30)))

        timer_txt = self._fuente_ui.render(
            f"Tiempo: {max(0.0, self.tiempo_restante):.1f}s", True, settings.BLANCO
        )
        pantalla.blit(timer_txt, (20, settings.HUD_ALTO + 10))

    def _dibujar_mazorca(self, pantalla: pygame.Surface) -> None:
        """Dibuja la mazorca con granos individuales que se van cayendo."""
        tam_grano = 13
        espacio   = 1
        paso      = tam_grano + espacio

        # Fondo de la mazorca (el marlo/color crema)
        mw = self.COLS * paso + 6
        mh = self.FILAS * paso + 6
        mx = self._cx - mw // 2
        my = self._cy - mh // 2

        # Marlo (interior marrón claro)
        pygame.draw.rect(pantalla, (200, 160, 100), (mx, my, mw, mh), border_radius=10)
        pygame.draw.rect(pantalla, (160, 110, 60),  (mx, my, mw, mh), width=2, border_radius=10)

        # Hojas decorativas a los lados de la mazorca
        for dx, flip in [(-mw // 2 - 18, False), (mw // 2 + 8, True)]:
            pts = [
                (self._cx + dx, my + mh // 2),
                (self._cx + dx + (-30 if flip else 30), my + mh // 5),
                (self._cx + dx + (-12 if flip else 12), my + mh // 2 - 10),
            ]
            pygame.draw.polygon(pantalla, (50, 150, 50), pts)

        # Dibuja granos individuales
        for i, activo in enumerate(self._granos_activos):
            fila = i // self.COLS
            col  = i % self.COLS
            gx = mx + 3 + col * paso
            gy = my + 3 + fila * paso

            if activo:
                # Grano en la mazorca
                pygame.draw.rect(pantalla, (255, 200, 30),
                                 (gx, gy, tam_grano, tam_grano), border_radius=4)
                # Brillo en la esquina superior izquierda del grano
                pygame.draw.rect(pantalla, (255, 240, 160),
                                 (gx + 1, gy + 1, 4, 3), border_radius=2)
                # Borde oscuro del grano
                pygame.draw.rect(pantalla, (200, 140, 0),
                                 (gx, gy, tam_grano, tam_grano), width=1, border_radius=4)
            else:
                # Hueco vacío (marlo expuesto)
                pygame.draw.rect(pantalla, (170, 120, 70),
                                 (gx, gy, tam_grano, tam_grano), border_radius=4)

    """"
    def _dibujar_tazon(self, pantalla: pygame.Surface) -> None:
        Tazón en la parte inferior que se va llenando de maíz.
        tx = settings.ANCHO // 2
        ty_base = settings.ALTO - 50

        # Contorno del tazón (elipse/trapecio)
        tw = 160
        th = 60
        pygame.draw.ellipse(pantalla, (120, 90, 50),
                            (tx - tw // 2, ty_base - th // 2, tw, th))

        # Maíz dentro del tazón (relleno proporcional al progreso)
        if self._nivel_tazón > 0.02:
            relleno_h = int(th * 0.7 * self._nivel_tazón)
            relleno_rect = pygame.Rect(
                tx - (tw - 20) // 2,
                ty_base + th // 2 - relleno_h - 8,
                tw - 20,
                relleno_h
            )
            pygame.draw.rect(pantalla, (255, 200, 30), relleno_rect, border_radius=4)

        # Borde del tazón encima del relleno
        pygame.draw.ellipse(pantalla, (160, 120, 60),
                            (tx - tw // 2, ty_base - th // 2, tw, th), width=3)

        # Etiqueta
        lbl = self._fuente_ui.render("Tazón", True, settings.BLANCO)
        pantalla.blit(lbl, lbl.get_rect(center=(tx, ty_base + th // 2 + 15)))
    """
    
    def _dibujar_barra_progreso(self, pantalla: pygame.Surface) -> None:
        """Barra horizontal de progreso debajo del título."""
        ancho_barra = 400
        alto_barra  = 30
        x_barra = settings.ANCHO // 2 - ancho_barra // 2
        y_barra = settings.HUD_ALTO + 62

        # Fondo
        pygame.draw.rect(pantalla, (50, 40, 10), (x_barra, y_barra, ancho_barra, alto_barra),
                         border_radius=8)

        # Relleno
        ancho_relleno = int(ancho_barra * (self.progreso / 100.0))
        if ancho_relleno > 0:
            # Gradiente simulado: amarillo a naranja
            pygame.draw.rect(pantalla, settings.NARANJA,
                             (x_barra, y_barra, ancho_relleno, alto_barra), border_radius=8)
            pygame.draw.rect(pantalla, settings.AMARILLO,
                             (x_barra, y_barra, ancho_relleno, alto_barra // 2), border_radius=8)

        # Borde
        pygame.draw.rect(pantalla, settings.BLANCO, (x_barra, y_barra, ancho_barra, alto_barra),
                         width=2, border_radius=8)

        # Porcentaje
        pct = self._fuente_ui.render(f"{int(self.progreso)}%", True, settings.NEGRO
                                     if self.progreso > 50 else settings.BLANCO)
        pantalla.blit(pct, pct.get_rect(center=(x_barra + ancho_barra // 2,
                                                 y_barra + alto_barra // 2)))
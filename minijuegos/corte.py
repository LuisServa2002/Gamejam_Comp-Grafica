import pygame
import random
from minijuegos.minijuego_base import MinijuegoBase
import settings


class Corte(MinijuegoBase):
    def __init__(self, nivel: int = 1):
        super().__init__()

        # Dificultad según nivel ----------------------------------------
        clave = min(nivel, max(settings.CORTE_LONGITUD_POR_NIVEL.keys()))
        self.longitud_secuencia = settings.CORTE_LONGITUD_POR_NIVEL[clave]
        self.tiempo_restante   = settings.CORTE_TIEMPO_POR_NIVEL[clave]
        self._tiempo_total     = self.tiempo_restante  # para la barra de tiempo

        # Teclas permitidas según la planificación
        self.teclas_posibles = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
        self.letras_mapeo = {
            pygame.K_a: "A", pygame.K_s: "S", pygame.K_d: "D",
            pygame.K_f: "F", pygame.K_j: "J", pygame.K_k: "K"
        }

        # Generar secuencia aleatoria
        self.secuencia = [random.choice(self.teclas_posibles) for _ in range(self.longitud_secuencia)]

        # Estado del progreso
        self.indice_actual = 0
        self._ultimo_error = False   # flag para efecto visual de tecla incorrecta
        self._tiempo_error = 0.0     # cuánto tiempo mostrar el error

    # ------------------------------------------------------------------ #
    # Eventos                                                              #
    # ------------------------------------------------------------------ #

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key in self.teclas_posibles:
                    self._evaluar_tecla(evento.key)

    def _evaluar_tecla(self, tecla_presionada):
        tecla_correcta = self.secuencia[self.indice_actual]

        if tecla_presionada == tecla_correcta:
            self._ultimo_error = False
            self.indice_actual += 1
            if self.indice_actual >= self.longitud_secuencia:
                self.resultado = True
        else:
            # Error: resetear secuencia con feedback visual
            self.indice_actual = 0
            self._ultimo_error = True
            self._tiempo_error = 0.35  # segundos de efecto rojo

    # ------------------------------------------------------------------ #
    # Actualizar                                                           #
    # ------------------------------------------------------------------ #

    def actualizar(self, dt):
        self.tiempo_restante -= dt

        if self._tiempo_error > 0:
            self._tiempo_error -= dt
            if self._tiempo_error <= 0:
                self._ultimo_error = False

        if self.tiempo_restante <= 0 and self.resultado is None:
            self.resultado = False

    # ------------------------------------------------------------------ #
    # Dibujar                                                              #
    # ------------------------------------------------------------------ #

    def dibujar(self, pantalla):
        # Capa de contraste semi-transparente sobre el fondo de la cocina
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        pantalla.blit(overlay, (0, 0))

        fuente_letras = pygame.font.SysFont("Arial", 52, bold=True)
        fuente_ui     = pygame.font.SysFont("Arial", 22)
        fuente_titulo = pygame.font.SysFont("Arial", 26, bold=True)

        # Título del minijuego
        titulo = fuente_titulo.render("¡EL CORTE! — Presiona la secuencia en orden", True, settings.NARANJA)
        pantalla.blit(titulo, titulo.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 30)))

        # --- Barra de tiempo ---
        ancho_barra_max = 500
        x_barra = (settings.ANCHO - ancho_barra_max) // 2
        y_barra = settings.HUD_ALTO + 65
        proporcion = max(0.0, self.tiempo_restante / self._tiempo_total)
        ancho_actual = int(ancho_barra_max * proporcion)

        # Color de la barra: verde → amarillo → rojo
        if proporcion > 0.5:
            color_barra = (50, 200, 80)
        elif proporcion > 0.25:
            color_barra = settings.AMARILLO
        else:
            color_barra = settings.ROJO

        pygame.draw.rect(pantalla, (60, 30, 30), (x_barra, y_barra, ancho_barra_max, 18), border_radius=5)
        if ancho_actual > 0:
            pygame.draw.rect(pantalla, color_barra, (x_barra, y_barra, ancho_actual, 18), border_radius=5)
        pygame.draw.rect(pantalla, settings.BLANCO, (x_barra, y_barra, ancho_barra_max, 18), width=2, border_radius=5)

        texto_timer = fuente_ui.render(f"{max(0.0, self.tiempo_restante):.1f}s", True, settings.BLANCO)
        pantalla.blit(texto_timer, (x_barra + ancho_barra_max + 10, y_barra))

        # --- Fondo de las teclas ---
        ancho_tecla = 60
        separacion_tecla = 14
        total_ancho = self.longitud_secuencia * (ancho_tecla + separacion_tecla) - separacion_tecla
        inicio_x = (settings.ANCHO - total_ancho) // 2
        y_letras = 280

        # Sombra / panel de fondo
        pad = 20
        panel_rect = pygame.Rect(inicio_x - pad, y_letras - pad,
                                 total_ancho + pad * 2, ancho_tecla + pad * 2)
        pygame.draw.rect(pantalla, (20, 15, 15), panel_rect, border_radius=12)
        pygame.draw.rect(pantalla, settings.NARANJA, panel_rect, width=2, border_radius=12)

        # --- Teclas individuales ---
        for i, tecla in enumerate(self.secuencia):
            letra = self.letras_mapeo[tecla]
            x = inicio_x + i * (ancho_tecla + separacion_tecla)

            if i < self.indice_actual:
                # Ya presionada correctamente
                bg_color  = (30, 140, 50)
                txt_color = settings.BLANCO
            elif i == self.indice_actual:
                # Activa: amarillo normal o rojo si hubo error
                if self._ultimo_error:
                    bg_color  = (160, 20, 20)
                    txt_color = settings.BLANCO
                else:
                    bg_color  = (160, 130, 0)
                    txt_color = settings.NEGRO
            else:
                # Pendiente
                bg_color  = (50, 40, 40)
                txt_color = (180, 180, 180)

            tecla_rect = pygame.Rect(x, y_letras, ancho_tecla, ancho_tecla)
            pygame.draw.rect(pantalla, bg_color, tecla_rect, border_radius=8)
            pygame.draw.rect(pantalla, settings.BLANCO, tecla_rect, width=2, border_radius=8)

            sup = fuente_letras.render(letra, True, txt_color)
            pantalla.blit(sup, sup.get_rect(center=tecla_rect.center))

            # Subrayado bajo la tecla activa
            if i == self.indice_actual and not self._ultimo_error:
                pygame.draw.line(
                    pantalla, settings.AMARILLO,
                    (x, y_letras + ancho_tecla + 6),
                    (x + ancho_tecla, y_letras + ancho_tecla + 6),
                    3
                )

        # --- Progreso textual ---
        progreso_txt = fuente_ui.render(
            f"Progreso: {self.indice_actual} / {self.longitud_secuencia}", True, settings.BLANCO
        )
        pantalla.blit(progreso_txt, progreso_txt.get_rect(center=(settings.ANCHO // 2, y_letras + ancho_tecla + 35)))

        # --- Mensaje de error ---
        if self._ultimo_error:
            err_txt = fuente_ui.render("¡Tecla incorrecta! Secuencia reiniciada", True, settings.ROJO)
            pantalla.blit(err_txt, err_txt.get_rect(center=(settings.ANCHO // 2, y_letras + ancho_tecla + 60)))
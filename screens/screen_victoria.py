import pygame

from settings import AMARILLO, BLANCO, NEGRO, NARANJA


class ScreenVictoria:
    """Pantalla de nivel completado.

    Se muestra cuando el timer llega a 0 y el jugador ha alcanzado la meta.
    ESPACIO llama a gm.subir_nivel() y el juego continúa en el siguiente nivel.
    """

    def __init__(self, gm):
        self.gm = gm
        self.fuente_titulo = pygame.font.SysFont("Arial", 52, bold=True)
        self.fuente_info = pygame.font.SysFont("Arial", 26)
        self.fuente_hint = pygame.font.SysFont("Arial", 20)
        # Capturar el nivel y excedente en el momento en que se abre la pantalla
        self._nivel_completado: int = 0
        self._excedente: int = 0
        self._bonus_inicial: int = 0

    def _capturar_estado(self) -> None:
        """Llamar una sola vez cuando se entra al estado nivel_completado."""
        self._nivel_completado = self.gm.nivel
        self._excedente = max(0, self.gm.dinero_acumulado - self.gm.get_meta_actual())
        self._bonus_inicial = int(self._excedente * 0.75)

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                self.gm.subir_nivel()

    def actualizar(self, dt):
        pass

    def dibujar(self, pantalla):
        pantalla.fill((20, 15, 10))

        # Título
        titulo = self.fuente_titulo.render(
            f"¡Nivel {self._nivel_completado} completado!", True, AMARILLO
        )
        pantalla.blit(titulo, titulo.get_rect(center=(400, 200)))

        # Línea decorativa
        pygame.draw.line(pantalla, NARANJA, (150, 240), (650, 240), 2)

        # Dinero acumulado
        info_dinero = self.fuente_info.render(
            f"Dinero acumulado: ${self.gm.dinero_acumulado + self._excedente}",
            True, BLANCO,
        )
        pantalla.blit(info_dinero, info_dinero.get_rect(center=(400, 290)))

        # Transferencia al siguiente nivel
        if self._bonus_inicial > 0:
            info_bonus = self.fuente_info.render(
                f"Bonus transferido al Nivel {self._nivel_completado + 1}: +${self._bonus_inicial}",
                True, NARANJA,
            )
            pantalla.blit(info_bonus, info_bonus.get_rect(center=(400, 335)))

        # Nueva meta
        nueva_meta = self.gm.get_meta_actual()  # ya refleja nivel+1 tras subir_nivel
        # Calculamos la meta del siguiente nivel sin subirlo aún
        from settings import NIVEL_METAS, NIVEL_META_TECHO
        siguiente_nivel = self._nivel_completado + 1
        siguiente_meta = NIVEL_METAS.get(siguiente_nivel, NIVEL_META_TECHO)
        info_meta = self.fuente_info.render(
            f"Meta del Nivel {siguiente_nivel}: ${siguiente_meta}",
            True, BLANCO,
        )
        pantalla.blit(info_meta, info_meta.get_rect(center=(400, 380)))

        # Hint
        hint = self.fuente_hint.render("Presiona ESPACIO para continuar", True, (180, 180, 180))
        pantalla.blit(hint, hint.get_rect(center=(400, 450)))

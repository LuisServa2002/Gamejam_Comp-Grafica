import pygame

from game_manager import GameManager
from screens.screen_derrota import ScreenDerrota
from screens.screen_inicio import ScreenInicio
from screens.screen_juego import ScreenJuego
from screens.screen_pausa import ScreenPausa
from screens.screen_victoria import ScreenVictoria
from settings import ALTO, ANCHO, FPS, TITULO


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO)
    clock = pygame.time.Clock()

    gm = GameManager()
    screen_juego = ScreenJuego(gm)
    screen_victoria = ScreenVictoria(gm)
    screens = {
        "inicio": ScreenInicio(gm),
        "juego": screen_juego,
        "minijuego": screen_juego,  # comparte instancia
        "nivel_completado": screen_victoria,
        "derrota": ScreenDerrota(gm),
        "pausa": ScreenPausa(gm),
    }

    corriendo = True
    while corriendo:
        dt = clock.tick(FPS) / 1000.0
        eventos = pygame.event.get()

        for evento in eventos:
            if evento.type == pygame.QUIT:
                corriendo = False

        # ESC como toggle: pausa ↔ reanuda (un solo bloque, nunca ambos en el mismo frame)
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if gm.estado in ("juego", "minijuego"):
                    gm.pausar()
                elif gm.estado == "pausa":
                    gm.reanudar()
                break  # Consumir el evento; no lo procesa ninguna otra pantalla

        screen_actual = screens.get(gm.estado)
        if screen_actual:
            # En pausa: primero dibujar el estado anterior (fondo del juego)
            # para que el overlay de pausa se superponga correctamente
            if gm.estado == "pausa" and gm._estado_previo:
                screen_fondo = screens.get(gm._estado_previo)
                if screen_fondo:
                    screen_fondo.dibujar(pantalla)

            # Capturar datos al entrar a nivel_completado por primera vez
            if gm.estado == "nivel_completado" and screen_victoria._nivel_completado != gm.nivel:
                screen_victoria._capturar_estado()

            screen_actual.manejar_eventos(eventos)
            if gm.estado != "pausa":
                screen_actual.actualizar(dt)
            screen_actual.dibujar(pantalla)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

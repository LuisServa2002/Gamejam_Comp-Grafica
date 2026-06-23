import pygame

from game_manager import GameManager
from screens.screen_derrota import ScreenDerrota
from screens.screen_inicio import ScreenInicio
from screens.screen_juego import ScreenJuego
from screens.screen_victoria import ScreenVictoria
from settings import ALTO, ANCHO, FPS, TITULO


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption(TITULO)
    clock = pygame.time.Clock()

    gm = GameManager()
    screens = {
        "inicio": ScreenInicio(gm),
        "juego": ScreenJuego(gm),
        "minijuego": ScreenJuego(gm),
        "victoria": ScreenVictoria(gm),
        "derrota": ScreenDerrota(gm),
    }

    corriendo = True
    while corriendo:
        dt = clock.tick(FPS) / 1000.0
        eventos = pygame.event.get()

        for evento in eventos:
            if evento.type == pygame.QUIT:
                corriendo = False

        screen_actual = screens.get(gm.estado)
        if screen_actual:
            screen_actual.manejar_eventos(eventos)
            screen_actual.actualizar(dt)
            screen_actual.dibujar(pantalla)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

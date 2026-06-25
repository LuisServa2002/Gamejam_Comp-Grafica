import pygame

from entities.pedido import Pedido
from settings import AMARILLO, BLANCO, META_DINERO, NARANJA, NEGRO, ROJO

from minijuegos.horno import Horno
from minijuegos.corte import Corte
from minijuegos.maiz import Maiz

def _formatear_tiempo(segundos: float) -> str:
    total = max(0, int(segundos))
    minutos = total // 60
    resto = total % 60
    return f"{minutos:02d}:{resto:02d}"


class ScreenJuego:
    def __init__(self, gm):
        self.gm = gm
        self.fuente_hud = pygame.font.SysFont("Arial", 28, bold=True)
        self.fuente_pedido = pygame.font.SysFont("Arial", 20)
        self.fuente_boton = pygame.font.SysFont("Arial", 18, bold=True)
        self.fuente_placeholder = pygame.font.SysFont("Arial", 22)
        self._botones_pedido: list[tuple[pygame.Rect, Pedido]] = []
        self._boton_exito: pygame.Rect | None = None
        self._boton_fallo: pygame.Rect | None = None

        self.MINIJUEGOS_REGISTRO = {
            "horno": Horno,
            "corte": Corte,
            "maiz": Maiz
        }

    def manejar_eventos(self, eventos):
        if self.gm.estado == "juego":
            for evento in eventos:
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for rect, pedido in self._botones_pedido:
                        if rect.collidepoint(evento.pos):
                            self.gm.seleccionar_pedido(pedido)

                            # Instanciamos dinámicamente el primer minijuego del pedido
                            id_minijuego = self.gm.get_minijuego_actual_id()
                            if id_minijuego in self.MINIJUEGOS_REGISTRO:
                                self.gm.minijuego_actual = self.MINIJUEGOS_REGISTRO[id_minijuego]()
                            break
        elif self.gm.estado == "minijuego":
            if self.gm.minijuego_actual is not None:
                self.gm.minijuego_actual.manejar_eventos(eventos)

    def actualizar(self, dt):
        self.gm.actualizar_timer(dt)
        
        if self.gm.estado == "minijuego":
            if self.gm.minijuego_actual is not None:
                self.gm.minijuego_actual.actualizar(dt)
                
                # Revisar si el minijuego ya tiene un veredicto (True/False)
                resultado = self.gm.minijuego_actual.get_resultado()
                if resultado is not None:
                    self.gm.registrar_resultado_minijuego(resultado)
                    self.gm.minijuego_actual = None
            else:
                # Si el minijuego anterior se destruyó pero seguimos en estado "minijuego",
                # significa que el pedido tiene otra etapa en su secuencia.
                id_siguiente = self.gm.get_minijuego_actual_id()
                if id_siguiente in self.MINIJUEGOS_REGISTRO:
                    self.gm.minijuego_actual = self.MINIJUEGOS_REGISTRO[id_siguiente]()
                else:
                    # Si el ID no está en nuestro registro (como "maiz" por ahora), lo salta para no colgarse
                    self.gm.registrar_resultado_minijuego(True)
                    self.gm.minijuego_actual = None

    def dibujar(self, pantalla):
        pantalla.fill((40, 30, 25))
        self._botones_pedido.clear()

        self._dibujar_hud(pantalla)

        if self.gm.estado == "juego":
            self._dibujar_cola_pedidos(pantalla)
        elif self.gm.estado == "minijuego":
            if self.gm.minijuego_actual is not None:
                self.gm.minijuego_actual.dibujar(pantalla)
            else:
                self._dibujar_placeholder_minijuego(pantalla)

    def _dibujar_hud(self, pantalla):
        tiempo = _formatear_tiempo(self.gm.tiempo_restante)
        texto_tiempo = self.fuente_hud.render(f"Tiempo: {tiempo}", True, BLANCO)
        texto_dinero = self.fuente_hud.render(
            f"Total: ${self.gm.dinero_acumulado} / ${META_DINERO}", True, AMARILLO
        )
        pantalla.blit(texto_tiempo, (20, 20))
        pantalla.blit(texto_dinero, (480, 20))

        pygame.draw.line(pantalla, NARANJA, (0, 70), (800, 70), 2)

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
            boton = self.fuente_boton.render("TOMAR", True, NEGRO)

            pantalla.blit(nombre, nombre.get_rect(center=(x + ancho // 2, y + 45)))
            pantalla.blit(precio, precio.get_rect(center=(x + ancho // 2, y + 80)))
            pygame.draw.rect(pantalla, AMARILLO, boton_rect, border_radius=6)
            pantalla.blit(boton, boton.get_rect(center=boton_rect.center))

    def _dibujar_placeholder_minijuego(self, pantalla):
        minijuego_id = self.gm.get_minijuego_actual_id() or "?"
        nombres = {"horno": "El Horno", "corte": "El Corte", "maiz": "El Maíz"}
        nombre = nombres.get(minijuego_id, minijuego_id)

        panel = pygame.Rect(150, 320, 500, 200)
        pygame.draw.rect(pantalla, (30, 25, 20), panel, border_radius=10)
        pygame.draw.rect(pantalla, NARANJA, panel, width=2, border_radius=10)

        titulo = self.fuente_placeholder.render(f"Minijuego: {nombre}", True, BLANCO)
        aviso = self.fuente_pedido.render("(placeholder — minijuego real pendiente)", True, AMARILLO)
        pantalla.blit(titulo, titulo.get_rect(center=(400, 360)))
        pantalla.blit(aviso, aviso.get_rect(center=(400, 395)))

        self._boton_exito = pygame.Rect(220, 430, 150, 40)
        self._boton_fallo = pygame.Rect(430, 430, 150, 40)

        pygame.draw.rect(pantalla, (50, 160, 80), self._boton_exito, border_radius=6)
        pygame.draw.rect(pantalla, ROJO, self._boton_fallo, border_radius=6)

        texto_exito = self.fuente_boton.render("ÉXITO", True, BLANCO)
        texto_fallo = self.fuente_boton.render("FALLO", True, BLANCO)
        pantalla.blit(texto_exito, texto_exito.get_rect(center=self._boton_exito.center))
        pantalla.blit(texto_fallo, texto_fallo.get_rect(center=self._boton_fallo.center))

        if self.gm.pedido_activo:
            info = self.fuente_pedido.render(
                f"Pedido: {self.gm.pedido_activo.nombre} — ${self.gm.pedido_activo.precio_actual}",
                True,
                BLANCO,
            )
            pantalla.blit(info, info.get_rect(center=(400, 290)))

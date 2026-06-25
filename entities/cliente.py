from __future__ import annotations

import pygame

import settings
from utils.assets import get_asset_manager


class AnimacionClientePedido:
    """Pollo mesero recibe el pedido (globo con el plato solicitado)."""

    def __init__(self, nombre_pedido: str) -> None:
        self.nombre_pedido = nombre_pedido
        self.tiempo = 0.0
        self.duracion = settings.ANIM_CLIENTE_DURACION
        self.terminada = False
        self._assets = get_asset_manager()
        self.fuente = pygame.font.SysFont("Arial", 22, bold=True)
        self.fuente_bocadillo = pygame.font.SysFont("Arial", 18)

    def reiniciar(self, nombre_pedido: str) -> None:
        self.nombre_pedido = nombre_pedido
        self.tiempo = 0.0
        self.terminada = False

    def actualizar(self, dt: float) -> None:
        if self.terminada:
            return
        self.tiempo += dt
        if self.tiempo >= self.duracion:
            self.terminada = True

    def dibujar(self, pantalla: pygame.Surface) -> None:
        sprite = self._assets.get("pollo_cocinero")
        if sprite is None:
            return

        progreso = min(1.0, self.tiempo / max(0.001, self.duracion * 0.6))
        x_inicio = -40
        x_fin = settings.ANCHO // 2 - 60
        x = int(x_inicio + (x_fin - x_inicio) * progreso)
        y = settings.HUD_ALTO + 200

        rect = sprite.get_rect(center=(x, y))
        pantalla.blit(sprite, rect)

        if self.tiempo > self.duracion * 0.35:
            texto = self.fuente_bocadillo.render(self.nombre_pedido, True, settings.NEGRO)
            padding = 10
            bocadillo = texto.get_rect()
            bocadillo.inflate_ip(padding * 2, padding * 2)
            bocadillo.center = (x + 130, y - 70)
            pygame.draw.rect(pantalla, settings.BLANCO, bocadillo, border_radius=8)
            pygame.draw.rect(pantalla, settings.NARANJA, bocadillo, width=2, border_radius=8)
            pantalla.blit(texto, texto.get_rect(center=bocadillo.center))

        titulo = self.fuente.render("Pollo mesero toma el pedido...", True, settings.BLANCO)
        pantalla.blit(titulo, titulo.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 40)))


class AnimacionHumanoHorno:
    """Humano se acerca al horno en línea recta (horno estático)."""

    def __init__(self) -> None:
        self.tiempo = 0.0
        self.duracion = settings.ANIM_HORNO_DURACION
        self.terminada = False
        self._assets = get_asset_manager()
        self.fuente = pygame.font.SysFont("Arial", 22, bold=True)

    def reiniciar(self) -> None:
        self.tiempo = 0.0
        self.terminada = False

    def actualizar(self, dt: float) -> None:
        if self.terminada:
            return
        self.tiempo += dt
        if self.tiempo >= self.duracion:
            self.terminada = True

    def dibujar(self, pantalla: pygame.Surface) -> None:
        humano_img = self._assets.get("humano_horno")
        if humano_img is None:
            return

        cx = settings.ANCHO // 2
        cy = settings.HUD_ALTO + 260

        # Humano se desliza y se encoge para simular entrar al horno en el fondo de la cocina
        progreso = min(1.0, self.tiempo / max(0.001, self.duracion * 0.85))
        x_inicio = 60
        x_fin = cx + 120
        x_humano = int(x_inicio + (x_fin - x_inicio) * progreso)
        y_humano = cy

        # Reducir escala gradualmente
        escala = 1.0 - 0.6 * progreso
        ancho = max(8, int(humano_img.get_width() * escala))
        alto = max(8, int(humano_img.get_height() * escala))
        
        humano_esc = pygame.transform.smoothscale(humano_img, (ancho, alto))
        humano_rect = humano_esc.get_rect(center=(x_humano, y_humano))
        pantalla.blit(humano_esc, humano_rect)

        titulo = self.fuente.render("¡Al horno!", True, settings.BLANCO)
        pantalla.blit(titulo, titulo.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 40)))


class AnimacionResultadoCliente:
    """Cliente satisfecho o enojado según el resultado del pedido."""

    def __init__(self) -> None:
        self.tiempo = 0.0
        self.duracion = settings.ANIM_RESULTADO_DURACION
        self.terminada = False
        self.feliz = True
        self._assets = get_asset_manager()
        self.fuente = pygame.font.SysFont("Arial", 24, bold=True)

    def reiniciar(self, feliz: bool) -> None:
        self.feliz = feliz
        self.tiempo = 0.0
        self.terminada = False

    def actualizar(self, dt: float) -> None:
        if self.terminada:
            return
        self.tiempo += dt
        if self.tiempo >= self.duracion:
            self.terminada = True

    def dibujar(self, pantalla: pygame.Surface) -> None:
        clave = "cliente_feliz" if self.feliz else "cliente_enojado"
        sprite = self._assets.get(clave)
        if sprite is None:
            return

        cx = settings.ANCHO // 2
        cy = settings.HUD_ALTO + 240
        pantalla.blit(sprite, sprite.get_rect(center=(cx, cy)))

        if self.feliz:
            mensaje = "¡Cliente satisfecho! Pedido entregado."
            color = settings.AMARILLO
        else:
            mensaje = "¡Cliente enojado! Se fue sin pagar."
            color = settings.ROJO

        titulo = self.fuente.render(mensaje, True, color)
        pantalla.blit(titulo, titulo.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 40)))

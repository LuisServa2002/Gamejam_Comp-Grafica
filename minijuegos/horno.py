import pygame
import random

from minijuegos.minijuego_base import MinijuegoBase
import settings
from utils.assets import get_asset_manager

# HORNO_VELOCIDAD_INICIAL=3 en settings equivale ~250 px/s (calibración visual)
_ESCALA_VELOCIDAD_PX = 250 / 3


class Horno(MinijuegoBase):
    _TECLAS_CARRILES = (pygame.K_LEFT, pygame.K_DOWN, pygame.K_UP, pygame.K_RIGHT)
    _CLAVES_FLECHAS = {
        pygame.K_LEFT: "flecha_izquierda",
        pygame.K_DOWN: "flecha_abajo",
        pygame.K_UP: "flecha_arriba",
        pygame.K_RIGHT: "flecha_derecha",
    }

    def __init__(self, velocidad_extra: float = 0):
        super().__init__()

        self.tiempo_transcurrido = 0.0
        self.ventana_tiempo = settings.HORNO_VENTANA_MS / 1000.0
        self.velocidad_caida = (
            settings.HORNO_VELOCIDAD_INICIAL + velocidad_extra
        ) * _ESCALA_VELOCIDAD_PX

        self.linea_impacto_y = settings.ALTO - 80

        margen_lateral = 180
        ancho_total = settings.ANCHO - 2 * margen_lateral
        self.carriles = {
            tecla: margen_lateral + i * (ancho_total / 3)
            for i, tecla in enumerate(self._TECLAS_CARRILES)
        }
        self.lista_teclas = list(self.carriles.keys())

        assets = get_asset_manager()
        self.imagenes_flechas = {
            tecla: assets.get(clave) for tecla, clave in self._CLAVES_FLECHAS.items()
        }

        zona = assets.get("zona_impacto")
        self.zona_impacto = (
            pygame.transform.smoothscale(zona, (80, 20)) if zona is not None else None
        )

        self.notas = []
        cantidad_notas = random.randint(5, 8)
        tiempo_inicial = 1.5
        separacion_tiempo = 0.8

        for i in range(cantidad_notas):
            self.notas.append({
                "tiempo": tiempo_inicial + (i * separacion_tiempo),
                "tecla": random.choice(self.lista_teclas),
                "activa": True,
            })

        self.total_notas = len(self.notas)
        self.aciertos = 0
        self.fallos = 0

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key in self.carriles:
                self._evaluar_presion(evento.key)

    def _evaluar_presion(self, tecla_presionada):
        for nota in self.notas:
            if nota["tecla"] == tecla_presionada and nota["activa"]:
                diferencia = abs(nota["tiempo"] - self.tiempo_transcurrido)
                if diferencia <= self.ventana_tiempo:
                    nota["activa"] = False
                    self.aciertos += 1
                    return

    def actualizar(self, dt):
        if self.resultado is not None:
            return

        self.tiempo_transcurrido += dt

        for nota in self.notas:
            if nota["activa"] and (self.tiempo_transcurrido - nota["tiempo"]) > self.ventana_tiempo:
                nota["activa"] = False
                self.fallos += 1

        if (self.aciertos + self.fallos) >= self.total_notas:
            ratio = self.aciertos / self.total_notas
            self.resultado = ratio >= settings.HORNO_PORCENTAJE_EXITO

    def dibujar(self, pantalla):
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        pantalla.blit(overlay, (0, 0))

        y_visible_min = settings.HUD_ALTO + 30

        if self.zona_impacto is not None:
            for x_pos in self.carriles.values():
                rect = self.zona_impacto.get_rect(center=(int(x_pos), self.linea_impacto_y))
                pantalla.blit(self.zona_impacto, rect)
        else:
            pygame.draw.line(
                pantalla,
                settings.BLANCO,
                (180, self.linea_impacto_y),
                (620, self.linea_impacto_y),
                3,
            )

        mitad_flecha = 20
        for tecla, x_pos in self.carriles.items():
            img_fija = self.imagenes_flechas[tecla]
            if img_fija is not None:
                pantalla.blit(
                    img_fija,
                    (int(x_pos) - mitad_flecha, self.linea_impacto_y - mitad_flecha),
                )

        for nota in self.notas:
            if not nota["activa"]:
                continue

            x_pos = self.carriles[nota["tecla"]]
            distancia_a_impacto = (nota["tiempo"] - self.tiempo_transcurrido) * self.velocidad_caida
            y_pos = self.linea_impacto_y - distancia_a_impacto

            if y_visible_min <= y_pos <= self.linea_impacto_y + 30:
                img_nota = self.imagenes_flechas[nota["tecla"]]
                if img_nota is not None:
                    pantalla.blit(img_nota, (int(x_pos) - mitad_flecha, int(y_pos) - mitad_flecha))

    def get_resultado(self):
        return self.resultado

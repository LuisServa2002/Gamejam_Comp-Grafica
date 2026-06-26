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

    def __init__(self, nivel: int = 1, velocidad_extra: float = 0):
        super().__init__()

        self.tiempo_transcurrido = 0.0

        # Dificultad por nivel (§10.4)
        _tabla_velocidad = {1: 3.0, 2: 3.5, 3: 4.0, 4: 4.5}
        _tabla_ventana   = {1: 150, 2: 135, 3: 120, 4: 110}  # ms
        nivel_clave = min(nivel, 4)
        velocidad_base = _tabla_velocidad.get(nivel_clave, 4.5)
        ventana_ms     = _tabla_ventana.get(nivel_clave, 110)

        self.ventana_tiempo = ventana_ms / 1000.0
        self.velocidad_caida = (velocidad_base + velocidad_extra) * _ESCALA_VELOCIDAD_PX

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
        self.fuente_ui = pygame.font.SysFont("Arial", 24, bold=True)

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
        # 1. Capa oscura para enfocar el minijuego
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        pantalla.blit(overlay, (0, 0))

        y_visible_min = settings.HUD_ALTO + 30

        # 2. Contador de aciertos
        texto_contador = f"Aciertos: {self.aciertos} / {self.total_notas}"
        texto_surf = self.fuente_ui.render(texto_contador, True, settings.BLANCO)
        rect_texto = texto_surf.get_rect(center=(settings.ANCHO // 2, settings.HUD_ALTO + 30))
        pantalla.blit(texto_surf, rect_texto)

        # 3. Flechas receptoras (fijas) semi-transparentes
        mitad_flecha = 20
        for tecla, x_pos in self.carriles.items():
            img_fija = self.imagenes_flechas[tecla]
            if img_fija is not None:
                img_fija.set_alpha(100)  # Semi-transparente para distinguirlas
                pantalla.blit(
                    img_fija,
                    (int(x_pos) - mitad_flecha, self.linea_impacto_y - mitad_flecha),
                )
                img_fija.set_alpha(255)  # Restaurar para las notas


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

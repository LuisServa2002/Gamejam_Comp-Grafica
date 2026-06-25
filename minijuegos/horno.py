import random

import pygame

import settings
from minijuegos.minijuego_base import MinijuegoBase

class Horno(MinijuegoBase):
    def __init__(self):
        super().__init__()
        
        # Configuración de la Zona de Impacto (Línea objetivo abajo)
        self.zona_y = settings.ALTO - 100
        self.zona_alto = 30  # Grosor de la zona de acierto
        
        # Lógica de los círculos (Notas de ritmo)
        self.circulos = []
        self.total_circulos = random.randint(5, 8)  # Entre 5 y 8 círculos por ronda
        self.circulos_lanzados = 0
        
        # Contadores de aciertos
        self.aciertos = 0
        self.intentos_totales = 0
        
        # Temporizador para espaciar la aparición de los círculos (en segundos)
        self.spawn_timer = 0.0
        self.tiempo_entre_spawns = 1.2  # Segundos entre círculo y círculo
        
        # Determinar la velocidad actual basándonos en las constantes
        self.velocidad = settings.HORNO_VELOCIDAD_INICIAL * 60  # Pixeles por segundo

    def _spawn_circulo(self):
        """Genera un nuevo círculo en la parte superior."""
        if self.circulos_lanzados < self.total_circulos:
            # Aparece en el centro del eje X, arriba en Y=0
            nuevo_circulo = {
                "y": 0.0,
                "procesado": False  # Para saber si ya se presionó o se pasó
            }
            self.circulos.append(nuevo_circulo)
            self.circulos_lanzados += 1

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    self._evaluar_presion_espacio()

    def _evaluar_presion_espacio(self):
        """Evalúa si el círculo más cercano está dentro de la ventana de impacto."""
        # Buscar el primer círculo que no haya sido procesado aún
        for circulo in self.circulos:
            if not circulo["procesado"]:
                self.intentos_totales += 1
                
                # Calcular la distancia en píxeles al centro de la zona de impacto
                distancia = abs(circulo["y"] - self.zona_y)
                
                # Convertir la ventana de tiempo (ms) a la tolerancia en píxeles
                # Distancia máxima = velocidad (px/s) * tiempo_tolerancia (s)
                tiempo_tolerancia_segundos = (settings.HORNO_VENTANA_MS / 1000.0)
                tolerancia_pixeles = self.velocidad * tiempo_tolerancia_segundos
                
                if distancia <= tolerancia_pixeles:
                    self.aciertos += 1

                circulo["procesado"] = True
                break  # Solo evaluamos el círculo más bajo en pantalla

    def actualizar(self, dt):
        # 1. Manejar el tiempo para lanzar nuevos círculos
        self.spawn_timer += dt
        if self.spawn_timer >= self.tiempo_entre_spawns:
            self._spawn_circulo()
            self.spawn_timer = 0.0
            
        # 2. Mover los círculos activos hacia abajo con delta time
        for circulo in self.circulos:
            circulo["y"] += self.velocidad * dt
            
            # Si el círculo se pasa del límite inferior y no ha sido procesado aún
            if circulo["y"] > settings.ALTO:
                if not circulo["procesado"]:
                    circulo["procesado"] = True
                    self.intentos_totales += 1

        # 3. Verificar si el minijuego ya terminó
        # El juego termina cuando todos los círculos planificados ya fueron procesados
        if self.intentos_totales >= self.total_circulos:
            self._finalizar_minijuego()

    def _finalizar_minijuego(self):
        """Calcula el porcentaje de aciertos y dicta el resultado."""
        if self.total_circulos > 0:
            porcentaje = self.aciertos / self.total_circulos
            # Éxito si supera el porcentaje de la rúbrica (60%)
            self.resultado = porcentaje >= settings.HORNO_PORCENTAJE_EXITO
        else:
            self.resultado = False

    def dibujar(self, pantalla):
        # Capa de contraste semi-transparente sobre el fondo de la cocina
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        pantalla.blit(overlay, (0, 0))
        
        # Dibujar la Zona de Impacto (Rectángulo indicador abajo)
        color_zona = settings.NARANJA
        from utils.assets import get_asset_manager
        zona_img = get_asset_manager().get("zona_impacto")
        if zona_img is not None:
            zona_esc = pygame.transform.smoothscale(zona_img, (settings.ANCHO - 200, self.zona_alto))
            pantalla.blit(zona_esc, (100, self.zona_y - (self.zona_alto // 2)))
        else:
            pygame.draw.rect(pantalla, color_zona, (100, self.zona_y - (self.zona_alto // 2), settings.ANCHO - 200, self.zona_alto), 2)
        
        # Dibujar los círculos que caen
        for circulo in self.circulos:
            if not circulo["procesado"]:
                # Círculo activo (Amarillo/Rojo como un pollo cocinándose)
                pygame.draw.circle(pantalla, settings.AMARILLO, (settings.ANCHO // 2, int(circulo["y"])), 20)
            else:
                # Círculo ya presionado (se vuelve gris apagado instantáneamente)
                pygame.draw.circle(pantalla, (80, 80, 80), (settings.ANCHO // 2, int(circulo["y"])), 15)

        # Dibujar UI temporal del minijuego (Aciertos en tiempo real)
        fuente = pygame.font.SysFont("Arial", 24)
        texto = fuente.render(f"Aciertos: {self.aciertos} / {self.total_circulos}", True, settings.BLANCO)
        pantalla.blit(texto, (20, settings.HUD_ALTO + 10))
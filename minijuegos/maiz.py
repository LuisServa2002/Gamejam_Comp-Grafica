import pygame
from minijuegos.minijuego_base import MinijuegoBase
import settings

class Maiz(MinijuegoBase):
    def __init__(self):
        super().__init__()
        
        # Progreso de la barra (0.0 a 100.0)
        self.progreso = 0.0
        
        # Tiempo límite (4 segundos según planificación)
        self.tiempo_restante = settings.MAIZ_TIEMPO_LIMITE
        
        # Configuración del juego (Valores calibrados para balancear la dificultad)
        self.fuerza_pulsacion = 8.0  # Cuánto sube por cada "espaciazo"
        self.velocidad_descarga = 15.0  # Cuánto baja por segundo de forma pasiva

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE:
                    # Sumar progreso al presionar ESPACIO
                    self.progreso = min(100.0, self.progreso + self.fuerza_pulsacion)
                    
                    # Condición de éxito: Si llega al 100% antes de acabar el tiempo
                    if self.progreso >= 100.0:
                        self.resultado = True

    def actualizar(self, dt):
        # 1. Restar tiempo usando Delta Time
        self.tiempo_restante -= dt
        
        # 2. Descarga pasiva de la barra (baja sola con el tiempo)
        if self.progreso > 0 and self.resultado is None:
            self.progreso = max(0.0, self.progreso - (self.velocidad_descarga * dt))
            
        # 3. Condición de fallo: Si el tiempo llega a 0 y no se llenó la barra
        if self.tiempo_restante <= 0 and self.resultado is None:
            self.resultado = False

    def dibujar(self, pantalla):
        # Fondo oscuro tirando para marrón/gris
        pantalla.fill((30, 30, 25))
        
        fuente_titulo = pygame.font.SysFont("Arial", 32, bold=True)
        fuente_ui = pygame.font.SysFont("Arial", 24)
        
        # 1. Dibujar el texto instructivo
        texto_instruccion = fuente_titulo.render("¡PRESIONA ESPACIO REPETIDAMENTE!", True, settings.AMARILLO)
        texto_timer = fuente_ui.render(f"Tiempo: {max(0.0, self.tiempo_restante):.1f}s", True, settings.BLANCO)
        pantalla.blit(texto_instruccion, texto_instruccion.get_rect(center=(settings.ANCHO // 2, 180)))
        pantalla.blit(texto_timer, (20, 20))
        
        # 2. Dibujar el contorno de la Barra de Progreso Maíz (Centro de la pantalla)
        ancho_barra = 400
        alto_barra = 40
        x_barra = settings.ANCHO // 2 - (ancho_barra // 2)
        y_barra = 300
        
        # Fondo de la barra (Gris apagado)
        pygame.draw.rect(pantalla, (60, 60, 60), (x_barra, y_barra, ancho_barra, alto_barra), border_radius=8)
        
        # Relleno de la barra proporcional al progreso (Color Amarillo Maíz)
        ancho_relleno = int(ancho_barra * (self.progreso / 100.0))
        if ancho_relleno > 0:
            pygame.draw.rect(pantalla, settings.AMARILLO, (x_barra, y_barra, ancho_relleno, alto_barra), border_radius=8)
            
        # Borde exterior de la barra para darle estilo
        pygame.draw.rect(pantalla, settings.BLANCO, (x_barra, y_barra, ancho_barra, alto_barra), width=3, border_radius=8)
        
        # 3. Mostrar el porcentaje en texto dentro de la barra o abajo
        texto_porcentaje = fuente_ui.render(f"{int(self.progreso)}%", True, settings.BLANCO)
        pantalla.blit(texto_porcentaje, texto_porcentaje.get_rect(center=(settings.ANCHO // 2, y_barra + alto_barra + 30)))
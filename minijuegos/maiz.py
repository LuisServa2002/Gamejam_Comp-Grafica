import pygame
from minijuegos.minijuego_base import MinijuegoBase
import settings

class Maiz(MinijuegoBase):
    def __init__(self, nivel: int = 1):
        super().__init__()
        
        # Progreso de la barra (0.0 a 100.0)
        self.progreso = 0.0
        
        # Dificultad por nivel (§10.4)
        _tabla_descarga = {1: 15.0, 2: 18.0, 3: 21.0, 4: 24.0}
        _tabla_tiempo   = {1: 4.0,  2: 3.5,  3: 3.5,  4: 3.0}
        nivel_clave = min(nivel, 4)
        tiempo_limite = _tabla_tiempo.get(nivel_clave, 3.0)

        self.tiempo_restante = tiempo_limite
        self._tiempo_limite = tiempo_limite  # para la barra de progreso si se necesita
        
        # Configuración del juego
        self.fuerza_pulsacion = 8.0  # Cuánto sube por cada pulsación
        self.velocidad_descarga = _tabla_descarga.get(nivel_clave, 24.0)

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
        # Capa de contraste semi-transparente sobre el fondo de la cocina
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        pantalla.blit(overlay, (0, 0))
        
        fuente_titulo = pygame.font.SysFont("Arial", 32, bold=True)
        fuente_ui = pygame.font.SysFont("Arial", 24)
        
        # Dibujar choclo si está disponible
        from utils.assets import get_asset_manager
        maiz_img = get_asset_manager().get("maiz")
        if maiz_img is not None:
            pantalla.blit(maiz_img, (settings.ANCHO // 2 - maiz_img.get_width() // 2, 215))

        # 1. Dibujar el texto instructivo
        texto_instruccion = fuente_titulo.render("¡PRESIONA ESPACIO REPETIDAMENTE!", True, settings.AMARILLO)
        texto_timer = fuente_ui.render(f"Tiempo: {max(0.0, self.tiempo_restante):.1f}s", True, settings.BLANCO)
        pantalla.blit(texto_instruccion, texto_instruccion.get_rect(center=(settings.ANCHO // 2, 170)))
        pantalla.blit(texto_timer, (20, settings.HUD_ALTO + 10))
        
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
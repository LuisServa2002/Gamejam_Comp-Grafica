import pygame
import random
from minijuegos.minijuego_base import MinijuegoBase
import settings

class Corte(MinijuegoBase):
    def __init__(self, nivel: int = 1):
        super().__init__()
        
        # Teclas permitidas según la planificación
        self.teclas_posibles = [pygame.K_a, pygame.K_s, pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
        self.letras_mapeo = {
            pygame.K_a: "A", pygame.K_s: "S", pygame.K_d: "D", 
            pygame.K_f: "F", pygame.K_j: "J", pygame.K_k: "K"
        }
        
        # Dificultad por nivel (§10.4)
        _tabla_longitud = {1: 5, 2: 5, 3: 6, 4: 7}
        _tabla_tiempo   = {1: 5.0, 2: 4.5, 3: 4.5, 4: 4.0}
        nivel_clave = min(nivel, 4)
        self.longitud_secuencia = _tabla_longitud.get(nivel_clave, 7)
        tiempo_limite = _tabla_tiempo.get(nivel_clave, 4.0)

        self.secuencia = [random.choice(self.teclas_posibles) for _ in range(self.longitud_secuencia)]
        
        # Estado del progreso en la secuencia
        self.indice_actual = 0  # Qué posición de la secuencia debe presionar ahora
        
        # Temporizador
        self.tiempo_restante = tiempo_limite
        self._tiempo_limite = tiempo_limite  # guardado para la barra de progreso

    def manejar_eventos(self, eventos):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                # Solo procesar si la tecla presionada está en nuestro abecedario de juego
                if evento.key in self.teclas_posibles:
                    self._evaluar_tecla(evento.key)

    def _evaluar_tecla(self, tecla_presionada):
        tecla_correcta = self.secuencia[self.indice_actual]
        
        if tecla_presionada == tecla_correcta:
            # Acierto: avanzamos en la secuencia
            self.indice_actual += 1
            # Si completó todas las letras con éxito
            if self.indice_actual >= self.longitud_secuencia:
                self.resultado = True
        else:
            # Fallo: la secuencia se castiga reseteándose al inicio
            self.indice_actual = 0

    def actualizar(self, dt):
        # Restar tiempo usando Delta Time
        self.tiempo_restante -= dt
        
        # Si se acaba el tiempo, el minijuego termina en fracaso
        if self.tiempo_restante <= 0 and self.resultado is None:
            self.resultado = False

    def dibujar(self, pantalla):
        # Capa de contraste semi-transparente sobre el fondo de la cocina
        overlay = pygame.Surface((settings.ANCHO, settings.ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        pantalla.blit(overlay, (0, 0))
        
        # Fuentes de texto
        fuente_letras = pygame.font.SysFont("Arial", 48, bold=True)
        fuente_ui = pygame.font.SysFont("Arial", 24)
        
        # 1. Dibujar Barra de Tiempo Restante (Visual)
        ancho_barra_max = 400
        proporcion_tiempo = max(0, self.tiempo_restante / self._tiempo_limite)
        ancho_barra_actual = int(ancho_barra_max * proporcion_tiempo)
        
        # Contenedor de la barra (Rojo oscuro) y relleno (Rojo vivo)
        pygame.draw.rect(pantalla, (80, 20, 20), (200, 150, ancho_barra_max, 20), border_radius=5)
        pygame.draw.rect(pantalla, settings.ROJO, (200, 150, ancho_barra_actual, 20), border_radius=5)
        
        # 2. Dibujar la secuencia de letras en el centro
        inicio_x = settings.ANCHO // 2 - (self.longitud_secuencia * 35)
        y_letras = 300
        
        for i, tecla in enumerate(self.secuencia):
            letra_texto = self.letras_mapeo[tecla]
            
            # Definir color según el progreso del jugador
            if i < self.indice_actual:
                color_letra = (50, 200, 80) # Verde si ya la presionó bien
            elif i == self.indice_actual:
                color_letra = settings.AMARILLO   # Amarillo parpadeante/activo para la actual
            else:
                color_letra = settings.BLANCO     # Blanco para las pendientes
                
            # Renderizar el texto de la letra
            superficie_letra = fuente_letras.render(letra_texto, True, color_letra)
            pantalla.blit(superficie_letra, (inicio_x + (i * 70), y_letras))
            
            # Dibujar un pequeño subrayado indicador bajo la letra activa
            if i == self.indice_actual:
                pygame.draw.line(pantalla, settings.AMARILLO, (inicio_x + (i * 70), y_letras + 55), (inicio_x + (i * 70) + 35, y_letras + 55), 3)

        # 3. Dibujar UI de soporte informativo
        texto_instruccion = fuente_ui.render("¡Presiona la secuencia en orden rápido!", True, settings.BLANCO)
        texto_timer = fuente_ui.render(f"Tiempo: {max(0.0, self.tiempo_restante):.1f}s", True, settings.BLANCO)
        
        pantalla.blit(texto_instruccion, texto_instruccion.get_rect(center=(settings.ANCHO // 2, 230)))
        pantalla.blit(texto_timer, (20, settings.HUD_ALTO + 10))
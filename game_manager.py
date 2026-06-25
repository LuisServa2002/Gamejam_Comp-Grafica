from entities.pedido import Pedido
from settings import META_DINERO, PRECIO_MINIMO_COBRO, TIEMPO_LIMITE

PEDIDOS_EN_COLA = 3


class GameManager:
    def __init__(self):
        self.dinero_acumulado = 0
        self.tiempo_restante = TIEMPO_LIMITE
        self.pedidos_disponibles: list[Pedido] = []
        self.pedido_activo: Pedido | None = None
        self.estado = "inicio"
        self.minijuego_actual = None
        self.indice_minijuego = 0
        self.fase_pedido: str | None = None  # anim_cliente | anim_horno | anim_resultado
        self._ultimo_pedido_exitoso: bool | None = None
        self._llenar_cola_pedidos()

    def reiniciar(self) -> None:
        self.dinero_acumulado = 0
        self.tiempo_restante = TIEMPO_LIMITE
        self.pedidos_disponibles.clear()
        self.pedido_activo = None
        self.estado = "inicio"
        self.minijuego_actual = None
        self.indice_minijuego = 0
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        self._llenar_cola_pedidos()

    def actualizar_timer(self, dt: float) -> None:
        if self.estado not in ("juego", "minijuego"):
            return

        self.tiempo_restante -= dt
        if self.tiempo_restante <= 0:
            self.tiempo_restante = 0
            self.estado = "victoria" if self.dinero_acumulado >= META_DINERO else "derrota"

    def seleccionar_pedido(self, pedido: Pedido) -> bool:
        if self.estado != "juego" or self.pedido_activo is not None:
            return False
        if pedido not in self.pedidos_disponibles:
            return False

        self.pedidos_disponibles.remove(pedido)
        self.pedido_activo = pedido
        self.indice_minijuego = 0
        self.minijuego_actual = None
        self.fase_pedido = "anim_cliente"
        # Permanece en estado "juego" hasta terminar animaciones
        return True    
    
    def avanzar_fase_pedido(self) -> None:
        """Transición anim_cliente → anim_horno (si aplica) → minijuego."""
        if self.pedido_activo is None:
            self.fase_pedido = None
            return

        if self.fase_pedido == "anim_cliente":
            if self.get_minijuego_actual_id() == "horno":
                self.fase_pedido = "anim_horno"
            else:
                self.fase_pedido = None
                self.estado = "minijuego"
            return

        if self.fase_pedido == "anim_horno":
            self.fase_pedido = None
            self.estado = "minijuego"
            return   

    def registrar_resultado_minijuego(self, exito: bool) -> None:
        if self.pedido_activo is None:
            return

        if not exito:
            self.pedido_activo.aplicar_penalizacion()
            if self.pedido_activo.cancelado:
                self._cancelar_pedido_activo()
                return

        self.indice_minijuego += 1
        if self.indice_minijuego >= len(self.pedido_activo.minijuegos):
            self.cobrar_pedido()

    def cobrar_pedido(self) -> None:
        if self.pedido_activo is None:
            return

        if self.pedido_activo.precio_actual > PRECIO_MINIMO_COBRO:
            self.dinero_acumulado += self.pedido_activo.precio_actual

        self._mostrar_resultado_pedido(exito=True)

    def generar_nuevo_pedido(self) -> None:
        self.pedidos_disponibles.append(Pedido.generar_aleatorio())

    def get_minijuego_actual_id(self) -> str | None:
        if self.pedido_activo is None:
            return None
        if self.indice_minijuego >= len(self.pedido_activo.minijuegos):
            return None
        return self.pedido_activo.minijuegos[self.indice_minijuego]

    def _cancelar_pedido_activo(self) -> None:
        self._mostrar_resultado_pedido(exito=False)

    def _mostrar_resultado_pedido(self, exito: bool) -> None:
        self._ultimo_pedido_exitoso = exito
        self.pedido_activo = None
        self.indice_minijuego = 0
        self.minijuego_actual = None
        self.estado = "juego"
        self.fase_pedido = "anim_resultado"

    def finalizar_resultado_pedido(self) -> None:
        exito = self._ultimo_pedido_exitoso
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        if exito:
            self.generar_nuevo_pedido()
        else:
            self._llenar_cola_pedidos()

    def _llenar_cola_pedidos(self) -> None:
        while len(self.pedidos_disponibles) < PEDIDOS_EN_COLA:
            self.generar_nuevo_pedido()

    def iniciar_partida(self) -> None:
        self.reiniciar()
        self.estado = "juego"

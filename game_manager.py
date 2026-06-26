from entities.pedido import Pedido
from settings import (
    FACTOR_TRANSFERENCIA,
    NIVEL_META_TECHO,
    NIVEL_METAS,
    TIEMPO_LIMITE,
    TIEMPO_BONUS_EXITO,
    TIEMPO_BONUS_PEDIDO,
    TIEMPO_PENALIZACION,
)

PEDIDOS_EN_COLA = 3

# Nivel máximo con tabla de datos (niveles > 4 usan clave 4)
_MAX_CLAVE_NIVEL = 4


def _valor_por_nivel(tabla: dict, nivel: int) -> int:
    clave = min(nivel, _MAX_CLAVE_NIVEL)
    return tabla.get(clave, 0)


class GameManager:
    def __init__(self):
        self.nivel: int = 1
        self.dinero_inicial: int = 0          # saldo transferido del nivel anterior
        self.dinero_acumulado: int = 0
        self.tiempo_restante: float = TIEMPO_LIMITE
        self.pedidos_disponibles: list[Pedido] = []
        self.pedido_activo: Pedido | None = None
        self.estado = "inicio"
        self.minijuego_actual = None
        self.indice_minijuego: int = 0
        self.fase_pedido: str | None = None   # anim_cliente | anim_horno | anim_resultado
        self._ultimo_pedido_exitoso: bool | None = None
        self._estado_previo: str | None = None
        self._fallos_pedido_actual: int = 0   # fallos en el pedido en curso (para bonus de tiempo)
        self._pedido_cancelado: bool = False
        self._llenar_cola_pedidos()

    # ------------------------------------------------------------------
    # Metas y niveles
    # ------------------------------------------------------------------

    def get_meta_actual(self) -> int:
        return NIVEL_METAS.get(self.nivel, NIVEL_META_TECHO)

    def subir_nivel(self) -> None:
        """Calcula transferencia, sube el nivel y reinicia la ronda."""
        excedente = max(0, self.dinero_acumulado - self.get_meta_actual())
        self.dinero_inicial = int(excedente * FACTOR_TRANSFERENCIA)
        self.nivel += 1
        self.tiempo_restante = TIEMPO_LIMITE
        self.dinero_acumulado = self.dinero_inicial
        self.pedidos_disponibles.clear()
        self.pedido_activo = None
        self.minijuego_actual = None
        self.indice_minijuego = 0
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        self._fallos_pedido_actual = 0
        self.estado = "juego"
        self._llenar_cola_pedidos()

    # ------------------------------------------------------------------
    # Reinicio completo (volver al nivel 1)
    # ------------------------------------------------------------------

    def reiniciar(self) -> None:
        self.nivel = 1
        self.dinero_inicial = 0
        self.dinero_acumulado = 0
        self.tiempo_restante = TIEMPO_LIMITE
        self.pedidos_disponibles.clear()
        self.pedido_activo = None
        self.estado = "inicio"
        self.minijuego_actual = None
        self.indice_minijuego = 0
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        self._estado_previo = None
        self._fallos_pedido_actual = 0
        self._llenar_cola_pedidos()

    # ------------------------------------------------------------------
    # Pausa
    # ------------------------------------------------------------------

    def pausar(self) -> None:
        """Congela el juego guardando el estado actual."""
        if self.estado in ("juego", "minijuego"):
            self._estado_previo = self.estado
            self.estado = "pausa"

    def reanudar(self) -> None:
        """Reanuda desde donde se pausó."""
        if self.estado == "pausa" and self._estado_previo:
            self.estado = self._estado_previo
            self._estado_previo = None

    def reiniciar_nivel(self) -> None:
        """Reinicia el nivel actual (mismo nivel, timer y dinero a cero)."""
        self.dinero_acumulado = self.dinero_inicial
        self.tiempo_restante = TIEMPO_LIMITE
        self.pedidos_disponibles.clear()
        self.pedido_activo = None
        self.minijuego_actual = None
        self.indice_minijuego = 0
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        self._estado_previo = None
        self._fallos_pedido_actual = 0
        self.estado = "juego"
        self._llenar_cola_pedidos()

    def salir_al_menu(self) -> None:
        """Vuelve al menú de inicio reiniciando todo."""
        self.reiniciar()

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def actualizar_timer(self, dt: float) -> None:
        if self.estado not in ("juego", "minijuego"):
            return

        self.tiempo_restante -= dt
        if self.tiempo_restante <= 0:
            self.tiempo_restante = 0
            if self.dinero_acumulado >= self.get_meta_actual():
                # Nivel superado → mostrar pantalla de nivel completado
                self.estado = "nivel_completado"
            else:
                self.estado = "derrota"

    # ------------------------------------------------------------------
    # Pedidos
    # ------------------------------------------------------------------

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
        self._fallos_pedido_actual = 0
        self._pedido_cancelado = False
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

        nivel_clave = min(self.nivel, _MAX_CLAVE_NIVEL)

        if exito:
            # Bonus de tiempo por éxito individual (nivel 2+)
            bonus = TIEMPO_BONUS_EXITO.get(nivel_clave, 0)
            self.tiempo_restante = min(TIEMPO_LIMITE, self.tiempo_restante + bonus)
        else:
            self._fallos_pedido_actual += 1
            self.pedido_activo.aplicar_penalizacion()
            # Penalización de tiempo por fallo (nivel 2+)
            penalizacion = TIEMPO_PENALIZACION.get(nivel_clave, 0)
            self.tiempo_restante = max(0.0, self.tiempo_restante - penalizacion)

            if self.pedido_activo.cancelado:
                self._cancelar_pedido_activo()
                return

        self.indice_minijuego += 1
        if self.indice_minijuego >= len(self.pedido_activo.minijuegos):
            # Pedido completado: bonus extra si no hubo ningún fallo
            if self._fallos_pedido_actual == 0:
                bonus_pedido = TIEMPO_BONUS_PEDIDO.get(nivel_clave, 0)
                self.tiempo_restante = min(TIEMPO_LIMITE, self.tiempo_restante + bonus_pedido)
            self.cobrar_pedido()

    def cobrar_pedido(self) -> None:
        if self.pedido_activo is None:
            return

        # Cliente enojado SOLO si falló todos los minijuegos (pedido cancelado)
        # Si falló algunos pero completó el pedido → cliente feliz con precio reducido
        pedido_exitoso = not self._pedido_cancelado

        # Siempre se cobra el precio restante (ya descontadas las penalizaciones)
        if self.pedido_activo.precio_actual > 0:
            self.dinero_acumulado += self.pedido_activo.precio_actual

        # Cliente feliz solo si NO se canceló el pedido
        self._mostrar_resultado_pedido(exito=pedido_exitoso)

    def generar_nuevo_pedido(self) -> None:
        self.pedidos_disponibles.append(Pedido.generar_aleatorio(self.nivel))

    def get_minijuego_actual_id(self) -> str | None:
        if self.pedido_activo is None:
            return None
        if self.indice_minijuego >= len(self.pedido_activo.minijuegos):
            return None
        return self.pedido_activo.minijuegos[self.indice_minijuego]

    def _cancelar_pedido_activo(self) -> None:
        self._pedido_cancelado = True
        self._mostrar_resultado_pedido(exito=False)

    def _mostrar_resultado_pedido(self, exito: bool) -> None:
        self._ultimo_pedido_exitoso = exito
        self.pedido_activo = None
        self.indice_minijuego = 0
        self.minijuego_actual = None
        self.estado = "juego"
        self.fase_pedido = "anim_resultado"

    def finalizar_resultado_pedido(self) -> None:
        cancelado = getattr(self, "_pedido_cancelado", False)
        self.fase_pedido = None
        self._ultimo_pedido_exitoso = None
        self._pedido_cancelado = False
        if cancelado:
            self._llenar_cola_pedidos()
        else:
            self.generar_nuevo_pedido()

    def _llenar_cola_pedidos(self) -> None:
        while len(self.pedidos_disponibles) < PEDIDOS_EN_COLA:
            self.generar_nuevo_pedido()

    def iniciar_partida(self) -> None:
        self.reiniciar()
        self.estado = "juego"

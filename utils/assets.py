from __future__ import annotations

from pathlib import Path

import pygame

import settings


def _ruta_asset(*partes: str) -> Path:
    base = Path(__file__).resolve().parent.parent
    return base.joinpath(*partes)


def _placeholder_rect(tamaño: tuple[int, int], color: tuple[int, int, int], etiqueta: str) -> pygame.Surface:
    ancho, alto = tamaño
    superficie = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.rect(superficie, color, superficie.get_rect(), border_radius=4)
    pygame.draw.rect(superficie, settings.BLANCO, superficie.get_rect(), width=2, border_radius=4)
    fuente = pygame.font.SysFont("Arial", max(10, min(ancho, alto) // 4))
    texto = fuente.render(etiqueta[:8], True, settings.BLANCO)
    superficie.blit(texto, texto.get_rect(center=superficie.get_rect().center))
    return superficie


def cargar_imagen(
    ruta_relativa: str,
    tamaño: tuple[int, int],
    *,
    color_fallback: tuple[int, int, int] = (120, 80, 60),
    etiqueta_fallback: str = "?",
) -> pygame.Surface:
    ruta = _ruta_asset(ruta_relativa)
    try:
        imagen = pygame.image.load(str(ruta)).convert_alpha()
        return pygame.transform.smoothscale(imagen, tamaño)
    except (FileNotFoundError, pygame.error):
        return _placeholder_rect(tamaño, color_fallback, etiqueta_fallback)


class AssetManager:
    """Carga perezosa de recursos usados en Día 3."""

    def __init__(self) -> None:
        self._cache: dict[str, pygame.Surface] = {}

    def get(self, clave: str) -> pygame.Surface | None:
        return self._cache.get(clave)

    def cargar_dia3(self) -> None:
        if self._cache:
            return

        self._cache["fondo_restaurante"] = cargar_imagen(
            settings.RUTA_FONDO_RESTAURANTE,
            (settings.ANCHO, settings.ALTO),
            color_fallback=(55, 40, 32),
            etiqueta_fallback="FONDO",
        )
        self._cache["fondo_cocina"] = cargar_imagen(
            settings.RUTA_FONDO_COCINA,
            (settings.ANCHO, settings.ALTO),
            color_fallback=(30, 25, 25),
            etiqueta_fallback="COCINA",
        )
        self._cache["pollo_cocinero"] = cargar_imagen(
            settings.RUTA_POLLO_COCINERO,
            (256, 256),
            color_fallback=settings.NARANJA,
            etiqueta_fallback="MESERO",
        )
        self._cache["cliente_feliz"] = cargar_imagen(
            settings.RUTA_CLIENTE_FELIZ,
            (300,300),
            color_fallback=settings.AMARILLO,
            etiqueta_fallback="FELIZ",
        )
        self._cache["cliente_enojado"] = cargar_imagen(
            settings.RUTA_CLIENTE_ENOJADO,
            (300,300),
            color_fallback=settings.ROJO,
            etiqueta_fallback="ENOJ",
        )
        self._cache["humano_horno"] = cargar_imagen(
            settings.RUTA_HUMANO_HORNO,
            (256,256),
            color_fallback=(220, 180, 140),
            etiqueta_fallback="HUM",
        )
        self._cache["horno_giratorio"] = cargar_imagen(
            settings.RUTA_HORNO_GIRATORIO,
            (128, 128),
            color_fallback=settings.NARANJA,
            etiqueta_fallback="HORNO",
        )
        self._cache["maiz"] = cargar_imagen(
            settings.RUTA_MAIZ,
            (64,64),
            color_fallback=settings.AMARILLO,
            etiqueta_fallback="MAIZ",
        )
        self._cache["zona_impacto"] = cargar_imagen(
            settings.RUTA_ZONA_IMPACTO,
            (200, 20),
            color_fallback=settings.NARANJA,
            etiqueta_fallback="",
        )
        self._cache["barra_progreso"] = cargar_imagen(
            settings.RUTA_BARRA_PROGRESO,
            (200, 30),
            color_fallback=(80, 80, 80),
            etiqueta_fallback="BAR",
        )


_asset_manager: AssetManager | None = None


def get_asset_manager() -> AssetManager:
    global _asset_manager
    if _asset_manager is None:
        _asset_manager = AssetManager()
        _asset_manager.cargar_dia3()
    return _asset_manager
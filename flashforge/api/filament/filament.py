"""
FlashForge Python API - Filament Module
"""


class Filament:
    """
    Represents a type of filament used in a 3D printer.
    It stores information about the filament's name and its recommended loading temperature.
    This class can be used to define specific filament types for printer operations
    like loading or preheating.
    """

    def __init__(self, name: str, load_temp: float = 220.0):
        """
        Creates an instance of the Filament class.

        Args:
            name: The name of the filament type (e.g., "PLA", "ABS", "PETG").
            load_temp: The recommended loading temperature for the filament in Celsius. Defaults to 220°C.
        """
        self._name = name
        self._load_temp = load_temp

    @property
    def name(self) -> str:
        """The name of the filament type."""
        return self._name

    @property
    def load_temp(self) -> float:
        """The recommended loading temperature for this filament in Celsius."""
        return self._load_temp

    def __repr__(self) -> str:
        return f"Filament(name='{self._name}', load_temp={self._load_temp})"

    def __str__(self) -> str:
        return f"{self._name} @ {self._load_temp}°C"

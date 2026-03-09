"""
FlashForge Python API - Print Status Parser

Parses print progress information from M27 command responses.
"""

from typing import Optional


class PrintStatus:
    """
    Represents the status of an ongoing print job, including SD card byte progress and layer progress.

    This information is typically parsed from the response of an M27 G-code command,
    which reports the print progress from the SD card.
    """

    def __init__(self) -> None:
        """Initialize a new PrintStatus instance."""
        self.sd_current: str = ""
        self.sd_total: str = ""
        self.layer_current: str = ""
        self.layer_total: str = ""

    def from_replay(self, replay: str) -> Optional["PrintStatus"]:
        """
        Parses a raw string replay (typically from an M27 command) to populate
        the print status properties of this instance.

        The parsing logic expects a multi-line string:
        - Line 1 (data[0]): Usually a command echo, ignored
        - Line 2 (data[1]): Contains SD card progress, e.g., "SD printing byte 12345/67890"
                            It extracts the current and total bytes
        - Line 3 (data[2]): Contains layer progress, e.g., "Layer: 10/250"
                            It extracts the current and total layers

        Args:
            replay: The raw multi-line string response from the printer

        Returns:
            The populated PrintStatus instance, or None if parsing fails
        """
        if not replay:
            return None

        try:
            self.sd_current = ""
            self.sd_total = ""
            self.layer_current = ""
            self.layer_total = ""
            lines = [line.strip() for line in replay.replace("\r", "\n").split("\n") if line.strip()]

            for line in lines:
                if "SD printing byte " in line:
                    sd_progress = line.split("SD printing byte ", 1)[1].strip().strip('"')
                    sd_progress_data = sd_progress.split("/")
                    if len(sd_progress_data) >= 2:
                        self.sd_current = sd_progress_data[0].strip()
                        self.sd_total = sd_progress_data[1].strip()
                elif line.startswith("Layer:"):
                    layer_progress = line.replace("Layer:", "", 1).strip()
                    lp_data = layer_progress.split("/")
                    if len(lp_data) >= 2:
                        self.layer_current = lp_data[0].strip()
                        self.layer_total = lp_data[1].strip()
                    else:
                        return None

            if not self.sd_current or not self.sd_total:
                print("PrintStatus: Invalid SD progress format")
                return None

            return self

        except Exception as e:
            print(f"Error parsing print status: {e}")
            return None

    def get_print_percent(self) -> float:
        """
        Calculates the print progress percentage based on the current and total layers.
        The result is clamped between 0 and 100.

        Returns:
            The print progress percentage (0-100), rounded to the nearest integer.
            Returns NaN if layer information is not available or invalid.
        """
        try:
            current_layer = int(self.layer_current)
            total_layers = int(self.layer_total)

            if total_layers == 0:
                return float("nan")

            perc = (current_layer / total_layers) * 100
            return round(min(100, max(0, perc)))  # Clamp between 0 and 100

        except (ValueError, TypeError):
            return self.get_sd_percent()

    def get_layer_progress(self) -> str:
        """
        Gets the layer progress as a string.

        Returns:
            A string in the format "currentLayer/totalLayers"
        """
        return f"{self.layer_current}/{self.layer_total}"

    def get_sd_progress(self) -> str:
        """
        Gets the SD card byte progress as a string.

        Returns:
            A string in the format "currentBytes/totalBytes"
        """
        return f"{self.sd_current}/{self.sd_total}"

    def get_sd_percent(self) -> float:
        """
        Calculates the SD card progress percentage based on current and total bytes.

        Returns:
            The SD progress percentage (0-100), or NaN if data is invalid
        """
        try:
            current_bytes = int(self.sd_current)
            total_bytes = int(self.sd_total)

            if total_bytes == 0:
                return float("nan")

            perc = (current_bytes / total_bytes) * 100
            return round(min(100, max(0, perc)))  # Clamp between 0 and 100

        except (ValueError, TypeError):
            return float("nan")

    def is_complete(self) -> bool:
        """
        Checks if the print is complete based on layer progress.

        Returns:
            True if current layer equals total layers, False otherwise
        """
        try:
            current = int(self.layer_current)
            total = int(self.layer_total)
            return current >= total and total > 0
        except (ValueError, TypeError):
            sd_percent = self.get_sd_percent()
            return sd_percent == 100 if sd_percent == sd_percent else False

    def __str__(self) -> str:
        """String representation of the print status."""
        layer_perc = self.get_print_percent()
        sd_perc = self.get_sd_percent()

        layer_str = "nan%" if layer_perc != layer_perc else f"{layer_perc}%"  # Check for NaN
        sd_str = "nan%" if sd_perc != sd_perc else f"{sd_perc}%"  # Check for NaN

        return (
            f"PrintStatus(layer={self.get_layer_progress()} [{layer_str}], "
            f"sd={self.get_sd_progress()} [{sd_str}])"
        )

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"PrintStatus("
            f"sd_current='{self.sd_current}', "
            f"sd_total='{self.sd_total}', "
            f"layer_current='{self.layer_current}', "
            f"layer_total='{self.layer_total}')"
        )

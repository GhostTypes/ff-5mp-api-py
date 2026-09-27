"""
FlashForge Python API - Slicer warning translations

Slicers in the OrcaSlicer family (OrcaSlicer, Orca-FlashForge, Flash Studio)
write slice warnings into ``Metadata/slice_info.config`` as raw i18n keys such
as ``bed_temperature_too_high_than_filament``, not as display text. This module
turns those keys into readable sentences. An unknown key falls back to a
prettified form, so a new warning still reads acceptably.

The keys come from OrcaSlicer's ``GCodeProcessor.hpp``, and the wording follows
``Plater::get_slice_warning_string()``, so the messages match what the slicer
itself shows. The table matches ``slicer-meta``'s ``warning-translations.ts``.
"""

from __future__ import annotations

_KNOWN_WARNINGS: dict[str, str] = {
    "bed_temperature_too_high_than_filament": (
        "The current hot bed temperature is relatively high. The nozzle may be clogged "
        "when printing this filament in a closed enclosure. Please open the front door "
        "and/or remove the upper glass."
    ),
    "the_actual_nozzle_hrc_smaller_than_the_required_nozzle_hrc": (
        "The nozzle hardness required by the filament is higher than the default nozzle "
        "hardness of the printer. Please replace the hardened nozzle or filament, "
        "otherwise, the nozzle will be attrited or damaged."
    ),
    "not_support_traditional_timelapse": (
        "Enabling traditional timelapse photography may cause surface imperfections. "
        "It is recommended to change to smooth mode."
    ),
    "not_generate_timelapse": "Timelapse will not be generated for this print.",
    "smooth_timelapse_without_prime_tower": (
        "Smooth mode for timelapse is enabled, but the prime tower is off, which may "
        "cause print defects. Please enable the prime tower, re-slice and print again."
    ),
    "activate_long_retraction_when_cut": "Long retraction when cut is enabled for this print.",
}


def translate_warning(key: str) -> str:
    """
    Translate a raw slicer warning key into readable text.

    Args:
        key: The warning key as the slicer wrote it.

    Returns:
        The curated message for a known key, a prettified form of an unknown
        snake_case key, or an empty string for an empty key.
    """
    if not key:
        return ""
    known = _KNOWN_WARNINGS.get(key)
    if known is not None:
        return known
    words = key.replace("_", " ").strip()
    return words[:1].upper() + words[1:] if words else ""

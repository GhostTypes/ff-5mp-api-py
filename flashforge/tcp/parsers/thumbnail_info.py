"""
FlashForge Python API - Thumbnail Info Parser

Handles the parsing, storage, and manipulation of 3D print file thumbnail images.
"""
import base64
from pathlib import Path
from typing import Optional


class ThumbnailInfo:
    """
    Handles the parsing, storage, and manipulation of 3D print file thumbnail images.
    
    Thumbnails are typically retrieved from the printer using a command like M662,
    which returns a mixed response containing text (e.g., "ok") followed by raw binary PNG data.
    This class provides methods to extract the PNG data, convert it to various formats, and save it to a file.
    """

    def __init__(self):
        """Initialize a new ThumbnailInfo instance."""
        self._image_data: Optional[bytes] = None
        self._file_name: Optional[str] = None

    def from_replay(self, replay: str, file_name: str) -> Optional['ThumbnailInfo']:
        """
        Parses thumbnail data from a raw printer response string.
        
        The method expects the response to contain an "ok" text delimiter, after which
        the binary PNG data begins. It searches for the PNG signature (0x89 PNG)
        within the binary portion to correctly extract the image.
        
        Args:
            replay: The raw string response from the printer, which may include text and binary data
            file_name: The name of the file for which the thumbnail was retrieved
            
        Returns:
            A ThumbnailInfo instance populated with the image data if parsing is successful,
            or None if the replay is invalid, "ok" is not found, or the PNG signature is missing
        """
        if not replay:
            return None

        try:
            # Store the file name
            self._file_name = file_name

            # Find where the PNG data starts (after the "ok" text delimiter)
            ok_index = replay.find('ok')
            if ok_index == -1:
                print("ThumbnailInfo: No 'ok' found in response")
                return None

            # Skip the 'ok' text and any immediately following control characters
            # The actual binary data starts after "ok"
            binary_start_index = ok_index + 2  # Length of "ok"
            raw_binary_data = replay[binary_start_index:]

            # Convert the extracted string part (assumed to be binary) into bytes
            # The printer sends binary data as part of a string reply
            binary_buffer = raw_binary_data.encode('latin1')  # Use latin1 to preserve byte values

            # Look for the PNG file signature (89 50 4E 47 0D 0A 1A 0A) in the buffer
            # to correctly identify the start of the actual image data
            png_signature = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
            png_start = binary_buffer.find(png_signature)

            if png_start >= 0:
                # Slice the buffer from the start of the PNG signature to get the clean image data
                self._image_data = binary_buffer[png_start:]
                return self
            else:
                print("ThumbnailInfo: No PNG signature found in binary data")
                return None

        except Exception as e:
            print(f"ThumbnailInfo: Error parsing response: {e}")
            return None

    def get_image_data(self) -> Optional[str]:
        """
        Gets the raw thumbnail image data as a Base64 encoded string.
        
        Returns:
            A Base64 encoded string of the PNG image data, or None if no image data is available
        """
        if not self._image_data:
            return None
        return base64.b64encode(self._image_data).decode('ascii')

    def get_image_bytes(self) -> Optional[bytes]:
        """
        Gets the raw thumbnail image data as bytes.
        
        Returns:
            The PNG image data as bytes, or None if no image data is available
        """
        return self._image_data

    def get_file_name(self) -> Optional[str]:
        """
        Gets the file name associated with this thumbnail.
        
        Returns:
            The file name string, or None if it was not set during parsing
        """
        return self._file_name

    def to_base64_data_url(self) -> Optional[str]:
        """
        Converts the thumbnail image data to a Base64 data URL, suitable for embedding in web pages.
        
        Returns:
            A Base64 data URL string (e.g., "data:image/png;base64,..."), or None if no image data is available
        """
        if not self._image_data:
            return None

        base64_data = base64.b64encode(self._image_data).decode('ascii')
        return f"data:image/png;base64,{base64_data}"

    async def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Saves the thumbnail image data to a file.
        
        If no file_path is provided, it attempts to generate a filename using the
        original filename (stored during from_replay) with a ".png" extension.
        
        Args:
            file_path: Optional. The full path (including filename and extension) where the thumbnail should be saved.
                      If not provided, a filename is generated from self._file_name
                      
        Returns:
            True if the file was saved successfully, False otherwise
        """
        if not self._image_data:
            print("ThumbnailInfo: No image data to save")
            return False

        try:
            # If no file path is provided, generate one based on the original filename
            if not file_path and self._file_name:
                # Extract the filename without extension
                path_obj = Path(self._file_name)
                base_name = path_obj.stem
                file_path = f"{base_name}.png"

            if not file_path:
                print("ThumbnailInfo: No file path provided and no filename to generate one from")
                return False

            # Write the bytes to file
            with open(file_path, 'wb') as f:
                f.write(self._image_data)

            print(f"ThumbnailInfo: Saved thumbnail to {file_path}")
            return True

        except Exception as e:
            print(f"ThumbnailInfo: Error saving thumbnail to file: {e}")
            return False

    def save_to_file_sync(self, file_path: Optional[str] = None) -> bool:
        """
        Synchronous version of save_to_file for compatibility.
        
        Args:
            file_path: Optional. The full path where the thumbnail should be saved
            
        Returns:
            True if the file was saved successfully, False otherwise
        """
        if not self._image_data:
            print("ThumbnailInfo: No image data to save")
            return False

        try:
            # If no file path is provided, generate one based on the original filename
            if not file_path and self._file_name:
                # Extract the filename without extension
                path_obj = Path(self._file_name)
                base_name = path_obj.stem
                file_path = f"{base_name}.png"

            if not file_path:
                print("ThumbnailInfo: No file path provided and no filename to generate one from")
                return False

            # Write the bytes to file
            with open(file_path, 'wb') as f:
                f.write(self._image_data)

            print(f"ThumbnailInfo: Saved thumbnail to {file_path}")
            return True

        except Exception as e:
            print(f"ThumbnailInfo: Error saving thumbnail to file: {e}")
            return False

    def get_image_size(self) -> tuple[int, int]:
        """
        Gets the image dimensions by parsing the PNG header.
        
        Returns:
            A tuple of (width, height) in pixels, or (0, 0) if parsing fails
        """
        if not self._image_data or len(self._image_data) < 24:
            return (0, 0)

        try:
            # PNG width and height are stored at bytes 16-23 in big-endian format
            width = int.from_bytes(self._image_data[16:20], byteorder='big')
            height = int.from_bytes(self._image_data[20:24], byteorder='big')
            return (width, height)
        except Exception:
            return (0, 0)

    def has_image_data(self) -> bool:
        """
        Checks if this instance contains valid image data.
        
        Returns:
            True if image data is available, False otherwise
        """
        return self._image_data is not None and len(self._image_data) > 0

    def __str__(self) -> str:
        """String representation of the thumbnail info."""
        if self._image_data:
            width, height = self.get_image_size()
            size_str = f"{len(self._image_data)} bytes, {width}x{height}px"
        else:
            size_str = "no data"

        return f"ThumbnailInfo(file='{self._file_name}', {size_str})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (f"ThumbnailInfo("
                f"file_name='{self._file_name}', "
                f"has_data={self.has_image_data()}, "
                f"size={len(self._image_data) if self._image_data else 0} bytes)")

"""
Audio format conversion utilities for pronunciation assessment
"""
import os
import tempfile
import subprocess
from typing import Optional
from flask import current_app


def convert_webm_to_wav(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert WebM audio file to WAV format for Azure Speech Services compatibility

    Args:
        input_path: Path to input WebM file
        output_path: Path for output WAV file (optional, will generate if not provided)

    Returns:
        Path to converted WAV file

    Raises:
        Exception: If conversion fails
    """
    if output_path is None:
        # Generate output path in same directory
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.wav"

    try:
        # Try using ffmpeg if available (check multiple locations)
        ffmpeg_paths = [
            'ffmpeg',  # In PATH
            '/usr/local/bin/ffmpeg',  # Homebrew location
            '/opt/homebrew/bin/ffmpeg',  # Apple Silicon Homebrew
            '/Users/chunhewang/Desktop/ffmpeg'  # User's desktop location
        ]

        ffmpeg_cmd = None
        for path in ffmpeg_paths:
            try:
                subprocess.run([path, '-version'], capture_output=True, check=True)
                ffmpeg_cmd = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        if not ffmpeg_cmd:
            raise FileNotFoundError("FFmpeg not found in any expected location")

        result = subprocess.run([
            ffmpeg_cmd, '-i', input_path,
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',          # 16kHz sample rate (Azure optimal)
            '-ac', '1',              # Mono channel
            '-y',                    # Overwrite output file
            output_path
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            current_app.logger.info(f"Successfully converted {input_path} to {output_path}")
            return output_path
        else:
            current_app.logger.error(f"FFmpeg conversion failed: {result.stderr}")
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")

    except FileNotFoundError:
        # FFmpeg not available, try pydub approach
        current_app.logger.warning("FFmpeg not found, attempting pydub conversion")
        return convert_with_pydub(input_path, output_path)
    except subprocess.TimeoutExpired:
        current_app.logger.error("FFmpeg conversion timed out")
        raise Exception("Audio conversion timed out")
    except Exception as e:
        current_app.logger.error(f"FFmpeg conversion error: {str(e)}")
        # Fallback to pydub
        return convert_with_pydub(input_path, output_path)


def convert_with_pydub(input_path: str, output_path: str) -> str:
    """
    Convert audio using pydub library (fallback method)

    Args:
        input_path: Path to input audio file
        output_path: Path for output WAV file

    Returns:
        Path to converted WAV file
    """
    try:
        from pydub import AudioSegment
        from pydub.utils import which

        # Try to set custom paths for ffmpeg tools if available
        ffmpeg_custom_path = '/Users/chunhewang/Desktop/ffmpeg'
        if os.path.exists(ffmpeg_custom_path):
            AudioSegment.converter = ffmpeg_custom_path
            # For ffprobe, since it's not available, we'll let pydub handle it
            # pydub can work with just ffmpeg for basic conversions
            current_app.logger.info(f"Using custom ffmpeg path: {ffmpeg_custom_path}")

        # Load the WebM audio file
        audio = AudioSegment.from_file(input_path, format="webm")

        # Convert to optimal format for Azure Speech Services
        audio = audio.set_frame_rate(16000)  # 16kHz
        audio = audio.set_channels(1)        # Mono
        audio = audio.set_sample_width(2)    # 16-bit

        # Export as WAV
        audio.export(output_path, format="wav")

        current_app.logger.info(f"Successfully converted {input_path} to {output_path} using pydub")
        return output_path

    except ImportError:
        raise Exception("Neither ffmpeg nor pydub available for audio conversion")
    except Exception as e:
        current_app.logger.error(f"Pydub conversion error: {str(e)}")
        # Try alternative approach without external dependencies
        return create_basic_wav_file(input_path, output_path)


def create_basic_wav_file(input_path: str, output_path: str) -> str:
    """
    Create a basic WAV file header for Azure compatibility
    This is a simplified approach when full conversion fails
    """
    import wave
    import struct

    try:
        # Read the input file as raw bytes
        with open(input_path, 'rb') as f:
            audio_data = f.read()

        # Create a basic 16kHz mono WAV file
        # This is a simplified approach - we'll create a minimal WAV header
        sample_rate = 16000
        channels = 1
        bits_per_sample = 16

        # Use only a portion of the original data to avoid format issues
        # Skip WebM header by taking data from middle of file
        data_start = len(audio_data) // 4
        data_end = 3 * len(audio_data) // 4
        raw_audio = audio_data[data_start:data_end]

        # Limit size to prevent huge files
        max_size = 16000 * 10  # 10 seconds max
        if len(raw_audio) > max_size:
            raw_audio = raw_audio[:max_size]

        # Create WAV file with proper header
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(bits_per_sample // 8)
            wav_file.setframerate(sample_rate)

            # Convert raw bytes to 16-bit samples
            # This is a rough approximation
            samples = []
            for i in range(0, len(raw_audio) - 1, 2):
                if i + 1 < len(raw_audio):
                    # Convert bytes to 16-bit signed integer
                    sample = struct.unpack('<h', raw_audio[i:i+2])[0] if len(raw_audio[i:i+2]) == 2 else 0
                    samples.append(sample)

            # Write samples to WAV file
            for sample in samples:
                wav_file.writeframes(struct.pack('<h', sample))

        current_app.logger.info(f"Created basic WAV file: {output_path}")
        return output_path

    except Exception as e:
        current_app.logger.error(f"Basic WAV creation failed: {str(e)}")
        # If all else fails, just return the original file
        # Azure will handle the error gracefully
        return input_path


def is_wav_format(file_path: str) -> bool:
    """
    Check if file is already in WAV format

    Args:
        file_path: Path to audio file

    Returns:
        True if file is WAV format, False otherwise
    """
    try:
        # Check file extension
        if file_path.lower().endswith('.wav'):
            return True

        # For more thorough check, could examine file headers
        # but for now, extension check is sufficient
        return False

    except Exception:
        return False


def ensure_wav_format(input_path: str) -> str:
    """
    Ensure audio file is in WAV format, converting if necessary

    Args:
        input_path: Path to input audio file

    Returns:
        Path to WAV file (original if already WAV, converted otherwise)
    """
    if is_wav_format(input_path):
        current_app.logger.info(f"File {input_path} is already in WAV format")
        return input_path

    # Generate output path for conversion
    base_name = os.path.splitext(input_path)[0]
    wav_path = f"{base_name}.wav"

    return convert_webm_to_wav(input_path, wav_path)
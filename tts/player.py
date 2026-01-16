import os
import tempfile
import platform


class AudioPlayer:
    """跨平台音频播放器"""

    @staticmethod
    def play(audio_data: bytes, format: str = "wav"):
        """
        播放音频数据

        Args:
            audio_data: 音频字节数据
            format: 音频格式
        """
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
                suffix=f".{format}",
                delete=False
        ) as tmp_file:
            tmp_file.write(audio_data)
            temp_path = tmp_file.name

        try:
            system = platform.system()

            if system == "Windows":
                import winsound
                winsound.PlaySound(temp_path, winsound.SND_FILENAME)
            elif system == "Darwin":  # macOS
                os.system(f"afplay {temp_path}")
            elif system == "Linux":
                # 尝试多个播放器
                for player in ["aplay", "paplay", "ffplay -nodisp -autoexit"]:
                    if os.system(f"which {player.split()[0]} > /dev/null 2>&1") == 0:
                        os.system(f"{player} {temp_path} > /dev/null 2>&1")
                        break
            else:
                print(f"[播放器] 不支持的系统: {system}")
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
from os import remove
import os
from pyannote.audio import Model
from pyannote.audio.pipelines import VoiceActivityDetection
from .vad_interface import VADInterface
from src.audio_utils import save_audio_to_file

class PyannoteVAD(VADInterface):
    """
    Pyannote-based implementation of the VADInterface.
    """

    def __init__(self, **kwargs):
        """
        Initializes Pyannote's VAD pipeline.

        Args:
            model_name (str): The model name for Pyannote.
            auth_token (str, optional): Authentication token for Hugging Face.
        """
        
        model_name = kwargs.get('model_name', "pyannote/segmentation")

        auth_token = os.environ.get('PYANNOTE_AUTH_TOKEN')
        if not auth_token:
            auth_token = kwargs.get('auth_token')
        
        if auth_token is None:
            raise ValueError("Authentication token is required but not provided. Please set the PYANNOTE_AUTH_TOKEN environment variable or pass 'auth_token' as an argument in --vad-args.")
        
        pyannote_args = kwargs.get('pyannote_args', {"onset": 0.5, "offset": 0.5, "min_duration_on": 0.3, "min_duration_off": 0.3})
        self.model = Model.from_pretrained(model_name, use_auth_token=auth_token)
        self.vad_pipeline = VoiceActivityDetection(segmentation=self.model)
        self.vad_pipeline.instantiate(pyannote_args)

    async def detect_activity(self, client):
        audio_file_path = None
        try:
            audio_file_path = await save_audio_to_file(client.scratch_buffer, client.get_file_name)
            vad_results = self.vad_pipeline(audio_file_path)
            
            vad_segments = []
            if len(vad_results):
                vad_segments = [
                    {"start": segment.start, "end": segment.end, "confidence": 1.0}
                    for segment in vad_results.itersegments()
                ]
            
            return vad_segments

        except Exception as e:
            print(f"Error in detect_activity: {str(e)}")
            return []

        finally:
            if audio_file_path:
                try:
                    remove(audio_file_path)
                except Exception as e:
                    print(f"Failed to remove temporary audio file: {str(e)}")

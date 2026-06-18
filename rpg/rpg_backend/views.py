from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from .sounds import VALID_SOUNDS, get_sound_path

@login_required
def sound_serve(request, sound_id):
	if sound_id not in VALID_SOUNDS:
		raise Http404
	path=get_sound_path(sound_id)
	if not path.exists():
		raise Http404
	return FileResponse(open(path, "rb"), content_type="audio/ogg")

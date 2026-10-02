from rest_framework.renderers import JSONRenderer

class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        already_wrapped = isinstance(data, dict) and "success" in data
        if response is not None and response.status_code < 400 and not already_wrapped:
            data = {"success": True, "data": data, "message": None}
        return super().render(data, accepted_media_type, renderer_context)
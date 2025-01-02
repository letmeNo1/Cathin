from cathin.common.request_api import _call_generate_image_caption_api
from cathin.common.utils import _crop_and_encode_image


class ImageProcessor:
    def __init__(self, img, bounds):
        self.img = img
        self.bounds = bounds

    @property
    def icon_description(self):
        a = _crop_and_encode_image(self.img, [self.bounds])

        text = _call_generate_image_caption_api(a).get("descriptions")[0]
        return text
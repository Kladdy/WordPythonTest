# encoding: utf-8
# This module monkey patches the docx library to add support for SVG images
# Put in a local folder and "import docx_svg_patch" to enable EMF support.

from __future__ import absolute_import, division, print_function

import docx
from docx.image.exceptions import UnrecognizedImageError
from docx.image.constants import MIME_TYPE
from docx.image.exceptions import InvalidImageStreamError
from docx.image.helpers import BIG_ENDIAN, StreamReader
from docx.image.image import BaseImageHeader
import struct
import xml.etree.ElementTree as ET



def _ImageHeaderFactory(stream):
    """
    Return a |BaseImageHeader| subclass instance that knows how to parse the
    headers of the image in *stream*.
    """
    from docx.image import SIGNATURES

    def read_64(stream):
        stream.seek(0)
        return stream.read(64)

    header = read_64(stream)
    for cls, offset, signature_bytes in SIGNATURES:
        end = offset + len(signature_bytes)
        found_bytes = header[offset:end]
        if found_bytes == signature_bytes:
            return cls.from_stream(stream)
    raise UnrecognizedImageError

class Svg(BaseImageHeader):
    """
    Image header parser for SVG images.
    """

    @classmethod
    def from_stream(cls, stream):
        """
        Return |Svg| instance having header properties parsed from SVG image
        in *stream*.
        """
        px_width, px_height = cls._dimensions_from_stream(stream)
        return cls(px_width, px_height, 72, 72)

    @property
    def content_type(self):
        """
        MIME content type for this image, unconditionally `image/svg+xml` for
        SVG images.
        """
        return MIME_TYPE.SVG

    @property
    def default_ext(self):
        """
        Default filename extension, always 'svg' for SVG images.
        """
        return "svg"

    @classmethod
    def _dimensions_from_stream(cls, stream):
        stream.seek(0)
        data = stream.read()
        root = ET.fromstring(data)
        # FIXME: The width could be expressed as '4cm'
        # See https://www.w3.org/TR/SVG11/struct.html#NewDocument
        width = int(root.attrib["width"])
        height = int(root.attrib["height"])
        return width, height


docx.image.Svg = Svg
docx.image.constants.MIME_TYPE.SVG = 'image/svg+xml'
docx.image.SIGNATURES = tuple(list(docx.image.SIGNATURES) + [(Svg,  0, b'<svg ')])
docx.image.image._ImageHeaderFactory = _ImageHeaderFactory
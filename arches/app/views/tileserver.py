import TileStache
from django.http import HttpResponse
import os, shutil, sys


def handle_request(request):
    config = os.path.join('arches', 'basemap_tiles', 'arches_default.cfg')
    path_info = request.path.replace('/tileserver/', '')
    query_string = None
    script_name = None

    status_code, headers, content = TileStache.requestHandler2(config, path_info, query_string, script_name)

    response = HttpResponse()
    response.content = content
    response.status_code = status_code
    for header, value in headers.items():
        response[header] = value
    response['Content-length'] = str(len(content))
    return response
#!/usr/bin/env python
"""
duffel.py

Flask app for routing to Rail outputs on various hosts. Currently supports only
Amazon Cloud Drive. Requires https://github.com/yadayada/acd_cli is authorized
and set up as owner of shared directory.
"""
from flask import Flask, redirect, render_template, abort, request, Response
from werkzeug import Headers
from contextlib import closing
import subprocess
import json
import requests
import sys
app = Flask(__name__)

# Path to ACD CLI is hardcoded so app works on Webfaction
_ACDCLI = '/home/verve/anaconda3/bin/acdcli'
# For local tests
_ACDCLI = 'acdcli'

@app.route('/')
def duffout():
    return "Duffel is your friendly neighborhood data broker."

@app.route('/<resource>/<path:identifier>')
def forward(resource, identifier):
    """ Redirects request for file to direct URL.

        Requires global "paths" dictionary is active. 

        resource: a given resource, like "recount2"
        identifier: relative path to file or directory

        Return value: Flask redirect response object
    """
    if resource == 'recount':
        try:
            templink = json.loads(
                            subprocess.check_output(
                                [
                                    _ACDCLI,
                                    'metadata',
                                    '/'.join(['', resource, identifier])
                            ]
                        )
                    )['tempLink']
        except Exception as e:
            # 404 out below
            pass
        else:
            print >>sys.stderr, request.headers.__str__()
            if request.method == 'HEAD':
                # Workaround: use GET and simulate header
                aws_response = requests.get(
                        templink,
                        headers={'range' : 'bytes=0-0'}
                    )
                headers_to_return = Headers(aws_response.headers.items())
                content_length = headers_to_return.get(
                                'content-range'
                            ).rpartition('/')[-1]
                headers_to_return.set('Content-Length', content_length)
                try:
                    content_range = request.headers['range'].replace(
                                            '=', ' '
                                        ).strip()
                    if content_range.endswith('-'):
                        content_range = ''.join(
                                [content_range, content_length,
                                    '/', content_length]
                            )
                    else:
                        content_range = ''.join([content_range,
                                                    '/', content_length])
                    headers_to_return.set(
                            'Content-Range',
                            content_range
                        )
                    content_range_present = True
                except KeyError:
                    headers_to_return.remove('Content-Range')
                    content_range_present = False
                return Response(
                        headers=headers_to_return,
                        status=(206 if content_range_present
                                    else 200),
                        content_type=aws_response.headers['content-type']
                    )
            return redirect(templink, code=302)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)

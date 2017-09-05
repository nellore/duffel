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
import gzip
import atexit
import os
import time
import mmh3
app = Flask(__name__)

# Path to ACD CLI is hardcoded so app works on Webfaction
_ACDCLI = '/home/verve/anaconda3/bin/acdcli'
# For local tests
# _ACDCLI = 'acdcli'
# Path to log file is hardcoded
# DO NOT TRACK IPs/LOCATIONS; track only times
# Always open new logfile when restarting
_LOGDIR = '/home/verve/recount_logs'
filename_numbers = []
for filename_number in [filename.split('.')[1] for filename
    in os.listdir(_LOGDIR) if 'recount_log' in filename]:
    try:
        filename_numbers.append(int(filename_number))
    except ValueError:
        # Not a recognized log file
        pass
try:
    new_filename_number = max(filename_numbers) + 1
except ValueError:
    # Starting from 0 here
    new_filename_number = 0
_LOGFILE = os.path.join(_LOGDIR,
        'recount_log.{filename_number}.{rando}.tsv.gz'.format(
        filename_number=new_filename_number,
        rando='{rando}'.format(rando=random.random())[2:]
    ))
_LOGSTREAM = gzip.open(_LOGFILE, 'a')
def close_log():
    """ Closes log stream; for use on script exit.

        No return value.
    """
    _LOGSTREAM.close()
atexit.register(close_log)

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
    # Log all requests, even weird ones
    print >>_LOGSTREAM, '\t'.join(
        [time.strftime('%A, %b %d, %Y at %I:%M:%S %p %Z'),
             str(mmh3.hash128(str(request.remote_addr) + 'recountsalt')),
             resource,
             identifier])
    _LOGSTREAM.flush()
    if resource == 'recount':
        # Redirect to IDIES URL first
        idies_url = '/'.join(['http://idies.jhu.edu/recount/data', identifier])
        idies_response = requests.head(idies_url)
        if idies_response.status_code == 200:
            return redirect(idies_url, code=302)
        # IDIES won't work; try Cloud Drive
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

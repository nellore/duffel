#!/usr/bin/env python
"""
duffel.py

Flask app for routing to Rail outputs on various hosts. Currently supports only
Amazon Cloud Drive. Requires https://github.com/yadayada/acd_cli is authorized
and set up as owner of shared directory.
"""
from flask import Flask, redirect, render_template, abort
from contextlib import closing
import subprocess
import json
app = Flask(__name__)

# Path to ACD CLI is hardcoded so app works on Webfaction
_ACDCLI = '/home/verve/anaconda3/bin/acdcli'

@app.before_request
def before_request():
    if method == 'HEAD':
        request.environ['REQUEST_METHOD'] = request.method = 'GET'

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
            # Redirect to temp URL obtained from ACD CLI
            return redirect(
                        json.loads(
                            subprocess.check_output(
                                [
                                    _ACDCLI,
                                    'metadata',
                                    '/'.join(['', resource, identifier])
                            ]
                        )
                    )['tempLink']
                )
        except Exception as e:
            # 404 out below
            pass
    abort(404)

if __name__ == '__main__':
    app.run()

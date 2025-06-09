# SPDX-FileCopyrightText: 2025-present Foxocube <git@foxocube.xyz>
#
# SPDX-License-Identifier: MIT
import click
import requests

from console.__about__ import __version__


#@click.command()
@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="Earthlings on Mars Foundation - Console test tool")
@click.option("-f", "--call-from", prompt="Number calling from")
@click.option("-t", "--call-to",   prompt="Number calling to")
def console(call_from, call_to):
    next_url = f"http://127.0.0.1:8000/call/{call_to}/"
    digits = None

    while True:
        response = call(next_url, call_from, digits)
        display_response(response)
        if "actionHook" in response:
            next_url = response["actionHook"]
        digits = input("> ")

def call(url, call_from, digits):
    response = requests.post(
        url,
        data={
            "dtmf": digits,
            "from": call_from
        },
        timeout=30
    )
    response.raise_for_status()
    return response.json()

def display_response(response):
    if response["verb"] == "gather":
        print(response["say"]["text"])
    elif response["verb"] == "say":
        print(response["text"])

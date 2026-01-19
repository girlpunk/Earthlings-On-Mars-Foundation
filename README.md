# Earthlings on Mars Foundation

Interactive Fiction telephone game for EMF Camp 2026

The [EMF](https://emfcamp.org) site has ~15 hard wired vintage public telephones around the site.  In this game, they each represent different areas in a colony base on Mars.  Players interact with the game by phoning various NPCs who hand out missions to complete that will involve calling back from specific phones, with specific numbers, etc.
Like a roll-your-own-adventure book/game, there will be some overall plot progression with various details released through out the 3 days of the event.  Some missions may only be available at certain times, etc.
The game will be advertised by stickers on the info boards around each public phone that direct players to call a given NPC.  Players can join the game by calling any of the main NPCs.

[![PyPI - Version](https://img.shields.io/pypi/v/earthlings-on-mars-foundation.svg)](https://pypi.org/project/earthlings-on-mars-foundation)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/earthlings-on-mars-foundation.svg)](https://pypi.org/project/earthlings-on-mars-foundation)

______________________________________________________________________

## Table of Contents

- [Game Structure](#game-structure)
- [Introduction](#introduction)
- [License](#license)

## Game Structure

### Player Interactive Structure

Basic call sequence:

* Player dials the extension of an NPC.
* Player is asked to enter their ID number, or can enter 0 to create a new account.
* If there is no in progress mission with this NPC, player is given the next available mission.
* Else if the NPC has an in progress mission with the NPC;
  * If they are calling fro required site, mission is completed.
  * If number is required, they are prompted to enter it.
  * Otherwise they are given a reminder of their mission.

### Players

NPCs will address players as "recruit" and such like terms.  Players identify themselves with a 4 digit ID that is given to them as part of the signup process.  They are then prompted to enter this ID each time they call an NPC (final process for player ID TBD).

### NPCs

Each NPC will have their own phone extension that will be registered in the EMF phone system and routed to the game engine.
It is up to the player to keep nodes about the phone number of each NPC.  Players can discover NPC numbers by one of:

* Advertising around the side.
* Given to them by another NPC.
* Given to them via another player (not something to be depending on but might be interesting for NPCs that are not advertised to have a specific reaction when cold-called?).

Players can call any NPC at any time.  The NPC will respond with one of;

* A new mission.
* A reminder of what their current mission.
* A repeat of a "busy" / repeatable mission.
* A message saying they do not need any assistance at the moment (ideally we want to avoid this).

Voices;
* For dev work, all NPCs are implemented using TTS.
* It would be nice to find some voice actors for the final game.  Though if we substitute text in the messages (like phone numbers) this will make it hard to record all the options.
* Pre-recorded voices will make it much harder to change any text.
* Perhaps some mix of automated systems and character voice memos and such within that?  So players get plot and msgs via voice notes and call automated systems for actual interaction.

Full NPC design and plot notes are private to avoid spoilers.

### Mission Parameters

A mission is a unit of interaction that a player can be given to complete.  They are intended to be chained together to form more complex interactions.
Dependencies between missions are both for building sequence of actions and for detecting if a particular action has already happened.  For example completing a mission for one NPC could result in another NPC being cross you went somewhere you did not actually have clearance to go.

See documentation: https://github.com/girlpunk/Earthlings-On-Mars-Foundation/blob/main/docs/Writing%20Missions.md

### Mission Types

* LOCATION: Call back from a specific location (call_back_from).
* NPC: Call the specified NPC (call_another).
* CODE: Call back with a code from a physical item (code).
* COUNT: Call back with an arbitrary number (currently not verified).

## Installation

```console
pip install earthlings-on-mars-foundation
```

## Run Locally

```shell
nix develop --command $SHELL
cd src/earthlings_on_mars_foundation
./manage.py migrate
DEBUG=true ./manage.py runserver 0.0.0.0:8000
```

## License

`earthlings-on-mars-foundation` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

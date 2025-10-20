# Lua

Lua is a scripting language that can be used to define custom missions.

General details about Lua are outside the scope of this document, however some additional functionality is available through the engine.

You may find the following references useful:
  - [Learn X in Y minutes](https://learnxinyminutes.com/lua/)
  - [Devhints Lua cheatsheet](https://devhints.io/lua)
  - [GitHub Lua cheatsheet](https://gist.github.com/nilesh-tawari/02078ae5b83ce3c90f476c4858c60693)
  - [opensource.com Lua Cheatsheet](https://opensource.com/sites/default/files/gated-content/cheat_sheet_lua.pdf)

## Available Objects

### `recruit_mission`

The player-mission many-to-many object, with both relations accessable. See the [RecruitMission](### RecruitMission) section below for more details.

### `state`

A generic object for storing state between phone calls when building a mission with Lua.

This can be used to store any arbitrary data relevent to the mission, and will be persisted through to the next time this player cals with this mission, and your Lua is run again.

## Available Functions

N.B. Functions return python coroutines. These must be completed by calling `python.coroutine` to allow them to complete.

For example:

```lua
python.coroutine(say("Hello, World!"))
```

### `complete_mission() -> Coroutine`

Complete the active mission. This will result in the mission being recorded as successful, points being assigned, and the completion text being read.

If you would like to add additional text before and/or after the completion text, this can be done by calling the `say()` method before or after respectively.
Messages will always be read in the voice of the NPC called, even if they are not the mission owner.

### `cancel_mission() -> Coroutine`

Fails the active mission. This will result in the mission being recorded as failed, points being deducted, and the failure text being read.

If you would like to add additional text before and/or after the completion text, this can be done by calling the `say()` method before or after respectively.

### `say(text: str?) -> Coroutine`

Read the specified text to the user.

### `gather(text: str?, digits: int?, min_digits: int?, max_digits: int?) -> Coroutine[[str, str]]`

Read the specified text to the user, and allow the user to reply with DTMF tones.

Optionally, a specific number of digits, or minimum and maximum number of digits can be supplied.
If possible, these should be provided to speed up the timeout on collection.

Results are provided as a tuple containing the string of digits, and a reason the collection stopped.

TODO: provide a code example.

## Additional Objects

### Recruit

#### `score`

The player's current score.

#### `missions`

Active and completed missions for the player. Note that this data may not be loaded.
[TODO: Check if loaded/accessable]

Contents are the same as the [`recruit_mission`](### `recruit_mission`) section above.

#### NPCs

Interactions between NPCs and the player. Note that this data may not be loaded.
[TODO: Check if loaded/accessable]

Contents are details in the [RecruitNPC](### RecruitNPC) section below.

### RecruitNPC

Interactions between NPCs and the player.

#### `recruit`

Recruit this interaction is with

#### `NPC`

NPC this interaction is with

#### `contacted`

If the NPC has been contacted

### RecruitMission

#### `recruit`

Information about this specific recruit. See the [Recruit](### Recruit) section below for more details.

#### `mission`

Information about this mission. See the [Mission](### Mission) section below for more details.

#### `started`

The time the mission was assigned to the player.

#### `finished`

The time the mission was finished by the player.

#### `completed`

If the mission was successfully completed.

#### `code_tries`

Number of attempts the player has made, when the mission type is to call back with a code from a physical item.

It is suggested to use `state` instead of this when building a mission with Lua.

TODO: design descision around what state Lua is allowed to manipulate.

#### `count_value = models.PositiveIntegerField(null=True)

The value entered by the player, when the mission type is to call back with any number.

#### `state`

JSON value of the state object for Lua missions.

It is suggested to use `state` instead of this when building a mission with Lua.

TODO: provide a code example.

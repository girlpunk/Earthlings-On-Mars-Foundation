# Writing Missions

Missions are imported from a series of YAML files.

Each YAML file has an ID number, which uniquely identifies it within that type of document. All documents must have a unique ID within that specific type.

Definitions of YAML are outside the scope of this document.

## Locations

Locations represent known locations that players can call from.
These should not be entered for NPCs' extensions, or players phone numbers.

### `id`

Unique identifier for this location.

### `name`

Name of this location. This is for reference only, and is not displayed to players.

### `extension`

Phone number that calls originated from this location will indicate ("A Number").

## NPCs

NPCs are in-game characters that players can call. They issue and complete missions, and provide contact points for all gameplay.

### `id`

Unique identifier for this NPC.

### `name`

Name of this NPC. This is for reference only, and is not displayed to players.

### `extension`

Phone number that calls to this NPC will indicate ("B Number").

### `introduction`

Text that will be read to the player when they call this NPC forthe first time.

## Missions

Missions provide specific tasks for players to complete. These are available in several preset types, as well as with Lua scripting for more customised missions.

### Mission Metadata

Some general parameters apply to all missions

#### `id`

Unique identifier for this Mission.

#### `name`

Name for this mission. This is for reference only, and is not displayed to players.

#### `giveText`

Text that will be read to the player when they are issued this mission

#### `reminderText`

Text that will be read to the player when they call the issuing NPC back before completing the mission.

#### `completionText`

Text that will be read to the player when they successfully complete the mission.

#### `type`

Type of mission, see below for specific types and details.

#### `points`

Points issues to the player when they successfully complete the mission, or removed from the user when they fail the mission.

#### `followupMission`

ID of a mission to immidiately start after successful completion of this mission.

#### `priority`

Importance of this mission compared to other missions. If multiple missions are available, the higher priority will be issued first.

#### `onlyStartFrom`

Only start this mission when calling from the specified location ID.

#### `prerequisites`

List of mission IDs that must be completed before this mission can be started.

#### `dependents`

Not used.

#### `repeatable`

Can this mission be completed multiple times.

#### `notBefore`

Wall time that this mission cannot be started before.

#### `notAfter`

Wall time that this mission cannot be started after.

#### `cancelAfterTime`

Wall time that this mission will automatically be cancelled at.

#### `cancelAfterTries`

Failed completions that this mission will automatically be cancelled after.

#### `cancelText`

Text read to the player when the mission is cancelled.

### Mission Types

#### Location

Player to call back from this location ID to complete the mission.

##### `callBackFrom`

Location ID to call from.

#### Call Another

Player to call another NPC to complete the mission.

##### `callAnother`

ID of the NPC to call.

#### Code

Player to enter a pre-defined code to complete the mission.

#### `code`

Code the user should enter. Ensure quoted if the code contains leading zeros.

#### `incorrectText`

Text read to the user after entering an incorrect code.

#### Count

Player to enter any number to complete the mission.

#### Lua

Lua code to run to determine if the mission should be completed. This is capable of taking user input, responding with text, and storing state.

#### `lua`

Lua script to run.

See [Lua](Lua.md) for more details.

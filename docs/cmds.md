# Minecraft-related commands

Minescript has a lot of Minecraft-related commands already build into it, in order to make your life easier and
simplify their usage, as well as to add some functionality.


| Command | Functionality | Usage | Example |
| :---: | :---: | :---: | :---: |
|`$addobj`| Add a new objective to the scoreboard | `$addobj(name, type)` | `$addobj("shot", "minecraft.used:minecraft.bow")` |
|`$addtag`| Add a new tag to an entity | `$addtag(selector, tag)` | `$addtag("@e[type=minecraft:pig]", "animal")` |
|`$count`| Return the number of entities of a certain type | `$count(selector)` | `$count("@a")` |
|`$execute`| Execute instructions within an execute command | `$execute(options) { code }` | `$execute("as @e at @s") { $mc("say @s") }` |
|`$getdata`| Get nbt data from an entity | `$getdata(selector, path, scale)` | `$getdata("@e[type=minecraft:pig]", "Rotation[0]", 0.5)` |
|`$getscore`| Get the score of an entity | `$getscore(selector, objective)` | `$getscore("@p", "shot")` |
|`$hastag`| Check if an entity has a specific tag | `$hastag(selector, tag)` | `$hastag("@e[type=minecraft:pig]", "animal")` |
|`$isblock`| Check if a specific block corresponds to an id | `$isblock(selector, coords, block)` | `$isblock("@e[type=minecraft:sheep]", "~ ~-1 ~", "minecraft:grass")` |
|`$mc`| Execute a minecraft command | `$mc(command)` | `$mc("say Hi @a!")` |
|`$pos`| Return the x, y or z component of the position of an entity | `$pos(selector, index)` | `$pos("@p[name=Alex]", 0)` |
|`$print`| Print something | `$print(text|COLOR,...)` | `$print("string"|green, 1|aqua, $x|red)` |
|`$remtag`| Remove a tag from an entity | `$remtag(selector, tag)` | `$remtag("@e[type=minecraft:pig]", "animal")` |
|`$setscore`| Set the score of an entity | `$setscore(selector, score, value)` | `$setscore("@a", "animal", $var)` |
|`$tp`| Teleports an entity (relative to itself) | `$tp(selector, coords/selector)` | `$tp("@p", "~ ~10 ~")` |
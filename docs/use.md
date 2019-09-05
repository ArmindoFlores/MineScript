# Usage

The first step is creating a file for your project. The default file extension for MineScript files is `.ms`,
and all code for your datapack should be in that file. You should also create a file with the same name, but with
the extension `.info`, where you'll write the name of your datapack in the first line and its description on the second.

## Basics

One important thing you should remember about MineScript is that it has two types of instructions: those that run inside Minecraft itself (and always start
with `$`), and those that run while the datapack is being created. For example, the following instruction:

```
print("Hello world!")
```

will run before the datapack is built, but this one:

```
$print("Hello world!")
```

will only run once you load the datapack is loaded onto your Minecraft world.

## Syntax

MineScript syntax is pretty similar to most programming languages, except in its use of the `$` symbol. Let's see what it can do:

### Basic arithmetic

```
x = 2
y = 3 * x
z = 1 / (2 + y)
print(z)
```

These are all valid expressions and MineScript will output the result `0.125`.

As of this version, there are only 5 arithmetic operators:

| Operation |       Meaning       |
| --------- | :-----------------: |
| `+`		| Addition |
| `-`		| Subtraction |
| `*`		| Multiplication |
| `/`		| Division |
| `%`		| Modulo |
| `^`		| Exponentiation |

### If / Else statements

```
if (1 + 2 == 3) {
	print("1 + 2 = 3") # This will run
} else {
	print("Something's gone wrong here...") # This won't run
}
```

If statements will run the code inside the curly brackets if the expression inside the 
parentheses evaluates to anything other than `0` or `false`, so this will still work:

```
if (1 + 2) {
	print("1 + 2") # This will run
}
```

There are 6 different comparison operators:

| Operation |       Meaning       |
| --------- | :-----------------: |
| `<`		| strictly less than |
| `<=`		| less than or equal |
| `>`		| strictly greater than |
| `>=`		| greater than or equal |
| `==`		| equal |
| `!=`		| not equal |

These operators will throw an error when used to compare objects of incompatible types (for example, and array and an integer).
You can also use `&&` - the AND operator - and `||` - the OR operator - to add different conditions to one if statement.

 
### For loops

For loops are setup similarly to java, using the following syntax:

```
for (i=0; i<10; i++) {
	print(i)  # This will run 10 times and print the numbers from 0 to 9
}
```

`i=0` initializes the variable `i`, `i<10` means the code within the brackets will run until this condition is no longer true, and `i++` updates
the variable each in iteration, in this case incrementing its value by 1.

### While loops

While loops are also setup similarly to java, using the following syntax:

```
i = 0
while (i < 10) {
	i++
	print(i)  # This will run 10 times and print the numbers from 1 to 10
}
```

`i < 10` is the condition, and the loop will run while this is true.

### Functions

Functions can be used to reduce the ammount of code you need to write in repetitive tasks, or just to help you organize your code better.

```
function printsum() {
	result = 0
	for (i=0; i<len(arr); i++) {
		result += arr[i]
	}
	print(result)
}

arr = [2,3,4]
printsum()  # Output 9 (2 + 3 + 4)
```

This function will print out the sum of all elements of an array `arr`, by iterating through all of them. Functions can also
return a value, using the keyword `return`.

```
function sum(a) {
	result = 0
	for (i=0; i<len(a); i++) {
		result += a[i]
	}
	return(result)
}

arr = [2,3,4]
print(sum(arr))  # Output 9 (2 + 3 + 4)
```

### Include

The `include` keyword is a special keyword that lets you include all the code from another `.ms` file into your current project.
It should always come before anything else on your code. An example would be:

File `myotherproject.ms`
```
$function afunction() {
	$print("Loaded from another file")
}
```

File `myproject.ms`
```
include myotherproject

$function load() {
	$afunction()
}
```

## In-game operations

Let's now take a look at how this code would work if run inside the game.
All code that is to run in-game should be inside a function (which will later be converted into an actual Minecraft function file),
and the functions `tick` and `load` are reserved - `tick` will run every tick (about 20 times/second) while `load` will run only when the datapack is loaded.

### Basic arithmetic

```
$function load() {
	$x = 2
	$y = 3 * $x
	$z = 1 / (2 + $y)
	$print($z)
}
```

Just like before, these are all valid expressions and will run, but only once you load the datapack onto your world. Unlike before, the result will be `0`,
because Minecraft `scoreboard` objectives do not support floating-point numbers.

### If / Else statements

```
$function load() {
	$x = 3
	$if($x == 3) {
		$print("1 + 2 = 3")
	} $else {
		$print("Something's gone wrong here...")
	}
}
```

If and else statements function as explained before, with the only difference being you can use in-game variables inside the parentheses:

```
$function load() {
	$x = 2
	$if ($x > 1) {
		$print($x, " is greater then 1")
	}
}
```

### For loops

The syntax for these loops is exactly the same as explained previously:

```
$function load() {
	$for ($i=0; $i<10; $i++) {
		$print($i) 
	}
}
```

But there is an additional for loop called `forentity` that iterates through all entities of a certain type:

```
$function load() {
	$forentity ("@e[type=minecraft:zombie]"; zombie) {
		$tp(zombie, "~ ~10 ~") # Teleports all zombies 10 blocks up
	}
}
```

`"@e[type=minecraft:zombie]"` is the selector - the type of entity that we're going to iterating through - and `zombie` is a variable that's going
to store the selector to the specific entity being targeted in each iteration.


### While loops

The syntax for these loops is also the same as explained previously:

```
$function load() {
	$i = 10
    $while($i > 0) {
		$i--
        $print($i)
    }
}
```

This will print out the numbers from 9 to 0.

### Functions

Functions are turned into Minecraft function files, and can be used later in your code, or called from within minecraft using `/function yourpack:yourfunction`

```
$function reset() {
	$a = 0
	$b = 0
	$c = 0
	$print("Reset")
}

$function load() {
	$reset()
}
```

This code will run your `$reset` function when the datapack is loaded.

### Minecraft Commands

You can still run any Minecraft command normally by using `$mc("your command here")`.


## Building your datapack

After you've finished writing all your code, you can build your datapack using the command `minescript --file yourpack.ms`.
MineScript will create your datapack `.zip` folder inside `/dist/datapack.zip`. If you want to change the name of the datapack
or some if its attributes, use `minescript --help` to get a list of all possible flags you can use.
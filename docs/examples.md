# Examples

Here you can check out some examples that will hopefully help you understand the language and what you can and can't do with it.


### Fibonacci Numbers

```
$function load() {
	# Setup variables
	$running = 1  
	$timer = 0
	$ffib = 1
	$sfib = 1
	$temp = 0
}

$function tick() {
	$if ($running == 1) {
		$timer++  							# Increment `$timer` by one each tick
		$if(($timer % 20) == 0) {  			# Check if one second has passed
			$print($ffib | dark_purple)  	# Print the next number in the sequence
			$temp = $sfib 
			$sfib += $ffib
			$ffib = $temp
		}
	}
}

$function stop() $running = 0  # Disable the `tick` function
```

How it looks in-game:

![Fib1](https://github.com/ArmindoFlores/MineScript/blob/master/docs/fib1.png?raw=true "Fibonacci Sequence")

![Fib2](https://github.com/ArmindoFlores/MineScript/blob/master/docs/fib2.png?raw=true "Fibonacci Sequence")


### Display a player's x position on the sidebar

```
$function load() {
	$posx = 0
	$setdisplay($posx, sidebar)
}

$function tick() {
	$posx = $pos("@p", 0)
}
```

### Using functions with arguments

```
$function load() {
	$n1 = 3
	$n2 = 5
	$print($add($n1, $n2))
}

$function add($x, $y) {
	$return($x + $y)
}
```

This will print out the expected result `8` when the datapack is loaded.


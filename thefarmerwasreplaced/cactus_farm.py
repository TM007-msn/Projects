# The Farmer Was Replaced - cactus farm
# Uses: functions, lists, tuples, senses, plant, till, cactus
#       (measure() and swap() come with the cactus unlock).
#
# How cacti work:
#   - Every cactus has a size (0-9), which measure() reads.
#   - If the whole farm is sorted - each cactus no bigger than the ones to
#     its North and East - harvesting one fully grown cactus harvests every
#     connected one too, and you get n*n cactus for n harvested.
#     Unsorted, you only get the one you harvested.
#
# Plan:
#   1. Plant a cactus on every square.
#   2. Sort every row (smallest at the West end) using swap().
#   3. Sort every column (smallest at the South end).
#      Sorting rows and then columns leaves the rows still sorted,
#      so the whole grid ends up sorted both ways.
#   4. Wait until every cactus is fully grown, then harvest once.
#
# Warning: the first pass clears anything that isn't a cactus.


def move_steps(direction, steps):
	for i in range(steps):
		move(direction)


def goto(tx, ty):
	# Shortest route, using the fact that the farm wraps round at the edges
	size = get_world_size()

	dx = tx - get_pos_x()
	if dx < 0:
		dx += size
	if dx * 2 <= size:
		move_steps(East, dx)
	else:
		move_steps(West, size - dx)

	dy = ty - get_pos_y()
	if dy < 0:
		dy += size
	if dy * 2 <= size:
		move_steps(North, dy)
	else:
		move_steps(South, size - dy)


def all_squares():
	# Snake order (up one column, down the next) so the drone never backtracks
	size = get_world_size()
	squares = []
	for x in range(size):
		for i in range(size):
			if x % 2 == 0:
				y = i
			else:
				y = size - 1 - i
			squares.append((x, y))
	return squares


# Plants a cactus on every square.
# Returns False if we couldn't afford one.
def plant_all():
	for square in all_squares():
		goto(square[0], square[1])
		entity = get_entity_type()
		if entity != Entities.Cactus:
			if entity != None:
				harvest()
			if get_ground_type() == Grounds.Grassland:
				till()
			if not plant(Entities.Cactus):
				return False
	return True


# Cocktail-shaker sort along one row / column: sweep forward pushing the
# biggest to the end, then back pushing the smallest to the start.
# Each pass shrinks the unsorted range to where the last swap happened,
# so already-sorted ends aren't walked over again.
def sort_row(y):
	lo = 0
	hi = get_world_size() - 1
	while lo < hi:
		# Forward pass: push the biggest cactus East
		goto(lo, y)
		last = lo
		x = lo
		while x < hi:
			if measure() > measure(East):
				swap(East)
				last = x
			move(East)
			x += 1
		hi = last
		if lo >= hi:
			break

		# Backward pass: push the smallest cactus West
		goto(hi, y)
		last = hi
		x = hi
		while x > lo:
			if measure(West) > measure():
				swap(West)
				last = x
			move(West)
			x -= 1
		lo = last


def sort_column(x):
	lo = 0
	hi = get_world_size() - 1
	while lo < hi:
		# Forward pass: push the biggest cactus North
		goto(x, lo)
		last = lo
		y = lo
		while y < hi:
			if measure() > measure(North):
				swap(North)
				last = y
			move(North)
			y += 1
		hi = last
		if lo >= hi:
			break

		# Backward pass: push the smallest cactus South
		goto(x, hi)
		last = hi
		y = hi
		while y > lo:
			if measure(South) > measure():
				swap(South)
				last = y
			move(South)
			y -= 1
		lo = last


def wait_until_all_grown():
	for square in all_squares():
		goto(square[0], square[1])
		while not can_harvest():
			do_a_flip()


while True:
	if not plant_all():
		print("Can't afford cactus - farm what it costs, then come back")
		break

	size = get_world_size()
	for y in range(size):
		sort_row(y)
	for x in range(size):
		sort_column(x)

	wait_until_all_grown()
	# The grid is sorted, so this one harvest takes the whole farm
	harvest()

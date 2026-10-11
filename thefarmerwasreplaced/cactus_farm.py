# The Farmer Was Replaced - cactus farm
#
# Sorted cacti (each one no bigger than its North and East neighbours)
# chain-harvest: one harvest takes the whole farm and pays n*n for n cacti.
# Brown = grown but out of order, green = sorted.
#
# Each cycle: plant every square -> sort rows -> sort columns
#             -> wait until all grown -> harvest once.
# Progress shows in the Output window.


def move_steps(direction, steps):
	for i in range(steps):
		move(direction)


def goto(tx, ty):
	# Shortest route, using the farm wrapping round at the edges
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
				squares.append((x, i))
			else:
				squares.append((x, size - 1 - i))
	return squares


def plant_all():
	# Returns False if we can't afford a cactus
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


def goto_on_line(index, pos, is_row):
	# Row: index is y, pos is x.  Column: index is x, pos is y.
	if is_row:
		goto(pos, index)
	else:
		goto(index, pos)


def sort_line(index, is_row):
	# Cocktail-shaker sort of one row (small -> West) or column (small -> South).
	# Each pass shrinks the unsorted range to where the last swap happened.
	if is_row:
		forward = East
		back = West
	else:
		forward = North
		back = South

	lo = 0
	hi = get_world_size() - 1
	while lo < hi:
		# Forward pass: push the biggest to the far end
		goto_on_line(index, lo, is_row)
		last = lo
		pos = lo
		while pos < hi:
			if measure() > measure(forward):
				swap(forward)
				last = pos
			move(forward)
			pos += 1
		hi = last
		if lo >= hi:
			break

		# Backward pass: push the smallest to the near end
		goto_on_line(index, hi, is_row)
		last = hi
		pos = hi
		while pos > lo:
			if measure(back) > measure():
				swap(back)
				last = pos
			move(back)
			pos -= 1
		lo = last


def wait_until_all_grown():
	for square in all_squares():
		goto(square[0], square[1])
		while not can_harvest():
			do_a_flip()


while True:
	quick_print("Planting")
	if not plant_all():
		print("Can't afford cactus - farm what it costs, then come back")
		break

	size = get_world_size()
	for y in range(size):
		quick_print("Sorting row " + str(y + 1) + " of " + str(size))
		sort_line(y, True)
	for x in range(size):
		quick_print("Sorting column " + str(x + 1) + " of " + str(size))
		sort_line(x, False)

	quick_print("Waiting for every cactus to finish growing")
	wait_until_all_grown()

	before = num_items(Items.Cactus)
	harvest()
	quick_print("Harvested " + str(num_items(Items.Cactus) - before) + " cactus")

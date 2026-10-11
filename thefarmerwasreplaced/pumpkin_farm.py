# The Farmer Was Replaced - pumpkin farm
# Uses: functions, lists, tuples, senses, plant, till, watering, pumpkins.
#
# How pumpkins work:
#   - Fully grown pumpkins next to each other merge into one giant pumpkin.
#     A bigger square gives far more than the same number of small ones,
#     so the aim is to fill the WHOLE farm and harvest it as one pumpkin.
#   - Some pumpkins die when they finish growing (Dead_Pumpkin). Those
#     squares must be replanted before the giant pumpkin can form.
#   - Planting a pumpkin costs carrots.
#
# Plan:
#   1. Keep a list of squares that aren't a fully grown pumpkin yet.
#   2. Visit only those squares: replant dead/empty ones, water growing ones.
#      A square drops off the list once its pumpkin is fully grown.
#   3. When the list is empty, the farm is one giant pumpkin: harvest it.
#
# Warning: the first pass clears anything that isn't a pumpkin.

# Only water a pumpkin when its water level is below this (each use adds 0.25)
WATER_BELOW = 0.5


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


def water_if_dry():
	if get_water() < WATER_BELOW and num_items(Items.Water) > 0:
		use_item(Items.Water)


# Visits each square in `pending` once.
# Returns the squares that still aren't fully grown pumpkins,
# or None if we ran out of carrots to plant with.
def tend_pass(pending):
	still_pending = []
	for square in pending:
		goto(square[0], square[1])
		entity = get_entity_type()

		if entity == Entities.Pumpkin:
			if can_harvest():
				# Fully grown: this square is done
				continue
			water_if_dry()
		else:
			# Empty, dead pumpkin, or some other crop: clear and replant
			if entity != None:
				harvest()
			if get_ground_type() == Grounds.Grassland:
				till()
			if not plant(Entities.Pumpkin):
				return None
			water_if_dry()

		still_pending.append(square)
	return still_pending


running = True
while running:
	pending = all_squares()
	while len(pending) > 0:
		pending = tend_pass(pending)
		if pending == None:
			print("Out of carrots - run farm_v2 for a while, then come back")
			running = False
			break

	if running:
		# Every square is grown, so the whole farm is one giant pumpkin
		harvest()

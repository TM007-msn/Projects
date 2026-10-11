# The Farmer Was Replaced - balanced farm v2
# Uses: functions, lists, tuples, senses, plant, till, watering,
#       trees, bushes, carrots, grass.
#
# Layout:
#   Checkerboard squares ((x + y) even) are always Trees, so no two trees
#   touch and none get slowed down.
#   Every other square is replanted by working through PLAN in turn, so
#   grass (wheat), bushes and carrots all keep growing, and the "lowest"
#   slot gives an extra share to whatever you're shortest on. The choice is
#   made only when a square is replanted, so nothing half-grown is destroyed.
#
# No clear() at the start: the script works from wherever the drone is,
# so restarting it doesn't wipe your growing crops.

# Which crop makes which item (used by the "lowest" slot)
CROPS = [
	(Items.Hay, Entities.Grass),
	(Items.Wood, Entities.Bush),
	(Items.Carrot, Entities.Carrot),
]

# Replant order for non-tree squares. None = "whatever you have least of".
# Add an entry to get more of something, e.g. a second Entities.Carrot.
PLAN = [None, Entities.Grass, Entities.Bush, Entities.Carrot]

# Only water a tree when its water level is below this (each use adds 0.25)
WATER_BELOW = 0.5


def lowest_crop():
	# Crop for the item we have least of
	best = None
	best_count = 0
	for entry in CROPS:
		count = num_items(entry[0])
		if best == None or count < best_count:
			best = entry[1]
			best_count = count
	return best


def pick_crop(turn):
	crop = PLAN[turn % len(PLAN)]
	if crop == None:
		crop = lowest_crop()
	return crop


def prepare_ground(crop):
	# Grass needs grassland. Trees, bushes and carrots go on soil,
	# which also stops wild grass growing back over them.
	ground = get_ground_type()
	if crop == Entities.Grass:
		if ground == Grounds.Soil:
			till()
	elif ground == Grounds.Grassland:
		till()


def plant_crop(crop):
	prepare_ground(crop)
	if get_entity_type() == None:
		if not plant(crop):
			# Couldn't plant (e.g. can't afford a carrot): fall back to grass
			prepare_ground(Entities.Grass)
			if get_entity_type() == None:
				plant(Entities.Grass)


# Returns turn, plus 1 if a non-tree square was replanted
def tend_tile(turn):
	x = get_pos_x()
	y = get_pos_y()
	tree_square = (x + y) % 2 == 0
	entity = get_entity_type()

	if tree_square:
		if entity == Entities.Tree:
			if can_harvest():
				harvest()
				plant_crop(Entities.Tree)
		else:
			# Wild grass or an old crop on a tree square: clear it, plant a tree
			if entity != None:
				harvest()
			plant_crop(Entities.Tree)

		# Wood is the slow one, so water goes to trees
		if get_water() < WATER_BELOW and num_items(Items.Water) > 0:
			use_item(Items.Water)
	else:
		replant = False
		if entity == Entities.Tree:
			# A tree here would slow its neighbours down
			harvest()
			replant = True
		elif entity == None:
			replant = True
		elif can_harvest():
			harvest()
			replant = True

		if replant:
			plant_crop(pick_crop(turn))
			turn += 1

	return turn


turn = 0
while True:
	size = get_world_size()
	for col in range(size):
		for row in range(size):
			turn = tend_tile(turn)
			move(North)
		move(East)

# The Farmer Was Replaced - balanced farm v2
# Uses: functions, lists, tuples, senses, plant, till, watering,
#       trees, bushes, carrots, grass.
#
# Layout:
#   Checkerboard squares ((x + y) even) are always Trees, so no two trees
#   touch and none get slowed down.
#   Every other square grows whichever of Grass / Bush / Carrot makes the
#   item you're shortest on (hay / wood / carrots). The choice is made each
#   time that square is replanted, so nothing half-grown is ever destroyed.
#
# No clear() at the start: the script works from wherever the drone is,
# so restarting it doesn't wipe your growing crops.

# Each entry: (item, crop that makes it, weight)
# Weight 2 = "keep twice as much of this as the others".
# Raise the weight of whatever your next upgrade costs.
CROPS = [
	(Items.Hay, Entities.Grass, 1),
	(Items.Wood, Entities.Bush, 1),
	(Items.Carrot, Entities.Carrot, 1),
]

# Only water a tree when its water level is below this (each use adds 0.25)
WATER_BELOW = 0.5


def pick_crop():
	# Crop for the item we have least of, relative to its weight
	best = None
	best_score = 0
	for entry in CROPS:
		score = num_items(entry[0]) / entry[2]
		if best == None or score < best_score:
			best = entry[1]
			best_score = score
	return best


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


def tend_tile():
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
		if entity == Entities.Tree:
			# A tree here would slow its neighbours down
			harvest()
			plant_crop(pick_crop())
		elif entity == None:
			plant_crop(pick_crop())
		elif can_harvest():
			harvest()
			plant_crop(pick_crop())


while True:
	size = get_world_size()
	for col in range(size):
		for row in range(size):
			tend_tile()
			move(North)
		move(East)

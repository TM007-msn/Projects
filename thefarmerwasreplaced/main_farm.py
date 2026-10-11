# The Farmer Was Replaced - mixed farm
# Only uses what's unlocked so far: loops, variables, operators, senses,
# plant, till, watering, trees, carrots, grass, expand.
#
# Layout (checkerboard by position):
#   (x + y) even -> Tree   (no tree touches another, so none are slowed down)
#   (x + y) odd  -> Carrot or Grass, whichever you currently have fewer of
#                   (carrots also cost hay + wood, so this self-balances)
#
# Trees and carrots get watered; grass grows fast enough not to bother.

clear()

while True:
	size = get_world_size()
	for col in range(size):
		for row in range(size):
			x = get_pos_x()
			y = get_pos_y()
			tree_tile = (x + y) % 2 == 0

			# 1. Harvest anything that's ripe
			if can_harvest():
				harvest()

			# 2. Replant if the tile is empty
			if get_entity_type() == None:
				if tree_tile:
					plant(Entities.Tree)
				elif num_items(Items.Carrot) < num_items(Items.Hay):
					if get_ground_type() == Grounds.Grassland:
						till()
					if not plant(Entities.Carrot):
						# Couldn't afford it: turn back to grassland and grow grass
						till()
						plant(Entities.Grass)
				else:
					if get_ground_type() == Grounds.Soil:
						till()
					plant(Entities.Grass)

			# 3. Water slow growers (each use adds 0.25 water)
			entity = get_entity_type()
			if entity == Entities.Tree or entity == Entities.Carrot:
				if get_water() < 0.75 and num_items(Items.Water) > 0:
					use_item(Items.Water)

			move(North)
		move(East)

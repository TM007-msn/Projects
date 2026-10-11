# The Farmer Was Replaced - mixed farm
# Only uses what's unlocked so far: loops, variables, operators, senses,
# plant, till, watering, trees, carrots, grass, expand.
#
# Fixed layout (by position):
#   (x + y) even          -> Tree   (no tree touches another, so none are slowed)
#   (x + y) odd, x even   -> Carrot
#   (x + y) odd, x odd    -> Grass  (hay)
#
# Trees and carrots live on soil, so wild grass can't grow back over them.
# Grass stays on grassland. Trees and carrots get watered.

clear()

while True:
	size = get_world_size()
	for col in range(size):
		for row in range(size):
			x = get_pos_x()
			y = get_pos_y()

			# Decide what belongs on this tile
			if (x + y) % 2 == 0:
				want = Entities.Tree
			elif x % 2 == 0:
				want = Entities.Carrot
			else:
				want = Entities.Grass

			entity = get_entity_type()

			if entity == want:
				# Right crop: harvest only when ripe
				if can_harvest():
					harvest()
			elif entity != None:
				# Wrong crop (usually wild grass): clear it out
				harvest()

			# Fix the ground: soil for trees/carrots, grassland for grass
			if want == Entities.Grass:
				if get_ground_type() == Grounds.Soil:
					till()
			elif get_ground_type() == Grounds.Grassland:
				till()

			# Replant if the tile is empty
			if get_entity_type() == None:
				plant(want)

			# Water slow growers (each use adds 0.25 water)
			if want != Entities.Grass:
				if get_water() < 0.75 and num_items(Items.Water) > 0:
					use_item(Items.Water)

			move(North)
		move(East)

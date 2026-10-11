# The Farmer Was Replaced - wheat (grass/hay) only farm
#
# Grass grows on its own on grassland, so all the drone has to do is
# sweep the farm and harvest every square that's ready.
# On the first sweep it turns any soil back into grassland and clears
# any other crop (ripe ones still pay out; unripe ones are lost).
#
# No watering: grass grows faster than the drone can get round the farm,
# so water would be wasted. Save it for trees or pumpkins.


def tend():
	entity = get_entity_type()

	if get_ground_type() == Grounds.Soil:
		# Leftover from another farm: clear it and turn back to grassland
		if entity != None:
			harvest()
		till()
	elif entity != None and entity != Entities.Grass:
		# Some other crop on grassland: clear it
		harvest()

	if can_harvest():
		harvest()

	if get_entity_type() == None:
		plant(Entities.Grass)


while True:
	size = get_world_size()
	for col in range(size):
		for row in range(size):
			tend()
			move(North)
		move(East)

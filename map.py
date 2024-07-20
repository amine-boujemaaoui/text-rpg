import random

from tile import Tile, Biome
from enum import Enum

class Direction(Enum):
    NORTH = 'north'
    SOUTH = 'south'
    EAST  = 'east'
    WEST = 'west'

class Map:
    def __init__(self, g, width = 40, height = 20):
        self.g = g
        self.width = width
        self.height = height
        self.data = self.generate_map()
        self.generate_patch(Biome.GRASS,    2,  5,  7)
        self.generate_patch(Biome.SAND,     3,  3,  6)
        self.generate_patch(Biome.WATER,    2,  4,  7)
        self.generate_patch(Biome.MOUNTAIN, 2,  4,  7)
        self.generate_patch(Biome.FOREST,   5,  5, 10)
        self.generate_shop(0.5)

    def generate_map(self):
        return [[Biome.GRASS for _ in range(self.width)] for _ in range(self.height)]
    
    def generate_patch(self, tile: Tile, num_patches: int, min_length: int, max_length: int, irregular: bool = True) -> None:
        for _ in range(num_patches):
            # Ensure patch dimensions are within the data boundaries
            width = random.randint(min_length, min(max_length, self.width - 2))
            height = random.randint(min_length, min(max_length, self.height - 2))
            
            # Randomly select the starting point within valid range
            x = random.randint(1, self.width - width - 1)
            y = random.randint(1, self.height - height - 1)
            
            for i in range(height):
                if irregular:
                    width = random.randint(int(0.7 * max_length), max_length)
                    width = min(width, self.width - 2)
                    init_x = x + random.randint(-2, 2)
                    init_x = max(1, min(init_x, self.width - width - 1))
                else:
                    init_x = x

                for j in range(width):
                    if 0 <= (y + i) < self.height and 0 <= (init_x + j) < self.width:
                        self.data[y + i][init_x + j] = tile
                    else:
                        break  # Exit if out of bounds
        
    def generate_shop(self, probability: float) -> None:
        if random.random() < probability:
            shop_x = random.randint(1, self.width - 2)
            shop_y = random.randint(1, self.height - 2)
            self.data[shop_y][shop_x] = Biome.SHOP

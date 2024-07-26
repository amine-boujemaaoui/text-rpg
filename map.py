import random
from tile import Tile, Biome
from enum import Enum

class Direction(Enum):
    NORTH = 'north'
    SOUTH = 'south'
    EAST  = 'east'
    WEST  = 'west'

class Map:
    def __init__(self, g, width=61, height=32, grid_size=11):
        self.g = g
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.maps = {}
        self.map_visited = [[0 for _ in range(grid_size)] for _ in range(grid_size)]
        self.current_map = (0, 0)
        self.data, self.data_explored = self.generate_map(self.current_map)
        
        self.generate_patches_and_shop(self.current_map)
        self.update_map_visited(self.current_map, 1)

    def generate_map(self, map_coords):
        if map_coords not in self.maps:
            self.maps[map_coords] = (
                [[Biome.GRASS for _ in range(self.width)] for _ in range(self.height)],
                [[1] * self.width for _ in range(self.height)]
            )
        return self.maps[map_coords]

    def generate_patches_and_shop(self, map_coords):
        if self.is_map_visited(map_coords):
            return
        self.generate_patch(Biome.SAND,     random.randint(2, 6),  4,  9)
        self.generate_patch(Biome.WATER,    random.randint(3, 7),  4, 11)
        self.generate_patch(Biome.MOUNTAIN, random.randint(0, 9),  4,  8)
        self.generate_patch(Biome.FOREST,   random.randint(5, 8),  5, 11)
        self.generate_shop(1)
        self.update_map_visited(map_coords, 1)

    def generate_patch(self, tile: Tile, num_patches: int, min_length: int, max_length: int, irregular: bool = True) -> None:
        for _ in range(num_patches):
            width  = random.randint(min_length, min(max_length, self.width))
            height = random.randint(min_length, min(max_length, self.height))
            
            x = random.randint(0, self.width  - width)
            y = random.randint(0, self.height - height)
            
            for i in range(height):
                if irregular:
                    width  = random.randint(int(0.7 * max_length), max_length)
                    width  = min(width, self.width - 2)
                    init_x = x + random.randint(-2, 2)
                    init_x = max(0, min(init_x, self.width - width))
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

    def change_map(self, direction):
        x, y = self.current_map
        if direction == Direction.NORTH:
            y -= 1
        elif direction == Direction.SOUTH:
            y += 1
        elif direction == Direction.EAST:
            x += 1
        elif direction == Direction.WEST:
            x -= 1
        
        half_size = self.grid_size // 2
        if -half_size <= x <= half_size and -half_size <= y <= half_size:
            self.current_map = (x, y)
            self.data, self.data_explored = self.generate_map(self.current_map)
            self.generate_patches_and_shop(self.current_map)
            self.update_map_visited(self.current_map, 1)

    def is_map_visited(self, map_coords):
        x, y = map_coords
        half_size = self.grid_size // 2
        return self.map_visited[half_size + y][half_size + x] == 1

    def update_map_visited(self, map_coords, value):
        x, y = map_coords
        half_size = self.grid_size // 2
        self.map_visited[half_size + y][half_size + x] = value
        
        
from enum import Enum
from utils import Colors as C

class Tile:
    def __init__(self, biome='g'):
        self.biome_key = biome
        self.color     = bioms[biome]['color']
        self.name      = bioms[biome]['name']
        self.symbol    = bioms[biome]['symbol']
        self.enemy     = bioms[biome]['enemy']
        self.solid     = bioms[biome]['solid']
        self.rate      = bioms[biome]['rate']
        
bioms = {
    'g': {
        'name'  : 'grass',
        'color' : C.DARK_GREEN,
        'emoji' : '🌱',
        'enemy' : False,
        'rate'  : 0,
        'symbol': ' ',
        'solid' : False,
    },
    'w': {
        'name'  : 'water',
        'color' : C.BLUE,
        'emoji' : '🌊',
        'enemy' : False,
        'rate'  : 0,
        'symbol': '~',
        'solid' : True,
    },
    's': {
        'name'  : 'sand',
        'color' : C.YELLOW,
        'emoji' : '🏖️',
        'enemy' : True,
        'rate'  : 4,
        'symbol': 's',
        'solid' : False,
    },
    'm': {
        'name'  : 'mountain',
        'color' : C.GRAY,
        'emoji' : '⛰️',
        'enemy' : True,
        'rate'  : 30,
        'symbol': '^',
        'solid' : False,
    },
    'f': {
        'name'  : 'forest',
        'color' : C.GREEN,
        'emoji' : '🌲',
        'enemy' : True,
        'rate'  : 3,
        'symbol': '*',
        'solid' : False,
    },
    'shop': {
        'name'  : 'shop',
        'color' : C.MAGENTA,
        'emoji' : '🏪',
        'enemy' : False,
        'rate'  : 0,
        'symbol': '$',
        'solid' : False,
    },
    'castle': {
        'name'  : 'castle',
        'color' : C.YELLOW,
        'emoji' : '🏰',
        'enemy' : False,
        'rate'  : 0,
        'symbol': 'C',
        'solid' : False,
    },
    'player': {
        'name'  : 'player',
        'color' : C.RED,
        'emoji' : '🧑',
        'enemy' : False,
        'rate'  : 0,
        'symbol': 'P',
        'solid' : False,
    },
}

ascii_art = {
    'GRASS': [
        "    ___     ",
        "   /   \\    ",
        "  |  _  |   ",
        "  |_| |_|   "
    ],
    'WATER': [
        "   ~ ~ ~   ",
        "  ~ ~ ~ ~  ",
        "   ~ ~ ~   ",
        "  ~ ~ ~ ~  "
    ],
    'SAND': [
        "   .....   ",
        "  : : : :  ",
        "   .....   ",
        "  : : : :  "
    ],
    'MOUNTAIN': [
        "    /\\    ",
        "   /  \\   ",
        "  / /\\ \\  ",
        "  /____\\  "
    ],
    'FOREST': [
        "    |||    ",
        "   |||||   ",
        "  |||||||  ",
        "    |||    "
    ],
    'SHOP': [
        "   _____   ",
        "  |[---]|  ",
        "  |  |  |  ",
        "  |__|__|  "
    ]
}

class Biome(Enum):
    GRASS     = Tile('g')
    WATER     = Tile('w')
    SAND      = Tile('s')
    MOUNTAIN  = Tile('m')
    FOREST    = Tile('f')
    SHOP      = Tile('shop')

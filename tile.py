from enum import Enum
from utils import Colors

class Tile:
    def __init__(self, biome='g'):
        self.biome_key = biome
        self.color     = bioms[biome]['color']
        self.name      = bioms[biome]['name']
        self.symbol    = bioms[biome]['symbol']
        
bioms = {
    'g': {
        'name': 'grass',
        'color': Colors.WHITE,
        'emoji': '🌱',
        'enemy': False,
        'symbol': '.',
        'solid': False,
    },
    'w': {
        'name': 'water',
        'color': Colors.BLUE,
        'emoji': '🌊',
        'enemy': False,
        'symbol': '~',
        'solid': True,
    },
    's': {
        'name': 'sand',
        'color': Colors.YELLOW,
        'emoji': '🏖️',
        'enemy': False,
        'symbol': 's',
        'solid': False,
    },
    'm': {
        'name': 'mountain',
        'color': Colors.WHITE,
        'emoji': '⛰️',
        'enemy': True,
        'symbol': '^',
        'solid': False,
    },
    'f': {
        'name': 'forest',
        'color': Colors.GREEN,
        'emoji': '🌲',
        'enemy': True,
        'symbol': '*',
        'solid': False,
    },
    'shop': {
        'name': 'shop',
        'color': Colors.MAGENTA,
        'emoji': '🏪',
        'enemy': False,
        'symbol': '$',
        'solid': False,
    },
    'castle': {
        'name': 'castle',
        'color': Colors.YELLOW,
        'emoji': '🏰',
        'enemy': False,
        'symbol': 'C',
        'solid': False,
    },
    'player': {
        'name': 'player',
        'color': Colors.RED,
        'emoji': '🧑',
        'enemy': False,
        'symbol': 'P',
        'solid': False,
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
    ],
    'CASTLE': [
        "  |¯¯|¯¯|  ",
        "  |_   _|  ",
        "  |  _  |  ",
        "  |_| |_|  "
    ]
}

class Biome(Enum):
    GRASS     = Tile('g')
    WATER     = Tile('w')
    SAND      = Tile('s')
    MOUNTAIN  = Tile('m')
    FOREST    = Tile('f')
    SHOP      = Tile('shop')
    CASTLE    = Tile('castle')

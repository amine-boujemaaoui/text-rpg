from objects import Weapons as W, Armors as A
from utils import add_notif, Colors as C
from tile import Biome as B

class Player:
    def __init__(self, g, name) -> None:
        self.g = g
        self.name = name
        self.standing = False
        self.position = {'x': 0, 'y': 0}
        self.stats = {
            'hp': 40,
            'max_hp': 50,
            'mana': 40,
            'max_mana': 50,
            'attack': 5,
            'defense': 2,
            'level': 4,
            'exp': 50,
            'gold': 1000,
        }
        # Equipement initial
        self.equipment = {
            'weapon': W.SHORT_SWORD,
            'armor':  A.LEATHER,
            'potions': {
                'healing': 6,
                'mana': 2,
            }
        }
        # Inventaire initial
        self.inventory = {
            'weapons': [W.SHORT_SWORD, W.LONG_SWORD],
            'armors':  [A.LEATHER],
        }

    def move(self, x, y) -> bool:
        if 0 <= self.position['x'] + x < self.g.map.width and 0 <= self.position['y'] + y < self.g.map.height:
            self.position['x'] += x
            self.position['y'] += y
            return True
        else:
            return False

    def use_potion(self, potion_name) -> None:
        if potion_name in self.equipment['potions'] and self.equipment['potions'][potion_name] > 0:
            self.equipment['potions'][potion_name] -= 1
            match potion_name:
                case 'healing':
                    self.stats['hp']   = min(self.stats['max_hp'], self.stats['hp'] + 20)
                    add_notif(self.g, "You drank a healing potion!")
                case 'mana':
                    self.stats['mana'] = min(self.stats['max_mana'], self.stats['mana'] + 20)
                    add_notif(self.g, "You drank a mana potion!")
        else:
            add_notif(self.g, f"You don't have any {potion_name} potion left!")
        
    def gain_exp(self, exp) -> None:
        self.stats['exp'] += exp
        while self.stats['exp'] >= self.g.exp_table.get(self.stats['level']):
            self.level_up()
            
    def level_up(self) -> None:
        self.stats['level']   += 1
        self.stats['exp']      = 0
        self.stats['max_hp']  += 10
        self.stats['hp']       = self.stats['max_hp']
        self.stats['attack']  += 2
        self.stats['defense'] += 2
        
    def attack(self, enemy) -> bool:
        damage = max(0, self.stats['attack'] - enemy.stats['defense'])
        if enemy.stats['hp'] - damage <= 0:
            enemy.stats['hp'] = enemy.stats['max_hp']
            add_notif(self.g, "")
            add_notif(self.g, "")
            
            add_notif(self.g, f"You gained {enemy.exp} exp and {enemy.money} gold!".center(40 + 20), C.YELLOW)
            add_notif(self.g, "")
            self.gain_exp(enemy.exp)
            self.stats['gold'] += enemy.money
            add_notif(self.g, f"You killed the {enemy.name}!".center(40 + 20), C.GREEN)
            add_notif(self.g, "")
            return True
        else:
            enemy.stats['hp'] -= damage
            add_notif(self.g, f"You attacked the {enemy.name} for {damage} damage!")
            return False
        
class Enemy:
    def __init__(self, game, key, name, stats, exp, money, weapon, armor, biome) -> None:
        self.g      = game
        self.key    = key
        self.name   = name
        self.stats  = stats
        self.exp    = exp
        self.money  = money
        self.weapon = weapon
        self.armor  = armor
        self.biome  = biome

    def attack(self, player) -> bool:
        damage = max(0, self.stats['attack'] - player.stats['defense'])
        if player.stats['hp'] - damage <= 0:
            player.stats['hp'] = 0
            player.standing = False
            add_notif(self.g, f"{self.name} killed you!")
            return True
        else:
            player.stats['hp'] -= damage
            add_notif(self.g, f"{self.name} attacked you for {damage} damage!")
            return False

# Dictionnaire des ennemis
ENEMIES = {
    'slime':   ('slime',    'Slime',      {'hp': 10, 'max_hp': 10, 'attack':  3, 'defense': 1}, 10,  2,   None,          None,      B.FOREST  ),
    'sqeleton':('sqeleton', 'Sqeleton',   {'hp': 15, 'max_hp': 15, 'attack':  4, 'defense': 1}, 15,  3, W.SHORT_SWORD,   None,      B.SAND    ),
    'goblin':  ('goblin',   'Goblin',     {'hp': 20, 'max_hp': 20, 'attack':  5, 'defense': 2}, 20,  4, W.BATTLE_AXE,  A.LEATHER,   B.FOREST  ),
    'hob_gob': ('hob_gob',  'Hob Goblin', {'hp': 25, 'max_hp': 25, 'attack':  6, 'defense': 3}, 25,  5, W.SHORT_BOW,   A.LEATHER,   B.FOREST  ),
    'orc':     ('orc',      'Orc',        {'hp': 30, 'max_hp': 30, 'attack':  8, 'defense': 4}, 30,  7, W.HAND_AXE,    A.PLATE,     B.FOREST  ),
    'troll':   ('troll',    'Troll',      {'hp': 40, 'max_hp': 40, 'attack': 10, 'defense': 6}, 40, 10, W.SHORT_SWORD, A.CHAINMAIL, B.SAND    ),
    'dragon':  ('dragon',   'Dragon',     {'hp': 50, 'max_hp': 50, 'attack': 12, 'defense': 8}, 50, 25,   None,          None,      B.MOUNTAIN),
}

ARTS = {
    'slime': [
        "╭───────────╮",
        "│    ___    │",
        "│   /   \\   │",
        "│  /     \\  │",
        "│  \\     /  │",
        "│   \\___/   │",
        "╰───────────╯",
    ],
    'sqeleton': [
        "╭───────────╮",
        "│   _____   │",
        "│  /     \\  │",
        "│ | () () | │",
        "│  \\  ^  /  │",
        "│   |||||   │",
        "╰───────────╯",
    ],
    'goblin': [
        "╭───────────╮",
        "│   _____   │",
        "│  /     \\  │",
        "│ | () () | │",
        "│  \\  ^  /  │",
        "│   |||||   │",
        "╰───────────╯",
    ],
    'hob_gob': [
        "╭───────────╮",
        "│   _____   │",
        "│  /     \\  │",
        "│ | () () | │",
        "│  \\  ^  /  │",
        "│   |||||   │",
        "╰───────────╯",
    ],
    'orc': [
        "╭───────────╮",
        "│    ___    │",
        "│   /   \\   │",
        "│  /     \\  │",
        "│  \\     /  │",
        "│   \\___/   │",
        "╰───────────╯",
    ],
    'troll': [
        "╭───────────╮",
        "│   _____   │",
        "│  /     \\  │",
        "│ | () () | │",
        "│  \\  ^  /  │",
        "│   |||||   │",
        "╰───────────╯",
    ],
    'dragon': [
        "╭───────────╮",
        "│ /\\ ___ /\\ │",
        "│(  o   o  )│",
        "│ \\   _   / │",
        "│  \\  ‾  /  │",
        "│   \\___/   │",
        "╰───────────╯",
    ],


    
    
}

def create_enemy(game, enemy_key):
    if enemy_key in ENEMIES:
        key, name, stats, exp, money, weapon, armor, biome = ENEMIES[enemy_key]
        return Enemy(game, key, name, stats, exp, money, weapon, armor, biome)
    else:
        raise ValueError(f"Unknown enemy key: {enemy_key}")
    


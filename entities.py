from objects import Weapons, Armors
from utils import add_notif
from tile import Biome

class Player:
    def __init__(self, g, name) -> None:
        self.g = g
        self.name = name
        self.standing = False
        self.position = {'x': 0, 'y': 0}
        self.stats = {
            'hp': 80,
            'max_hp': 100,
            'mana': 40,
            'max_mana': 50,
            'attack': 10,
            'defense': 10,
            'level': 1,
            'exp': 50,
            'gold': 0,
        }
        # Equipement initial
        self.equipment = {
            'weapon': Weapons.SHORT_SWORD,
            'armor': Armors.LEATHER,
            'potions': {
                'healing': 6,
                'mana': 2,
            }
        }
        # Inventaire initial
        self.inventory = [
            Weapons.HAND_AXE,
            Weapons.SHORT_BOW,
            Armors.CHAINMAIL,
        ]

    def move(self, x, y) -> bool:
        if 0 <= self.position['x'] + x < self.g.map.width and 0 <= self.position['y'] + y < self.g.map.height:
            self.position['x'] += x
            self.position['y'] += y
            return True
        else:
            return False   

    def equip_weapon(self, weapon: Weapons) -> bool:
        if weapon in Weapons:
            self.equipment['weapon'] = weapon
            return True
        else:
            return False

    def equip_armor(self, armor: Armors) -> bool:
        if armor in Armors:
            self.equipment['armor'] = armor
            return True
        else:
            return False

    def use_potion(self, potion_name) -> bool:
        if potion_name in self.equipment['potions'] and self.equipment['potions'][potion_name] > 0:
            self.equipment['potions'][potion_name] -= 1
            match potion_name:
                case 'healing':
                    self.stats['hp']   = min(self.stats['max_hp'], self.stats['hp'] + 20)
                case 'mana':
                    self.stats['mana'] = min(self.stats['max_mana'], self.stats['mana'] + 20)
            return True
        else:
            return False
        
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
        self.stats['speed']   += 2
        
class Enemy:
    def __init__(self, game, key, name, stats, exp, weapon, armor, biome) -> None:
        self.g      = game
        self.key    = key
        self.name   = name
        self.stats  = stats
        self.exp    = exp
        self.weapon = weapon
        self.armor  = armor
        self.biome  = biome

    def attack(self, player) -> None:
        damage = max(0, self.stats['attack'] - player.stats['defense'])
        if player.stats['hp'] - damage <= 0:
            player.stats['hp'] = 0
            player.standing = False
            add_notif(self.g, f"{self.name} killed you!")
        else:
            player.stats['hp'] -= damage
            add_notif(self.g, f"{self.name} attacked you for {damage} damage!")

# Dictionnaire des ennemis
ENEMIES = {
    'goblin': ('goblin', 'Goblin', {'hp': 20, 'attack':  5, 'defense': 2}, 20, Weapons.BATTLE_AXE,  Armors.LEATHER,   Biome.FOREST),
    'orc':    ('orc',    'Orc',    {'hp': 30, 'attack':  8, 'defense': 4}, 30, Weapons.HAND_AXE,    Armors.PLATE,     Biome.FOREST),
    'troll':  ('troll',  'Troll',  {'hp': 40, 'attack': 10, 'defense': 6}, 40, Weapons.SHORT_SWORD, Armors.CHAINMAIL, Biome.SAND),
    'dragon': ('dragon', 'Dragon', {'hp': 50, 'attack': 12, 'defense': 8}, 50,         None,               None,      Biome.MOUNTAIN),
}

ARTS = {
    'goblin': [
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
            "│    ___    │",
            "│   /   \\   │",
            "│  /     \\  │",
            "│  \\     /  │",
            "│   \\___/   │",
            "╰───────────╯",
        ],
    
    
}

def create_enemy(game, enemy_key):
    if enemy_key in ENEMIES:
        key, name, stats, exp, weapon, armor, biome = ENEMIES[enemy_key]
        return Enemy(game, key, name, stats, exp, weapon, armor, biome)
    else:
        raise ValueError(f"Unknown enemy key: {enemy_key}")
    


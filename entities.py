from objects import Weapons as W, Armors as A
from utils import add_notif, Colors as C
from tile import Biome as B
from map import Direction

class Player:
    def __init__(self, g, name) -> None:
        self.g = g
        self.name     = name
        self.standing = False
        self.position = {'x': 0, 'y': 0}
        self.stats = {
            'hp':           50,
            'max_hp':       50,
            'mana':         50,
            'max_mana':     50,
            'attack':       20,
            'base_attack':  20,
            'defense':      30,
            'base_defense': 30,
            'level':         1,
            'exp':           0,
            'gold':         10,
        }
        # Equipement initial
        self.equipment = {
            'weapon': None,
            'armor':  None,
            'potions': {
                'healing': 2,
                'mana':    2,
            }
        }
        # Inventaire initial
        self.inventory = {
            'weapons': [W.SHORT_SWORD, W.BATTLE_AXE],
            'armors':  [A.LEATHER],
        }

    def move(self, dx, dy) -> bool:
        new_x = self.position['x'] + dx
        new_y = self.position['y'] + dy

        if 0 <= new_x < self.g.map.width and 0 <= new_y < self.g.map.height:
            self.position['x'] = new_x
            self.position['y'] = new_y
            return True
        return False

    def move_direction(self, direction) -> bool:
        x, y = self.g.map.current_map
        half_size = self.g.map.grid_size // 2

        if direction == Direction.NORTH and self.position['y'] == 0:
            if y > -half_size:
                self.g.map.change_map(direction)
                self.position['y'] = self.g.map.height - 1
        elif direction == Direction.SOUTH and self.position['y'] == self.g.map.height - 1:
            if y < half_size:
                self.g.map.change_map(direction)
                self.position['y'] = 0
        elif direction == Direction.WEST and self.position['x'] == 0:
            if x > -half_size:
                self.g.map.change_map(direction)
                self.position['x'] = self.g.map.width - 1
        elif direction == Direction.EAST and self.position['x'] == self.g.map.width - 1:
            if x < half_size:
                self.g.map.change_map(direction)
                self.position['x'] = 0
        else:
            return False
        return True

    def use_potion(self, potion_name) -> None:
        if potion_name in self.equipment['potions'] and self.equipment['potions'][potion_name] > 0:
            self.equipment['potions'][potion_name] -= 1
            match potion_name:
                case 'healing':
                    self.stats['hp']   = min(self.stats['max_hp'], self.stats['hp'] + 20)
                    add_notif(self.g.play, "You drank a healing potion!")
                case 'mana':
                    self.stats['mana'] = min(self.stats['max_mana'], self.stats['mana'] + 20)
                    add_notif(self.g.play, "You drank a mana potion!")
        else:
            add_notif(self.g.play, f"You don't have any {potion_name} potion left!")
        
    def gain_exp(self, exp) -> None:
        self.stats['exp'] += exp
        while self.stats['exp'] >= self.g.exp_table.get(self.stats['level']):
            self.level_up()
            
    def level_up(self) -> None:
        self.stats['level']        += 1
        self.stats['exp']           = 0
        self.stats['max_hp']       += 10
        self.stats['hp']            = self.stats['max_hp']
        self.stats['base_attack']  += 2
        self.stats['base_defense'] += 2
    
    def level_down(self) -> None:
        self.stats['level']        -= 1
        self.stats['exp']           = 0
        self.stats['max_hp']       -= 10
        self.stats['hp']            = self.stats['max_hp']
        self.stats['base_attack']  -= 2
        self.stats['base_defense'] -= 2

        if self.stats['level'] < 1:
            self.stats['level'] = 1
        
        if self.stats['base_attack'] < 0:
            self.stats['exp'] = 0
        
        if self.stats['base_defense'] < 0:
            self.stats['exp'] = 0
            
        self.stats['attack']        = self.stats['base_attack'] + W[self.equipment['weapon']].value.attack
        self.stats['defense']       = self.stats['base_defense'] + A[self.equipment['armor']].value.defense
        
    def attack(self, enemy) -> bool:
        damage = max(0, self.stats['attack'] - enemy.stats['defense'])
        if enemy.stats['hp'] - damage <= 0:
            enemy.stats['hp'] = enemy.stats['max_hp']
            add_notif(self.g.play, "")
            add_notif(self.g.play, "")
            
            add_notif(self.g.play, f"You gained {enemy.exp} exp and {enemy.money} gold!".center(40 + 20), C.YELLOW)
            add_notif(self.g.play, "")
            self.gain_exp(enemy.exp)
            self.stats['gold'] += enemy.money
            add_notif(self.g.play, f"You killed the {enemy.name}!".center(40 + 20), C.GREEN)
            add_notif(self.g.play, "")
            return True
        else:
            enemy.stats['hp'] -= damage
            add_notif(self.g.play, f"You attacked the {enemy.name} for {damage} damage!")
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
        
        self.stats['attack']  += self.weapon.value.attack if self.weapon else 0
        self.stats['defense'] += self.armor.value.defense if self.armor  else 0

    def attack(self, player) -> bool:
        damage = max(0, self.stats['attack'] - player.stats['defense'])
        if player.stats['hp'] - damage <= 0:
            player.stats['hp'] = 0
            player.standing = False
            add_notif(self.g.play, f"{self.name} killed you!")
            return True
        else:
            player.stats['hp'] -= damage
            add_notif(self.g.play, f"{self.name} attacked you for {damage} damage!")
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
    


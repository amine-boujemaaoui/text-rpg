from objects import Weapons, Armors

class Player:
    def __init__(self, g, name) -> None:
        self.g = g
        self.name = name
        self.position = {'x': 0, 'y': 0}
        self.stats = {
            'hp': 80,
            'max_hp': 100,
            'mana': 40,
            'max_mana': 50,
            'attack': 10,
            'defense': 10,
            'speed': 10,
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
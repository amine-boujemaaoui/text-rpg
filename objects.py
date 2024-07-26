from enum import Enum

class Weapon:
    def __init__(self, category, name, rarity, attack) -> None:
        self.category = category
        self.name     = name
        self.rarity   = rarity
        self.attack   = attack
        
    def apply(self, entity, remove=False):
        value = -self.attack if remove else self.attack
        entity.stats['attack'] += value

class Armor:
    def __init__(self, name, rarity, defense) -> None:
        self.name    = name
        self.rarity  = rarity
        self.defense = defense
        
    def apply(self, entity, remove=False):
        value = -self.defense if remove else self.defense
        entity.stats['defense'] += value
        
class Ring:
    def __init__(self, name, rarity, effect, value) -> None:
        self.name   = name
        self.rarity = rarity
        self.effect = effect
        self.value  = value
        
    def apply(self, entity, remove=False):
        value = -self.value if remove else self.value
        match self.effect:
            case 'attack':
                entity.stats['base_attack']  += value
            case 'defense':
                entity.stats['base_defense'] += value
            case 'health':
                entity.stats['max_hp']       += value
            case 'critical':
                entity.stats['critical']     += value
    
        
class Rarity(Enum):
    COMMON    = 'common'
    UNCOMMON  = 'uncommon'
    RARE      = 'rare'
    EPIC      = 'epic'
    LEGENDARY = 'legendary'
        
class Weapons(Enum):
    SHORT_SWORD  = Weapon('sword', 'Short Sword',  Rarity.COMMON,    10)
    LONG_SWORD   = Weapon('sword', 'Long Sword',   Rarity.RARE,      15)
    HAND_AXE     = Weapon('axe',   'Hand Axe',     Rarity.COMMON,    12)
    BATTLE_AXE   = Weapon('axe',   'Battle Axe',   Rarity.EPIC,      18)
    SHORT_BOW    = Weapon('bow',   'Short Bow',    Rarity.COMMON,     8)
    LONG_BOW     = Weapon('bow',   'Long Bow',     Rarity.RARE,      14)
    WOODEN_STAFF = Weapon('staff', 'Wooden Staff', Rarity.COMMON,     6)
    MAGIC_STAFF  = Weapon('staff', 'Magic Staff',  Rarity.RARE,      22)
    KATANA       = Weapon('sword', 'Katana',       Rarity.LEGENDARY, 30)
    
class SHOP_WEAPONS(Enum):
    SHORT_SWORD  = (Weapons.SHORT_SWORD, 10)
    LONG_SWORD   = (Weapons.LONG_SWORD,  20)
    HAND_AXE     = (Weapons.HAND_AXE,    30)
    BATTLE_AXE   = (Weapons.BATTLE_AXE,  40)
    SHORT_BOW    = (Weapons.SHORT_BOW,   50)
    
class Armors(Enum):
    LEATHER    = Armor('leather',    Rarity.COMMON,    10)
    CHAINMAIL  = Armor('chainmail',  Rarity.RARE,      15)
    PLATE      = Armor('plate',      Rarity.EPIC,      20)
    ADAMANTITE = Armor('adamantite', Rarity.LEGENDARY, 30)
    
class SHOP_ARMORS(Enum):
    LEATHER   = (Armors.LEATHER,   10)
    CHAINMAIL = (Armors.CHAINMAIL, 15)
    PLATE     = (Armors.PLATE,     15)
    
class Rings(Enum):
    RING_OF_STRENGTH = Ring('Ring of Str', Rarity.EPIC,      'attack',    2)
    RING_OF_HEALTH   = Ring('Ring of Hp',  Rarity.RARE,      'health',    5)
    RING_OF_DEFENSE  = Ring('Ring of Def', Rarity.COMMON,    'defense',   2)
    RING_OF_CRIT     = Ring('Ring of Crt', Rarity.LEGENDARY, 'critical', 30)

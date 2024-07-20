from enum import Enum

class Weapon:
    def __init__(self, category, name, rarity, attack) -> None:
        self.category = category
        self.name = name
        self.rarity = rarity
        self.attack = attack

class Armor:
    def __init__(self, name, defense) -> None:
        self.name = name
        self.defense = defense
        
class Rarity(Enum):
    COMMON = 'common'
    RARE   = 'rare'
    EPIC   = 'epic'
        
class Weapons(Enum):
    SHORT_SWORD  = Weapon('sword', 'Short Sword',  Rarity.COMMON, 10)
    LONG_SWORD   = Weapon('sword', 'Long Sword',   Rarity.RARE,   15)
    HAND_AXE     = Weapon('axe',   'Hand Axe',     Rarity.COMMON, 12)
    BATTLE_AXE   = Weapon('axe',   'Battle Axe',   Rarity.EPIC,   18)
    SHORT_BOW    = Weapon('bow',   'Short Bow',    Rarity.COMMON,  8)
    LONG_BOW     = Weapon('bow',   'Long Bow',     Rarity.RARE,   14)
    WOODEN_STAFF = Weapon('staff', 'Wooden Staff', Rarity.COMMON,  6)
    MAGIC_STAFF  = Weapon('staff', 'Magic Staff',  Rarity.RARE,   22)
    
class Armors(Enum):
    LEATHER   = Armor('leather',   10)
    CHAINMAIL = Armor('chainmail', 15)
    PLATE     = Armor('plate',     20)

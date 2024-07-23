from enum import Enum

class Weapon:
    def __init__(self, category, name, rarity, attack) -> None:
        self.category = category
        self.name     = name
        self.rarity   = rarity
        self.attack   = attack
        
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
    
class SHOP_WEAPONS(Enum):
    SHORT_SWORD  = (Weapons.SHORT_SWORD, 10)
    LONG_SWORD   = (Weapons.LONG_SWORD,  20)
    HAND_AXE     = (Weapons.HAND_AXE,    30)
    BATTLE_AXE   = (Weapons.BATTLE_AXE,  40)
    SHORT_BOW    = (Weapons.SHORT_BOW,   50)
    
def main():
    shop_weapons_list = list(SHOP_WEAPONS)
    weapon, price = shop_weapons_list[2].value
    print(weapon.name, price)
    
if __name__ == "__main__":
    main()
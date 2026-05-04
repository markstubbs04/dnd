import requests
from openai import OpenAI
import json


payload = {}
headers = {
  'Accept': 'application/json'
}

def getWeaponsandArmor(character_sheet: dict):
    armor = list()
    weapons = list()

    # Iterate over each starting equipment, if it is armor or a weapon, then put it in the proper list and remove it from starting equipment [No DUPES]
    for key in character_sheet["Starting Equipment"]:
        equipment_info = getEquipmentInfo(key)
        if equipment_info != {}:
            match equipment_info["equipment_category"]:
                case "Armor":
                    armor.append(equipment_info)
                    del character_sheet["Starting Equipment"][key]
                case "Weapon":
                    weapons.append(equipment_info)
                    del character_sheet["Starting Equipment"][key]
    current_weapons = character_sheet["weapons"]
    for weapon in weapons:
        current_weapons.append({
            "name": weapon["name"],
            "range": weapon["category_range"],
            "weaponProperty": weapon["properties"],
            "weaponDamageType": weapon["damage_type"],
            "damageDie": weapon["damage_die"]
        })
    
    character_sheet["weapons"] = weapons
    character_sheet["Armor"] = armor



        
#Gets the general info for each equipment item, specifically the required attributes for armor pieves and weapons
def getEquipmentInfo(equipment: str):
    equipment_formatted = equipment.replace(" ","-").lower()
    url = f"https://www.dnd5eapi.co/api/2014/classes/{equipment_formatted}"

    response = requests.request("GET", url, headers=headers, data=payload)
    try:
        class_data = response.json()
    except requests.JSONDecodeError:
        return {}
    class_data = response.json()
    equipment_info = dict()
    equipment_info["name"] = equipment
    equipment_info["equipment_category"] = class_data["equipment_category"]["name"]
    if "damage" in class_data:
        equipment_info["damage_die"] = class_data["damage"]["damage_dice"]
        equipment_info["damage_type"] = class_data["damage"]["damage_type"]["name"]
        equipment_info["category_range"] = class_data["category_range"]
    if "properties" in class_data:
        equipment_info["properties"] = (prop["name"] for prop in class_data["properties"] )
    if "armor_category" in class_data:
        equipment_info["armor_category"] = class_data["armor_category"]
        equipment_info["armor_class"] = class_data["armor_class"]["base"]

    return equipment_info

    
#!/usr/bin/python3

"""Staff of Shape Shifting

Usage:
    SoSS.py list
    SoSS.py random <pc_stats> [--weights=WEIGHT_FILE>]
    SoSS.py specific <pc_stats> <race_name> [--weights=WEIGHT_FILE]
    SoSS.py (-h | --help)
    SoSS.py --version

Options:
    -h --help                   Print the usage information
    --version                   Show the version information
    --weights=WEIGHT_FILE       Specify a custom weights file.
"""

from docopt import docopt
import os
import random
import yaml


def main(argd):

    # print(argd)

    # custom files
    if not (argd['--weights'] == None):
        WEIGHTS_FILE = argd['--weights']
    else:
        WEIGHTS_FILE = "race-weights.yaml"

    weights_dict = parse_weights(WEIGHTS_FILE)

    # Commands 
    if (argd['list']):
        print_all_races(weights_dict)
        exit(0)
    elif(argd['random']):
        pc_stats = parse_pc_stats(argd['<pc_stats>'])
        chosen_race = get_random(weights_dict)
        race_stats = parse_race_stats(chosen_race)
        print_stat_block(pc_stats, race_stats)

    elif(argd['specific']):
        pc_stats = parse_pc_stats(argd['<pc_stats>'])
        race_name = argd['<race_name>']
        for race_details in weights_dict:
            if race_details['name'] == race_name:
                race_stats = parse_race_stats(race_details)
                print_stat_block(pc_stats, race_stats)
        print("Error: Race name not found")
        print(__doc__)

    else:
        print("\n")
        exit(0)


def get_random(weights_dict):
    race_list = []

    # print(weights_dict)
    for race_details in weights_dict:
        race_list.extend([race_details['name'] for i in range(race_details['w'])])
    
    index = random.randrange(0,len(race_list))

    # print(race_list[index])
    for race_details in weights_dict:
        if race_details['name'] == race_list[index]:
            return race_details 

# ======================[ Parse YAML ]============================

def parse_weights(fname):
    weights = []
    with open(os.getcwd()+"/"+fname, "r") as stream:
        try: 
            data = yaml.load(stream)["weights"]
        except yaml.YAMLError as exc:
             print(exc)
             exit(1)

    for i, (rtype, contents) in enumerate(data.items()):
        if rtype == "books":
            for i, book_contents in enumerate(contents):
                for race_details in book_contents['races']:
                    race_details.update(book_contents['book-meta'])
                    weights.append(race_details)
        elif rtype == "race":
            weights.append(contents)

    return weights


def parse_race_stats(race):
    # print(race)
    data=[]
    with open(race['file'], 'r') as stream:
        try: 
            data.extend([doc['race'] for doc in yaml.load_all(stream)])
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

    # for entry in data:
    #     print(entry)

    for race_stats in data:
        if race_stats['name'] == race['name']:
            return race_stats


def parse_pc_stats(fname):
    with open(os.getcwd()+"/"+fname, "r") as stream:
        try: 
            return yaml.load(stream)['character']
        except yaml.YAMLError as exc:
            print(exc)
            exit(1)

# ========================[ Output ]==============================

def print_all_races(weights_dict):
    print("Number- Weight   NAME\t\t  filename")
    for i, race_d in enumerate(weights_dict):
        print(" [{0}]  -  {02:2}\t {1}\t\t{3}".format(i, race_d['name'], race_d['w'], race_d['file']))
    return

def print_stat_block(pc_stats, race_stats):
    pc_stats['stats'] = {}
    pc_stats['stats-b'] = {}
    all_stats = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]

    print("RACE: {0}".format(race_stats['name']))
    print("Type: {0}".format(race_stats['type']))

    print("\n======[ STATS ]======")
    for stat, pc_stat_value in pc_stats['stats-base'].items():
        modified = ""
        if stat in race_stats['stats-bonus']:
            pc_stats['stats'][stat] = pc_stat_value + race_stats['stats-bonus'][stat]
            modified = "(R+{0})".format(race_stats['stats-bonus'][stat])
        else:
            pc_stats['stats'][stat] = pc_stat_value
        pc_stats['stats-b'][stat] = int((pc_stats['stats'][stat]-10)/2)
        print("{0}:{1}[{2:+}] -- {3:>2} {4}".format(stat, " "*(13-len(stat)), 
            pc_stats['stats-b'][stat.lower()], pc_stats['stats'][stat.lower()], modified))

    print("\n======[ SAVES ]======")
    for stat in all_stats:
        prof = " "
        save_stat = pc_stats['stats-b'][stat.lower()]
        if stat.lower() in pc_stats['saving-throw-profs']:
            prof = "X"
            save_stat += pc_stats['proficiency-bonus']
        print("[{3}] {0}:{1}[{2:+}]".format(stat, " "*(13-len(stat)), save_stat, prof))

    print("\n======[ SKILLS ]======")
    all_skills = {
            "acrobatics": "dexterity", "animal-handling": "wisdom", 
            "arcana": "intelligence", "athletics": "strength",
            "deception": "charisma",  "history": "intelligence",
            "insight": "wisdom", "intimidation": "charisma",
            "investigation": "intelligence", "medicine": "wisdom",
            "nature": "intelligence", "perception": "wisdom",
            "performance": "charisma", "persuasion": "charisma",
            "religion": "intelligence", "sleight-of-hand": "dexterity",
            "stealth": "dexterity", "survival": "wisdom" }

    for skill, stat in all_skills.items():
        prof = " "
        skill_bonus = pc_stats['stats-b'][stat]
        if (skill in pc_stats['skill-profs']) or (skill in race_stats['skill-profs']):
            skill_bonus += pc_stats['proficiency-bonus']
        if (skill in pc_stats['skill-profs']) and not (skill in race_stats['skill-profs']):
            prof = "X"
        elif (skill in race_stats['skill-profs']) and not (skill in pc_stats['skill-profs']):
            prof = "R"
        elif (skill in race_stats['skill-profs']) and (skill in pc_stats['skill-profs']):
            prof = "B"
        print("[{0}] [{1:>+3}] {2}{3}- ({4})".format(prof, skill_bonus, skill, 
            " "*(16-len(skill)), stat))

    passive_wisdom = 10 + pc_stats['stats-b']['wisdom']
    if 'wisdom' in pc_stats['saving-throw-profs']:
        passive_wisdom += pc_stats['proficiency-bonus']
    print("\nPassive Wisdom (Perception): {0}".format(passive_wisdom))

    print("\n====[ ABILITIES ]======")
    for ability in list(set(pc_stats['abilities']) | set(race_stats['abilities'])):
        print(" * {0}".format(ability))

    print("\n====[ LANGUAGES ]======")
    for language in list(set(pc_stats['languages']) | set(race_stats['languages'])):
        print(" * {0}".format(language))

    # print("\n======[ OTHER ]======")
    print("\n")


if __name__=="__main__":
    argd = docopt(__doc__, version='Staff of Shape Shifting 1.0.0')
    main(argd)


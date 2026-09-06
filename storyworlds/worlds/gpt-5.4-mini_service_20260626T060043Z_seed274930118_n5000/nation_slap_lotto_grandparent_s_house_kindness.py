#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nation_slap_lotto_grandparent_s_house_kindness.py
=================================================================================

A standalone story world for a small Animal Story-style domain set in a
grandparent's house, with kindness and teamwork as the turn and resolution.

Seed-tale sketch:
---
A little animal from an imaginary nation visits Grandparent's house with a
picture-lotto board. An object makes a harmless slap sound and disrupts the
game. Then the family investigates, uses kindness and teamwork, and finishes
the game together.

World premise:
- "nation" is the origin-word of the little traveler.
- "slap" is a nonviolent sound or an object-to-object motion.
- "lotto" is a no-money picture-matching game, never gambling.
- Kindness and Teamwork are the emotional tools that resolve the story.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- imports results eagerly, asp lazily
- exposes StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "grandparent's house"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tag: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    kind: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slap", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scattered"] = item.meters.get("scattered", 0.0) + 1
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            incident = world.facts["incident"]
            out.append(incident["conflict"].format(hero=actor.label))
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("messy", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"{carer.label} was concerned about the pieces, but looked for evidence before assigning blame.")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kind", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0.0) - 1)
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        incident = world.facts["incident"]
        out.append(incident["kindness"].format(hero=actor.label))
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    team = sum(1 for c in world.characters() if c.memes.get("teamwork", 0.0) >= THRESHOLD)
    if team < 2:
        return out
    sig = ("team", team)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for item in world.entities.values():
        if item.meters.get("messy", 0.0) >= THRESHOLD:
            item.meters["messy"] = 0.0
            item.meters["sorted"] = item.meters.get("sorted", 0.0) + 1
    incident = world.facts["incident"]
    out.append(incident["teamwork"].format(hero=world.facts["hero"].label))
    return out


CAUSAL_RULES = [
    Rule("spill", _r_spill),
    Rule("worry", _r_worry),
    Rule("kind", _r_kind),
    Rule("team", _r_team),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting(place="grandparent's house", indoors=True, affords={"lotto"})

ACTIVITIES = {
    "lotto": Activity(
        id="lotto",
        verb="play lotto",
        gerund="playing lotto",
        rush="reach for the lotto cards",
        mess="slap",
        soil="scattered all over",
        tag="lotto",
    )
}

PRIZES = {
    "lotto": Prize(
        label="lotto board",
        phrase="a bright lotto board with little animal pictures",
        type="lotto_board",
        location="table",
    )
}

AIDS = {
    "kindness": Aid(
        id="kindness",
        label="kindness",
        prep="speak kindly and help tidy up",
        tail="smiled and took turns",
        kind="kindness",
    ),
    "teamwork": Aid(
        id="teamwork",
        label="teamwork",
        prep="work together to sort the cards",
        tail="worked side by side",
        kind="teamwork",
    ),
}

NAMES = {
    "fox": ["Fia", "Finn", "Fawn"],
    "rabbit": ["Rumi", "Rae", "Ro"],
    "bear": ["Bibi", "Bram", "Bo"],
}

TYPES = ["fox", "rabbit", "bear"]
NATIONS = ["Sun Nation", "River Nation", "Hill Nation"]

TRAITS = ["curious", "gentle", "brave", "playful"]


INCIDENTS = [
    {
        "id": "window_gust",
        "premise": "Grandparent had set the picture tiles in careful rows beside an open window.",
        "conflict": "A gust snapped the curtain against the table with a cloth slap and sent the light tiles skating under the chairs.",
        "mistake": "At first, {hero} hurried after the nearest cards, nudging two farther away.",
        "clue": "A fluttering corner of the map showed that the wind, not any player, had moved them.",
        "dialogue": "\"Let us stop the breeze before we chase the pieces,\" Grandparent said.",
        "kindness": "{hero} checked that Grandparent was comfortable and held the curtain gently aside.",
        "teamwork": "Grandparent latched the window while {hero} gathered the tiles by animal family.",
        "cause": "an open window let a gust reach the lightweight cards",
        "lesson": "kindness can begin with noticing what another person needs",
        "ending": "The last sunbeam rested on a tidy row of owls while the curtain stayed peacefully still.",
    },
    {
        "id": "box_lid",
        "premise": "The lotto box had a new cardboard divider for birds, fish, and forest animals.",
        "conflict": "Its springy lid fell with a cardboard slap, tipping three groups of tiles into one bright heap.",
        "mistake": "{hero} tried to scoop the heap at once, but matching corners slipped between the paws.",
        "clue": "Three colored divider tabs were still poking from beneath the mixed cards.",
        "dialogue": "\"Those tabs can tell us where each family belongs,\" {hero} realized.",
        "kindness": "{hero} apologized for rushing and invited Grandparent to choose the easiest color first.",
        "teamwork": "They made three small piles, checked every picture together, and reset the divider.",
        "cause": "the box lid was not folded behind its cardboard catch",
        "lesson": "a patient invitation is kinder than taking over",
        "ending": "When the lid finally closed, three colored tabs stood straight like tiny flags.",
    },
    {
        "id": "table_leaf",
        "premise": "They chose the folding table so the whole lotto board would fit beside their cocoa mugs.",
        "conflict": "A loose table leaf lifted and settled with a wooden slap, making the round markers roll toward the edge.",
        "mistake": "{hero} reached across Grandparent too quickly and blocked the safest path to the rolling pieces.",
        "clue": "A brass support beneath the leaf was hanging sideways instead of locked flat.",
        "dialogue": "\"Hands back for a moment; I know this old table,\" Grandparent said calmly.",
        "kindness": "{hero} listened, cleared the mugs, and made room for Grandparent to show the safe latch.",
        "teamwork": "Grandparent secured the support while {hero} caught the markers in a shallow basket.",
        "cause": "the folding-table support had not clicked into its locked position",
        "lesson": "listening to experience is part of working kindly together",
        "ending": "Two cocoa rings and one perfectly level board glowed beneath the kitchen lamp.",
    },
    {
        "id": "sticky_note",
        "premise": "Grandparent had marked the game columns with removable notes so a new player could follow them.",
        "conflict": "One note peeled free and landed on the board with a papery slap, hiding the row everyone needed.",
        "mistake": "{hero} guessed where the hidden tiles belonged, and the guesses made the pattern more confusing.",
        "clue": "The note's faint pencil arrow lined up with a tiny moon printed beside the covered row.",
        "dialogue": "\"We can uncover the clue without blaming the note,\" {hero} said with a grin.",
        "kindness": "{hero} asked before lifting Grandparent's labels and read each small word aloud.",
        "teamwork": "One held the guide steady while the other restored the moon row in picture order.",
        "cause": "a removable guide note had curled over the moon-picture row",
        "lesson": "asking before moving another person's things shows care",
        "ending": "The little moon appeared again, silver and clear above the completed row.",
    },
    {
        "id": "dog_tail",
        "premise": "The board waited on a low table while Grandparent's sleepy dog dozed safely on a nearby rug.",
        "conflict": "The dog dreamed, and its tail gave the empty box a cheerful slap that bounced the counters onto the rug.",
        "mistake": "{hero} nearly called the dog naughty, then noticed it was still sound asleep.",
        "clue": "A fan of tail marks in the rug pointed from the dog to the overturned box.",
        "dialogue": "\"It was an accident, so let us solve it without scolding,\" Grandparent whispered.",
        "kindness": "{hero} moved slowly, left the resting dog undisturbed, and fetched a quiet tray.",
        "teamwork": "Grandparent lifted the box while {hero} counted every counter from the rug into the tray.",
        "cause": "a dreaming dog's wagging tail bumped an empty game box",
        "lesson": "kindness means checking what happened before deciding whom to blame",
        "ending": "The dog slept on as the final counter clicked softly into its round hollow.",
    },
    {
        "id": "book_bump",
        "premise": "They built a reading-and-lotto corner with the game below Grandparent's animal atlas.",
        "conflict": "The atlas slid from its cushion and met the table with a flat slap, covering half the board.",
        "mistake": "{hero} tugged one edge, but Grandparent's bookmark began to slip from its special page.",
        "clue": "The bookmark ribbon showed exactly which side of the heavy book should be lifted first.",
        "dialogue": "\"My place matters, and so does our game,\" Grandparent said. \"We can protect both.\"",
        "kindness": "{hero} stopped pulling, saved the bookmark, and asked Grandparent how to carry the atlas.",
        "teamwork": "They lifted it together onto a firm shelf, then rebuilt the covered picture row.",
        "cause": "a heavy atlas had been balanced on a cushion instead of the shelf",
        "lesson": "caring for someone's treasured place is a practical kind of kindness",
        "ending": "The atlas ribbon and the lotto's red fox tile both rested exactly where they belonged.",
    },
    {
        "id": "clock_chime",
        "premise": "Their quiet game began just before Grandparent's tall clock was due to chime.",
        "conflict": "At noon, the clock's little hatch opened with a wooden slap, startling {hero} into dropping the draw bag.",
        "mistake": "{hero} crawled toward the scattered tokens before noticing one had rolled near the clock case.",
        "clue": "The clock's painted noon mark explained both the sudden sound and where the last token had stopped.",
        "dialogue": "\"That sound surprised us; it did not mean danger,\" Grandparent said.",
        "kindness": "{hero} admitted feeling startled, and Grandparent waited without teasing.",
        "teamwork": "They used a flashlight from the floor and a long cardboard guide to roll the token safely into reach.",
        "cause": "the noon clock hatch opened beside an unsecured draw bag",
        "lesson": "kind words make it easier to admit surprise and think clearly",
        "ending": "The clock ticked gently above a full bag and two relieved smiles.",
    },
    {
        "id": "serving_tray",
        "premise": "Grandparent carried the lotto pieces on a serving tray so the table could be set in stages.",
        "conflict": "A cork coaster sprang upright and slapped the underside of the tray, hopping the picture tiles out of their stacks.",
        "mistake": "{hero} sorted by size alone, which put a small whale beside a large mouse.",
        "clue": "The pictures' blue, green, and gold borders matched three bowls on the tray.",
        "dialogue": "\"Size fooled us, but the borders will not,\" {hero} said.",
        "kindness": "{hero} praised Grandparent's bowl idea and returned the coaster instead of tossing it aside.",
        "teamwork": "They called border colors in turn and rebuilt the stacks without rushing.",
        "cause": "a bent cork coaster had been trapped beneath the serving tray",
        "lesson": "kind teamwork values another person's useful idea",
        "ending": "Blue, green, and gold stacks rose neatly beside the now-flat coaster.",
    },
    {
        "id": "door_draft",
        "premise": "A neighbor had just delivered apples when the family started the no-money picture lotto game.",
        "conflict": "The screen door closed with a screen-frame slap, and its draft flipped every face-down card face up.",
        "mistake": "{hero} covered the cards with both paws, accidentally seeing pictures Grandparent had not seen.",
        "clue": "A clean tea towel was folded nearby and large enough to hide the whole board fairly.",
        "dialogue": "\"We can reset the round so neither of us gets an unfair peek,\" {hero} offered.",
        "kindness": "{hero} volunteered to turn away while Grandparent mixed the covered cards.",
        "teamwork": "They tucked the towel over the board, shuffled beneath it, and restarted with equal information.",
        "cause": "the closing screen door pushed a draft across face-down cards",
        "lesson": "kindness includes protecting fairness even when no one asks",
        "ending": "The apples shone in their bowl as two honestly matched cards met in the center.",
    },
    {
        "id": "sneeze_fan",
        "premise": "Grandparent dusted the game shelf before bringing down the old lotto set.",
        "conflict": "A sudden sneeze made a paper fan fall with a light slap, fanning the score markers into the hallway.",
        "mistake": "{hero} laughed at the surprising sound before seeing that Grandparent felt embarrassed.",
        "clue": "A trail of colored dots led from the shelf to each marker along the hall runner.",
        "dialogue": "\"I am sorry I laughed before I checked on you,\" {hero} said.",
        "kindness": "{hero} brought a tissue, waited for Grandparent's nod, and turned cleanup into a color hunt.",
        "teamwork": "They followed opposite sides of the dotted trail and met at the final purple marker.",
        "cause": "a loose paper fan fell when a harmless sneeze shook the shelf",
        "lesson": "a quick apology should be followed by thoughtful help",
        "ending": "The purple marker returned home beside a fresh tissue box and a shared chuckle.",
    },
    {
        "id": "map_fold",
        "premise": "Beside the lotto board lay a hand-drawn map of the imaginary nations in their animal stories.",
        "conflict": "A folded map flap sprang open with a paper slap and swept the matching cards into the wrong nation columns.",
        "mistake": "{hero} assumed every card from one column must belong together, although the map showed many kinds of neighbors.",
        "clue": "Tiny bridge symbols connected all three nation columns across the creases.",
        "dialogue": "\"A nation contains many different people; a column cannot tell us anyone's nature,\" Grandparent said.",
        "kindness": "{hero} listened and described each card by its picture instead of making guesses about its nation.",
        "teamwork": "They followed the bridge symbols, restored the matching pattern, and flattened the map with soft weights.",
        "cause": "a tightly folded story map sprang open across the game board",
        "lesson": "kindness treats each person as an individual, never as a national stereotype",
        "ending": "Three paper bridges crossed the flat map while every different animal card found its match.",
    },
    {
        "id": "chair_cushion",
        "premise": "They used a lap-sized lotto board so Grandparent could play comfortably from a favorite chair.",
        "conflict": "A firm cushion settled with a muffled slap and tilted the board, sliding buttons into the blanket folds.",
        "mistake": "{hero} suggested moving to the floor, forgetting that Grandparent had chosen the chair for comfort.",
        "clue": "The breakfast tray nearby had folding legs and a level rim made for holding things steady.",
        "dialogue": "\"Let us adapt the game to the player, not the player to the game,\" {hero} said after thinking.",
        "kindness": "{hero} asked what felt comfortable and brought the tray only after Grandparent agreed.",
        "teamwork": "Together they searched each blanket fold, counted the buttons, and set the board on the level tray.",
        "cause": "a settling chair cushion tilted a lap board that needed firmer support",
        "lesson": "kindness makes room for another person's comfort and choice",
        "ending": "The level tray held a finished row while Grandparent relaxed against the soft cushion.",
    },
]


ROUTES = [
    ("On a visit filled with small plans,", "The first idea did not work.", "By evening,"),
    ("The mystery began quietly:", "That guess only deepened the muddle.", "Before the lamp came on,"),
    ("Grandparent called it a good day for noticing details.", "For one worried moment, the game seemed spoiled.", "After careful work,"),
    ("Rain tapped outside while a bright indoor game waited.", "Rushing made the trouble harder to read.", "When the rain softened,"),
    ("The visit began with a promise to take turns.", "Then the promise was tested by a surprising mess.", "Once both players had helped,"),
    ("A familiar room can still hold a new puzzle.", "The obvious answer proved incomplete.", "At the end of the puzzle,"),
    ("Before choosing a card, Grandparent invited one careful look around.", "Even so, an impatient response missed the important clue.", "With the clue understood,"),
    ("The picture game was ready, but the room had its own small surprise.", "Neither blame nor speed put things right.", "Soon afterward,"),
    ("That afternoon's best tool was not in the game box.", "The scattered pieces called for thought before action.", "Because they acted together,"),
    ("At Grandparent's house, an ordinary game became a lesson worth remembering.", "A mistaken first move showed why patience mattered.", "When every piece was accounted for,"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    animal: str
    nation: str
    grandparent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def validate_combo(activity: Activity, prize: Prize) -> bool:
    return activity.id == "lotto" and prize.type == "lotto_board"


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this world only supports the lotto game in grandparent's house, "
        f"and the chosen prize must be the lotto board.)"
    )


def _story_choices(params: StoryParams) -> tuple[dict[str, str], tuple[str, str, str]]:
    if params.seed is None:
        signature = "|".join(
            [params.name, params.animal, params.nation, params.grandparent, params.trait]
        )
        key = sum((index + 1) * ord(char) for index, char in enumerate(signature))
    else:
        key = params.seed
    incident = INCIDENTS[key % len(INCIDENTS)]
    route = ROUTES[(key // len(INCIDENTS)) % len(ROUTES)]
    return incident, route


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    incident, route = _story_choices(params)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        label=params.name,
        meters={},
        memes={"kindness": 0.0, "teamwork": 0.0, "joy": 0.0, "worry": 0.0},
    ))
    grandparent = world.add(Entity(
        id="Grandparent",
        kind="character",
        type=params.grandparent,
        label="Grandparent",
        memes={"worry": 0.0, "joy": 0.0},
    ))
    prize = world.add(Entity(
        id="LottoBoard",
        type="lotto_board",
        label="lotto board",
        phrase="a bright lotto board with little animal pictures",
        owner=hero.id,
        caretaker=grandparent.id,
        worn_by=hero.id,
        meters={"messy": 0.0, "sorted": 0.0, "scattered": 0.0},
    ))

    world.facts.update(
        hero=hero,
        grandparent=grandparent,
        prize=prize,
        params=params,
        incident=incident,
        route=route,
        lotto_kind="a no-money picture-matching game",
    )
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    params: StoryParams = f["params"]
    incident: dict[str, str] = f["incident"]
    route = f["route"]
    world.say(route[0])
    world.say(
        f"{hero.label}, a {params.trait} little {params.animal}, had come from the imaginary "
        f"{params.nation} to visit {params.grandparent} at {world.setting.place}."
    )
    world.say(
        "That imaginary nation was a place on a family story map, drawn with rivers, "
        "roads, and many different neighborhoods."
    )
    world.say(
        "Their lotto was a no-money picture-matching game: nobody bet, bought a ticket, "
        "or won a prize."
    )
    world.say(incident["premise"].format(hero=hero.label))


def conflict(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    prize: Entity = f["prize"]
    incident: dict[str, str] = f["incident"]
    route = f["route"]

    world.para()
    world.say(route[1])
    hero.meters["slap"] = hero.meters.get("slap", 0.0) + 1
    propagate(world)
    world.say(incident["mistake"].format(hero=hero.label))
    world.say(incident["clue"].format(hero=hero.label))
    world.say(incident["dialogue"].format(hero=hero.label))
    world.say(f"The evidence showed what had happened: {incident['cause']}.")
    world.say("The slap was only an object sound; nobody had hit a person or animal.")
    world.facts.update(
        conflict=incident["conflict"].format(hero=hero.label),
        clue=incident["clue"].format(hero=hero.label),
        cause=incident["cause"],
    )


def resolve(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    prize: Entity = f["prize"]
    incident: dict[str, str] = f["incident"]
    route = f["route"]

    world.para()
    world.say(route[2])
    world.say("Kindness shaped their next choice, and teamwork gave each player a useful job.")
    hero.memes["kindness"] = 1.0
    hero.memes["teamwork"] = 1.0
    gp.memes["teamwork"] = 1.0
    propagate(world)
    world.say(
        f"They checked every piece of the {prize.label}; none was lost, and the safe play area was clear again."
    )
    world.say(
        f"Then {hero.label} and {gp.label} played a fair round of picture lotto and took turns calling the animals."
    )
    world.say(
        f"{hero.label} learned that {incident['lesson']}."
    )
    world.say(incident["ending"].format(hero=hero.label))
    world.facts.update(
        resolution=incident["teamwork"].format(hero=hero.label),
        lesson=incident["lesson"],
        ending=incident["ending"].format(hero=hero.label),
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    conflict(world)
    resolve(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    incident: dict[str, str] = f["incident"]
    return [
        f"Write an animal story about {params.name}, a {params.trait} {params.animal} from the imaginary {params.nation}, visiting {params.grandparent}'s house for no-money picture lotto.",
        f"Use this cause in a child-friendly story: {incident['cause']}. The event should create a nonviolent slap sound and a problem with a lotto board.",
        f"Write a story in which kindness and teamwork solve the {incident['id'].replace('_', ' ')} incident, ending with {incident['ending'][0].lower() + incident['ending'][1:]}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    gp: Entity = f["grandparent"]
    params: StoryParams = f["params"]
    incident: dict[str, str] = f["incident"]
    qa = [
        QAItem(
            question="Who was the visiting player?",
            answer=f"The visiting player was {hero.label}, a {params.trait} little {params.animal} from the imaginary {params.nation}.",
        ),
        QAItem(
            question=f"What did lotto mean in {hero.label}'s story?",
            answer="Lotto was a no-money picture-matching game. Nobody bet, bought a ticket, or won a prize.",
        ),
        QAItem(
            question="What caused the slap sound and the game problem?",
            answer=f"The problem happened because {incident['cause']}. The slap was not directed at a person or animal.",
        ),
        QAItem(
            question=f"What clue helped {hero.label} understand the problem?",
            answer=incident["clue"].format(hero=hero.label),
        ),
        QAItem(
            question=f"How did {hero.label} show kindness?",
            answer=incident["kindness"].format(hero=hero.label),
        ),
        QAItem(
            question=f"How did {hero.label} and {gp.label} use teamwork?",
            answer=incident["teamwork"].format(hero=hero.label),
        ),
        QAItem(
            question="What lesson did the visitor learn?",
            answer=f"{hero.label} learned that {incident['lesson']}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to do a job better and faster.",
        ),
        QAItem(
            question="Why do people tidy up scattered game pieces?",
            answer="People tidy up game pieces so the game stays organized and everyone can keep playing safely.",
        ),
        QAItem(
            question="Can the word lotto describe a game without gambling?",
            answer="Yes. Picture lotto is a matching game that can be played without money, betting, tickets, or prizes.",
        ),
        QAItem(
            question="Does a person's nation determine their personality?",
            answer="No. A nation is a place or community, while every person has individual traits, choices, and experiences.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Place, Activity, Prize) :- setting(Place), affords(Place, Activity), prize(Prize), activity(Activity), at_risk(Activity, Prize), has_fix(Activity, Prize).

at_risk(lotto, lotto_board).

has_fix(lotto, lotto_board).

valid_story(Place, Activity, Prize, Animal) :- valid(Place, Activity, Prize), wears(Animal, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "grandparent_house"))
    lines.append(asp.fact("affords", "grandparent_house", "lotto"))
    lines.append(asp.fact("activity", "lotto"))
    lines.append(asp.fact("prize", "lotto_board"))
    for animal in TYPES:
        lines.append(asp.fact("wears", animal, "lotto_board"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("grandparent's house", "lotto", "lotto")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    cl = {
        ("grandparent's house", activity, "lotto" if prize == "lotto_board" else prize)
        for _, activity, prize in cl
    }
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: nation, slap, lotto, kindness, teamwork.")
    ap.add_argument("--place", choices=["grandparent's house"], default=None)
    ap.add_argument("--activity", choices=sorted(ACTIVITIES), default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default=None)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=TYPES)
    ap.add_argument("--nation", choices=NATIONS)
    ap.add_argument("--grandparent", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        if not validate_combo(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], PRIZES[args.prize]))
    combos = valid_combos()
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    animal = args.animal or rng.choice(TYPES)
    nation = args.nation or rng.choice(NATIONS)
    grandparent = args.grandparent or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=name,
        animal=animal,
        nation=nation,
        grandparent=grandparent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with animal):")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            place="grandparent's house",
            activity="lotto",
            prize="lotto",
            name="Fia",
            animal="fox",
            nation="Sun Nation",
            grandparent="grandmother",
            trait="gentle",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

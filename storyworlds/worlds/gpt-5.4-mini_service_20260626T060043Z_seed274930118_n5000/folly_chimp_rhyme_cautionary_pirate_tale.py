#!/usr/bin/env python3
"""
A small cautionary pirate tale world with rhyme, centered on a chimp whose
folly leads to trouble and a wiser ending.

The simulated domain:
- A pirate ship setting with one chimp, one captain, one treasure chest, and a
  risky action.
- Physical meters track things like balance, soaked, tangled, and secure.
- Emotional memes track pride, caution, worry, shame, relief, and trust.
- The story is generated from world state, not from a fixed paragraph template.

The tale style:
- Pirate-tale voice
- Gentle rhyme in a few key beats
- Cautionary structure: warning -> folly -> consequence -> wiser turn
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["balance", "soaked", "tangled", "secure", "dusty"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "pride", "caution", "worry", "shame", "relief", "trust", "folly"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "captainess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str
    setting: str
    rhyme: str = ""
    caution: str = ""


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.ship)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Milo"
    gender: str = "chimp"
    captain: str = "Captain Reed"
    ship: str = "the Ruby Gull"
    treasure: str = "golden map"
    folly: str = "swing from the mast in a storm"
    rhyme: bool = True
    cautionary: bool = True


NAMES = ["Milo", "Kiki", "Bram", "Nori", "Pip", "Tiki", "Bobo", "Sage"]
CAPTAINS = ["Captain Reed", "Captain Mire", "Captain Sol", "Captain Vale"]
SHIPS = ["the Ruby Gull", "the Sea Lantern", "the Briny Star", "the Drifted Comet"]
TREASURES = [
    ("golden map", "map"),
    ("silver key", "key"),
    ("pearl compass", "compass"),
    ("bronze coin pouch", "pouch"),
]


@dataclass(frozen=True)
class PirateArc:
    premise: str
    warning: str
    folly: str
    consequence: str
    clue: str
    choice: str
    action: str
    result: str
    lesson: str
    ending: str


ARCS = [
    PirateArc(
        premise="A fog bank hid Needle Reef while the lookout bell waited beside the mast.",
        warning="Leave the bell rope clear until the lookout calls",
        folly="loop the bell rope into a grand swinging vine",
        consequence="The knot swallowed the rope, so the lookout could not ring when black rocks appeared through the fog.",
        clue="a gull's cry echoed back too quickly from the unseen reef",
        choice="cut the playful knot instead of defending it",
        action="freed the bell rope and rang three sharp warnings while the crew hauled the tiller",
        result="the ship turned into open water before its hull touched Needle Reef",
        lesson="A signal line is a promise to everyone aboard, not a toy for one proud sailor.",
        ending="Behind them, three bell notes crossed the fog while the reef faded like a row of sleeping teeth.",
    ),
    PirateArc(
        premise="At dusk, the deck lantern guarded a sailmaker who was mending the mainsail.",
        warning="Dance far from the lamp, for one wild step can start a fire",
        folly="balance on the rail and kick a showy jig beside the lantern",
        consequence="A heel struck the lantern hook, and hot oil spilled toward the folded canvas.",
        clue="one bright thread of flame began crawling along an oily seam",
        choice="drop the applause and raise the alarm",
        action="clapped a wet swab over the flame while the captain righted the lantern",
        result="the fire went dark before it could bite the sail",
        lesson="Showing off is never worth hiding a danger that others must face.",
        ending="The saved sail shone silver in the moonlight, without so much as a spark at its hem.",
    ),
    PirateArc(
        premise="The crew opened the chart chest as a crosswind hurried them toward a maze of sandbars.",
        warning="Brace the chest before you reach for any chart",
        folly="snatch the prettiest map while ignoring the rolling deck",
        consequence="The chest slid loose, scattering charts across the deck and sending the harbor map toward the sea.",
        clue="the needed map bore a blue heron mark at one corner",
        choice="save the useful chart rather than pocket a glittering coin",
        action="caught the heron-marked map with a boathook and helped lash the chest",
        result="the captain found the safe channel between the sandbars",
        lesson="A careful hand protects shared knowledge before it grabs private treasure.",
        ending="At sunrise, the blue-heron chart lay flat beneath four tidy brass corners.",
    ),
    PirateArc(
        premise="A flock of gulls swooped over breakfast while the ship entered a narrow harbor.",
        warning="Do not race birds beneath a working sail",
        folly="chase the gulls across the deck with a banana held high",
        consequence="The chimp tripped the jib sheet, and the loose sail covered the helmsman's view.",
        clue="a red buoy vanished behind the flapping canvas",
        choice="stop chasing the thief and help clear the helm",
        action="crawled low, released the snagged line, and called where the red buoy stood",
        result="the helmsman steered past the harbor wall with room to spare",
        lesson="A silly chase must end the moment it blinds someone doing important work.",
        ending="The gull escaped with half a banana; the red buoy bobbed safely astern.",
    ),
    PirateArc(
        premise="Rain filled the sail while the crew prepared to lower it before a squall.",
        warning="Keep your paws away from the reefing cleats until the order comes",
        folly="untie three cleats to prove a chimp could lower the sail alone",
        consequence="The heavy canvas dropped crookedly and pinned two sailors' coats to the deck.",
        clue="the free corner hammered harder each time the wind rose",
        choice="admit which cleats had been loosened",
        action="named the three lines in order and hauled with the crew instead of alone",
        result="the sail folded evenly and both sailors stepped free before the squall",
        lesson="Truth repairs a reckless mistake faster than pride can conceal it.",
        ending="Rain drummed on a neatly reefed sail as every freed coat hung beside the stove.",
    ),
    PirateArc(
        premise="A powder keg rolled from the storeroom when the ship climbed a steep wave.",
        warning="Never roll a barrel whose painted mark you have not checked",
        folly="ride the keg downhill as if it were a festival drum",
        consequence="The keg struck a hatch rim and began leaking black powder near the galley stove.",
        clue="a skull-shaped shipping mark showed that the barrel was not flour",
        choice="call for the captain instead of pushing the keg out of sight",
        action="covered the leak with damp canvas and helped carry the cold keg to the powder locker",
        result="the dangerous trail was swept away before a galley spark reached it",
        lesson="Unknown cargo deserves a label check, especially when fun makes haste tempting.",
        ending="Only a clean wet streak remained where the dangerous black trail had lain.",
    ),
    PirateArc(
        premise="The anchor chain rattled as the ship waited above a garden of coral.",
        warning="Do not spin the windlass while divers are below",
        folly="crank the great wheel for the pleasure of hearing its iron clatter",
        consequence="The anchor dragged, tugging its chain toward the divers' guide rope.",
        clue="three bubbles rose beside the yellow guide float instead of beyond it",
        choice="reverse the wheel and listen for the divers' signal",
        action="walked the windlass backward with the captain until the chain slackened",
        result="the divers surfaced safely and the coral remained unbroken",
        lesson="A machine can reach farther than the paw that moves it, so warnings protect unseen neighbors.",
        ending="Three divers waved beside living coral, and the quiet chain hung straight below.",
    ),
    PirateArc(
        premise="A young deckhand was carrying medicine to an island before the tide turned.",
        warning="Leave the compass in its padded box when lightning crowds the sky",
        folly="wear the pearl compass as a medal and parade beneath the rigging",
        consequence="A swinging block knocked it loose, and the compass cracked against the deck.",
        clue="the sun broke through for one breath beside a west-flying tern",
        choice="confess the broken compass and share the clue",
        action="marked the brief sun line while the captain matched the tern's flight to the island chart",
        result="the medicine reached the island before the falling tide closed its inlet",
        lesson="Owning a mistake gives the crew time to solve it together.",
        ending="The medicine basket crossed the pier just as the inlet stones rose from the ebbing sea.",
    ),
    PirateArc(
        premise="The cook cooled a pot of soup while a hungry crew repaired storm damage.",
        warning="Wait for bowls; never carry a boiling pot across a tilted deck",
        folly="lift the whole soup pot to win the first taste",
        consequence="A wave tipped the pot, and hot broth rushed toward the carpenter's bare feet.",
        clue="a coil of clean rope could stop the pot without touching the hot iron",
        choice="give up the first taste and protect the carpenter",
        action="wedged the rope coil around the pot while the cook covered it with a lid",
        result="no one was burned and enough soup remained for every tired sailor",
        lesson="Patience keeps a small appetite from becoming everybody's emergency.",
        ending="Twelve bowls steamed in a calm row, with the chimp's bowl placed last by choice.",
    ),
    PirateArc(
        premise="A caged messenger parrot carried the harbor master's tide warning.",
        warning="Do not open a working cage simply to teach its bird a trick",
        folly="free the parrot so it could perform a grand loop around the mast",
        consequence="The frightened bird flew into the rigging with the tide message still tied to its leg.",
        clue="the parrot answered the ship's whistle with the same two-note call",
        choice="use patience rather than climb after it recklessly",
        action="whistled from the open cage and waited with a slice of mango",
        result="the parrot returned, and the captain read the warning before the channel emptied",
        lesson="Kindness includes respecting an animal's task and fear, not merely granting sudden freedom.",
        ending="The parrot ate mango by the open hatch while the ship crossed the last deep water.",
    ),
    PirateArc(
        premise="The crew stretched a rescue net beneath a cliff where a stranded sailor waited.",
        warning="Keep every knot untouched until the sailor is aboard",
        folly="borrow one bright knot to fasten a feathered pirate hat",
        consequence="The loosened corner sagged just as the stranded sailor began climbing down.",
        clue="the captain saw one diamond of netting widening near the chimp's new hat",
        choice="return the stolen cord before anyone stepped onto the net",
        action="retied the corner with the knotmaster's guidance and tested it with a water cask",
        result="the net held firm and brought the stranded sailor safely aboard",
        lesson="Even a tiny borrowed piece can be carrying someone else's safety.",
        ending="The rescued sailor slept beneath a plain hat while the bright cord held the net square.",
    ),
    PirateArc(
        premise="The ship sheltered in a cove where turtle nests dotted the moonlit sand.",
        warning="Fire no signal flare while the hatchlings are finding the sea",
        folly="light a flare to make the chimp's midnight leap look magnificent",
        consequence="The red glare turned the hatchlings away from the moonlit water and toward the rocks.",
        clue="their tiny tracks curved toward the false red light",
        choice="smother the flare and repair the harm quietly",
        action="screened the deck lamps while the crew marked a dark path toward the moon",
        result="the hatchlings followed the pale horizon and reached the gentle surf",
        lesson="A splendid moment is folly when its light steals another creature's way home.",
        ending="Tiny tracks met the silver tide, and the final shell slipped under a moonlit ripple.",
    ),
]

OPENINGS = [
    "The pirate crew had trusted the quick-pawed chimp with small but useful duties.",
    "Among the patched sails and salt-stiff ropes, the chimp wanted badly to look fearless.",
    "The voyage had been peaceful long enough for pride to begin whispering foolish ideas.",
    "Every sailor knew the chimp was clever; the trouble was that the chimp knew it too.",
    "That morning, the captain praised careful work, but the chimp heard only the praise.",
    "With treasure below and work above, the pirate ship needed every paw to mind its task.",
]

WARNING_RHYMES = [
    "A warning is a lantern when a hazard hides from sight; / ignore its little circle, and you may lose the light.",
    "Check the rope and check the rail; careful paws complete the sail.",
    "Pride may crow and hurry may call; one calm breath can steady all.",
    "Hear before you leap away; wise paws bring the ship to bay.",
    "A boast is quick, a mishap quicker; stop and think before winds flicker.",
    "When shipmates warn, do not make sport; their words may steer you safe to port.",
]

ACTION_RHYMES = [
    "No more show and no more boast; mend the harm that matters most.",
    "Name the wrong and make it right; honest work can trim the night.",
    "Paw by paw and side by side, wiser hands can turn the tide.",
    "First take heed, then lend a hand; careful crews reach safer land.",
    "Folly fled when truth drew near; useful courage mastered fear.",
    "Slow the race and share the load; that is how a safe ship rode.",
]

DIALOGUES = [
    "\"I caused this,\" {name} told {captain}. \"Show me the safest first step.\"",
    "{captain} asked, \"Will you guard your pride or guard the crew?\" \"The crew,\" {name} answered.",
    "\"No excuse, Captain,\" said {name}. \"I saw the warning and chose the trick. I will help repair it.\"",
    "\"What changed?\" called {captain}. {name} pointed to the clue and explained the danger plainly.",
    "{name} swallowed a boast and shouted, \"Stop! My folly caused this. Follow me to the clue.\"",
    "\"I wanted cheers,\" {name} admitted, \"but now the ship needs careful paws more than a performance.\"",
]


def _r_slip(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.meters["balance"] < THRESHOLD:
        sig = ("slip",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        chimp.meters["soaked"] += 1
        chimp.meters["tangled"] += 1
        chimp.memes["worry"] += 1
        out.append("The deck gave a creak and a sneaky squeal; down went the chimp in a foamy gale.")
    return out


def _r_shame(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.meters["soaked"] >= THRESHOLD and ("shame",) not in world.fired:
        world.fired.add(("shame",))
        chimp.memes["shame"] += 1
        captain = world.get("captain")
        captain.memes["worry"] += 1
        out.append("The captain frowned, not hard or grim, but said, 'A fool's tide can drown a trim.'")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    chimp = world.get("chimp")
    if chimp.memes["caution"] >= THRESHOLD and chimp.memes["trust"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        chimp.memes["relief"] += 1
        chimp.memes["worry"] = max(0.0, chimp.memes["worry"] - 1.0)
        out.append("With steady paws and a softer sway, the chimp chose sense and saved the day.")
    return out


RULES = [_r_slip, _r_shame, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                produced.extend(lines)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_folly(world: World) -> dict[str, float]:
    sim = world.copy()
    chimp = sim.get("chimp")
    chimp.meters["balance"] = 0.0
    propagate(sim, narrate=False)
    return {
        "soaked": sim.get("chimp").meters["soaked"],
        "shame": sim.get("chimp").memes["shame"],
    }


def make_world(params: StoryParams) -> World:
    ship = Ship(name=params.ship, place="at sea", setting="pirate ship", rhyme="rhyme", caution="caution")
    world = World(ship)
    chimp = world.add(Entity(id="chimp", kind="character", type="chimp", label=params.name))
    captain = world.add(Entity(id="captain", kind="character", type="captain", label=params.captain))
    chest = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=params.treasure,
        phrase=f"the {params.treasure}",
        owner=captain.id,
        caretaker=captain.id,
        region="hold",
    ))

    chimp.memes["joy"] += 1
    chimp.memes["pride"] += 1
    chimp.memes["caution"] += 1
    captain.memes["trust"] += 1
    chest.meters["secure"] += 1
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    chimp = world.get("chimp")
    captain = world.get("captain")
    treasure = world.get("treasure")

    variant = params.seed if params.seed is not None else sum(
        ord(ch) for ch in f"{params.name}|{params.captain}|{params.ship}|{params.treasure}|{params.folly}"
    )
    arc_index = variant % len(ARCS)
    opening_index = (variant // len(ARCS)) % len(OPENINGS)
    warning_index = (variant // (len(ARCS) * len(OPENINGS))) % len(WARNING_RHYMES)
    action_index = (variant // 5) % len(ACTION_RHYMES)
    dialogue_index = (variant // 7) % len(DIALOGUES)
    structure = (variant // 11) % 4
    arc = ARCS[arc_index]

    opening = OPENINGS[opening_index]
    warning_rhyme = WARNING_RHYMES[warning_index].replace(" / ", " ")
    action_rhyme = ACTION_RHYMES[action_index]
    dialogue = DIALOGUES[dialogue_index].format(name=chimp.label, captain=captain.label)

    world.say(
        f"Aboard {world.ship.name}, a pirate ship, {captain.label} sailed with {chimp.label}, "
        f"a lively chimp, while the {treasure.label} rested secure below deck."
    )
    world.say(opening)
    world.para()
    world.say(arc.premise)
    world.say(f"{captain.label} warned, \"{arc.warning}.\" {warning_rhyme}")

    chimp.memes["folly"] += 1
    chimp.memes["pride"] += 1
    captain.memes["worry"] += 1
    chimp.meters["balance"] = 0.0
    folly_line = (
        f"Yet {chimp.label} let pride outrun caution. Instead of merely trying to {params.folly}, "
        f"the chimp chose a sharper folly: to {arc.folly}."
    )
    consequence_line = f"The choice had a real cost. {arc.consequence}"
    if structure == 0:
        world.say(folly_line)
        world.say(consequence_line)
    elif structure == 1:
        world.say(
            f"It began with the boast that {chimp.label} could {params.folly}. Then the chimp decided "
            f"to {arc.folly}. That was the sharper folly the warning had named."
        )
        world.say(arc.consequence)
    elif structure == 2:
        world.say(folly_line)
        world.para()
        world.say(f"Too late, the crew saw why the warning mattered: {arc.consequence}")
    else:
        world.say(
            f"{chimp.label} imagined cheers and chose to {arc.folly}. That folly turned the old urge "
            f"to {params.folly} into a danger, not an adventure."
        )
        world.say(consequence_line)

    chimp.meters["at_risk"] = 1.0
    chimp.memes["worry"] += 1
    chimp.memes["shame"] += 1
    world.para()
    clue_line = f"Amid the confusion, {chimp.label} noticed that {arc.clue}."
    if structure in {0, 2}:
        world.say(clue_line)
        world.say(dialogue)
    else:
        world.say(dialogue)
        world.say(clue_line)
    world.say(f"The cautionary choice was clear: {chimp.label} would {arc.choice}.")

    chimp.memes["caution"] += 2
    chimp.memes["trust"] += 1
    chimp.memes["relief"] += 1
    captain.memes["relief"] += 1
    chimp.memes["worry"] = max(0.0, chimp.memes["worry"] - 1.0)
    chimp.meters["balance"] = 1.0
    chimp.meters["at_risk"] = 0.0
    chimp.meters["repaired"] = 1.0
    repair_line = f"Working with the pirate crew, the chimp {arc.action}."
    result_line = f"Because of that careful action, {arc.result}."
    if structure in {0, 3}:
        world.say(repair_line)
        world.say(action_rhyme)
        world.say(result_line)
    else:
        world.say(action_rhyme)
        world.say(repair_line)
        world.say(result_line)

    world.para()
    world.say(f"{captain.label} did not praise the earlier stunt. The captain praised the honest repair.")
    world.say(f"{chimp.label} learned this: {arc.lesson}")
    world.say(arc.ending)

    world.facts.update(
        chimp=chimp,
        captain=captain,
        treasure=treasure,
        params=params,
        arc=arc,
        clue=arc.clue,
        choice=arc.choice,
        action=arc.action,
        result=arc.result,
        lesson=arc.lesson,
        ending=arc.ending,
        predicted={"trouble": 1.0, "shame": 1.0},
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    chimp = world.facts["chimp"]
    captain = world.facts["captain"]
    treasure = world.facts["treasure"]
    params = world.facts["params"]
    arc = world.facts["arc"]
    qa = [
        QAItem(
            question=f"Who is the story mainly about aboard {params.ship} with {captain.label} and the {treasure.label}?",
            answer=f"It is about {chimp.label}, a chimp sailing with {captain.label}. The chimp makes a poor choice while the {treasure.label} remains secure below, then learns a wiser one.",
        ),
        QAItem(
            question=f"What did {chimp.label} do out of folly after {captain.label}'s warning aboard {params.ship}?",
            answer=f"After being warned, {chimp.label} chose to {arc.folly}. Pride made the chimp treat a working part of the pirate ship like a prop.",
        ),
        QAItem(
            question=f"What danger did {chimp.label}'s choice cause while {params.ship} carried the {treasure.label}?",
            answer=f"{arc.consequence} The danger interrupted the crew's work even though the {treasure.label} stayed secure below deck.",
        ),
        QAItem(
            question=f"What clue helped {chimp.label} answer {captain.label}'s warning on {params.ship}?",
            answer=f"{chimp.label} noticed that {arc.clue}. That clue revealed the immediate danger instead of merely showing that something had gone wrong.",
        ),
        QAItem(
            question=f"How did {chimp.label} help {captain.label} repair the harm aboard {params.ship}?",
            answer=f"The chimp {arc.action}. As a result, {arc.result}, while {captain.label}'s crew regained control of the ship.",
        ),
        QAItem(
            question=f"What cautionary lesson did {chimp.label} learn from this folly on {params.ship}?",
            answer=f"{arc.lesson} That lesson mattered to {chimp.label} because one proud choice had endangered the whole crew.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used for sailing on the sea, often with ropes, sails, and a deck that can get slippery.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking about danger before acting.",
        ),
        QAItem(
            question="What is folly?",
            answer="Folly is a very foolish choice that ignores good advice and can lead to trouble.",
        ),
        QAItem(
            question="Why can the sea be dangerous?",
            answer="The sea can be dangerous because waves, wind, and wet decks can make people slip or get lost.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    arc = world.facts["arc"]
    return [
        f"Write a short pirate tale in rhyme about a chimp named {params.name} whose folly involves trying to {arc.folly}.",
        f"Tell a cautionary story aboard {params.ship} where a chimp ignores the warning '{arc.warning}' and must repair the result.",
        f"Write a child-friendly pirate adventure using the clue that {arc.clue}, helping the hero choose caution over pride.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A chimp is in folly if the story chooses a risky action after a warning.
folly(chimp) :- warned(chimp), ignores_warning(chimp).

% The consequence follows when folly meets the ship's danger.
trouble(chimp) :- folly(chimp), stormy_sea, slippery_deck.

% Caution and trust support a safer ending.
resolved(chimp) :- learns(chimp), cautious(chimp), trusts_captain(chimp).

#show folly/1.
#show trouble/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("warned", "chimp"),
        asp.fact("ignores_warning", "chimp"),
        asp.fact("stormy_sea"),
        asp.fact("slippery_deck"),
        asp.fact("learns", "chimp"),
        asp.fact("cautious", "chimp"),
        asp.fact("trusts_captain", "chimp"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"folly/1", "trouble/1", "resolved/1"}
    if atoms == expected:
        print("OK: ASP twin matches the intended tiny pirate logic.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale world with rhyme and a chimp.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--treasure", choices=[t[0] for t in TREASURES])
    ap.add_argument("--folly", choices=[
        "swing from the mast in a storm",
        "dance on the rail while the sea heaves",
        "reach for the map without looking down",
        "race the gulls across the deck",
    ])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    captain = args.captain or rng.choice(CAPTAINS)
    ship = args.ship or rng.choice(SHIPS)
    treasure = args.treasure or rng.choice([t[0] for t in TREASURES])
    folly = args.folly or rng.choice([
        "swing from the mast in a storm",
        "dance on the rail while the sea heaves",
        "reach for the map without looking down",
        "race the gulls across the deck",
    ])
    gender = "chimp"
    return StoryParams(
        seed=args.seed,
        name=name,
        gender=gender,
        captain=captain,
        ship=ship,
        treasure=treasure,
        folly=folly,
        rhyme=True,
        cautionary=True,
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


CURATED = [
    StoryParams(name="Milo", captain="Captain Reed", ship="the Ruby Gull", treasure="golden map", folly="swing from the mast in a storm"),
    StoryParams(name="Kiki", captain="Captain Mire", ship="the Sea Lantern", treasure="silver key", folly="dance on the rail while the sea heaves"),
    StoryParams(name="Bram", captain="Captain Sol", ship="the Briny Star", treasure="pearl compass", folly="reach for the map without looking down"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(" ".join(str(sym) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

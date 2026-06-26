#!/usr/bin/env python3
"""
storyworlds/worlds/particular_rhyme_twist_kindness_detective_story.py
=====================================================================

A standalone story world for a gentle detective tale where a child detective
solves a rhyming riddle, discovers a kind twist, and helps everyone feel better.

Initial story:
---
Pat was a little detective who noticed every single clue. Pat was very particular—
every shelf had to be neat, every clue had to make sense. Pat's best friend was
a dog named Dot. One morning, Pat's grandma called: "My special cookie jar is
empty! The cookies for the picnic are gone!"

Pat put on a detective hat, took a magnifying glass, and went to the kitchen.
Dot sniffed around. There was a rhyme written on the chalkboard:

    "I am round and sweet and oh so small,
    I rolled away from the counter, that's all.
    If you look behind the broom and mop,
    You will find me near the mop's drippy drop."

Pat read the rhyme aloud. "That is particular—it says where the cookie rolled."

Pat and Dot looked behind the mop bucket. There was one single cookie! But where
were the rest? Then Pat saw a trail of crumbs leading to the garden.

Outside, Mrs. Robin was standing by the flower bed. "I saw a squirrel run by
with something in its mouth," she said.

Pat followed the crumb trail to a little hole under the fence. Inside the hole
was the cookie jar—tipped over, but most cookies were safe! The squirrel had
taken only a tiny bite.

Pat smiled. "The squirrel was hungry, not mean. We can share a cookie with him."
Pat and Dot left a small piece by the hole. Then Pat carried the jar back to
Grandma.

Grandma hugged Pat. "You solved the mystery with kindness. That is the best kind
of detective work."

Pat and Dot and Grandma shared the cookies on the porch. Dot wagged her tail.
The squirrel peeked out and nibbled his piece. Everyone was happy.

Causal state updates:
---
    examine clue                 -> detective.clues_found += 1
    solve rhyme                  -> detective.understanding += 1
    follow trail                 -> detective.progress += 1
    find lost item (twist)       -> detective.happiness += 1 ; suspect.blame -> 0
    show kindness to culprit     -> culprit.gratitude += 1 ; detective.kindness_done += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# Keys that represent the "mess" (mystery intensity) for accumulated effects
MESS_KINDS = {"confusion", "missing"}


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    suspect_role: str = ""  # "culprit" or "witness"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "grandma", "robin", "squirrel", "woman"}
        male = {"boy", "grandpa", "man", "dog"}
        if self.id == "Dot" or self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandma": "grandma", "grandpa": "grandpa", "dog": "dog"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the kitchen"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    lost_item: str  # e.g. "cookies"
    rhyme_line: str  # the rhyming clue
    twist_reveal: str  # what really happened
    mess: str  # "confusion" or "missing"
    zone: set[str]  # not used for body but for location tags
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    missing_key: str  # matches Mystery.id
    plural: bool = False


@dataclass
class Gear:
    """Detective tool that helps solve the mystery."""
    id: str
    label: str
    covers: set[str]  # not body regions, but clue types
    guards: set[str]  # kinds of trickiness it neutralizes
    prep: str  # "put on your thinking cap"
    tail: str  # closing clause
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.clues_found = 0
        self.culprit_found = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.clues_found = self.clues_found
        clone.culprit_found = self.culprit_found
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_find_clue(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["confusion"] < THRESHOLD:
            continue
        if world.clues_found < 1:
            sig = ("clue", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.clues_found += 1
            actor.meters["understanding"] += 0.5
            out.append("A clue appeared, and the detective's eyes grew wide with curiosity.")
    return out


def _r_solve_rhyme(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["understanding"] >= THRESHOLD and not world.culprit_found:
            sig = ("solve", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["progress"] += 1
            out.append("The rhyme made sense now. The detective knew where to look.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["progress"] >= THRESHOLD and not world.culprit_found:
            sig = ("twist", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.culprit_found = True
            actor.memes["happiness"] += 1
            # find the real culprit (the one with suspect_role "culprit")
            culprit = [e for e in world.entities.values() if e.suspect_role == "culprit"]
            if culprit:
                culprit[0].meters["blame"] = 0
            out.append("But the truth was kinder than anyone expected!")
    return out


CAUSAL_RULES = [
    Rule(name="find_clue", tag="physical", apply=_r_find_clue),
    Rule(name="solve_rhyme", tag="social", apply=_r_solve_rhyme),
    Rule(name="twist", tag="social", apply=_r_twist),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_is_reasonable(mystery: Mystery, prize: Prize) -> bool:
    return mystery.id == prize.missing_key


def select_tool(mystery: Mystery) -> Optional[Gear]:
    for tool in GEAR:
        if mystery.id in tool.guards:
            return tool
    return None


# Prediction: simulate the mystery outcome (not used much in this domain)
def predict_resolution(world: World, detective: Entity, mystery: Mystery) -> dict:
    sim = world.copy()
    _do_investigate(sim, sim.get(detective.id), mystery, narrate=False)
    return {
        "solved": detective.memes["progress"] >= THRESHOLD,
        "happy": detective.memes["happiness"] >= THRESHOLD,
    }


def activity_delight(mystery: Mystery) -> str:
    return {
        "cookies": "the sweet smell and crumbly clues made the search feel like a game",
        "toy": "the bright red color of the toy stood out against the green grass",
        "book": "the torn page was a puzzle piece waiting to be put back",
    }.get(mystery.id, "every clue felt like a surprise")


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet and full of nooks."
    return f"{setting.place.capitalize()} was sunny and full of hiding spots."


def prize_was_found(detective: Entity, prize: Entity) -> str:
    return f"{detective.pronoun('possessive')} {prize.label} was found at last"


def _do_investigate(world: World, actor: Entity, mystery: Mystery, narrate: bool = True) -> None:
    if mystery.id not in world.setting.affords:
        return
    world.zone = set(mystery.zone)
    actor.meters[mystery.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, detective: Entity) -> None:
    trait = next((t for t in detective.traits if t != "little"), "")
    desc = f"little {trait} detective {detective.type}".strip()
    world.say(f"{detective.id} was a {desc} who noticed every single clue.")


def loves_investigating(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["love_investigate"] += 1
    world.say(
        f"{detective.pronoun().capitalize()} loved solving puzzles and finding lost things; "
        f"{activity_delight(mystery)}."
    )


def reports_loss(world: World, reporter: Entity, detective: Entity, prize: Entity) -> None:
    world.say(
        f"One morning, {detective.id}'s {reporter.label_word} called: "
        f'"My {prize.phrase} is gone! I need a clever detective!"'
    )


def gear_up(world: World, detective: Entity, tool: Gear) -> None:
    world.say(
        f"{detective.id} put on a detective hat and took a {tool.label}."
    )


def examine_clue(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.meters["understanding"] += 0.5
    world.say(
        f"On the chalkboard, a rhyme appeared:\n\n    \"{mystery.rhyme_line}\"\n\n"
        f"{detective.id} read the rhyme aloud. \"That is particular—it says where to look.\""
    )


def follow_trail(world: World, detective: Entity, sidekick: Entity) -> None:
    detective.memes["progress"] += 1
    world.say(
        f"{detective.pronoun().capitalize()} and {sidekick.id} followed the trail of crumbs."
    )


def witness_speak(world: World, witness: Entity, direction: str) -> None:
    world.say(
        f"\"I saw something run by with a {direction},\" said {witness.id}."
    )


def discover_twist(world: World, detective: Entity, culprit: Entity, mystery: Mystery) -> None:
    world.say(
        f"Inside the hole was the {mystery.lost_item}—tipped over, but most were safe! "
        f"The {culprit.type} had only taken a tiny bite."
    )


def show_kindness(world: Entity, detective: Entity, culprit: Entity) -> None:
    detective.memes["kindness_done"] += 1
    world.say(
        f"{detective.id} smiled. \"The {culprit.type} was hungry, not mean. We can share.\""
    )
    world.say(
        f"{detective.pronoun().capitalize()} left a small piece by the hole."
    )


def return_item(world: World, detective: Entity, reporter: Entity, prize: Entity) -> None:
    world.say(
        f"Then {detective.id} carried the {prize.label} back to {reporter.id}."
    )
    world.say(
        f"{reporter.id} hugged {detective.pronoun('object')}. "
        f"\"You solved the mystery with kindness. That is the best kind of detective work.\""
    )


def celebrate(world: World, detective: Entity, reporter: Entity, sidekick: Entity, culprit: Entity) -> None:
    world.say(
        f"{detective.id} and {reporter.id} and {sidekick.id} shared the "
        f"{' '.join(world.facts['missing_item'].split())} on the porch. "
        f"{sidekick.id} wagged her tail. The {culprit.type} peeked out and nibbled "
        f"{detective.pronoun('possessive')} piece. Everyone was happy."
    )


def tell(setting: Setting, mystery: Mystery, prize_cfg: Prize,
         detective_name: str = "Pat", gender: str = "girl",
         traits: Optional[list[str]] = None, sidekick_type: str = "dog",
         reporter_type: str = "grandma", culprit_type: str = "squirrel",
         witness_type: str = "robin") -> World:
    world = World(setting)
    world.facts["missing_item"] = prize_cfg.label

    detective = world.add(Entity(
        id=detective_name, kind="character", type=gender,
        traits=["little", "particular"] + (traits or ["curious", "kind"]),
    ))
    sidekick = world.add(Entity(
        id="Dot", kind="character", type=sidekick_type, label="dog",
        traits=["friendly", "sniffy"],
    ))
    reporter = world.add(Entity(
        id="Reporter", kind="character", type=reporter_type, label="grandma",
    ))
    culprit = world.add(Entity(
        id="Culprit", kind="character", type=culprit_type, label="squirrel",
        suspect_role="culprit",
    ))
    witness = world.add(Entity(
        id="Witness", kind="character", type=witness_type, label="robin",
        suspect_role="witness",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, plural=prize_cfg.plural,
    ))

    tool_def = select_tool(mystery)
    if tool_def is None:
        # fallback gear
        tool_def = Gear(id="glass", label="magnifying glass", covers=set(),
                        guards={mystery.id}, prep="look at every crumb",
                        tail="looked at every crumb closely")

    # Act 1
    introduce(world, detective)
    loves_investigating(world, detective, mystery)
    reports_loss(world, reporter, detective, prize)
    world.para()
    gear_up(world, detective, tool_def)
    world.say(f"{detective.id} and {sidekick.id} went to investigate.")

    # Act 2
    examine_clue(world, detective, mystery)
    follow_trail(world, detective, sidekick)
    witness_speak(world, witness, mystery.lost_item)
    world.para()

    # Act 3 - twist
    discover_twist(world, detective, culprit, mystery)
    show_kindness(world, detective, culprit)
    return_item(world, detective, reporter, prize)
    celebrate(world, detective, reporter, sidekick, culprit)

    # Record facts
    world.facts.update(
        detective=detective, sidekick=sidekick, reporter=reporter,
        culprit=culprit, witness=witness, prize=prize,
        mystery=mystery, setting=setting, tool=tool_def,
        resolved=True
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"cookies", "toy", "book"}),
    "garden": Setting(place="the garden", indoor=False, affords={"cookies"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"toy", "book"}),
}

MYSTERIES = {
    "cookies": Mystery(
        id="cookies",
        lost_item="cookies",
        rhyme_line=(
            "I am round and sweet and oh so small,\n"
            "I rolled away from the counter, that's all.\n"
            "If you look behind the broom and mop,\n"
            "You will find me near the mop's drippy drop."
        ),
        twist_reveal="The squirrel was hungry, not mean.",
        mess="missing",
        zone={"kitchen", "garden"},
        keyword="cookies",
        tags={"cookie", "sweet"},
    ),
    "toy": Mystery(
        id="toy",
        lost_item="red toy car",
        rhyme_line=(
            "I am red and fast and love to zoom,\n"
            "I rolled under the table in the room.\n"
            "Look behind the big blue chair,\n"
            "You'll find me sitting right there."
        ),
        twist_reveal="The puppy had nudged it under the chair.",
        mess="missing",
        zone={"playroom"},
        keyword="toy",
        tags={"toy", "red"},
    ),
    "book": Mystery(
        id="book",
        lost_item="picture book",
        rhyme_line=(
            "I am full of pictures, bright and wide,\n"
            "I slipped behind the couch to hide.\n"
            "Peek between the cushion and the wall,\n"
            "I am not lost, I just took a fall."
        ),
        twist_reveal="The book had fallen behind the couch.",
        mess="missing",
        zone={"playroom", "living room"},
        keyword="book",
        tags={"book", "pages"},
    ),
}

GEAR = [
    Gear(
        id="hat",
        label="detective hat",
        covers=set(),
        guards={"cookies", "toy", "book"},
        prep="put on your detective hat",
        tail="put on the detective hat",
    ),
    Gear(
        id="glass",
        label="magnifying glass",
        covers=set(),
        guards={"cookies", "toy", "book"},
        prep="take your magnifying glass",
        tail="took the magnifying glass",
    ),
    Gear(
        id="notebook",
        label="notebook and pencil",
        covers=set(),
        guards={"cookies", "toy", "book"},
        prep="get your notebook and pencil",
        tail="got the notebook and pencil",
    ),
]

PRIZES = {
    "cookies": Prize(label="cookies", phrase="special picnic cookies", type="food", missing_key="cookies", plural=True),
    "toy": Prize(label="red toy car", phrase="shiny red toy car", type="toy", missing_key="toy"),
    "book": Prize(label="picture book", phrase="favorite picture book", type="book", missing_key="book"),
}

DETECTIVE_NAMES = {"girl": ["Pat", "Sam", "Lee", "Rae", "Max"], "boy": ["Arlo", "Finn", "Leo", "Jax", "Sky"]}
TRAITS = ["particular", "curious", "brave", "kind", "clever", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mystery = MYSTERIES[mid]
            for prize_id, prize in PRIZES.items():
                if mystery_is_reasonable(mystery, prize) and select_tool(mystery):
                    combos.append((place, mid, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cookie": [
        ("Why are cookies sometimes called 'sweet'?",
         "Cookies are made with sugar, and sugar tastes sweet, so cookies are a sweet treat.")
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is when two words have the same ending sound, like 'cat' and 'hat'.")
    ],
    "detective": [
        ("What does a detective do?",
         "A detective looks for clues and solves mysteries to find missing things or answer questions.")
    ],
    "particular": [
        ("What does 'particular' mean?",
         "If someone is particular, they pay close attention to details and want things to be just right.")
    ],
    "kindness": [
        ("Why is kindness important?",
         "Kindness means being nice and helpful to others, and it makes everyone feel good.")
    ],
    "squirrel": [
        ("What do squirrels eat?",
         "Squirrels eat nuts, seeds, fruits, and sometimes small pieces of bread or cookies.")
    ],
    "magnifying glass": [
        ("What does a magnifying glass do?",
         "A magnifying glass makes small things look bigger so you can see them better.")
    ],
}
KNOWLEDGE_ORDER = ["cookie", "rhyme", "detective", "particular", "kindness", "squirrel", "magnifying glass"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det, side, rep, myst = f["detective"], f["sidekick"], f["reporter"], f["mystery"]
    return [
        f'Write a short detective story for a child that includes the words "rhyme", "twist", and "kindness".',
        f'Tell a story about a {det.type} detective named {det.id} who solves the mystery of the missing {myst.lost_item} using a rhyming clue.',
        f'Write a story where a particular little detective finds a kind twist at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, side, rep, myst, prize, culprit = f["detective"], f["sidekick"], f["reporter"], f["mystery"], f["prize"], f["culprit"]
    pos = det.pronoun("possessive")
    sub = det.pronoun("subject")
    obj = det.pronoun("object")
    qa = [
        QAItem(
            question=f"Who is the story about, and what did {sub} want to find?",
            answer=f"It is about a little {det.type} detective named {det.id}. "
                   f"{det.id} wanted to find {rep.id}'s missing {prize.label}."
        ),
        QAItem(
            question=f"What clue did {det.id} read on the chalkboard?",
            answer=f"{det.id} read a rhyme that said: \"{myst.rhyme_line}\"."
        ),
        QAItem(
            question=f"Who was the real culprit, and why did {sub} take the {prize.label}?",
            answer=f"The real culprit was a {culprit.type}. {culprit.pronoun('possessive').capitalize()} took only a tiny bite because {sub} was hungry."
        ),
        QAItem(
            question=f"How did {det.id} show kindness at the end?",
            answer=f"{det.id} shared a piece of the {prize.label} with the {culprit.type} and forgave {culprit.pronoun('object')}, because the {culprit.type} was hungry, not mean."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What did {rep.id} say about {det.id}'s detective work?",
            answer=f"{rep.id} said, 'You solved the mystery with kindness. That is the best kind of detective work.'"
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["mystery"].tags)
    keywords_to_include = {"cookie", "rhyme", "detective", "particular", "kindness", "squirrel", "magnifying glass"}
    tags_intersection = tags & keywords_to_include
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags_intersection or tag in {"rhyme", "detective", "particular", "kindness"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    # Always include rhyme, detective, particular, kindness as they are theme words
    for topic in ["rhyme", "detective", "particular", "kindness"]:
        if topic not in [item.split("?")[0] for item in out]:  # simple dedup
            pass
    return out


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.suspect_role:
            bits.append(f"role={e.suspect_role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  clues_found={world.clues_found}  culprit_found={world.culprit_found}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", mystery="cookies", prize="cookies", name="Pat", gender="girl", sidekick="dog", trait="particular"),
    StoryParams(place="playroom", mystery="toy", prize="toy", name="Arlo", gender="boy", sidekick="dog", trait="curious"),
    StoryParams(place="playroom", mystery="book", prize="book", name="Sam", gender="girl", sidekick="dog", trait="kind"),
]


def explain_rejection(mystery: Mystery, prize: Prize) -> str:
    if not mystery_is_reasonable(mystery, prize):
        return (f"(No story: mystery '{mystery.id}' expects a lost '{mystery.lost_item}', "
                f"but prize is '{prize.label}'. They must match.)")
    return "(No story: no detective tool can help solve this mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a particular detective solves a rhyming mystery with a kind twist. Unspecified choices are randomized.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=["dog", "cat"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos")
    ap.add_argument("--verify", action="store_true", help="check ASP parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.prize:
        myst = MYSTERIES[args.mystery]
        pr = PRIZES[args.prize]
        if not mystery_is_reasonable(myst, pr) or not select_tool(myst):
            raise StoryError(explain_rejection(myst, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(DETECTIVE_NAMES[gender])
    sidekick = args.sidekick or "dog"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, mystery=mystery_id, prize=prize_id,
        name=name, gender=gender, sidekick=sidekick, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], MYSTERIES[params.mystery], PRIZES[params.prize],
        params.name, params.gender, [params.trait, "kind"], params.sidekick, "grandma", "squirrel", "robin"
    )
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


ASP_RULES = r"""
% A mystery is reasonable when the missing item matches the prize.
reasonable(M, P) :- mystery(M), prize(P), missing_key(M, P).

% A tool is compatible if it guards that mystery.
can_solve(T, M) :- tool(T), guards(T, K), mystery(M), id(M, K).

% A story is valid when setting affords mystery, mystery matches prize, and a tool exists.
valid(Place, M, P) :- affords(Place, M), reasonable(M, P), can_solve(_, M).
"""


def asp_facts() -> str:
    import asp as _asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(_asp.fact("setting", pid))
        for m in sorted(s.affords):
            lines.append(_asp.fact("affords", pid, m))
    for mid, m in MYSTERIES.items():
        lines.append(_asp.fact("mystery", mid))
        lines.append(_asp.fact("missing_key", mid, m.lost_item))
        lines.append(_asp.fact("id", mid, mid))
        for r in sorted(m.zone):
            lines.append(_asp.fact("zone", mid, r))
    for pid, pr in PRIZES.items():
        lines.append(_asp.fact("prize", pid))
        lines.append(_asp.fact("missing_key", pid, pr.missing_key))
        if pr.plural:
            lines.append(_asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(_asp.fact("tool", g.id))
        for m in sorted(g.guards):
            lines.append(_asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid/3."))
    return sorted(set(_asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, mystery, prize) combos:\n")
        for place, myst, prize in triples:
            print(f"  {place:10} {myst:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: mystery '{p.mystery}' at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

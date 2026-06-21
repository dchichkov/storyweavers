#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py
==========================================================================

A tiny bedtime-story world about children who find strange black pieces of slag,
wonder where they came from, and solve the mystery with the help of an elder's
flashback. Every generated story ends safely and happily, with the mystery
genuinely resolved from world state rather than by swapping nouns in one fixed
paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py --place creek --site forge
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py --clue bottle
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/slag_happy_ending_flashback_mystery_to_solve.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# the import path by walking up two directories from the file's directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "grandma", "woman"}
        male = {"boy", "father", "grandfather", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    hiding_spot: str
    night_image: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Site:
    id: str
    label: str
    made: str
    worker: str
    flashback: str
    clue: str
    produces_slag: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hint: str
    site: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ElderConfig:
    id: str
    type: str
    style: str
    memory_intro: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    works: bool
    opening: str
    solve_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mystery(world: World) -> list[str]:
    child = world.get("child")
    slag = world.get("slag")
    clue = world.get("clue")
    if slag.meters["found"] < THRESHOLD or clue.meters["found"] < THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["puzzled"] += 1
    world.get("mystery").meters["open"] += 1
    return []


def _r_solved(world: World) -> list[str]:
    mystery = world.get("mystery")
    elder = world.get("elder")
    if mystery.meters["open"] < THRESHOLD or elder.meters["explained"] < THRESHOLD:
        return []
    sig = ("solved",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mystery.meters["open"] = 0.0
    mystery.meters["solved"] += 1
    child = world.get("child")
    helper = world.get("friend")
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="knowledge", apply=_r_mystery),
    Rule(name="solved", tag="knowledge", apply=_r_solved),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def clue_matches(site: Site, clue: Clue) -> bool:
    return site.id == clue.site


def place_supports(place: Place, site: Site) -> bool:
    return site.id in place.affords


def method_is_sensible(method: Method) -> bool:
    return method.sense >= SENSE_MIN and method.works


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for site_id, site in SITES.items():
            if not place_supports(place, site) or not site.produces_slag:
                continue
            for clue_id, clue in CLUES.items():
                if clue_matches(site, clue):
                    combos.append((place_id, site_id, clue_id))
    return combos


def predict_solution(place: Place, site: Site, clue: Clue, method: Method) -> bool:
    return place_supports(place, site) and clue_matches(site, clue) and method_is_sensible(method)


def discover(world: World, child: Entity, friend: Entity, place: Place) -> None:
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f"At the end of a soft day, {child.id} and {friend.id} walked through {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"Near {place.hiding_spot}, they found a few black, glassy lumps that winked in the last light."
    )
    world.say(
        f'"They look like little night stones," {friend.id} whispered, but {child.id} did not know what they were.'
    )
    world.get("slag").meters["found"] += 1
    propagate(world, narrate=False)


def inspect_clue(world: World, child: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    world.get("clue").meters["found"] += 1
    world.say(
        f"Beside the dark pieces lay {clue.phrase}. It was only a tiny thing, but it felt like a clue."
    )
    world.say(
        f"{child.id} turned it carefully in small fingers and noticed {clue.hint}."
    )
    propagate(world, narrate=False)


def wonder_about_it(world: World, child: Entity, friend: Entity) -> None:
    mystery = world.get("mystery")
    if mystery.meters["open"] >= THRESHOLD:
        world.say(
            f'"Where did this come from?" {child.id} asked. The question made the evening feel like a small mystery waiting to be solved.'
        )
        world.say(
            f"{friend.id} leaned close and made three guesses in a whisper: a dragon crumb, a burnt star, or treasure from under the roots."
        )


def ask_elder(world: World, child: Entity, friend: Entity, elder: Entity, method: Method) -> None:
    child.memes["trust"] += 1
    elder.memes["care"] += 1
    world.say(method.opening.format(child=child.id, friend=friend.id, elder=elder.label_word.capitalize()))
    world.say(
        f"{elder.label_word.capitalize()} sat down with them on the low stone wall and listened before answering."
    )


def flashback_and_explain(
    world: World,
    elder: Entity,
    elder_cfg: ElderConfig,
    site: Site,
    clue: Clue,
    method: Method,
) -> None:
    elder.meters["explained"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{elder_cfg.memory_intro} "{site.flashback}"'
    )
    world.say(
        f"{elder.label_word.capitalize()} smiled at {clue.label} and the black pieces. "
        f"{method.solve_text.format(site=site.label, made=site.made, worker=site.worker)}"
    )
    world.say(
        f'"These dark pieces are called slag," {elder.pronoun()} said softly. '
        f'"They are what can be left after very hot work is done."'
    )


def resolution(world: World, child: Entity, friend: Entity, place: Place, clue: Clue, site: Site) -> None:
    world.say(
        f"The strange pieces were not dragon crumbs after all. They were quiet leftovers from the old {site.label}, and the little {clue.label} had helped tell the truth."
    )
    world.say(
        f"{child.id} and {friend.id} placed the prettiest piece on a windowsill dish with a paper note that said where it came from."
    )
    world.say(
        f"Later, under blankets, {child.id} thought of {place.night_image} and felt glad that mysteries could turn into stories once kind people shared what they remembered."
    )


def tell(
    place: Place,
    site: Site,
    clue: Clue,
    elder_cfg: ElderConfig,
    method: Method,
    child_name: str = "Nora",
    child_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_cfg.type, label=elder_cfg.type, role="elder"))
    world.add(Entity(id="slag", type="slag", label="slag", phrase="black pieces of slag", tags={"slag"}))
    world.add(Entity(id="clue", type="clue", label=clue.label, phrase=clue.phrase, tags=set(clue.tags)))
    world.add(Entity(id="mystery", type="mystery", label="mystery"))

    discover(world, child, friend, place)
    inspect_clue(world, child, clue)

    world.para()
    wonder_about_it(world, child, friend)
    ask_elder(world, child, friend, elder, method)

    world.para()
    flashback_and_explain(world, elder, elder_cfg, site, clue, method)
    resolution(world, child, friend, place, clue, site)

    world.facts.update(
        place=place,
        site=site,
        clue_cfg=clue,
        elder_cfg=elder_cfg,
        method=method,
        child=child,
        friend=friend,
        elder=elder,
        solved=world.get("mystery").meters["solved"] >= THRESHOLD,
        clue_found=world.get("clue").meters["found"] >= THRESHOLD,
        slag_found=world.get("slag").meters["found"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the moonlit garden behind the house",
        opening="The mint leaves smelled cool, and the path still held a little warmth from the sun.",
        hiding_spot="the edge of the old flower bed",
        night_image="the moon shining on the garden path",
        affords={"forge", "glasshouse"},
    ),
    "creek": Place(
        id="creek",
        label="the little creek path",
        opening="Water ticked over stones, and the reeds nodded like sleepy heads.",
        hiding_spot="a bend in the bank where rain had washed the soil away",
        night_image="silver water slipping past the reeds",
        affords={"forge", "kiln"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard edge",
        opening="Fallen apples smelled sweet, and a late bird sang only once before going quiet.",
        hiding_spot="the roots of the oldest tree",
        night_image="round apples gleaming like dim lanterns",
        affords={"kiln", "glasshouse"},
    ),
}

SITES = {
    "forge": Site(
        id="forge",
        label="forge",
        made="horseshoes and little iron hooks",
        worker="the blacksmith",
        flashback="When I was small, the forge stood near here, and all afternoon we heard the ring of hammer on iron.",
        clue="horseshoe",
        produces_slag=True,
        tags={"forge", "metal"},
    ),
    "glasshouse": Site(
        id="glasshouse",
        label="glasshouse furnace",
        made="green bottles and little jars",
        worker="the glass maker",
        flashback="Long ago, a hot glasshouse furnace glowed near this ground, and people carried shining bottles out to cool in rows.",
        clue="bottle",
        produces_slag=True,
        tags={"glass", "furnace"},
    ),
    "kiln": Site(
        id="kiln",
        label="brick kiln",
        made="red bricks for cottages and chimneys",
        worker="the kiln keeper",
        flashback="Years ago, the brick kiln burned here, and the air smelled warm and earthy while rows of bricks dried in the sun.",
        clue="brick",
        produces_slag=True,
        tags={"brick", "kiln"},
    ),
    "bakery": Site(
        id="bakery",
        label="old bakery oven",
        made="bread and buns",
        worker="the baker",
        flashback="Once there was a bakery here, and the whole lane smelled like warm bread.",
        clue="spoon",
        produces_slag=False,
        tags={"bread"},
    ),
}

CLUES = {
    "horseshoe": Clue(
        id="horseshoe",
        label="bent horseshoe piece",
        phrase="a small bent piece from an old horseshoe",
        hint="a rusty curve with nail holes",
        site="forge",
        tags={"horseshoe", "forge"},
    ),
    "bottle": Clue(
        id="bottle",
        label="green bottle shard",
        phrase="a smooth green bottle shard",
        hint="how the edge caught the light like sleepy water",
        site="glasshouse",
        tags={"bottle", "glass"},
    ),
    "brick": Clue(
        id="brick",
        label="crumb of red brick",
        phrase="a crumb of very old red brick",
        hint="powdery red dust tucked in its corners",
        site="kiln",
        tags={"brick", "kiln"},
    ),
    "spoon": Clue(
        id="spoon",
        label="tiny spoon bowl",
        phrase="the bowl of a tiny old spoon",
        hint="a worn silver shine",
        site="bakery",
        tags={"spoon"},
    ),
}

ELDERS = {
    "grandma": ElderConfig(
        id="grandma",
        type="grandmother",
        style="gentle",
        memory_intro='Grandma folded her hands and said, "This place is older than it looks.',
        tags={"grandma", "memory"},
    ),
    "grandpa": ElderConfig(
        id="grandpa",
        type="grandfather",
        style="warm",
        memory_intro='Grandpa chuckled softly and said, "I remember this patch of ground from long ago.',
        tags={"grandpa", "memory"},
    ),
}

METHODS = {
    "ask_elder": Method(
        id="ask_elder",
        label="ask an elder",
        sense=3,
        works=True,
        opening='"Let us ask {elder}," said {child}. "{elder} remembers old things better than anyone."',
        solve_text="Years ago, this was the place of an old {site}, where {worker} made {made}.",
        qa_text="They asked an elder who remembered what used to stand there.",
        tags={"memory", "ask_adult"},
    ),
    "bring_box": Method(
        id="bring_box",
        label="carry a clue box",
        sense=2,
        works=True,
        opening='"We should take the pieces carefully to {elder}," said {friend}, and together they carried them in a little box.',
        solve_text="Looking closely, {elder} recognized the signs of the old {site}, where {worker} made {made}.",
        qa_text="They carried the clue pieces to an elder and looked at them together.",
        tags={"memory", "careful"},
    ),
    "guess_dragon": Method(
        id="guess_dragon",
        label="guess without checking",
        sense=1,
        works=False,
        opening='"{child} said it must be dragon treasure,"',
        solve_text="",
        qa_text="",
        tags={"guess"},
    ),
}


GIRL_NAMES = ["Nora", "Mila", "Ella", "Lucy", "Ivy", "Rose", "Maya", "Lena"]
BOY_NAMES = ["Ben", "Owen", "Max", "Theo", "Finn", "Sam", "Eli", "Noah"]


@dataclass
class StoryParams:
    place: str
    site: str
    clue: str
    elder: str
    method: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="garden",
        site="forge",
        clue="horseshoe",
        elder="grandma",
        method="ask_elder",
        child_name="Nora",
        child_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        seed=1,
    ),
    StoryParams(
        place="creek",
        site="kiln",
        clue="brick",
        elder="grandpa",
        method="bring_box",
        child_name="Mila",
        child_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        seed=2,
    ),
    StoryParams(
        place="orchard",
        site="glasshouse",
        clue="bottle",
        elder="grandma",
        method="ask_elder",
        child_name="Finn",
        child_gender="boy",
        friend_name="Rose",
        friend_gender="girl",
        seed=3,
    ),
]


KNOWLEDGE = {
    "slag": [
        (
            "What is slag?",
            "Slag is a hard, stony leftover that can be made when very hot fire is used to melt or heat materials. It is not treasure, but it can tell us about old work that happened long ago.",
        )
    ],
    "forge": [
        (
            "What is a forge?",
            "A forge is a very hot place where a blacksmith heats metal and shapes it with tools. People can make things like horseshoes and hooks there.",
        )
    ],
    "glass": [
        (
            "How is glass made hot enough to shape?",
            "Glass is heated in a very hot furnace until it softens. Then a glass maker can shape it into bottles or jars.",
        )
    ],
    "kiln": [
        (
            "What is a kiln?",
            "A kiln is a very hot oven used to bake things like bricks or pottery until they turn hard. It stays much hotter than an ordinary kitchen oven.",
        )
    ],
    "horseshoe": [
        (
            "What is a horseshoe?",
            "A horseshoe is a curved piece fixed to a horse's hoof to help protect it. Blacksmiths often make or fit them.",
        )
    ],
    "brick": [
        (
            "What are bricks made from?",
            "Bricks are usually made from clay that is shaped, dried, and baked very hot until it becomes hard. That is why old bricks can last a long time.",
        )
    ],
    "bottle": [
        (
            "Why can old glass shine in the light?",
            "Glass has a smooth surface, so it catches and reflects light. Even a small old shard can sparkle when you tilt it.",
        )
    ],
    "memory": [
        (
            "Why can an older person help solve a mystery?",
            "An older person may remember how a place used to be years ago. Their memory can connect today's clues to yesterday's story.",
        )
    ],
}
KNOWLEDGE_ORDER = ["slag", "forge", "glass", "kiln", "horseshoe", "brick", "bottle", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    site = f["site"]
    clue = f["clue_cfg"]
    elder = f["elder_cfg"]
    return [
        'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "slag", a mystery to solve, a flashback, and a happy ending.',
        f"Tell a sleepy mystery story where two children find strange black pieces in {place.label}, notice {clue.phrase}, and ask {elder.id} for help.",
        f"Write a story in which an elder's memory reveals that an old {site.label} once stood nearby, turning a puzzling discovery into a calm, happy bedtime ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    elder = f["elder"]
    place = f["place"]
    site = f["site"]
    clue = f["clue_cfg"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label} and {friend.label}, two children who found strange black pieces in {place.label}. It is also about {elder.label_word}, who helped them understand what they had found.",
        ),
        (
            "What made the children curious?",
            f"They found black, glassy pieces of slag and did not know what they were. Then they noticed {clue.phrase}, which made the discovery feel like a real mystery.",
        ),
        (
            f"How did they solve the mystery?",
            f"{method.qa_text} {elder.label_word.capitalize()} used a memory from long ago to explain what used to stand there. That flashback connected the clue to the old {site.label}.",
        ),
        (
            "What did the flashback explain?",
            f"The flashback explained that an old {site.label} once stood near that place, where {site.worker} made {site.made}. The slag was a leftover from that very hot work.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the children were no longer worried or confused. They understood the mystery and kept one pretty piece as a reminder of the old story hidden in the ground.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"slag", "memory"} | set(f["site"].tags) | set(f["clue_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Optional[Place], site: Optional[Site], clue: Optional[Clue], method: Optional[Method]) -> str:
    if method is not None and not method_is_sensible(method):
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"or does not really solve the mystery. Choose one that checks the clue with a remembering elder.)"
        )
    if site is not None and not site.produces_slag:
        return (
            f"(No story: an old {site.label} does not fit a slag mystery here, so the children would have no honest explanation for the black pieces.)"
        )
    if place is not None and site is not None and not place_supports(place, site):
        return (
            f"(No story: {place.label} does not fit an old {site.label} in this tiny world. Pick a site that belongs in that place.)"
        )
    if site is not None and clue is not None and not clue_matches(site, clue):
        return (
            f"(No story: {clue.label} points to a different past place, so it would not fairly solve a mystery about an old {site.label}.)"
        )
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
% --- world gate ------------------------------------------------------------
valid(Place, Site, Clue) :- place(Place), site(Site), clue(Clue),
                            affords(Place, Site), produces_slag(Site),
                            clue_for(Clue, Site).

sensible(Method) :- method(Method), sense(Method, S), sense_min(M), S >= M, works(Method).

% --- scenario solved-ness --------------------------------------------------
solved :- chosen_place(P), chosen_site(S), chosen_clue(C), chosen_method(M),
          affords(P, S), produces_slag(S), clue_for(C, S), sensible(M).

outcome(solved) :- solved.
outcome(rejected) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for site_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, site_id))
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        if site.produces_slag:
            lines.append(asp.fact("produces_slag", site_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_for", clue_id, clue.site))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.works:
            lines.append(asp.fact("works", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_site", params.site),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    site = SITES[params.site]
    clue = CLUES[params.clue]
    method = METHODS[params.method]
    return "solved" if predict_solution(place, site, clue, method) else "rejected"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_methods = {mid for mid, method in METHODS.items() if method_is_sensible(method)}
    asp_methods = set(asp_sensible_methods())
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({sorted(py_methods)}).")
    else:
        rc = 1
        print("MISMATCH in sensible methods:")
        print("  python:", sorted(py_methods))
        print("  asp   :", sorted(asp_methods))

    cases = list(CURATED)
    for seed in range(20):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random case generation for seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    smoke_cases = cases[:5]
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story during verify.")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime mystery storyworld about finding slag and solving where it came from."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = PLACES.get(args.place) if args.place else None
    site = SITES.get(args.site) if args.site else None
    clue = CLUES.get(args.clue) if args.clue else None
    method = METHODS.get(args.method) if args.method else None

    if args.method and method is not None and not method_is_sensible(method):
        raise StoryError(explain_rejection(place, site, clue, method))
    if args.site and site is not None and not site.produces_slag:
        raise StoryError(explain_rejection(place, site, clue, method))
    if args.place and args.site and place is not None and site is not None and not place_supports(place, site):
        raise StoryError(explain_rejection(place, site, clue, method))
    if args.site and args.clue and site is not None and clue is not None and not clue_matches(site, clue):
        raise StoryError(explain_rejection(place, site, clue, method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.site is None or combo[1] == args.site)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError(explain_rejection(place, site, clue, method))

    place_id, site_id, clue_id = rng.choice(sorted(combos))
    elder_id = args.elder or rng.choice(sorted(ELDERS))
    sensible = sorted(mid for mid, m in METHODS.items() if method_is_sensible(m))
    method_id = args.method or rng.choice(sensible)

    child_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if child_gender == "girl" else "girl" if rng.random() < 0.6 else child_gender
    child_name = pick_name(rng, child_gender)
    friend_name = pick_name(rng, friend_gender, avoid=child_name)

    return StoryParams(
        place=place_id,
        site=site_id,
        clue=clue_id,
        elder=elder_id,
        method=method_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    missing = [
        field_name
        for field_name, registry in [
            ("place", PLACES),
            ("site", SITES),
            ("clue", CLUES),
            ("elder", ELDERS),
            ("method", METHODS),
        ]
        if getattr(params, field_name) not in registry
    ]
    if missing:
        raise StoryError(f"(Invalid parameters: unknown keys for {', '.join(missing)}.)")

    place = PLACES[params.place]
    site = SITES[params.site]
    clue = CLUES[params.clue]
    elder_cfg = ELDERS[params.elder]
    method = METHODS[params.method]

    if not predict_solution(place, site, clue, method):
        raise StoryError(explain_rejection(place, site, clue, method))

    world = tell(
        place=place,
        site=site,
        clue=clue,
        elder_cfg=elder_cfg,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name).replace("friend", params.friend_name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} compatible (place, site, clue) combos:\n")
        for place, site, clue in combos:
            print(f"  {place:8} {site:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.friend_name}: {p.site} at {p.place} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py
=================================================================

A standalone story world for a child-facing rhyming suspense story built around
one small, concrete premise:

    At dusk, a child hears a small sob from a shadowy place.
    The sound is frightening at first because its source is hidden.
    The child speaks to a calm grown-up, they bring a light, discover a trapped
    little creature, and use the right simple tool to set it free.

The world model drives the prose:

* a trapped creature causes a hidden sobbing sound
* hearing the unseen sound raises fear and care
* bringing a light reveals the source
* the right rescue tool frees the creature
* freedom turns suspense into relief and a warm ending image

The script supports random sampling, pinned parameters, JSON/QA output, world
trace, and an inline ASP twin for the reasonableness gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py --trap drain --tool scarf_loop
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py --trap brambles --tool stool
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/sob_dialogue_suspense_rhyming_story.py --verify
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
# This file lives one level deeper than most worlds:
#   storyworlds/worlds/gpt-5.4/<this file>
# so we add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def adult_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    moon_line: str
    hiding_line: str
    echo_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    voice: str
    move: str
    thanks: str
    can_perch: bool = False
    can_fit_drain: bool = False
    can_tangle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    phrase: str
    clue: str
    needs: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


PLACES = {
    "garden": Place(
        "garden",
        "the garden behind the house",
        "The moon was a silver spoon above the garden soon.",
        "Tall beans and broad leaves made a whispery wall.",
        "leaf",
        tags={"garden", "night"},
    ),
    "shed": Place(
        "shed",
        "the little shed by the fence",
        "The moon made the shed look quiet and red.",
        "Rakes stood still in a shadowy row, and the corners kept secrets below.",
        "board",
        tags={"shed", "night"},
    ),
    "porch": Place(
        "porch",
        "the back porch steps",
        "The moon laid a pale thin stripe on the porch that night.",
        "Flowerpots huddled close, and the railing threw bars of shade.",
        "step",
        tags={"porch", "night"},
    ),
    "orchard": Place(
        "orchard",
        "the little orchard path",
        "The moon hung white where the apple leaves swayed in the night.",
        "Branches knitted a dim green roof over the narrow path.",
        "branch",
        tags={"orchard", "night"},
    ),
}

CREATURES = {
    "kitten": Creature(
        "kitten",
        "kitten",
        "a tiny gray kitten",
        "a thin little mew that sounded almost like a sob",
        "curled against the child's shoe",
        "The kitten gave one last mew, then began to purr.",
        can_perch=True,
        can_fit_drain=True,
        can_tangle=True,
        tags={"kitten", "pet"},
    ),
    "puppy": Creature(
        "puppy",
        "puppy",
        "a small spotted puppy",
        "a shaky little whine that sounded almost like a sob",
        "wobbled in a happy circle",
        "The puppy licked the grown-up's hand and stopped trembling.",
        can_perch=False,
        can_fit_drain=False,
        can_tangle=True,
        tags={"puppy", "pet"},
    ),
    "duckling": Creature(
        "duckling",
        "duckling",
        "a fluffy yellow duckling",
        "a peeping cry that sounded like a wet small sob",
        "tucked its beak beneath one wing for a blink",
        "The duckling shook its feathers and gave a bright peep.",
        can_perch=False,
        can_fit_drain=True,
        can_tangle=False,
        tags={"duckling", "bird"},
    ),
    "rabbit": Creature(
        "rabbit",
        "rabbit",
        "a little brown rabbit",
        "a soft thin squeak that sounded almost like a sob",
        "pressed close to the grass, then gave one careful hop",
        "The rabbit twitched its nose and breathed easy again.",
        can_perch=False,
        can_fit_drain=False,
        can_tangle=True,
        tags={"rabbit", "wild"},
    ),
}

TRAPS = {
    "brambles": Trap(
        "brambles",
        "brambles",
        "a nest of thorny brambles",
        "something rustled where the thorns were tight",
        "gloves",
        "caught in the brambles",
        tags={"brambles", "thorn"},
    ),
    "drain": Trap(
        "drain",
        "drain",
        "a narrow rain drain",
        "the sound came up from a dark little grate",
        "scarf_loop",
        "stuck in the rain drain",
        tags={"drain", "water"},
    ),
    "basket": Trap(
        "basket",
        "basket",
        "an upside-down garden basket",
        "a basket gave the grass a tiny wobble",
        "broom_lift",
        "hidden under an upside-down basket",
        tags={"basket"},
    ),
    "ledge": Trap(
        "ledge",
        "ledge",
        "a high shed ledge",
        "the sound slipped down from somewhere above",
        "stool",
        "stranded on a high ledge",
        tags={"ledge", "high"},
    ),
}

TOOLS = {
    "gloves": Tool(
        "gloves",
        "gloves",
        "a pair of garden gloves",
        "slipped on the gloves and gently parted the thorny stems",
        solves={"brambles"},
        tags={"gloves"},
    ),
    "scarf_loop": Tool(
        "scarf_loop",
        "scarf",
        "a soft scarf made into a loop",
        "lowered the scarf loop slowly and lifted with two steady hands",
        solves={"drain"},
        tags={"scarf"},
    ),
    "broom_lift": Tool(
        "broom_lift",
        "broom",
        "a broom handle",
        "tilted the basket up with the broom handle just enough to make a safe gap",
        solves={"basket"},
        tags={"broom"},
    ),
    "stool": Tool(
        "stool",
        "stool",
        "a small wooden stool",
        "set the stool by the wall and reached up carefully",
        solves={"ledge"},
        tags={"stool"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ella", "Tessa", "Ivy", "Poppy", "Ruth"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Owen", "Finn", "Miles", "Theo", "Jude"]
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]
CHILD_TRAITS = ["careful", "kind", "quiet", "curious", "gentle", "brave"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_hidden_sound(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    if creature.meters["trapped"] >= THRESHOLD and creature.meters["visible"] < THRESHOLD:
        sig = ("hidden_sound",)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["crying"] += 1
            child.memes["fear"] += 1
            child.memes["care"] += 1
            out.append("__sob__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    light = world.get("light")
    if creature.meters["trapped"] >= THRESHOLD and light.meters["on"] >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            creature.meters["visible"] += 1
            out.append("__reveal__")
    return out


def _r_free(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    tool = world.get("tool")
    trap = world.get("trap")
    if creature.meters["visible"] >= THRESHOLD and tool.meters["used"] >= THRESHOLD:
        if trap.id in tool.attrs.get("solves", set()):
            sig = ("free",)
            if sig not in world.fired:
                world.fired.add(sig)
                creature.meters["trapped"] = 0.0
                creature.meters["freed"] += 1
                out.append("__free__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    child = world.get("child")
    adult = world.get("adult")
    if creature.meters["freed"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0.0
            child.memes["relief"] += 1
            adult.memes["relief"] += 1
            creature.memes["calm"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("hidden_sound", "suspense", _r_hidden_sound),
    Rule("reveal", "perception", _r_reveal),
    Rule("free", "physical", _r_free),
    Rule("relief", "emotional", _r_relief),
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
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def creature_fits_trap(creature: Creature, trap: Trap) -> bool:
    if trap.id == "drain":
        return creature.can_fit_drain
    if trap.id == "ledge":
        return creature.can_perch
    if trap.id == "brambles":
        return creature.can_tangle
    if trap.id == "basket":
        return True
    return False


def tool_solves_trap(tool: Tool, trap: Trap) -> bool:
    return trap.id in tool.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for creature_id, creature in CREATURES.items():
            for trap_id, trap in TRAPS.items():
                if not creature_fits_trap(creature, trap):
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_solves_trap(tool, trap):
                        combos.append((place_id, creature_id, trap_id, tool_id))
    return combos


def explain_rejection(creature: Creature, trap: Trap, tool: Optional[Tool] = None) -> str:
    if not creature_fits_trap(creature, trap):
        return (
            f"(No story: {creature.phrase} would not plausibly be {trap.reveal}. "
            f"Pick a creature that fits that kind of trouble.)"
        )
    if tool is not None and not tool_solves_trap(tool, trap):
        need = TOOLS[trap.needs].phrase
        return (
            f"(No story: {tool.phrase} is not a sensible way to solve {trap.phrase}. "
            f"For this trap, the story needs {need}.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def begin_evening(world: World, child: Entity, adult: Entity, place: Place) -> None:
    trait = next((t for t in child.traits if t), "quiet")
    world.say(
        f"{place.moon_line} {child.id}, a {trait} little {child.type}, stayed near "
        f"{adult.adult_word} in {place.label}."
    )
    world.say(
        f"{place.hiding_line} The air felt hushed and deep, as if the dark had secrets to keep."
    )


def hear_sob(world: World, child: Entity, creature: Creature, trap: Trap) -> None:
    world.get("creature").meters["trapped"] += 1
    propagate(world, narrate=False)
    child.memes["wonder"] += 1
    world.say(
        f"Then from the dark came {creature.voice}. It trembled near {trap.phrase}, "
        f"and {child.id} stopped still from head to toe."
    )
    world.say(
        f'"Did you hear that sob?" whispered {child.id}. "It came from there... but I do not know."'
    )


def adult_answers(world: World, adult: Entity) -> None:
    adult.memes["calm"] += 1
    world.say(
        f'"I heard it too," said {adult.adult_word}, soft and low. '
        f'"We will go kindly, slow by slow."'
    )


def bring_light(world: World, adult: Entity, place: Place, trap: Trap) -> None:
    light = world.get("light")
    light.meters["on"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{adult.adult_word.capitalize()} clicked on the lantern. A gold round glow "
        f"slid over the {place.echo_word}, then found {trap.clue}."
    )


def reveal_creature(world: World, creature: Creature, trap: Trap) -> None:
    world.say(
        f"There in the shine was {creature.phrase}, {trap.reveal}. For one beat longer, "
        f"the child could only stare."
    )
    world.say(
        f'"Oh!" cried {world.get("child").id}. "It is only small... and scared, and all alone there."'
    )


def choose_help(world: World, child: Entity, adult: Entity, tool: Tool) -> None:
    child.memes["courage"] += 1
    world.say(
        f'"Can we help?" asked {child.id}. "{tool.phrase.capitalize()} might do." '
        f'"Yes," said {adult.adult_word}, "and I will help with you."'
    )


def rescue(world: World, tool: Tool, creature: Creature) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{world.get('adult').adult_word.capitalize()} {tool.action}. The child held the light, "
        f"still as a star in the night."
    )
    world.say(
        f"Out came {creature.phrase} at last, no longer hidden, no longer held fast."
    )


def comfort(world: World, child: Entity, creature: Creature) -> None:
    world.say(
        f'{child.id} bent down with a careful smile. "You are safe now. Rest a while."'
    )
    world.say(f"{creature.thanks} Then it {creature.move}.")


def ending(world: World, child: Entity, adult: Entity, place: Place, creature: Creature) -> None:
    child.memes["love"] += 1
    world.say(
        f"The night was not so scary then. {place.label.capitalize()} felt gentle once again."
    )
    world.say(
        f"{child.id} walked back beside {adult.adult_word}, lantern-light mild and small, "
        f"and no dark sound felt big at all."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    creature_cfg: Creature,
    trap_cfg: Trap,
    tool_cfg: Tool,
    child_name: str = "Lila",
    child_type: str = "girl",
    adult_type: str = "grandmother",
    trait: str = "careful",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child",
                             traits=[trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult",
                             label="the grown-up"))
    creature = world.add(Entity(id="creature", kind="thing", type=creature_cfg.id,
                                label=creature_cfg.label, role="creature"))
    trap = world.add(Entity(id="trap", kind="thing", type=trap_cfg.id,
                            label=trap_cfg.label, role="trap"))
    tool = world.add(Entity(id="tool", kind="thing", type=tool_cfg.id,
                            label=tool_cfg.label, role="tool",
                            attrs={"solves": set(tool_cfg.solves)}))
    light = world.add(Entity(id="light", kind="thing", type="lantern", label="lantern", role="light"))

    begin_evening(world, child, adult, place)

    world.para()
    hear_sob(world, child, creature_cfg, trap_cfg)
    adult_answers(world, adult)

    world.para()
    bring_light(world, adult, place, trap_cfg)
    reveal_creature(world, creature_cfg, trap_cfg)
    choose_help(world, child, adult, tool_cfg)

    world.para()
    rescue(world, tool_cfg, creature_cfg)
    comfort(world, child, creature_cfg)

    world.para()
    ending(world, child, adult, place, creature_cfg)

    world.facts.update(
        place=place,
        creature_cfg=creature_cfg,
        trap_cfg=trap_cfg,
        tool_cfg=tool_cfg,
        child=child,
        adult=adult,
        creature=creature,
        trap=trap,
        tool=tool,
        light=light,
        heard_sob=creature.meters["crying"] >= THRESHOLD,
        revealed=creature.meters["visible"] >= THRESHOLD,
        freed=creature.meters["freed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    creature: str
    trap: str
    tool: str
    child_name: str
    child_type: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "night": [
        ("Why can a sound feel scarier at night?",
         "At night it is harder to see where a sound comes from, so your mind can imagine something bigger than it really is. Light and a calm grown-up can make the mystery feel smaller.")
    ],
    "kitten": [
        ("Why might a kitten cry like a tiny sob?",
         "A kitten may cry when it is scared, stuck, or looking for help. Its small voice can sound sad and shaky.")
    ],
    "puppy": [
        ("Why might a puppy whine?",
         "A puppy can whine when it feels scared, lonely, or trapped. The sound is its way of asking for help.")
    ],
    "duckling": [
        ("Why does a duckling peep loudly when it is in trouble?",
         "A duckling peeps to call for help or to find safety. Little birds use sound when they are frightened.")
    ],
    "rabbit": [
        ("Why should you be gentle with a scared rabbit?",
         "A scared rabbit can panic very quickly. Quiet, gentle help keeps it from feeling even more afraid.")
    ],
    "brambles": [
        ("Why are brambles hard to reach into with bare hands?",
         "Brambles have sharp thorns that can scratch skin. Gloves help protect your hands while you work carefully.")
    ],
    "drain": [
        ("Why is a narrow drain tricky for a small animal?",
         "A narrow drain can be deep and slippery, so a little animal may not climb out easily. It often needs careful help.")
    ],
    "basket": [
        ("Why can an upside-down basket trap a small animal?",
         "An upside-down basket blocks the way out and can feel dark and frightening underneath. A small gap can let the animal slip free.")
    ],
    "ledge": [
        ("Why is a high ledge a problem for a tiny animal?",
         "A tiny animal on a high ledge may be too scared to jump down. Reaching safely from a stool can help.")
    ],
    "gloves": [
        ("What are garden gloves for?",
         "Garden gloves protect your hands from scratches and rough stems. They help grown-ups handle thorny plants more safely.")
    ],
    "scarf": [
        ("How can a soft loop help in a rescue?",
         "A soft loop can give a small animal something gentle to rest in while it is lifted. It works slowly and carefully, not roughly.")
    ],
    "broom": [
        ("How can a broom help without poking an animal?",
         "A broom handle can lift or tip something nearby from a little distance. Used gently, it can make space without grabbing the animal.")
    ],
    "stool": [
        ("Why is a stool useful for reaching high places?",
         "A stool lets a grown-up reach safely without stretching too far. It makes a careful rescue easier.")
    ],
}
KNOWLEDGE_ORDER = [
    "night", "kitten", "puppy", "duckling", "rabbit",
    "brambles", "drain", "basket", "ledge",
    "gloves", "scarf", "broom", "stool",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    creature = f["creature_cfg"]
    trap = f["trap_cfg"]
    place = f["place"]
    return [
        'Write a rhyming story for a 3-to-5-year-old that includes the word "sob", uses dialogue, and begins with a mysterious sound in the dark.',
        f"Tell a gentle suspense story where {child.id} hears something like a sob in {place.label} and whispers to a grown-up before discovering {creature.phrase}.",
        f"Write a child-facing rhyming story with dialogue, a hidden sound, and a kind rescue from {trap.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    creature = f["creature_cfg"]
    trap = f["trap_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {child.id}, a little {child.type}, and {adult.adult_word} walking in {place.label}. They also find {creature.phrase} hidden in trouble."),
        ("What made the story feel suspenseful at first?",
         f"{child.id} heard a small sound like a sob before anyone could see what made it. The darkness and the hidden place made the sound feel mysterious."),
        (f"What did {child.id} say when the sound came?",
         f'{child.id} whispered, "Did you hear that sob?" That line shows {child.pronoun("subject")} was startled and trying to understand the sound.'),
        ("What was making the sob-like sound?",
         f"The sound came from {creature.phrase}. It was crying because it was {trap.reveal}."),
        ("How did they find out what was there?",
         f"{adult.adult_word.capitalize()} turned on a lantern and shone the light toward the sound. Once the hidden place lit up, they could finally see the trapped creature."),
        ("How did they help?",
         f"They used {tool.phrase} to rescue the little animal. That tool matched the problem, so the creature could come out safely."),
        ("How did the story end?",
         f"The frightening mystery turned into relief. The creature was free, and {child.id} walked back beside {adult.adult_word} feeling calm instead of scared."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["place"].tags) | set(f["creature_cfg"].tags) | set(f["trap_cfg"].tags) | set(f["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {}
            for k, v in e.attrs.items():
                shown[k] = sorted(v) if isinstance(v, set) else v
            bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(C, drain)    :- creature(C), can_fit_drain(C).
fits(C, ledge)    :- creature(C), can_perch(C).
fits(C, brambles) :- creature(C), can_tangle(C).
fits(C, basket)   :- creature(C).

solves(Tool, Trap) :- tool(Tool), trap(Trap), tool_solve(Tool, Trap).

valid(P, C, Trap, Tool) :- place(P), creature(C), trap(Trap), tool(Tool),
                           fits(C, Trap), solves(Tool, Trap).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for cid, c in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        if c.can_fit_drain:
            lines.append(asp.fact("can_fit_drain", cid))
        if c.can_perch:
            lines.append(asp.fact("can_perch", cid))
        if c.can_tangle:
            lines.append(asp.fact("can_tangle", cid))
    for tid in TRAPS:
        lines.append(asp.fact("trap", tid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for trap_id in sorted(tool.solves):
            lines.append(asp.fact("tool_solve", tool_id, trap_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test generated incomplete QA data.")
        print("OK: random generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("garden", "kitten", "drain", "scarf_loop", "Lila", "girl", "grandmother", "careful"),
    StoryParams("shed", "puppy", "basket", "broom_lift", "Ben", "boy", "father", "kind"),
    StoryParams("orchard", "rabbit", "brambles", "gloves", "Nora", "girl", "grandfather", "gentle"),
    StoryParams("porch", "kitten", "ledge", "stool", "Leo", "boy", "mother", "curious"),
]


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming suspense story world: a hidden sob in the dark becomes a kind rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("--trait", choices=CHILD_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, child_type: Optional[str], name: Optional[str]) -> tuple[str, str]:
    picked_type = child_type or rng.choice(["girl", "boy"])
    if name:
        return name, picked_type
    pool = GIRL_NAMES if picked_type == "girl" else BOY_NAMES
    return rng.choice(pool), picked_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.trap:
        creature = CREATURES[args.creature]
        trap = TRAPS[args.trap]
        if not creature_fits_trap(creature, trap):
            raise StoryError(explain_rejection(creature, trap))
    if args.trap and args.tool:
        trap = TRAPS[args.trap]
        tool = TOOLS[args.tool]
        creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        if not tool_solves_trap(tool, trap):
            raise StoryError(explain_rejection(creature, trap, tool))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.creature is None or c[1] == args.creature)
        and (args.trap is None or c[2] == args.trap)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, trap_id, tool_id = rng.choice(sorted(combos))
    child_name, child_type = _pick_child(rng, args.child_type, args.child_name)
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    trait = args.trait or rng.choice(CHILD_TRAITS)

    return StoryParams(
        place=place_id,
        creature=creature_id,
        trap=trap_id,
        tool=tool_id,
        child_name=child_name,
        child_type=child_type,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        CREATURES[params.creature],
        TRAPS[params.trap],
        TOOLS[params.tool],
        child_name=params.child_name,
        child_type=params.child_type,
        adult_type=params.adult_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, trap, tool) combos:\n")
        for place, creature, trap, tool in combos:
            print(f"  {place:8} {creature:8} {trap:9} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
            header = f"### {p.child_name}: {p.creature} in {p.trap} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

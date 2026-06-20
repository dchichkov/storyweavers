#!/usr/bin/env python3
"""
storyworlds/worlds/sparkly_river_dusty_cave_sound.py
====================================================

A standalone story world sketch for a TinyStories-style fairy tale: a child
follows the sounds of a sparkly river into a dusty cave, gets turned around, and
must use sound carefully to find the way back.

The constraint is about sound, not bravery. The river must be loud enough to
reach the cave, and the child's chosen signal must be gentle enough for the
dusty cave. A loud tool is known to the registry but refused: in this world, a
careless noise shakes dust down and makes the echoes confusing instead of useful.
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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class RiverVoice:
    id: str
    phrase: str
    bank: str
    sound: str
    carried_words: str
    carry: int
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cave:
    id: str
    phrase: str
    mouth: str
    inside: str
    dust: int
    depth: int
    stability: int
    echo: int
    fairy_mark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundTool:
    id: str
    label: str
    try_text: str
    careful_text: str
    sound: str
    force: int
    needs_echo: bool
    lesson: str
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


def _r_dust_blurs_path(world: World) -> list[str]:
    hero = world.entities.get("hero")
    cave = world.entities.get("cave")
    if not hero or not cave:
        return []
    if hero.meters["inside_cave"] < THRESHOLD or cave.meters["dust"] < THRESHOLD:
        return []
    sig = ("trail_lost", hero.id, cave.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    cave.meters["trail_blurred"] += 1
    return ["__trail_lost__"]


def _r_loud_sound_confuses(world: World) -> list[str]:
    cave = world.entities.get("cave")
    hero = world.entities.get("hero")
    if not cave or not hero:
        return []
    if cave.meters["sound_force"] <= cave.meters["stability"]:
        return []
    sig = ("dust_fall", cave.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cave.meters["dust_fall"] += 1
    hero.memes["worry"] += 1
    return ["__dust_fall__"]


def _r_soft_echo_guides(world: World) -> list[str]:
    cave = world.entities.get("cave")
    river = world.entities.get("river")
    hero = world.entities.get("hero")
    if not cave or not river or not hero:
        return []
    if hero.meters["careful_signal"] < THRESHOLD:
        return []
    if cave.meters["dust_fall"] >= THRESHOLD:
        return []
    if river.meters["audible"] < THRESHOLD:
        return []
    sig = ("echo_path", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cave.meters["echo_path"] += 1
    hero.memes["calm"] += 1
    return ["__echo_path__"]


CAUSAL_RULES: list[Rule] = [
    Rule("dust_blurs_path", "physical", _r_dust_blurs_path),
    Rule("loud_sound_confuses", "physical", _r_loud_sound_confuses),
    Rule("soft_echo_guides", "sound", _r_soft_echo_guides),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def river_reaches_cave(river: RiverVoice, cave: Cave) -> bool:
    return river.carry >= cave.depth


def signal_is_safe(tool: SoundTool, cave: Cave) -> bool:
    return tool.force <= cave.stability


def signal_can_guide(tool: SoundTool, river: RiverVoice, cave: Cave) -> bool:
    if not river_reaches_cave(river, cave):
        return False
    return not tool.needs_echo or cave.echo >= 1


def valid_combo(river: RiverVoice, cave: Cave, tool: SoundTool) -> bool:
    return (river_reaches_cave(river, cave)
            and signal_is_safe(tool, cave)
            and signal_can_guide(tool, river, cave))


def _do_signal(world: World, tool: SoundTool, narrate: bool = True) -> None:
    cave = world.get("cave")
    hero = world.get("hero")
    cave.meters["sound_force"] += tool.force
    if signal_is_safe(tool, CAVES[cave.attrs["cave_id"]]):
        hero.meters["careful_signal"] += 1
    propagate(world, narrate=narrate)


def predict_signal(world: World, river: RiverVoice, cave: Cave,
                   tool: SoundTool) -> dict:
    sim = world.copy()
    _do_signal(sim, tool, narrate=False)
    return {
        "safe": sim.get("cave").meters["dust_fall"] < THRESHOLD,
        "guides": sim.get("cave").meters["echo_path"] >= THRESHOLD,
        "river_audible": river_reaches_cave(river, cave),
    }


def introduce(world: World, hero: Entity, river: RiverVoice) -> None:
    trait = next((t for t in hero.traits if t), "curious")
    world.say(
        f"Once upon a time, there was a little {trait} {hero.type} named "
        f"{hero.id} who loved bright water and tiny sounds."
    )
    world.say(
        f"One morning {hero.pronoun()} found {river.phrase} beside "
        f"{river.bank}. It glittered {river.sparkle} and sang, "
        f'"{river.sound}."'
    )


def follow_river(world: World, hero: Entity, river: RiverVoice,
                 cave: Cave) -> None:
    hero.memes["wonder"] += 1
    river_ent = world.get("river")
    river_ent.meters["audible"] = 1.0 if river_reaches_cave(river, cave) else 0.0
    words = river.carried_words.strip('"')
    world.say(
        f'The sound seemed to say, "{words}." So {hero.id} '
        f"followed it along the stones."
    )
    world.say(
        f"The path led to {cave.phrase}, where {cave.mouth}. "
        f"A mark like {cave.fairy_mark} shone near the door."
    )


def enter_cave(world: World, hero: Entity, cave: Cave, river: RiverVoice) -> None:
    cave_ent = world.get("cave")
    cave_ent.meters["dust"] = float(cave.dust)
    cave_ent.meters["stability"] = float(cave.stability)
    hero.meters["inside_cave"] += 1
    world.say(
        f"Inside, {cave.inside}. The river still whispered behind "
        f"{hero.pronoun('object')}, faint but real."
    )
    propagate(world, narrate=False)
    if cave_ent.meters["trail_blurred"] >= THRESHOLD:
        world.say(
            f"When {hero.id} turned around, {hero.pronoun('possessive')} "
            f"footprints had softened into dusty smudges."
        )
    world.say(
        f"Three dark cracks in the stone all looked like the way back, and "
        f"{hero.pronoun()} felt {hero.pronoun('possessive')} tummy grow small."
    )
    world.facts["lost"] = True


def almost_loud(world: World, hero: Entity, cave: Cave) -> None:
    if cave.stability <= 2:
        warning = "a loose sprinkle of dust slid from the roof before any word came out"
    else:
        warning = "the cave seemed to hold its breath, waiting to see if the sound would be gentle"
    world.say(
        f"{hero.id} almost shouted for help. Then {hero.pronoun()} noticed "
        f"what loud sound might do: {warning}."
    )


def use_careful_sound(world: World, hero: Entity, river: RiverVoice,
                      cave: Cave, tool: SoundTool) -> None:
    pred = predict_signal(world, river, cave, tool)
    if not (pred["safe"] and pred["guides"]):
        return
    world.facts["predicted_safe"] = True
    world.say(
        f"So {hero.id} made a careful plan. {hero.pronoun().capitalize()} "
        f"{tool.careful_text}, just enough to ask the cave a question: "
        f'"{tool.sound}."'
    )
    _do_signal(world, tool, narrate=False)
    world.say(
        f"The cave answered softly. One echo came back dusty and flat, but one "
        f"echo carried the river's sparkle in it."
    )
    hero.memes["trust"] += 1
    world.facts["used_sound"] = True


def return_home(world: World, hero: Entity, river: RiverVoice,
                cave: Cave, tool: SoundTool) -> None:
    cave_ent = world.get("cave")
    if cave_ent.meters["echo_path"] < THRESHOLD:
        return
    hero.meters["inside_cave"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} walked toward that bright little answer. Step by step, "
        f"{hero.pronoun()} paused, listened, and kept the sound small."
    )
    world.say(
        f"At last the cave opened around {hero.pronoun('object')}, and "
        f"daylight flashed on the river."
    )
    world.say(
        f"{hero.id} touched the fairy mark by the doorway with one dusty hand. "
        f"{hero.pronoun().capitalize()} had learned {tool.lesson}, and the "
        f'river went on singing "{river.sound}" as if a tiny fairy were '
        f"polishing every ripple."
    )
    world.facts["outcome"] = "home"


def tell(river: RiverVoice, cave: Cave, tool: SoundTool,
         name: str = "Lily", gender: str = "girl",
         trait: str = "curious") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=gender, label=name,
                            traits=[trait], role="seeker"))
    hero.id = name
    world.entities["hero"] = hero
    world.add(Entity("river", type="river", label=river.phrase,
                     attrs={"river_id": river.id}))
    world.add(Entity("cave", type="cave", label=cave.phrase,
                     attrs={"cave_id": cave.id}))

    introduce(world, hero, river)
    follow_river(world, hero, river, cave)

    world.para()
    enter_cave(world, hero, cave, river)
    almost_loud(world, hero, cave)

    world.para()
    use_careful_sound(world, hero, river, cave, tool)
    return_home(world, hero, river, cave, tool)

    world.facts.update(hero=hero, river=river, cave=cave, tool=tool,
                       cave_ent=world.get("cave"),
                       river_ent=world.get("river"))
    return world


RIVERS = {
    "sparkly": RiverVoice(
        "sparkly", "a sparkly river", "a willow bank", "plink, plink, hush",
        '"come closer, but listen well"', 3, "like spilled stars",
        tags={"river", "sparkly", "sound"}),
    "silver": RiverVoice(
        "silver", "a sparkly river with a silver voice", "the ferny bank", "ting, ting, shhh",
        '"follow the silver song"', 2, "like moon buttons",
        tags={"river", "sound"}),
    "laughing": RiverVoice(
        "laughing", "a sparkly river that laughed", "a mossy bank", "ha-ha, lap-lap",
        '"this way to the hidden cool"', 4, "in quick bright flecks",
        tags={"river", "sound"}),
}

CAVES = {
    "dusty": Cave(
        "dusty", "a dusty cave", "dry vines curled around a low stone mouth",
        "dust lay soft as flour on the floor, and old crystals blinked from the walls",
        dust=2, depth=2, stability=2, echo=1,
        fairy_mark="a blue fairy thumbprint",
        tags={"cave", "dust", "echo"}),
    "deep_dusty": Cave(
        "deep_dusty", "a dusty cave that dipped deep", "the opening dipped under a root like a secret door",
        "the air smelled of chalk, and the walls folded the sound into long tunnels",
        dust=2, depth=3, stability=2, echo=1,
        fairy_mark="a silver leaf",
        tags={"cave", "dust", "echo"}),
    "crystal": Cave(
        "crystal", "a dusty cave with crystal walls", "small clear stones framed the doorway",
        "pale crystals made the dark look gentle, but dust still hid the floor",
        dust=1, depth=2, stability=3, echo=1,
        fairy_mark="a star no bigger than a pea",
        tags={"cave", "dust", "echo", "crystal"}),
    "muffling": Cave(
        "muffling", "a dusty cave with muffling moss", "black moss hung over the mouth like a curtain",
        "the walls drank sounds quickly, and the dust sat thick in every corner",
        dust=2, depth=4, stability=1, echo=0,
        fairy_mark="a faded gray curl",
        tags={"cave", "dust"}),
}

TOOLS = {
    "pebble_taps": SoundTool(
        "pebble_taps", "two smooth pebbles",
        "tapped two smooth pebbles together",
        "tapped two smooth pebbles together near the wall",
        "tik, tik", force=1, needs_echo=True,
        lesson="that small sounds can be brave when they are careful",
        tags={"sound", "echo", "pebble"}),
    "soft_song": SoundTool(
        "soft_song", "a soft song",
        "sang a tiny song",
        "sang the river tune under one breath",
        "la-la, hush", force=1, needs_echo=False,
        lesson="that listening is part of finding the way",
        tags={"sound", "song"}),
    "cupped_hands": SoundTool(
        "cupped_hands", "cupped hands",
        "called through cupped hands",
        "cupped both hands and made one little owl note",
        "hoo, hoo", force=2, needs_echo=True,
        lesson="that a careful call can point home without shaking the cave",
        tags={"sound", "echo"}),
    "shout": SoundTool(
        "shout", "a big shout",
        "shouted as loudly as possible",
        "shouted as loudly as possible",
        "HEY!", force=4, needs_echo=False,
        lesson="that loud is not always helpful",
        tags={"sound", "loud"}),
    "tin_drum": SoundTool(
        "tin_drum", "a tin drum",
        "banged a tin drum",
        "banged a tin drum",
        "BANG, BANG", force=5, needs_echo=True,
        lesson="that noise is not the same as guidance",
        tags={"sound", "loud", "echo"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["curious", "gentle", "thoughtful", "bright-eyed", "careful", "wondering"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid, river in RIVERS.items():
        for cid, cave in CAVES.items():
            for tid, tool in TOOLS.items():
                if valid_combo(river, cave, tool):
                    combos.append((rid, cid, tid))
    return combos


@dataclass
class StoryParams:
    river: str
    cave: str
    tool: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "river": [("Why can a river make sound?",
               "A river makes sound when water moves over stones, roots, and little drops in its path. The moving water can splash, tap, and whisper.")],
    "sparkly": [("Why can a river look sparkly?",
                 "A river looks sparkly when sunlight bounces off moving water. Each ripple catches the light for a tiny moment.")],
    "cave": [("What is a cave?",
              "A cave is a hollow place inside rock or earth. Some caves are dark, cool, and echo when sounds bounce off the walls.")],
    "dust": [("Why was the cave dusty?",
              "Dust can settle in quiet places where not many feet or winds move through. In the story, the dust is light enough to cover footprints.")],
    "echo": [("What is an echo?",
              "An echo is a sound that bounces back after it hits something hard, like a cave wall. You hear the sound again a little later.")],
    "sound": [("Why did the child use sound to get back?",
               "Sound could travel where the child could not see. By listening to the river and the echoes, the child could tell which tunnel led home.")],
    "song": [("Can a soft song help someone listen?",
              "Yes. A soft song can give your ears a pattern to follow, and it does not shake loose dust the way a shout might.")],
    "pebble": [("Why did the pebble taps help?",
                "The pebble taps made small clear sounds that bounced from the cave wall. The useful echo pointed toward the river side of the cave.")],
}
KNOWLEDGE_ORDER = ["river", "sparkly", "cave", "dust", "echo", "sound", "song", "pebble"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, river, cave, tool = f["hero"], f["river"], f["cave"], f["tool"]
    return [
        f'Write a TinyStories-style fairy tale for a child where {hero.id} follows '
        f'{river.phrase} into {cave.phrase} and uses sound effects to find the way back.',
        f'Tell a concrete, child-facing story using the seed words "sparkly river" '
        f'and "dusty cave"; the ending should show that careful sound guides the child home.',
        f"Write a gentle adventure where a little {hero.type} gets turned around in a cave, "
        f"chooses {tool.label} instead of loud noise, and follows the river sound out.",
    ]


def qa_tool_action(tool: SoundTool) -> str:
    return {
        "pebble_taps": "tapped them gently near the wall",
        "soft_song": "sang the river tune under one breath",
        "cupped_hands": "made one little owl note through them",
    }.get(tool.id, tool.careful_text)


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, river, cave, tool = f["hero"], f["river"], f["cave"], f["tool"]
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    pos = hero.pronoun("possessive")
    qa = [
        ("Who is the story about?",
         f"The story is about a little {hero.type} named {hero.id}. {hero.id} follows the sound of {river.phrase} into {cave.phrase}."),
        (f"Why did {hero.id} go into the cave?",
         f"{hero.id} followed the river because it sounded as if it was calling {obj} along the stones. The fairy-like mark at the cave made the place feel magical and worth a careful look."),
        (f"What problem did {hero.id} have inside the cave?",
         f"{hero.id}'s footprints blurred in the dust, and three dark cracks all looked like the way back. That made {obj} feel worried because sight was no longer enough."),
        (f"Why did {hero.id} avoid shouting?",
         f"{hero.id} noticed that a loud sound might shake dust down and confuse the echoes. {sub.capitalize()} needed a sound small enough for the cave to answer clearly."),
        (f"How did {hero.id} find the way back?",
         f"{hero.id} used {tool.label} and {qa_tool_action(tool)}. One echo carried the river's sparkle, so {sub} followed that sound toward daylight."),
        ("What changed by the end?",
         f"{hero.id} was back beside the river and was not afraid of the cave anymore. {sub.capitalize()} had learned that careful listening can be braver than a big noise."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["river"].tags) | set(f["cave"].tags) | set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sparkly", "dusty", "pebble_taps", "Lily", "girl", "curious"),
    StoryParams("silver", "dusty", "soft_song", "Theo", "boy", "gentle"),
    StoryParams("laughing", "deep_dusty", "cupped_hands", "Mia", "girl", "careful"),
    StoryParams("sparkly", "crystal", "soft_song", "Finn", "boy", "thoughtful"),
    StoryParams("laughing", "crystal", "pebble_taps", "Nora", "girl", "wondering"),
]


def explain_rejection(river: RiverVoice, cave: Cave, tool: SoundTool) -> str:
    if not river_reaches_cave(river, cave):
        return (f"(No story: {river.phrase} is not loud enough to reach "
                f"{cave.phrase}. The child needs a real sound to follow back.)")
    if not signal_is_safe(tool, cave):
        return (f"(No story: {tool.label} is too loud for {cave.phrase}. "
                f"In this world, careless sound shakes down dust and hides the way.)")
    if tool.needs_echo and cave.echo < 1:
        return (f"(No story: {tool.label} needs a clear echo, but {cave.phrase} "
                f"muffles echoes. The sound could not point the way home.)")
    return "(No story: this river, cave, and sound do not make a grounded path home.)"


ASP_RULES = r"""
river_reaches(R, C) :- carry(R, CR), depth(C, D), CR >= D.
has_echo(C)         :- echo(C, E), E >= 1.
safe_signal(T, C)   :- force(T, F), stability(C, S), F <= S.

guides(T, R, C) :- tool(T), river_reaches(R, C), not needs_echo(T).
guides(T, R, C) :- tool(T), needs_echo(T), has_echo(C), river_reaches(R, C).

valid(R, C, T) :- river(R), cave(C), tool(T),
                  river_reaches(R, C), safe_signal(T, C), guides(T, R, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, river in RIVERS.items():
        lines.append(asp.fact("river", rid))
        lines.append(asp.fact("carry", rid, river.carry))
    for cid, cave in CAVES.items():
        lines.append(asp.fact("cave", cid))
        lines.append(asp.fact("depth", cid, cave.depth))
        lines.append(asp.fact("stability", cid, cave.stability))
        lines.append(asp.fact("echo", cid, cave.echo))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("force", tid, tool.force))
        if tool.needs_echo:
            lines.append(asp.fact("needs_echo", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child follows river sounds into a dusty cave "
                    "and uses careful sound to find the way back.")
    ap.add_argument("--river", choices=RIVERS)
    ap.add_argument("--cave", choices=CAVES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.river and args.cave and args.tool:
        river, cave, tool = RIVERS[args.river], CAVES[args.cave], TOOLS[args.tool]
        if not valid_combo(river, cave, tool):
            raise StoryError(explain_rejection(river, cave, tool))

    combos = [c for c in valid_combos()
              if (args.river is None or c[0] == args.river)
              and (args.cave is None or c[1] == args.cave)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        if args.river and args.cave and args.tool:
            raise StoryError(explain_rejection(RIVERS[args.river], CAVES[args.cave],
                                               TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    river, cave, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(names)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(river, cave, tool, name, gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(RIVERS[params.river], CAVES[params.cave], TOOLS[params.tool],
                 params.name, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (river, cave, tool) combos:\n")
        for river, cave, tool in combos:
            print(f"  {river:9} {cave:11} {tool}")
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

    for idx, sample in enumerate(samples, 1):
        header = f"=== Story {idx} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()


if __name__ == "__main__":
    main()

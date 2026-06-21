#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mesh_accordion_alphabet_sound_effects_repetition_bedtime.py
=======================================================================================

A standalone storyworld for a tiny bedtime domain built from the seed words
"mesh", "accordion", and "alphabet".

Premise
-------
A small child is almost asleep when a soft night sound begins: hush-hiss,
tap-tap, swish-swish. The sound comes from some ordinary thing made of or hung
on mesh. The child grows worried in the dark. A calm grown-up looks, fixes the
real cause in a sensible way, and then slows the room down with an accordion
alphabet book. The letters become a repeating bedtime rhythm instead of one more
busy thing to think about.

This world models:
- physical state with meters (rattling, moving, secured, room_noise)
- emotional state with memes (fear, relief, love, sleepiness, curiosity)
- a reasonableness gate over which response fits which source
- a small inline ASP twin that mirrors the Python gate and outcome logic

Every generated story includes the words:
- mesh
- accordion
- alphabet

and uses gentle sound effects and repetition in a bedtime style.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    location: str
    sound: str
    repeat: str
    cause: str
    fix_by: str
    response_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    action: str
    handles: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Ritual:
    id: str
    label: str
    first_line: str
    repeat_line: str
    ending_image: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    room = world.get("room")
    if source.meters["rattling"] >= THRESHOLD:
        sig = ("noise", "source")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["room_noise"] += 1
            child.memes["fear"] += 1
            out.append("__noise__")
    return out


def _r_secure_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    room = world.get("room")
    if source.meters["secured"] >= THRESHOLD:
        sig = ("relief", "secured")
        if sig not in world.fired:
            world.fired.add(sig)
            source.meters["rattling"] = 0.0
            room.meters["room_noise"] = 0.0
            child.memes["relief"] += 1
            if child.memes["fear"] > 0:
                child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
            out.append("__quiet__")
    return out


def _r_ritual_sleep(world: World) -> list[str]:
    out: list[str] = []
    book = world.get("book")
    child = world.get("child")
    parent = world.get("parent")
    if book.meters["open"] >= THRESHOLD and book.meters["reading"] >= THRESHOLD:
        sig = ("sleep", "ritual")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["sleepiness"] += 2
            child.memes["love"] += 1
            parent.memes["love"] += 1
            child.memes["curiosity"] += 1
            out.append("__sleepy__")
    return out


CAUSAL_RULES = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="secure_relief", tag="physical", apply=_r_secure_relief),
    Rule(name="ritual_sleep", tag="emotional", apply=_r_ritual_sleep),
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
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


def response_fits(source: Source, response: Response) -> bool:
    return source.fix_by in response.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, source in SOURCES.items():
        for rid, response in RESPONSES.items():
            if not response_fits(source, response):
                continue
            for tid in RITUALS:
                combos.append((sid, rid, tid))
    return combos


def predict_unfixed(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["rattling"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "room_noise": sim.get("room").meters["room_noise"],
    }


def predict_fixed(world: World, response: Response) -> dict:
    sim = world.copy()
    if response_fits(SOURCES[sim.facts["source_cfg"].id], response):
        sim.get("source").meters["secured"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "room_noise": sim.get("room").meters["room_noise"],
    }


def introduce(world: World, child: Entity, parent: Entity) -> None:
    book = world.get("book")
    pocket = world.get("pocket")
    toy = child.attrs.get("comfort")
    extra = f" Beside the bed hung {pocket.phrase}." if pocket.phrase else ""
    world.say(
        f"It was bedtime, and {child.id}'s room had gone soft and dim. "
        f"On the blanket lay {book.phrase}, and its pages folded out like a tiny accordion.{extra}"
    )
    if toy:
        world.say(f"{child.id} tucked {toy} under one arm while {parent.label_word} kissed {child.pronoun('possessive')} forehead.")
    else:
        world.say(f"{parent.label_word.capitalize()} tucked the blanket around {child.id} and smoothed one sleepy corner.")


def first_letters(world: World, child: Entity, ritual: Ritual) -> None:
    child.memes["calm"] += 1
    world.say(ritual.first_line)
    world.say(ritual.repeat_line)


def start_sound(world: World, source_cfg: Source) -> None:
    source = world.get("source")
    source.meters["rattling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {source_cfg.location}, came a little sound: "
        f'"{source_cfg.sound}... {source_cfg.repeat}... {source_cfg.sound}..."'
    )
    world.say(
        f"The {source_cfg.label} had begun to move because {source_cfg.cause}."
    )


def worry(world: World, child: Entity, source_cfg: Source) -> None:
    child.memes["worry"] += 1
    fear_word = "too big for the room" if child.memes["fear"] >= THRESHOLD else "strange"
    world.say(
        f"{child.id} sat up and listened. The sound did not feel tiny in the dark. "
        f"It felt {fear_word}."
    )
    world.say(
        f'"What is that {source_cfg.sound} sound?" {child.id} whispered. '
        f'"It keeps going {source_cfg.repeat}, {source_cfg.repeat}."'
    )


def inspect(world: World, parent: Entity, child: Entity, source_cfg: Source, response: Response) -> None:
    unfixed = predict_unfixed(world)
    fixed = predict_fixed(world, response)
    world.facts["predicted_noise"] = unfixed["room_noise"]
    world.facts["predicted_fear"] = unfixed["fear"]
    world.facts["predicted_quiet"] = fixed["room_noise"]
    world.say(
        f"{parent.label_word.capitalize()} listened too. "
        f'"Let me look," {parent.pronoun()} said softly. "Sounds grow bigger when we do not know them."'
    )
    if unfixed["room_noise"] > fixed["room_noise"]:
        world.say(
            f"{parent.pronoun().capitalize()} followed the sound to {source_cfg.location} and found the real cause."
        )


def fix_source(world: World, parent: Entity, source_cfg: Source, response: Response) -> None:
    source = world.get("source")
    source.meters["secured"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} {source_cfg.response_text}."
    )
    world.say(
        f'The room listened again. "{source_cfg.sound}" stopped. "{source_cfg.repeat}" stopped. '
        f'Soon there was only a small, kind quiet.'
    )


def ritual_read(world: World, child: Entity, parent: Entity, ritual: Ritual) -> None:
    book = world.get("book")
    book.meters["open"] += 1
    book.meters["reading"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} opened the accordion alphabet book across the blanket."
    )
    world.say(
        ritual.repeat_line
    )
    world.say(
        f'{child.id} said the letters after {parent.pronoun("object")}, slower and slower: '
        f'"A to B, B to C, C to D."'
    )


def settle(world: World, child: Entity, parent: Entity, ritual: Ritual) -> None:
    world.say(
        f'Soon the letters were not busy letters at all. They were bedtime letters. '
        f'"Soft and slow," {parent.label_word} whispered. "Soft and slow."'
    )
    if child.memes["sleepiness"] >= 2:
        world.say(
            f"{child.id}'s eyes grew heavy. {ritual.ending_image}"
        )
    else:
        world.say(
            f"{child.id} breathed more easily and lay back down."
        )


SOURCES = {
    "window_screen": Source(
        id="window_screen",
        label="window mesh",
        phrase="the window mesh",
        location="the half-open window",
        sound="hush-hiss",
        repeat="hush-hiss",
        cause="a cool breeze kept pressing the screen and letting it spring back",
        fix_by="close_window",
        response_text="closed the window a little more until the window mesh rested still",
        tags={"mesh", "wind", "window"},
    ),
    "toy_bag": Source(
        id="toy_bag",
        label="mesh toy bag",
        phrase="the mesh toy bag",
        location="the hook by the shelf",
        sound="tap-tap",
        repeat="tap-tap",
        cause="the hanging bag kept brushing the wall and the blocks inside clicked together",
        fix_by="hang_still",
        response_text="lifted the mesh toy bag, set the blocks down softly, and hung the bag so it would not tap the wall",
        tags={"mesh", "bag", "blocks"},
    ),
    "laundry_hamper": Source(
        id="laundry_hamper",
        label="mesh laundry hamper",
        phrase="the mesh laundry hamper",
        location="the corner near the chair",
        sound="swish-swish",
        repeat="swish-swish",
        cause="a pajama sleeve draped over the side and rubbed each time the fan stirred the air",
        fix_by="tuck_cloth",
        response_text="tucked the loose pajama sleeve into the mesh hamper so nothing rubbed or swished anymore",
        tags={"mesh", "laundry", "fan"},
    ),
}

RESPONSES = {
    "close_window": Response(
        id="close_window",
        label="close the window",
        action="close the window a little",
        handles={"close_window"},
        tags={"window"},
    ),
    "hang_still": Response(
        id="hang_still",
        label="steady the bag",
        action="steady the hanging bag",
        handles={"hang_still"},
        tags={"bag"},
    ),
    "tuck_cloth": Response(
        id="tuck_cloth",
        label="tuck the sleeve in",
        action="tuck the loose cloth in",
        handles={"tuck_cloth"},
        tags={"laundry"},
    ),
}

RITUALS = {
    "whisper_letters": Ritual(
        id="whisper_letters",
        label="whisper letters",
        first_line="Together they looked at the first page of the alphabet and touched one letter with one finger.",
        repeat_line='Page by page went the accordion book: "A is for apple. B is for bed. C is for candlelight gone sleepy."',
        ending_image="The open accordion book made a little paper hill on the blanket, and one small hand stayed resting on the letter B for bed.",
        tags={"alphabet", "book"},
    ),
    "hum_letters": Ritual(
        id="hum_letters",
        label="hum letters",
        first_line="They began at the beginning of the alphabet and let each letter have a tiny hum.",
        repeat_line='The accordion folds opened wider and wider as they murmured, "Aaa, Bbb, Ccc," soft as blanket sounds.',
        ending_image="By the time they reached the middle folds, the book drooped like a paper moon and the room felt round and quiet.",
        tags={"alphabet", "book"},
    ),
    "goodnight_letters": Ritual(
        id="goodnight_letters",
        label="goodnight letters",
        first_line="Instead of hurrying, they told the alphabet good night one letter at a time.",
        repeat_line='They whispered, "Good night A. Good night B. Good night C," while the accordion pages folded and unfolded with a papery shhh.',
        ending_image="When the last fold bent closed, the blanket was warm, the pillow was cool, and the whole alphabet seemed ready to sleep too.",
        tags={"alphabet", "book"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ella", "Ruby", "Ivy", "June", "Tessa"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Ben", "Noah", "Jude"]
COMFORTS = ["a plush bunny", "a sleepy bear", "a little fox toy", "a soft moon pillow", ""]


@dataclass
class StoryParams:
    source: str
    response: str
    ritual: str
    child_name: str
    child_gender: str
    parent: str
    comfort: str = ""
    seed: Optional[int] = None


def tell(
    *,
    source_cfg: Source,
    response: Response,
    ritual: Ritual,
    child_name: str,
    child_gender: str,
    parent_type: str,
    comfort: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"comfort": comfort},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label="room"))
    book = world.add(Entity(
        id="book",
        type="book",
        label="accordion alphabet book",
        phrase="an accordion alphabet book",
        tags={"accordion", "alphabet"},
    ))
    pocket = world.add(Entity(
        id="pocket",
        type="pocket",
        label="mesh pocket",
        phrase="a small mesh pocket full of bedtime cards",
        tags={"mesh"},
    ))
    source = world.add(Entity(
        id="source",
        type="source",
        label=source_cfg.label,
        phrase=source_cfg.phrase,
        tags=set(source_cfg.tags),
    ))

    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        book=book,
        pocket=pocket,
        source_cfg=source_cfg,
        response=response,
        ritual=ritual,
        child_name=child_name,
    )

    introduce(world, child, parent)
    first_letters(world, child, ritual)

    world.para()
    start_sound(world, source_cfg)
    worry(world, child, source_cfg)

    world.para()
    inspect(world, parent, child, source_cfg, response)
    fix_source(world, parent, source_cfg, response)

    world.para()
    ritual_read(world, child, parent, ritual)
    settle(world, child, parent, ritual)

    world.facts.update(
        quiet=world.get("room").meters["room_noise"] < THRESHOLD,
        secured=world.get("source").meters["secured"] >= THRESHOLD,
        sleepy=world.get("child").memes["sleepiness"] >= THRESHOLD,
        afraid=world.get("child").memes["fear"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    source_cfg = world.facts["source_cfg"]
    ritual = world.facts["ritual"]
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        'Write a bedtime story for a 3-to-5-year-old that includes the words "mesh," "accordion," and "alphabet," and uses soft sound effects and repetition.',
        f"Tell a gentle bedtime story where a child named {world.facts['child_name']} hears {source_cfg.sound} in the dark, a grown-up finds the ordinary cause, and an accordion alphabet book helps the room feel safe again.",
        f"Write a sleepy story with repeated sound words, a small night worry, and a calm ending where {child.pronoun('possessive')} {parent.label_word} uses {ritual.label} to turn bedtime quiet again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    source_cfg = world.facts["source_cfg"]
    response = world.facts["response"]
    ritual = world.facts["ritual"]
    child_name = world.facts["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name} and {child.pronoun('possessive')} {parent.label_word} at bedtime. They start with a cozy room, then work together when a night sound feels scary.",
        ),
        (
            "What sound did the child hear?",
            f"{child_name} heard {source_cfg.sound}, again and again. The repeated sound felt bigger in the dark because {child_name} did not know what was making it yet.",
        ),
        (
            f"Where did the sound really come from?",
            f"It came from {source_cfg.phrase} at {source_cfg.location}. {source_cfg.cause[0].upper()}{source_cfg.cause[1:]}, so the sound had an ordinary cause instead of a monster cause.",
        ),
        (
            f"How did {child_name}'s {parent.label_word} solve the problem?",
            f"{parent.label_word.capitalize()} chose to {response.action}. That worked because it matched the real cause of the noise and made the room quiet again.",
        ),
        (
            "What was the accordion alphabet book for?",
            f"The accordion alphabet book helped slow the room down after the sound was fixed. The repeated letters turned {child_name}'s attention from worry toward a calm bedtime rhythm.",
        ),
        (
            "How did the story end?",
            f"It ended quietly, with the source secured and the child growing sleepy. {ritual.ending_image}",
        ),
    ]
    return qa


KNOWLEDGE = {
    "mesh": [
        (
            "What is mesh?",
            "Mesh is a material with many little holes in it, like a net or screen. Air can pass through it, which is why mesh bags and window screens are useful.",
        )
    ],
    "accordion": [
        (
            "What does accordion mean in a book?",
            "An accordion book folds out in connected sections, like a zigzag. You can stretch it open and fold it closed again.",
        )
    ],
    "alphabet": [
        (
            "What is the alphabet?",
            "The alphabet is the set of letters we use to make words. Children often learn it a little at a time by seeing, saying, and hearing the letters.",
        )
    ],
    "window": [
        (
            "Why can a window screen make a sound?",
            "If air pushes on a loose screen, it can vibrate or tap lightly. Small movements can sound bigger at night when a room is quiet.",
        )
    ],
    "bag": [
        (
            "Why might a hanging bag tap the wall?",
            "If a hanging bag swings and bumps the wall, it can make a tapping sound. Things inside the bag can click too.",
        )
    ],
    "laundry": [
        (
            "Why can cloth make swishing sounds?",
            "Loose cloth can rub against other things when air moves it. That rubbing can make a soft swish-swish sound.",
        )
    ],
    "bedtime": [
        (
            "Why do gentle repeated sounds help at bedtime?",
            "Gentle repetition can help your body slow down because it feels steady and predictable. That makes it easier to relax and get sleepy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mesh", "accordion", "alphabet", "window", "bag", "laundry", "bedtime"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    source_cfg = world.facts["source_cfg"]
    tags = {"mesh", "accordion", "alphabet", "bedtime"} | set(source_cfg.tags) | set(world.facts["ritual"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="window_screen",
        response="close_window",
        ritual="goodnight_letters",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        comfort="a plush bunny",
    ),
    StoryParams(
        source="toy_bag",
        response="hang_still",
        ritual="whisper_letters",
        child_name="Milo",
        child_gender="boy",
        parent="father",
        comfort="a sleepy bear",
    ),
    StoryParams(
        source="laundry_hamper",
        response="tuck_cloth",
        ritual="hum_letters",
        child_name="Ella",
        child_gender="girl",
        parent="mother",
        comfort="a little fox toy",
    ),
]


def explain_rejection(source: Source, response: Response) -> str:
    return (
        f"(No story: '{response.id}' does not sensibly fix {source.phrase}. "
        f"The source needs a response that handles '{source.fix_by}'.)"
    )


ASP_RULES = r"""
fits(S, R) :- source(S), response(R), needs_fix(S, F), handles(R, F).
valid(S, R, T) :- source(S), response(R), ritual(T), fits(S, R).

outcome(calm) :- chosen_source(S), chosen_response(R), fits(S, R), chosen_ritual(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("needs_fix", sid, source.fix_by))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        for handle in sorted(response.handles):
            lines.append(asp.fact("handles", rid, handle))
    for tid in RITUALS:
        lines.append(asp.fact("ritual", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_ritual", params.ritual),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    if params.source not in SOURCES or params.response not in RESPONSES or params.ritual not in RITUALS:
        return "invalid"
    return "calm" if response_fits(SOURCES[params.source], RESPONSES[params.response]) else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld with mesh sounds, an accordion alphabet book, and a calm fix."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--ritual", choices=sorted(RITUALS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid source/response/ritual combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.response:
        source = SOURCES[args.source]
        response = RESPONSES[args.response]
        if not response_fits(source, response):
            raise StoryError(explain_rejection(source, response))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.response is None or combo[1] == args.response)
        and (args.ritual is None or combo[2] == args.ritual)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, response_id, ritual_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    if args.child_name:
        child_name = args.child_name
    else:
        child_name = rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    comfort = rng.choice(COMFORTS)
    return StoryParams(
        source=source_id,
        response=response_id,
        ritual=ritual_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.ritual not in RITUALS:
        raise StoryError(f"(Unknown ritual: {params.ritual})")
    source_cfg = SOURCES[params.source]
    response = RESPONSES[params.response]
    if not response_fits(source_cfg, response):
        raise StoryError(explain_rejection(source_cfg, response))

    world = tell(
        source_cfg=source_cfg,
        response=response,
        ritual=RITUALS[params.ritual],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        comfort=params.comfort,
    )

    story_text = world.render().replace(" child ", f" {params.child_name} ")
    story_text = story_text.replace("child's", f"{params.child_name}'s")
    story_text = story_text.replace("child", params.child_name)
    story_text = story_text.replace("Parent", world.get("parent").label_word.capitalize())
    story_text = story_text.replace("parent", world.get("parent").label_word)

    return StorySample(
        params=params,
        story=story_text,
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


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during param resolution at seed {seed}.")
            continue

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python outcome on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (source, response, ritual) combos:\n")
        for source, response, ritual in combos:
            print(f"  {source:15} {response:13} {ritual}")
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
            header = f"### {p.child_name}: {p.source} -> {p.response} with {p.ritual}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

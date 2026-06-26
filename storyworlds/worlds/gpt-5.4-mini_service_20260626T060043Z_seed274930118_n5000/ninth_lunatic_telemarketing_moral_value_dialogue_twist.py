#!/usr/bin/env python3
"""
storyworlds/worlds/ninth_lunatic_telemarketing_moral_value_dialogue_twist.py
============================================================================

A small adventure-flavored storyworld about a ninth call, a telemarketing pitch,
and a moral turn that changes the ending.

Seed tale used to build the world model:
---
On the ninth evening of the fair, a child helper worked from a tiny booth on
the old ship called the Lunatic. Their job was telemarketing: calling lantern
shops to sell a shiny rescue beacon. The helper had a loud script and a brave
voice, but the script was too slippery. It promised things the beacon could not
do.

When the first shopkeeper asked a sharp question, the helper began to stumble.
Then the helper noticed a real problem: the shopkeeper did not need a fancy
promise. She needed a beacon that would actually guide lost sailors home.

So the helper changed the pitch, told the truth, and spoke plainly. The shopkeeper
laughed, thanked the helper for being honest, and ordered the beacon because
honesty was more valuable than tricks. The ninth call became the best call of the
night.

World model:
---
    setting.meters["distance"]     -> how far the helper is from a safe ending
    setting.memes["noise"]         -> noisy, confusing telemarketing energy
    caller.memes["courage"]        -> how brave the helper is to speak
    caller.memes["honesty"]        -> whether the helper tells the truth
    caller.memes["worry"]          -> pressure when the script feels slippery
    customer.memes["trust"]        -> how much the customer believes the caller
    customer.memes["interest"]     -> willingness to listen
    customer.memes["relief"]       -> how good it feels to hear an honest pitch

Story beats:
---
    ninth attempt     -> caller courage rises; worry rises if the script is false
    dialogue question -> customer tests the promise
    moral turn        -> the caller tells the truth and repairs trust
    twist resolution  -> the customer wants the honest version, not the loud one
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "setting"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Pitch:
    id: str
    label: str
    phrase: str
    honest_phrase: str
    false_phrase: str
    keyword: str
    value: str
    risk: str
    benefit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    pitch: str
    name: str
    role: str
    customer: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


def _narrate(world: World, text: str) -> None:
    world.say(text)


def _beat_intro(world: World, caller: Entity, customer: Entity, pitch: Pitch) -> None:
    caller.memes["courage"] += 1
    caller.memes["worry"] += 1
    world.say(
        f"On the ninth call, {caller.id} stood in the tiny booth on the old ship called the Lunatic."
    )
    world.say(
        f"The {world.setting.place} was loud with ringing wires, and {caller.id} was making telemarketing calls about {pitch.label}."
    )
    world.say(
        f"{caller.pronoun().capitalize()} wanted to sound bold, because {caller.pronoun('possessive')} script promised {pitch.false_phrase}."
    )
    world.say(
        f"At the other end, {customer.id} listened carefully, waiting to hear whether the story was true."
    )


def _beat_dialogue(world: World, caller: Entity, customer: Entity, pitch: Pitch) -> None:
    customer.memes["interest"] += 1
    customer.memes["trust"] += 0.5
    world.say(
        f'"Can it really do that?" {customer.id} asked.'
    )
    world.say(
        f'{caller.id} opened {caller.pronoun("possessive")} mouth, then paused.'
    )
    world.say(
        f"The old script felt slippery. It wanted a bigger promise than {pitch.label} could keep."
    )


def _beat_moral_turn(world: World, caller: Entity, customer: Entity, pitch: Pitch) -> None:
    caller.memes["honesty"] += 1
    caller.memes["worry"] = max(0.0, caller.memes["worry"] - 1.0)
    customer.memes["trust"] += 2.0
    world.say(
        f"Then {caller.id} took a steady breath and said, \"No, not that part.\""
    )
    world.say(
        f"\"What {pitch.label} really does is {pitch.honest_phrase}.\""
    )
    world.say(
        f"That plain answer was not flashy, but it was brave."
    )


def _beat_twist(world: World, caller: Entity, customer: Entity, pitch: Pitch) -> None:
    customer.memes["relief"] += 1.5
    customer.meters["orders"] = customer.meters.get("orders", 0.0) + 1.0
    caller.meters["distance"] = max(0.0, caller.meters.get("distance", 0.0) - 1.0)
    world.say(
        f"{customer.id} smiled. \"I don't need a miracle,\" {customer.pronoun()} said."
    )
    world.say(
        f"\"I need something that really helps, and I trust you now.\""
    )
    world.say(
        f"So the ninth call became the best one of the night, because the honest {pitch.keyword} was exactly what {customer.id} wanted."
    )


SETTINGS = {
    "harbor": Setting(place="harbor office", mood="windy", afford={"telemarketing"}),
    "fair": Setting(place="fair booth", mood="busy", afford={"telemarketing"}),
    "tower": Setting(place="lighthouse room", mood="echoey", afford={"telemarketing"}),
}

PITCHES = {
    "beacon": Pitch(
        id="beacon",
        label="a rescue beacon",
        phrase="a shiny rescue beacon",
        honest_phrase="guides lost sailors home with a bright safe light",
        false_phrase="finds anyone anywhere in a blink",
        keyword="beacon",
        value="truth",
        risk="a false promise would break trust",
        benefit="an honest promise can save time and fear",
        tags={"light", "safety", "truth"},
    ),
    "map": Pitch(
        id="map",
        label="a pocket map",
        phrase="a small pocket map",
        honest_phrase="shows the safe trail through the cliffs",
        false_phrase="knows every secret path in the whole world",
        keyword="map",
        value="honesty",
        risk="a false promise would confuse the customer",
        benefit="a clear map helps people choose a safe road",
        tags={"map", "safety", "truth"},
    ),
    "bell": Pitch(
        id="bell",
        label="a warning bell",
        phrase="a little warning bell",
        honest_phrase="rings when the harbor fog gets thick",
        false_phrase="can chase away every storm",
        keyword="bell",
        value="courage",
        risk="a false promise would sound silly",
        benefit="a real warning helps people act early",
        tags={"sound", "warning", "truth"},
    ),
}

CALLER_ROLES = ["helper", "apprentice", "runner"]
CUSTOMER_ROLES = ["shopkeeper", "captain", "dockmaster", "baker"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, pid) for place, s in SETTINGS.items() for pid in PITCHES if "telemarketing" in s.afford]


@dataclass
class StoryWorld:
    pass


def tell(setting: Setting, pitch: Pitch, name: str, role: str, customer_role: str) -> World:
    world = World(setting)
    caller = world.add(Entity(
        id=name,
        kind="character",
        type=role,
        label=role,
        meters={"distance": 2.0},
        memes={"courage": 0.0, "honesty": 0.0, "worry": 0.0},
    ))
    customer = world.add(Entity(
        id=f"the {customer_role}",
        kind="character",
        type=customer_role,
        label=f"the {customer_role}",
        meters={"orders": 0.0},
        memes={"interest": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    prop = world.add(Entity(
        id=pitch.id,
        kind="thing",
        type="thing",
        label=pitch.label,
        phrase=pitch.phrase,
        owner=caller.id,
    ))

    _beat_intro(world, caller, customer, pitch)
    world.para()
    _beat_dialogue(world, caller, customer, pitch)
    world.para()
    _beat_moral_turn(world, caller, customer, pitch)
    _beat_twist(world, caller, customer, pitch)

    world.facts.update(
        caller=caller,
        customer=customer,
        pitch=pitch,
        prop=prop,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    caller = f["caller"]
    customer = f["customer"]
    pitch = f["pitch"]
    return [
        f'Write an adventure story for a young child about the ninth telemarketing call for {pitch.label}.',
        f"Tell a dialogue-heavy story where {caller.id} must choose honesty over a slippery script.",
        f"Write a short moral-value story with a twist: the customer likes the truthful version better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    caller = f["caller"]
    customer = f["customer"]
    pitch = f["pitch"]
    qa = [
        QAItem(
            question=f"What was {caller.id} doing on the ninth call?",
            answer=f"{caller.id} was making telemarketing calls about {pitch.label} from the little booth on the old ship called the Lunatic.",
        ),
        QAItem(
            question=f"Why did {customer.id} ask a sharp question?",
            answer=f"{customer.id} wanted to know whether the promise about {pitch.label} was real, not just loud.",
        ),
        QAItem(
            question=f"What changed when {caller.id} spoke honestly?",
            answer=f"The pitch became trustworthy, and {customer.id} felt relieved enough to listen and order it.",
        ),
        QAItem(
            question=f"What was the moral value in the story?",
            answer="The story showed that honesty is more valuable than a fancy trick.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pitch = f["pitch"]
    return [
        QAItem(
            question="What is telemarketing?",
            answer="Telemarketing is when someone talks to people by phone to tell them about something they might want to buy or learn about.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth instead of making up a story that sounds better than it really is.",
        ),
        QAItem(
            question=f"What does {pitch.label} do in this world?",
            answer=pitch.honest_phrase.capitalize() + ".",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Pitch) :- place(Place), pitch(Pitch), afford(Place, telemarketing).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", pid, a))
    for pid in PITCHES:
        lines.append(asp.fact("pitch", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: ninth, lunatic, telemarketing, moral value, dialogue, twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--pitch", choices=PITCHES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=CALLER_ROLES)
    ap.add_argument("--customer", choices=CUSTOMER_ROLES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.pitch and "telemarketing" not in SETTINGS[args.place].afford:
        raise StoryError("This place cannot host a telemarketing story.")
    places = [p for p in SETTINGS if args.place is None or p == args.place]
    pitches = [p for p in PITCHES if args.pitch is None or p == args.pitch]
    if not places or not pitches:
        raise StoryError("No valid combination matches the given options.")
    place = rng.choice(places)
    pitch = rng.choice(pitches)
    name = args.name or rng.choice(["Nia", "Milo", "Tess", "Oren", "June"])
    role = args.role or rng.choice(CALLER_ROLES)
    customer = args.customer or rng.choice(CUSTOMER_ROLES)
    return StoryParams(place=place, pitch=pitch, name=name, role=role, customer=customer)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PITCHES[params.pitch], params.name, params.role, params.customer)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, pitch) combos:\n")
        for place, pitch in combos:
            print(f"  {place:10} {pitch}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for pitch in PITCHES:
                p = StoryParams(place=place, pitch=pitch, name="Nia", role="helper", customer="shopkeeper")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

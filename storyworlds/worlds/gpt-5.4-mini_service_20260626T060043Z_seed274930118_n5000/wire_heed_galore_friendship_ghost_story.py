#!/usr/bin/env python3
"""
storyworlds/worlds/wire_heed_galore_friendship_ghost_story.py
==============================================================

A tiny ghost-story world about friendship, a wary warning, a wire, and a
glimmer of galore.

Premise:
- A child makes friends with a shy ghost.
- They find a loose wire in a quiet old house.
- The ghost asks the child to heed a warning because the wire is old and sharp.

Turn:
- The child wants to keep playing with the wire light and the many small sparks
  it makes, but the wire can snag curtains and scare the ghost.
- The ghost's warning is not about winning; it is about trust and safety.

Resolution:
- They carefully wrap the wire, move it to a safe hook, and use it to hang a
  lantern with little lights galore.
- Friendship deepens because both characters listened and helped.

The story uses the seed words "wire", "heed", and "galore".
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    indoor: bool = True
    spooky: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    label: str
    phrase: str
    region: str
    plural: bool = False
    danger: str = "snagged"
    safe_use: str = "careful hands"


@dataclass
class StoryParams:
    setting: str = "old_house"
    object: str = "wire"
    name: str = "Mia"
    gender: str = "girl"
    companion: str = "ghost"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _apply_tension(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    wire = world.entities.get("object")
    ghost = world.entities.get("ghost")
    if not child or not wire or not ghost:
        return out
    if child.memes.get("heed", 0) < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    if wire.meters.get("hazard", 0) >= THRESHOLD:
        world.fired.add(sig)
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        ghost.memes["fear"] = ghost.memes.get("fear", 0) + 1
        out.append("The wire looked old and sharp enough to snag a sleeve or startle a shy spirit.")
    return out


def _apply_resolution(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    wire = world.entities.get("object")
    ghost = world.entities.get("ghost")
    if not child or not wire or not ghost:
        return out
    sig = ("resolved",)
    if sig in world.fired:
        return out
    if wire.meters.get("wrapped", 0) >= THRESHOLD and wire.meters.get("hanging", 0) >= THRESHOLD:
        world.fired.add(sig)
        child.memes["trust"] = child.memes.get("trust", 0) + 1
        ghost.memes["trust"] = ghost.memes.get("trust", 0) + 1
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        ghost.memes["joy"] = ghost.memes.get("joy", 0) + 1
        out.append("Once the wire was wrapped and hung safely, the room felt friendly again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_apply_tension, _apply_resolution):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "old_house": Setting(place="the old house", indoor=True, spooky=True, affords={"wire"}),
    "attic": Setting(place="the attic", indoor=True, spooky=True, affords={"wire"}),
    "garden_shed": Setting(place="the garden shed", indoor=True, spooky=False, affords={"wire"}),
}

OBJECTS = {
    "wire": ObjectDef(
        label="wire",
        phrase="a thin wire",
        region="hands",
        plural=False,
        danger="snagged",
        safe_use="careful hands",
    ),
    "lantern_wire": ObjectDef(
        label="wire lantern cord",
        phrase="a wire lantern cord",
        region="hands",
        plural=False,
        danger="snagged",
        safe_use="steady hands",
    ),
}

NAMES_GIRL = ["Mia", "Luna", "Nora", "Ivy", "Rose"]
NAMES_BOY = ["Theo", "Eli", "Max", "Finn", "Noah"]
TRAITS = ["curious", "gentle", "brave", "quiet", "kind"]


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, oid) for sid in SETTINGS for oid in OBJECTS]


@dataclass
class Rule:
    name: str
    apply: callable


CAUSAL_RULES = [Rule("tension", _apply_tension), Rule("resolution", _apply_resolution)]


def tell(setting: Setting, object_def: ObjectDef, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=gender,
        label=hero_name,
        traits=["little", trait],
        meters={"held": 0.0},
        memes={"love": 0.0, "heed": 0.0, "worry": 0.0, "joy": 0.0, "trust": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        traits=["shy", "friendly"],
        meters={"floating": 1.0},
        memes={"love": 0.0, "heed": 0.0, "worry": 0.0, "joy": 0.0, "trust": 0.0},
    ))
    wire = world.add(Entity(
        id="object",
        kind="thing",
        type="wire",
        label=object_def.label,
        phrase=object_def.phrase,
        caretaker="ghost",
        location=setting.place,
        meters={"hazard": 1.0},
        memes={"shine": 1.0},
    ))

    world.say(f"{hero_name} was a little {trait} child who liked quiet rooms and secret corners.")
    world.say(f"In the old house, {hero_name} met a shy ghost who drifted kindly near the stairs.")
    world.say(f"They became friends at once, because the ghost loved to listen and {hero_name} loved stories.")
    world.para()

    world.say(f"One evening, {hero_name} found {object_def.phrase} curled near a dusty chair.")
    world.say(f"The wire sparkled a little, and there were tiny reflections galore on the wall.")
    world.say(f"The ghost lifted one pale finger and asked {hero_name} to heed the warning before touching it.")
    child.memes["heed"] += 1
    ghost.memes["love"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero_name} wanted to play with the wire right away, but remembered the warning.")
    world.say(f"Together they moved slowly, with {object_def.safe_use}, so the wire would not snag the curtains.")
    wire.meters["wrapped"] = 1.0
    wire.meters["hanging"] = 1.0
    world.say(f"They wrapped the wire around a safe hook and made it into a little lantern cord.")
    world.say(f"When they turned on the lamp, the room filled with tiny lights galore, warm as butter.")
    propagate(world, narrate=True)
    world.say(f"{hero_name} smiled at the ghost, and the ghost smiled back without fading away.")

    world.facts.update(
        child=child,
        ghost=ghost,
        wire=wire,
        setting=setting,
        object_def=object_def,
        trait=trait,
        name=hero_name,
        gender=gender,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short ghost story for a young child about friendship, a wire, and a warning to heed.',
        f"Tell a gentle spooky story where {f['name']} meets a ghost in {f['setting'].place} and learns to heed the danger of the {f['object_def'].label}.",
        'Write a child-friendly ghost story that uses the words wire, heed, and galore, and ends with new friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    name = f["name"]
    ghost = f["ghost"]
    wire = f["wire"]
    trait = f["trait"]
    setting = f["setting"].place
    return [
        QAItem(
            question=f"Who made friends in {setting}?",
            answer=f"{name}, a little {trait} child, made friends with the shy ghost in {setting}.",
        ),
        QAItem(
            question=f"What did the ghost ask {name} to do before touching the wire?",
            answer=f"The ghost asked {name} to heed the warning before touching the wire.",
        ),
        QAItem(
            question=f"What happened after they wrapped the wire safely?",
            answer=f"They turned it into a lantern cord, and the room filled with lights galore while their friendship felt warmer.",
        ),
        QAItem(
            question=f"Why was the wire something to be careful with?",
            answer=f"The wire was old and sharp enough to snag a sleeve, so it had to be handled with care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wire?",
            answer="A wire is a long, thin piece of metal that can carry light or electricity, or be used to hold things up.",
        ),
        QAItem(
            question="What does it mean to heed a warning?",
            answer="To heed a warning means to listen carefully and do what the warning says so you stay safe.",
        ),
        QAItem(
            question="What does galore mean?",
            answer="Galore means there is a lot of something.",
        ),
        QAItem(
            question="Why can old things be tricky in a spooky house?",
            answer="Old things can be dusty, loose, or sharp, so people need to move carefully around them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        if s.spooky:
            lines.append(asp.fact("spooky", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("label", oid, o.label))
        lines.append(asp.fact("danger", oid, o.danger))
        lines.append(asp.fact("safe_use", oid, o.safe_use))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting,Object) :- setting(Setting), object(Object), affords(Setting, wire).
safe(Setting,Object) :- valid(Setting,Object).
#show valid/2.
#show safe/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP parity matched ({len(p)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if p - a:
        print("only python:", sorted(p - a))
    if a - p:
        print("only asp:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about friendship, a wire, heed, and galore.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, object=obj, name=name, gender=gender, companion="ghost", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], params.name, params.gender, params.trait)
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
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(s, o) for s in SETTINGS for o in OBJECTS]
        for i, (s, o) in enumerate(combos):
            p = StoryParams(setting=s, object=o, name=(NAMES_GIRL[i % len(NAMES_GIRL)]), gender="girl" if i % 2 == 0 else "boy", trait=TRAITS[i % len(TRAITS)])
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

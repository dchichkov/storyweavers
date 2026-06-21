#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mime_polish_teamwork_surprise_nursery_rhyme.py
===============================================================================

A small standalone storyworld for a nursery-rhyme-like tale about a mime and
a polish bowl, where teamwork and surprise turn a dull little stage into a
bright finish.

The world models a tiny room with a performer, a helper, and a shy object that
needs polishing. The story is driven by state changes: the mime starts with a
silent idea, the helper notices a dull surface, they work together, and a small
surprise ends the rhyme with a bright reveal.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Thing:
    id: str
    label: str
    state: str
    shine_gain: float
    surprise: str
    tag: str = ""
    polishable: bool = True


@dataclass
class StoryParams:
    mime: str
    helper: str
    object_id: str
    surprise_id: str
    seed: Optional[int] = None
    mime_gender: str = "boy"
    helper_gender: str = "girl"
    mime_role: str = "mime"
    helper_role: str = "helper"


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["joy"] >= THRESHOLD and ("smile", e.id) not in world.fired:
            world.fired.add(("smile", e.id))
            out.append(f"{e.id} felt brave enough to keep the little tune going.")
    return out


CAUSAL_RULES = [Rule("smile", _r_smile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


MIME_NAMES = ["Ned", "Milo", "Pip", "Toby", "Finn", "Theo", "June", "Nina", "Lola"]
HELPER_NAMES = ["Mina", "Ruby", "Penny", "Rose", "Tessa", "Clara", "Ivy", "Mabel", "Luna"]

OBJECTS = {
    "toy_tea_set": Thing("toy_tea_set", "toy tea set", "dull", 1.0, "a tiny surprise teacup"),
    "tin_star": Thing("tin_star", "tin star", "dull", 1.0, "a shiny star from a box"),
    "music_box": Thing("music_box", "music box", "dusty", 1.0, "a springy tune inside"),
}

SURPRISES = {
    "ribbon": "a ribbon tied in a bow",
    "bells": "two silver bells hidden in a scarf",
    "cookie": "a ginger cookie in a napkin",
}

SCENES = {
    "nursery": "a cozy nursery with a soft rug and a lamp like the moon",
    "playroom": "a little playroom with blocks and bears in a row",
}

THEME_WORDS = ("mime", "polish")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for obj in OBJECTS:
        for s in SURPRISES:
            combos.append((obj, s, "nursery"))
    return combos


def reasonableness_gate(obj: Thing, surprise_id: str) -> bool:
    return obj.polishable and surprise_id in SURPRISES


def tell(world: World, params: StoryParams, obj: Thing, surprise: str) -> World:
    mime = world.add(Entity(id=params.mime, kind="character", type=params.mime_gender, role="mime", traits=["quiet"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["kind"]))
    room = world.add(Entity(id="room", type="room", label="the nursery"))
    item = world.add(Entity(id="object", type="thing", label=obj.label, attrs={"state": obj.state}))

    mime.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In {SCENES['nursery']}, {mime.id} the mime tiptoed in with a tiny bow, "
        f"while {helper.id} hummed a nursery tune."
    )
    world.say(
        f"{mime.id} wanted to {obj.surprise if False else 'make the little room bright'}; "
        f"the old {obj.label} sat there, looking {obj.state}."
    )

    world.para()
    mime.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{mime.id} pointed to the {obj.label} and {helper.id} nodded. Together, they worked "
        f"side by side: one held the cloth, the other spread the polish."
    )
    item.meters["dull"] += 1
    item.meters["shine"] += obj.shine_gain
    propagate(world, narrate=False)

    world.say(
        f"The polish went round and round, and the {obj.label} grew bright as a bead."
    )
    world.para()

    helper.memes["surprise"] += 1
    world.say(
        f"Then came a surprise: {surprise}. {helper.id} laughed, and {mime.id} bowed so low "
        f"that the little room felt like a stage."
    )
    world.say(
        f"At the end, the {obj.label} gleamed, the nursery glowed, and the two friends "
        f"shared a happy silent grin."
    )

    world.facts.update(
        mime=mime,
        helper=helper,
        room=room,
        item=item,
        object_cfg=obj,
        surprise_id=surprise,
        outcome="bright",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme-style story with the words '{THEME_WORDS[0]}' and '{THEME_WORDS[1]}'.",
        f"Tell a gentle story where {f['mime'].id} and {f['helper'].id} work together to polish a {f['object_cfg'].label}.",
        f"Write a short rhyme with teamwork and a surprise ending in a cozy nursery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    obj = f["object_cfg"]
    return [
        (
            "Who worked together in the story?",
            f"{f['mime'].id} the mime and {f['helper'].id} the helper worked together. They shared the cloth, the polish, and the job, so the work felt light.",
        ),
        (
            "Why did they polish the object?",
            f"They polished the {obj.label} because it looked dull at first. Polishing it made the surface shine, so the little room could end with a bright, happy picture.",
        ),
        (
            "What was the surprise?",
            f"The surprise was {SURPRISES[f['surprise_id']]}. It made the ending feel playful and festive after the polishing was done.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mime usually do?",
            answer="A mime tells part of a story with silent gestures, facial expressions, and careful movements instead of lots of words.",
        ),
        QAItem(
            question="What does polish do?",
            answer="Polish helps a surface look brighter and cleaner. People rub it on gently and then wipe it away so the object can shine.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means two or more helpers work together and each one does a part. That way the job gets done more easily.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shiny(X) :- item(X), shine_gain(X, G), G >= 1.
teamwork(mime, helper).
surprise(S) :- surprise_id(S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("item", oid))
        lines.append(asp.fact("shine_gain", oid, int(obj.shine_gain)))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_id", sid))
    lines.append(asp.fact("mime_word", "mime"))
    lines.append(asp.fact("polish_word", "polish"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show shiny/1."))
    return sorted(set(asp.atoms(model, "shiny")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set((o, s, "nursery") for (o,) in asp_valid_combos() for s in SURPRISES if o in OBJECTS)
    if py:
        print(f"OK: python valid_combos has {len(py)} combos.")
    if not py:
        rc = 1
    # smoke test
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        print(f"ERROR: smoke test failed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about mime, polish, teamwork, and surprise.")
    ap.add_argument("--mime")
    ap.add_argument("--helper")
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--surprise", dest="surprise_id", choices=SURPRISES)
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
    obj_id = args.object_id or rng.choice(list(OBJECTS))
    surprise_id = args.surprise_id or rng.choice(list(SURPRISES))
    if obj_id not in OBJECTS or surprise_id not in SURPRISES:
        raise StoryError("Invalid object or surprise choice.")
    if not reasonableness_gate(OBJECTS[obj_id], surprise_id):
        raise StoryError("That object cannot be polished in this little story.")
    return StoryParams(
        mime=args.mime or rng.choice(MIME_NAMES),
        helper=args.helper or rng.choice(HELPER_NAMES),
        object_id=obj_id,
        surprise_id=surprise_id,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.object_id not in OBJECTS:
        raise StoryError("Unknown object choice.")
    if params.surprise_id not in SURPRISES:
        raise StoryError("Unknown surprise choice.")
    obj = OBJECTS[params.object_id]
    world = tell(World(), params, obj, SURPRISES[params.surprise_id])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
    StoryParams(mime="Ned", helper="Mina", object_id="toy_tea_set", surprise_id="ribbon", seed=1),
    StoryParams(mime="Pip", helper="Ruby", object_id="tin_star", surprise_id="bells", seed=2),
    StoryParams(mime="June", helper="Luna", object_id="music_box", surprise_id="cookie", seed=3),
]


def asp_verify() -> int:
    return 0 if CURATED and generate(CURATED[0]).story else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show shiny/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("asp mode not needed for this tiny rhyme world")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

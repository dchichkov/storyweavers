#!/usr/bin/env python3
"""
storyworlds/worlds/foreign_afford_kerosene_farmyard_happy_ending_slice.py
=========================================================================

A tiny slice-of-life storyworld set in a farmyard, built from the seed idea of
a child noticing something foreign, learning what they can afford, and safely
choosing a kerosene lamp for an evening chore.

The story is intentionally small and domestic: a farmyard task, a little
uncertainty, a practical helper, and a happy ending image that proves what
changed.
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
    role: str = ""
    owner: str = ""
    helper_to: str = ""
    foreign: bool = False
    afford: set[str] = field(default_factory=set)
    lit: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Farmyard:
    place: str = "the farmyard"
    affordances: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str = "farmyard"
    activity: str = "lantern"
    object: str = "blanket"
    child: str = "Mina"
    child_type: str = "girl"
    grownup: str = "grandmother"
    grownup_type: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Farmyard) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    lamp = world.entities.get("lamp")
    if lamp and lamp.lit and lamp.meters.get("warmth", 0) < THRESHOLD:
        sig = ("warm",)
        if sig not in world.fired:
            world.fired.add(sig)
            lamp.meters["warmth"] = 1.0
            out.append("The lamp gave a soft warm pool of light.")
    return out


def _r_foreign_to_familiar(world: World) -> list[str]:
    out: list[str] = []
    obj = world.entities.get("object")
    child = world.entities.get("child")
    if not obj or not child:
        return out
    if obj.memes.get("foreign_feel", 0) >= THRESHOLD and child.memes.get("understanding", 0) >= THRESHOLD:
        sig = ("familiar",)
        if sig not in world.fired:
            world.fired.add(sig)
            obj.memes["foreign_feel"] = 0
            obj.memes["safe"] = 1
            child.memes["understanding"] += 1
            out.append("The odd thing felt less foreign after they talked about it.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_warm, _r_foreign_to_familiar):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    return [("farmyard", "lantern", "blanket"), ("farmyard", "lantern", "crate")]


def explain_rejection(place: str, activity: str, obj: str) -> str:
    return f"(No story: this world only supports a safe farmyard lantern scene, not {place}/{activity}/{obj}.)"


def ASP_RULES() -> str:
    return r"""
valid(P,A,O) :- place(P), activity(A), object(O), afford(P,A), foreign_ok(O).
happy(P,A,O) :- valid(P,A,O).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "farmyard")]
    lines.append(asp.fact("activity", "lantern"))
    lines.append(asp.fact("afford", "farmyard", "lantern"))
    lines.append(asp.fact("object", "blanket"))
    lines.append(asp.fact("object", "crate"))
    lines.append(asp.fact("foreign_ok", "blanket"))
    lines.append(asp.fact("foreign_ok", "crate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0 if py == cl else 1
    if rc == 0:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH:")
        print("  python:", sorted(py))
        print("  clingo :", sorted(cl))
    # smoke test
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life farmyard storyworld with a foreign object and a kerosene lamp.")
    ap.add_argument("--place", choices=["farmyard"])
    ap.add_argument("--activity", choices=["lantern"])
    ap.add_argument("--object", choices=["blanket", "crate"])
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-type", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["curious", "careful", "quiet", "practical"])
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
    if args.place and args.place != "farmyard":
        raise StoryError(explain_rejection(args.place, args.activity or "lantern", args.object or "blanket"))
    if args.activity and args.activity != "lantern":
        raise StoryError(explain_rejection("farmyard", args.activity, args.object or "blanket"))
    if args.object and args.object not in {"blanket", "crate"}:
        raise StoryError(explain_rejection("farmyard", "lantern", args.object))
    obj = args.object or rng.choice(["blanket", "crate"])
    return StoryParams(
        place="farmyard",
        activity="lantern",
        object=obj,
        child=args.child or rng.choice(["Mina", "Lena", "June", "Ivy", "Nora"]),
        child_type=args.child_type or rng.choice(["girl", "boy"]),
        grownup=args.grownup or rng.choice(["grandmother", "mother", "uncle", "father"]),
        grownup_type=args.grownup_type or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(["curious", "careful", "quiet", "practical"]),
        seed=args.seed,
    )


def tell(params: StoryParams) -> World:
    world = World(Farmyard(place="the farmyard", affordances={"lantern"}))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child, role="child"))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup_type, label=params.grownup, role="grownup"))
    lamp = world.add(Entity(id="lamp", type="thing", label="kerosene lamp", phrase="a kerosene lamp", lit=False))
    obj = world.add(Entity(id="object", type="thing", label=params.object, phrase=f"a {params.object}", foreign=True))
    child.meters.update({"care": 0.0})
    child.memes.update({"curiosity": 1.0, "understanding": 0.0, "joy": 0.0})
    grownup.meters.update({"work": 0.0})
    grownup.memes.update({"calm": 1.0})
    lamp.meters.update({"warmth": 0.0})
    obj.meters.update({"weight": 1.0})
    obj.memes.update({"foreign_feel": 1.0, "safe": 0.0})
    world.facts.update(child=child, grownup=grownup, lamp=lamp, object=obj, params=params)

    world.say(f"Late in the farmyard, {params.child} found {obj.phrase} by the gate.")
    world.say(f"It looked a little foreign, but not scary, just new and out of place.")
    world.para()
    world.say(f"{params.child} wanted a light for the chicken feed, and the only thing nearby was a kerosene lamp.")
    world.say(f"{params.grownup} said they could afford a small, careful light and not a big fuss.")
    child.memes["understanding"] += 1
    lamp.lit = True
    propagate(world, narrate=True)
    world.para()
    world.say(f"So they carried the lamp to the coop, finished the evening chore, and the farmyard stayed warm and calm.")
    world.say(f"At the end, the foreign little thing was simply part of the evening, and the lamp glowed beside the hay.")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle slice-of-life story set in a farmyard that uses the words "foreign", "afford", and "kerosene".',
        f"Tell a short happy story about {world.facts['child'].label} in the farmyard finding something foreign and choosing a kerosene lamp for a small chore.",
        "Write a calm farmyard story where a child learns what they can afford, and the evening ends peacefully.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    return [
        QAItem(
            question=f"What did {p.child} find in the farmyard?",
            answer=f"{p.child} found a {p.object} by the gate. It seemed foreign at first, but it was just a new little thing in an ordinary evening.",
        ),
        QAItem(
            question=f"Why did {p.child} use the kerosene lamp?",
            answer="They needed a small light for the chore, and the lamp was a safe, steady choice. That let them finish the work without making the farmyard feel hectic.",
        ),
        QAItem(
            question=f"What did {p.grownup} say they could afford?",
            answer=f"{p.grownup} said they could afford a small, careful light and a simple plan. That choice fit the evening and kept everything calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kerosene?",
            answer="Kerosene is a fuel that can burn in a lamp. It is used carefully because it gives steady light when a grown-up handles it the right way.",
        ),
        QAItem(
            question="What does afford mean?",
            answer="Afford can mean have enough money, time, or room for something. In a story, it often means a family can manage a choice without trouble.",
        ),
        QAItem(
            question="What does foreign mean?",
            answer="Foreign means from somewhere else or new and unfamiliar. A foreign thing can seem odd at first, even when it is harmless.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    bits = ["--- world ---"]
    for e in world.entities.values():
        bits.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(bits)


CURATED = [
    StoryParams(place="farmyard", activity="lantern", object="blanket", child="Mina", child_type="girl", grownup="grandmother", grownup_type="mother", trait="curious", seed=7),
    StoryParams(place="farmyard", activity="lantern", object="crate", child="Eli", child_type="boy", grownup="father", grownup_type="father", trait="practical", seed=11),
]


def generate(params: StoryParams) -> StorySample:
    if params.place != "farmyard" or params.activity != "lantern" or params.object not in {"blanket", "crate"}:
        raise StoryError("invalid story parameters for this farmyard world")
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class MeteredThing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get(self, store: str, key: str) -> float:
        return self.meters.get(key, 0.0) if store == "meters" else self.memes.get(key, 0.0)


@dataclass
class Character(MeteredThing):
    kind: str = "character"
    type: str = "child"

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    setting: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    plural: bool = False
    heavy: bool = False


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    helps: str


@dataclass
class StoryParams:
    place: str
    material: str
    name: str
    friend_name: str
    gender: str
    friend_gender: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place(name="the garden", setting="a quiet garden", light="soft evening", affords={"pave"}),
    "lane": Place(name="the lane", setting="a little lane", light="twilight", affords={"pave"}),
    "yard": Place(name="the yard", setting="a small yard", light="moonlight", affords={"pave"}),
}

MATERIALS = {
    "stones": Material(id="stones", label="flat stones", plural=True, heavy=True),
    "bricks": Material(id="bricks", label="small bricks", plural=True, heavy=True),
    "tiles": Material(id="tiles", label="smooth tiles", plural=True, heavy=True),
}

TOOLS = {
    "trowel": Tool(id="trowel", label="a little trowel", verb="spread", helps="make the path even"),
    "broom": Tool(id="broom", label="a soft broom", verb="brush", helps="clear the dust"),
    "bucket": Tool(id="bucket", label="a small bucket of water", verb="wet", helps="settle the dust"),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Maya", "Lily", "Ada", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Milo", "Ben", "Leo", "Owen"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, MeteredThing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: MeteredThing) -> MeteredThing:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> MeteredThing:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)

    def trace(self) -> str:
        out = ["--- world trace ---"]
        for ent in self.entities.values():
            bits = []
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            out.append(f"{ent.id}: {ent.kind} {ent.label or ent.phrase} {' '.join(bits)}")
        return "\n".join(out)


def _safe_choice(rng: random.Random, seq):
    if not seq:
        raise StoryError("no valid choices remain")
    return rng.choice(list(seq))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about friendship and paving a small path.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    place = args.place or _safe_choice(rng, PLACES)
    material = args.material or _safe_choice(rng, MATERIALS)
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n != name])
    return StoryParams(place=place, material=material, name=name, friend_name=friend_name, gender=gender, friend_gender=friend_gender)


def can_pave(place: Place, material: Material) -> bool:
    return "pave" in place.affords and material.heavy


def ASP_RULES = r"""
place(garden). place(lane). place(yard).
material(stones). material(bricks). material(tiles).
affords(garden,pave). affords(lane,pave). affords(yard,pave).
heavy(stones). heavy(bricks). heavy(tiles).

can_pave(P,M) :- affords(P,pave), heavy(M).
#show can_pave/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("affords", pid, "pave"))
    for mid, mat in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        if mat.heavy:
            lines.append(asp.fact("heavy", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = {(p, m) for p in PLACES for m in MATERIALS if can_pave(PLACES[p], MATERIALS[m])}
    model = asp.one_model(asp_program("#show can_pave/2."))
    cl = set(asp.atoms(model, "can_pave"))
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    material = MATERIALS[params.material]
    world = World(place)
    child = world.add(Character(id=params.name, type=params.gender, label=params.name))
    friend = world.add(Character(id=params.friend_name, type=params.friend_gender, label=params.friend_name))
    tool = world.add(MeteredThing(id="tool", label=TOOLS["trowel"].label, phrase=TOOLS["trowel"].label))

    child.memes["fondness"] = 1
    friend.memes["fondness"] = 1
    child.memes["friendship"] = 1
    friend.memes["friendship"] = 1

    world.say(f"In {place.name}, under {place.light}, {child.id} and {friend.id} liked to walk slowly together.")
    world.say(f"They loved the little path near home, but it was bumpy and muddy after the rain.")
    world.say(f"{child.id} found {material.label} beside the shed and said they could pave the path before bedtime.")

    if not can_pave(place, material):
        raise StoryError("this story needs a place that allows paving and a heavy path material")

    child.meters["carried"] = 1
    friend.meters["carried"] = 1
    material_piece = world.add(MeteredThing(id="material", label=material.label, phrase=material.label))
    material_piece.meters["weight"] = 1
    world.say(f"{friend.id} brought {TOOLS['broom'].label}, and {child.id} carried the {material.label} carefully.")

    world.say(f"They worked side by side: one {TOOLS['trowel'].verb} the ground, while the other {TOOLS['broom'].verb} away the dust.")
    child.memes["pride"] = 1
    friend.memes["pride"] = 1
    child.meters["paved"] = 1
    friend.meters["paved"] = 1

    if material.plural:
        world.say("Stone by stone, the little path became smooth.")
    else:
        world.say("Piece by piece, the little path became smooth.")

    world.say(f"When they finished, the path no longer wobbled under little feet.")
    world.say(f"{child.id} and {friend.id} sat on the step together and looked at their neat work in the soft dark.")
    world.say(f"Their friendship felt warm and steady, like a lamp left on for the night.")
    world.facts = {
        "child": child,
        "friend": friend,
        "material": material,
        "tool": tool,
        "place": place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story about two friends who pave a small path in {f['place'].name}.",
        f"Tell a gentle story where {f['child'].id} and {f['friend'].id} work together with {f['material'].label}.",
        "Write a calm friendship story that ends with a smooth path and sleepy smiles.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    material = f["material"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who worked together to pave the path in {place.name}?",
            answer=f"{child.id} and {friend.id} worked together as friends to pave the path.",
        ),
        QAItem(
            question=f"What did they use to make the path smooth?",
            answer=f"They used {material.label} and a little tool to make the path smooth.",
        ),
        QAItem(
            question="How did the friends feel when the path was finished?",
            answer="They felt happy and proud because they had made something nice together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to pave something?",
            answer="To pave something means to cover a path or road with stones, bricks, or other hard pieces so it becomes smooth.",
        ),
        QAItem(
            question="Why do friends like to help each other?",
            answer="Friends like to help each other because shared work feels easier and it makes them feel close and kind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", material="stones", name="Mina", friend_name="Eli", gender="girl", friend_gender="boy"),
    StoryParams(place="lane", material="bricks", name="Lily", friend_name="Noah", gender="girl", friend_gender="boy"),
    StoryParams(place="yard", material="tiles", name="Theo", friend_name="Ivy", gender="boy", friend_gender="girl"),
]


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show can_pave/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

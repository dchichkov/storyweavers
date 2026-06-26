#!/usr/bin/env python3
"""
storyworlds/worlds/garb_pack_reconciliation_nursery_rhyme.py
============================================================

A tiny nursery-rhyme story world about garb, a pack, and reconciliation.

Premise:
A little child wants to dress up and go out with a special pack of things,
but a worried companion fears the outfit and pack will be muddled or lost.
They quarrel, pause, and then make peace by packing neatly and sharing care.

The simulation tracks:
- physical meters: tidiness, wear, weight, patch, sparkle
- emotional memes: joy, worry, pride, hurt, tenderness, calm, friendship

The prose is intentionally child-facing and rhythmic, with clear setup,
a small turn, and a gentle reconciliation at the end.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tidiness", "wear", "weight", "patch", "sparkle"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "hurt", "tenderness", "calm", "friendship"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    can_pack: bool = True
    can_dress: bool = True


@dataclass
class Garb:
    id: str
    label: str
    phrase: str
    region: str
    lovely: str
    risk: str
    style: str = "bright"


@dataclass
class Pack:
    id: str
    label: str
    phrase: str
    kind: str
    tidy_boost: float
    holds: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


SETTINGS = {
    "nursery": Setting("the nursery", indoors=True, can_pack=True, can_dress=True),
    "garden": Setting("the garden path", indoors=False, can_pack=True, can_dress=True),
    "porch": Setting("the porch", indoors=False, can_pack=True, can_dress=True),
}

GARB = {
    "ribbon": Garb("ribbon", "a ribbon", "a bright ribbon", "head", "shiny", "tugged loose"),
    "cloak": Garb("cloak", "a cloak", "a soft cloak", "torso", "swished crooked"),
    "boots": Garb("boots", "boots", "little boots", "feet", "got muddied"),
}

PACKS = {
    "satchel": Pack("satchel", "a satchel", "a little satchel", "small", 1.0, holds={"ribbon", "cloak"}),
    "basket": Pack("basket", "a basket", "a woven basket", "medium", 1.0, holds={"boots", "ribbon"}),
}


@dataclass
class StoryParams:
    place: str
    garb: str
    pack: str
    name: str
    friend: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lily", "Nora", "Poppy", "Tess", "Wren"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Otto", "Jack", "Ned"]
FRIENDS = ["mother", "father", "sister", "brother"]
TRAITS = ["merry", "little", "brave", "cheery", "tiny"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for g in GARB:
            for p in PACKS:
                if g in PACKS[p].holds:
                    out.append((place, g, p))
    return out


def explain_rejection(garb: Garb, pack: Pack) -> str:
    return (
        f"(No story: {pack.label} does not reasonably carry {garb.label} in this little world. "
        f"Choose a pack whose pockets can hold that garb.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about garb, a pack, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--garb", choices=GARB)
    ap.add_argument("--pack", choices=PACKS)
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=FRIENDS)
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
    if args.garb and args.pack:
        if args.garb not in PACKS[args.pack].holds:
            raise StoryError(explain_rejection(GARB[args.garb], PACKS[args.pack]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.garb is None or c[1] == args.garb)
              and (args.pack is None or c[2] == args.pack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, garb, pack = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    return StoryParams(place=place, garb=garb, pack=pack, name=name, friend=friend)


def reasonableness_gate(params: StoryParams) -> None:
    if params.garb not in PACKS[params.pack].holds:
        raise StoryError(explain_rejection(GARB[params.garb], PACKS[params.pack]))


def _show(name: str, *args) -> str:
    if not args:
        return f"{name}."
    return f"{name}({','.join(json.dumps(a, ensure_ascii=False) if isinstance(a, str) else str(a) for a in args)})."


def asp_facts() -> str:
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(_show("setting", sid))
        if s.indoors:
            lines.append(_show("indoors", sid))
    for gid, g in GARB.items():
        lines.append(_show("garb", gid))
        lines.append(_show("worn_on", gid, g.region))
    for pid, p in PACKS.items():
        lines.append(_show("pack", pid))
        for h in sorted(p.holds):
            lines.append(_show("holds", pid, h))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(G, P) :- garb(G), pack(P), holds(P, G).
valid_story(S, G, P) :- setting(S), compatible(G, P).
#show valid_story/3.
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def make_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    child = w.add(Entity(id=params.name, kind="character", type="child"))
    kin = w.add(Entity(id="Kin", kind="character", type=params.friend, label=f"the {params.friend}"))
    garb = w.add(Entity(id="Garb", type="garb", label=GARB[params.garb].label, phrase=GARB[params.garb].phrase, owner=child.id))
    pack = w.add(Entity(id="Pack", type="pack", label=PACKS[params.pack].label, phrase=PACKS[params.pack].phrase, owner=child.id, caretaker=kin.id))
    garb.worn_by = child.id
    pack.worn_by = child.id
    pack.meters["weight"] = 1.0
    return w


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    w = make_world(params)
    child = w.get(params.name)
    kin = w.get("Kin")
    garb = w.get("Garb")
    pack = w.get("Pack")
    garb_def = GARB[params.garb]
    pack_def = PACKS[params.pack]

    child.memes["joy"] += 1
    child.memes["pride"] += 1
    w.say(f"{child.id} was a little merry child in {w.setting.place}, and {child.pronoun()} loved {garb_def.label} and {pack_def.label}.")
    w.say(f"{child.id} had {garb_def.phrase} tucked near {pack_def.phrase}, and every ribbon seemed to sing a soft, sweet song.")

    w.para()
    child.memes["desire"] = 1.0
    kin.memes["worry"] += 1
    w.say(f"One day, {child.id} wanted to go {('out' if not w.setting.indoors else 'around')} and wear {garb_def.label} with {pack_def.label}.")
    w.say(f"But {kin.pronoun('possessive')} {params.friend} grew worried, for the {garb_def.lovely} might get {garb_def.risk} if they hurried too hard.")

    child.memes["hurt"] += 1
    child.memes["hurt_by_warning"] = 1.0
    child.memes["hurt"] += 0.5
    kin.memes["worry"] += 0.5
    w.say(f"{child.id} frowned and said, 'I want my pretty {garb_def.label}!'")
    w.say(f"{kin.pronoun().capitalize()} said, 'We can still play, but we must pack with care and keep the day from going awry.'")

    w.para()
    child.memes["hurt"] += 0.5
    kin.memes["hurt"] += 0.5
    w.say(f"{child.id} turned away, but the little heart still felt the tug of the tune.")
    w.say(f"Then {child.id} and {kin.id} sat by the little {pack_def.label}, and the room grew calm as the moon.")

    pack.meters["tidiness"] += pack_def.tidy_boost
    child.memes["tenderness"] += 1.0
    kin.memes["tenderness"] += 1.0
    child.memes["calm"] += 1.0
    kin.memes["calm"] += 1.0
    child.memes["hurt"] = 0.0
    kin.memes["worry"] = 0.0

    w.say(f"They folded the {garb_def.label}, tucked it into {pack_def.phrase}, and tied it with a neat little bow.")
    w.say(f"{kin.pronoun().capitalize()} showed {child.id} how to carry the pack so the {garb_def.label} would stay fine and new.")

    child.memes["joy"] += 1.0
    kin.memes["friendship"] += 1.0
    child.memes["friendship"] += 1.0
    w.para()
    w.say(f"Then {child.id} smiled, and {kin.id} smiled too; their quarrel faded like morning dew.")
    w.say(f"Together they went on, {garb_def.label} tidy and bright, {pack_def.label} snug at the side, and peace in the light.")

    w.facts.update(child=child, kin=kin, garb=garb, pack=pack, params=params)
    return w


def generation_prompts(w: World) -> list[str]:
    p = w.facts["params"]
    return [
        f'Write a short nursery-rhyme story about {p.name}, {p.garb}, and {p.pack}.',
        f"Tell a gentle tale where {p.name} wants to wear {GARB[p.garb].label} with {PACKS[p.pack].label}, but {p.friend} worries, and they make peace.",
        f"Write a rhyme-like story set in {p.place} that begins with a little child and ends with reconciliation.",
    ]


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    child = w.facts["child"]
    kin = w.facts["kin"]
    garb = w.facts["garb"]
    pack = w.facts["pack"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with {garb.label} and {pack.label}?",
            answer=f"{child.id} wanted to wear {garb.phrase} with {pack.phrase} and go out to play.",
        ),
        QAItem(
            question=f"Why did {kin.label} worry about the {garb.label}?",
            answer=f"{kin.label} worried that the {garb.lovely} would get {garb.risk} if they rushed about too quickly.",
        ),
        QAItem(
            question=f"How did {child.id} and {kin.label} make things right?",
            answer=f"They sat together, packed the {garb.label} neatly into {pack.label}, and turned their quarrel into friendship.",
        ),
    ]


KNOWLEDGE = {
    "garb": [("What is garb?", "Garb is clothing or dress-up clothes, like a pretty outfit for play or a special day.")],
    "pack": [("What is a pack?", "A pack is something that carries things together, like a bag, satchel, or basket.")],
    "tidiness": [("Why do people pack things neatly?", "Packing neatly helps keep things safe, easy to find, and less likely to get squashed or lost.")],
    "friendship": [("What does reconciliation mean?", "Reconciliation means making peace after a disagreement and being friendly again.")],
}


def world_knowledge_qa(w: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["garb", "pack", "tidiness", "friendship"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in w.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", garb="ribbon", pack="satchel", name="Mina", friend="mother"),
    StoryParams(place="garden", garb="boots", pack="basket", name="Finn", friend="father"),
    StoryParams(place="porch", garb="cloak", pack="satchel", name="Lily", friend="sister"),
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible (setting, garb, pack) combos:\n")
        for item in items:
            print("  ", item)
        return

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
            header = f"### {p.name}: {p.garb} with {p.pack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

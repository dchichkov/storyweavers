#!/usr/bin/env python3
"""
storyworlds/worlds/sieve_update_space_magic_fairy_tale.py
=========================================================

A small fairy-tale storyworld about a magic sieve, a needed update, and a tiny
space problem that is solved by care, kindness, and a little enchantment.

Seed-inspired premise:
- A child or helper needs to sort magical crumbs, sparkles, or moon-dust with a sieve.
- The sieve gets clogged or outdated, so an update is needed.
- A cramped space or crowded shelf creates tension.
- Magic helps transform the situation in a gentle fairy-tale way.

The simulated world uses typed entities with physical meters and emotional memes.
State changes drive the prose: the sieve can clog, the workshop can feel crowded,
and an update spell can clear or improve the system. The ending proves the change.
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def ensure(self) -> None:
        for k in ("clogged", "updated", "crowded", "sparkle", "order", "joy", "worry", "relief"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "fairy", "mother", "woman"}
        male = {"boy", "king", "wizard", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    space: str
    crowded: bool = False
    magical: bool = False


@dataclass
class Sieve:
    id: str
    label: str
    purpose: str
    mesh: str
    magical: bool = True
    can_update: bool = True


@dataclass
class Update:
    id: str
    label: str
    spell: str
    effect: str
    magical: bool = True


@dataclass
class Dust:
    id: str
    label: str
    kind: str
    mess: str
    glittery: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        ent.ensure()
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    sieve: str
    update: str
    space: str
    dust: str
    seed: Optional[int] = None


PLACES = {
    "tower": Place(id="tower", label="the moonlit tower room", space="a narrow shelf", crowded=True, magical=True),
    "garden": Place(id="garden", label="the old garden shed", space="a tiny workbench", crowded=True, magical=True),
    "castle": Place(id="castle", label="the castle pantry", space="a cramped corner", crowded=True, magical=False),
}

SIEVES = {
    "golden_sieve": Sieve(id="golden_sieve", label="a golden sieve", purpose="sort sparkle bits", mesh="fine"),
    "star_sieve": Sieve(id="star_sieve", label="a starry sieve", purpose="catch moon-dust", mesh="gentle"),
}

UPDATES = {
    "glimmer_update": Update(id="glimmer_update", label="a glimmering update", spell="whisper a better pattern", effect="the mesh loosens and brightens"),
    "lattice_update": Update(id="lattice_update", label="a lattice update", spell="murmur a new weave", effect="the holes line up just right"),
}

DUSTS = {
    "sparkles": Dust(id="sparkles", label="sparkles", kind="sparkles", mess="shiny", glittery=True),
    "moon_dust": Dust(id="moon_dust", label="moon-dust", kind="moon-dust", mess="pale", glittery=True),
}

GIRL_NAMES = ["Mina", "Luna", "Ella", "Nora", "Ivy", "Rosie"]
BOY_NAMES = ["Theo", "Finn", "Ari", "Leo", "Ned", "Owen"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACES:
        for s in SIEVES:
            for u in UPDATES:
                for d in DUSTS:
                    out.append((p, s, u, d))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a magic sieve, an update, and a cramped space.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sieve", choices=SIEVES)
    ap.add_argument("--update", choices=UPDATES)
    ap.add_argument("--space", choices=["shelf", "corner", "bench"])
    ap.add_argument("--dust", choices=DUSTS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=["fairy", "wizard", "queen"])
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.sieve:
        combos = [c for c in combos if c[1] == args.sieve]
    if args.update:
        combos = [c for c in combos if c[2] == args.update]
    if args.dust:
        combos = [c for c in combos if c[3] == args.dust]
    if not combos:
        raise StoryError("No valid story matches the given options.")

    place, sieve, update, dust = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    guide_type = args.guide_type or rng.choice(["fairy", "wizard", "queen"])
    guide_name = args.guide or rng.choice(["Aster", "Maris", "Bran", "Eira"])
    space = args.space or rng.choice(["shelf", "corner", "bench"])
    return StoryParams(place, child_name, child_type, guide_name, guide_type, sieve, update, space, dust)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place == "castle" and params.space == "bench":
        raise StoryError("The castle pantry is too narrow for a bench-sized ending.")
    if params.sieve not in SIEVES or params.update not in UPDATES or params.dust not in DUSTS:
        raise StoryError("Invalid registry choice.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    sieve = SIEVES[params.sieve]
    update = UPDATES[params.update]
    dust = DUSTS[params.dust]

    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, label=params.guide_name))
    s = world.add(Entity(id="sieve", type="tool", label=sieve.label, phrase=sieve.purpose, attrs={"mesh": sieve.mesh}))
    u = world.add(Entity(id="update", type="magic", label=update.label, phrase=update.spell))
    d = world.add(Entity(id="dust", type="thing", label=dust.label, phrase=dust.mess))

    # initialize all values before use
    child.meters["worry"] = 0.0
    child.meters["joy"] = 0.0
    guide.meters["relief"] = 0.0
    s.meters["clogged"] = 0.0
    s.meters["updated"] = 0.0
    d.meters["sparkle"] = 0.0
    world.place.crowded = True

    child.memes["worry"] = 1.0
    guide.memes["joy"] = 0.0

    world.say(f"Once upon a time, {child.label} lived near {place.label}.")
    world.say(f"{guide.label} brought {s.label} to {sieve.purpose} in {world.place.space}, but the little space felt crowded.")
    world.say(f"On the table lay {d.label}, bright as a bit of starlight, and the sieve grew clogged as soon as the child began.")

    # state-driven changes
    s.meters["clogged"] += 1.0
    child.memes["worry"] += 1.0
    world.para()
    world.say(f"{child.label} frowned. The sieve could not do its work in such a tight space.")
    world.say(f"{guide.label} smiled and offered {u.label}: {u.phrase}.")
    u.meters["updated"] += 1.0

    # magic update clears clutter and improves space
    s.meters["clogged"] = 0.0
    s.meters["updated"] = 1.0
    place.crowded = False
    child.memes["worry"] = 0.0
    child.memes["joy"] += 1.0
    guide.memes["relief"] += 1.0

    world.para()
    world.say(f"{guide.label.capitalize()} spoke the spell and the sieve changed at once; {update.effect}.")
    world.say(f"The cramped {params.space} seemed to stretch into a kinder little space for careful hands.")
    world.say(f"{child.label} tried again, and this time the {d.label} shone through the sieve like dawn.")

    world.para()
    world.say(f"By the end, {child.label} had sorted the {d.label} neatly, and the old crowding was gone.")
    world.say(f"{guide.label} laughed softly, and the magic sieve rested bright and ready on the table.")

    world.facts = {
        "child": child,
        "guide": guide,
        "sieve": s,
        "update": u,
        "dust": d,
        "place": place,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle fairy tale about {p.child_name} and a magic sieve in a cramped space.",
        f"Tell a short story where a sieve needs an update so {p.child_name} can sort {DUSTS[p.dust].label}.",
        f"Create a fairy-tale ending in which magic makes the space kinder and the sieve works again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    guide = world.facts["guide"]
    sieve = world.facts["sieve"]
    update = world.facts["update"]
    dust = world.facts["dust"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label} and {guide.label}, who worked together near {place.label}.",
        ),
        QAItem(
            question=f"What did {guide.label} give to help?",
            answer=f"{guide.label} gave {child.label} {update.label}, a magical fix that helped the sieve work again.",
        ),
        QAItem(
            question=f"Why did the sieve need help?",
            answer=f"The sieve got clogged in the small space, so it could not sort the {dust.label} well until the magic update changed it.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The crowded space became kinder and the sieve became ready again, so {child.label} could sort the {dust.label} neatly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sieve?", answer="A sieve is a tool with tiny holes that lets small bits pass through and holds bigger bits back."),
        QAItem(question="What does an update do?", answer="An update changes something so it works in a newer or better way."),
        QAItem(question="What is space?", answer="Space is the room around things, where they can fit, move, and breathe a little easier."),
        QAItem(question="What is magic in a fairy tale?", answer="Magic is a special story power that can change things in surprising but gentle ways."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Sieve,Update,Dust) :- place(Place), sieve(Sieve), update(Update), dust(Dust).
crowded_space(Place) :- place(Place), crowded(Place).
sieve_needs_update(Sieve) :- sieve(Sieve), can_update(Sieve).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].crowded:
            lines.append(asp.fact("crowded", p))
    for s in SIEVES:
        lines.append(asp.fact("sieve", s))
        if SIEVES[s].can_update:
            lines.append(asp.fact("can_update", s))
    for u in UPDATES:
        lines.append(asp.fact("update", u))
    for d in DUSTS:
        lines.append(asp.fact("dust", d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("tower", "Mina", "girl", "Aster", "fairy", "golden_sieve", "glimmer_update", "shelf", "sparkles"),
    StoryParams("garden", "Theo", "boy", "Eira", "queen", "star_sieve", "lattice_update", "bench", "moon_dust"),
    StoryParams("castle", "Luna", "girl", "Maris", "wizard", "golden_sieve", "glimmer_update", "corner", "sparkles"),
]


if __name__ == "__main__":
    main()

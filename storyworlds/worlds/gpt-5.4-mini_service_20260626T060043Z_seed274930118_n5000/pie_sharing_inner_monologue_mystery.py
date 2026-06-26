#!/usr/bin/env python3
"""
storyworlds/worlds/pie_sharing_inner_monologue_mystery.py
=========================================================

A small story world about pie, sharing, and a gentle mystery.

Premise:
- A child has a pie to share.
- Someone asks for a piece, but a piece seems missing or mistaken.
- The child notices clues, thinks through them, and learns how to share fairly.

The world is built around:
- physical state: pie slices, plates, crumbs, and who holds what
- emotional state: curiosity, worry, pride, fairness, relief
- inner monologue: the child's private thoughts as part of the mystery tone
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Pie:
    id: str
    flavor: str
    slices: int
    whole_phrase: str
    plate_phrase: str
    clue_color: str


@dataclass
class StoryParams:
    place: str
    pie: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_missing_slice(world: World) -> list[str]:
    out: list[str] = []
    pie = world.get("pie")
    child = world.get("child")
    if pie.meters.get("slices", 0) >= 1 and child.memes.get("curiosity", 0) >= THRESHOLD:
        sig = ("missing_slice",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["mystery"] = "slice_missing"
            out.append(f"{child.pronoun().capitalize()} noticed one slice was gone.")
    return out


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    pie = world.get("pie")
    if pie.meters.get("crumbs", 0) >= THRESHOLD:
        sig = ("crumbs",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["crumbs"] = True
            out.append("Tiny crumbs dotted the plate like a trail.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    guest = world.get("guest")
    pie = world.get("pie")
    if child.memes.get("fairness", 0) >= THRESHOLD and pie.meters.get("slices", 0) >= 2:
        sig = ("share",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["shared"] = True
            pie.meters["slices"] -= 1
            guest.held_by = child.id
            out.append(f"{child.pronoun().capitalize()} cut a clean slice and placed it on {guest.label}.")
    return out


CAUSAL_RULES = [_r_missing_slice, _r_crumbs, _r_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    pie = sim.get("pie")
    return {
        "shared": sim.facts.get("shared", False),
        "slices_left": pie.meters.get("slices", 0),
    }


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.memes.keys() if t not in {"curiosity", "worry", "fairness", "relief"}), "careful")
    world.say(
        f"{child.id} was a little {child.type} who liked noticing tiny details. "
        f"{child.pronoun().capitalize()} was {trait} and always looked twice."
    )


def set_scene(world: World, setting: Setting, pie: Pie, child: Entity, parent: Entity, guest: Entity) -> None:
    world.say(
        f"One afternoon at {setting.place}, a {pie.flavor} pie waited on the table."
    )
    world.say(
        f"{child.id} had promised to share {child.pronoun('possessive')} {pie.label} with {guest.label}, while {parent.label} watched nearby."
    )


def notice_mystery(world: World, child: Entity, pie: Pie) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} leaned closer. One slice should have matched the others, but the plate looked uneven."
    )
    world.say(
        f'"Something is different," {child.id} thought. "Did someone take a piece, or did I count wrong?"'
    )


def question_and_clue(world: World, child: Entity, parent: Entity, pie: Pie) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id} asked {parent.label} quietly about the pie."
    )
    world.say(
        f"{parent.label} pointed to the little crumbs. " + "\"Look carefully,\"" + f" {parent.pronoun('subject')} said. \"The answer is in the clues.\""
    )
    pie.meters["crumbs"] = pie.meters.get("crumbs", 0) + 1
    propagate(world, narrate=True)
    world.say(
        f'{child.id} thought again. "Maybe I didn't lose a slice at all. Maybe I forgot where I put it."'
    )


def resolve(world: World, child: Entity, guest: Entity, pie: Pie) -> None:
    child.memes["fairness"] = child.memes.get("fairness", 0) + 1
    world.say(
        f"{child.id} smiled, because the mystery was really about sharing, not losing."
    )
    propagate(world, narrate=True)
    if world.facts.get("shared"):
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        world.say(
            f"{child.id} handed over the slice and watched {guest.label} take a happy bite."
        )
        world.say(
            f"At the end, the pie was smaller, the table was calmer, and everyone had a piece."
        )
    else:
        world.say(
            f"{child.id} carefully counted the slices again and made a new plan so everyone could get one."
        )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"pie"}),
    "porch": Setting(place="the porch", affords={"pie"}),
    "picnic_table": Setting(place="the picnic table", affords={"pie"}),
}

PIES = {
    "apple": Pie(
        id="apple",
        flavor="apple",
        slices=4,
        whole_phrase="a warm apple pie",
        plate_phrase="the pie plate",
        clue_color="golden",
    ),
    "berry": Pie(
        id="berry",
        flavor="berry",
        slices=4,
        whole_phrase="a berry pie",
        plate_phrase="the pie plate",
        clue_color="purple",
    ),
    "pumpkin": Pie(
        id="pumpkin",
        flavor="pumpkin",
        slices=4,
        whole_phrase="a pumpkin pie",
        plate_phrase="the pie plate",
        clue_color="orange",
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Sam", "Max", "Finn"]
TRAITS = ["careful", "curious", "quiet", "patient", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery about pie sharing and inner thoughts.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--pie", choices=PIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, pie) for place, s in SETTINGS.items() for pie in s.affords]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.pie is None or c[1] == args.pie)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, pie = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, pie=pie, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    pie_cfg = PIES[params.pie]
    world = World(setting)

    child = world.add(Entity(
        id="child", kind="character", type=params.gender, label=params.name,
        memes={params.trait: 1.0},
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent, label=params.parent,
    ))
    guest = world.add(Entity(
        id="guest", kind="character", type="boy" if params.gender == "girl" else "girl",
        label="the neighbor", memes={"polite": 1.0},
    ))
    pie = world.add(Entity(
        id="pie", type="pie", label="pie", phrase=pie_cfg.whole_phrase,
        owner=child.id, meters={"slices": float(pie_cfg.slices)},
    ))

    world.facts["pie_flavor"] = pie_cfg.flavor
    world.facts["place"] = setting.place
    world.facts["name"] = params.name
    world.facts["guest"] = guest.label

    introduce(world, child)
    world.para()
    set_scene(world, setting, pie_cfg, child, parent, guest)
    notice_mystery(world, child, pie_cfg)
    question_and_clue(world, child, parent, pie_cfg)
    world.para()
    resolve(world, child, guest, pie_cfg)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short story for a child about a {f["pie_flavor"]} pie, a missing slice, and sharing.',
        f'Tell a gentle mystery where {f["name"]} thinks about a pie and notices clues before sharing.',
        f'Write a simple story set at {f["place"]} that uses inner monologue and ends with pie being shared fairly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("child")
    parent = world.get("parent")
    guest = world.get("guest")
    pie = world.get("pie")
    return [
        QAItem(
            question=f"What kind of pie was in the story?",
            answer=f"It was a {f['pie_flavor']} pie.",
        ),
        QAItem(
            question=f"Why did {child.id} think something was strange about the pie?",
            answer=f"{child.id} noticed that one slice did not seem to match the others, so {child.pronoun('subject')} thought carefully about the missing piece and the crumbs on the plate.",
        ),
        QAItem(
            question=f"How did {child.id} solve the mystery?",
            answer=f"{child.id} looked at the clues, talked with {parent.label}, and then shared a slice with {guest.label}. That turned the mystery into a fair plan.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The pie had fewer slices, but the table felt calmer because {child.id} shared it kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pie?",
            answer="Pie is a baked food with a crust and a sweet or savory filling, often cut into slices to share.",
        ),
        QAItem(
            question="Why do people share pie?",
            answer="People share pie so everyone can have a piece and enjoy it together.",
        ),
        QAItem(
            question="What can crumbs tell you?",
            answer="Crumbs can be a clue that something was eaten, moved, or handled nearby.",
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
pie_filled(P) :- pie(P), slices(P,N), N > 0.
clue_present(P) :- crumbs(P).
mystery(P) :- pie(P), clue_present(P).
shared(P) :- pie(P), slices(P,N), N < 4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", place, item))
    for pid, pie in PIES.items():
        lines.append(asp.fact("pie", pid))
        lines.append(asp.fact("flavor", pid, pie.id))
        lines.append(asp.fact("slices", pid, pie.slices))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show shared/1."))
    clingo_set = set(asp.atoms(model, "shared"))
    python_set = {(k,) for k in PIES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches the simple pie inventory ({len(clingo_set)} pies).")
        return 0
    print("MISMATCH between clingo and python pie inventory:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


CURATED = [
    StoryParams(place="kitchen", pie="apple", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", pie="berry", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="picnic_table", pie="pumpkin", name="Nora", gender="girl", parent="mother", trait="patient"),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is pie?", answer="Pie is a baked food with a crust and a filling, usually cut into slices to share."),
        QAItem(question="Why are crumbs useful as clues?", answer="Crumbs can show that something was moved or eaten nearby, so they help solve a mystery."),
        QAItem(question="What does sharing mean?", answer="Sharing means letting other people have some of what you have, like giving someone a slice of pie."),
    ]


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
        print(asp_program("#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shared/1."))
        print(sorted(set(asp.atoms(model, "shared"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/seamstress_twist_misunderstanding_bedtime_story.py
========================================================================================================

A small, self-contained bedtime-story world about a seamstress, a twist, and a
gentle misunderstanding that gets cleared up before sleep.

Premise sketch:
- A child loves a soft bedtime garment made by a seamstress.
- A twisted ribbon or sleeve makes the child worry.
- The misunderstanding grows because the child thinks the garment is ruined.
- The seamstress notices the real problem, fixes the twist, and the child falls
  asleep feeling safe and loved.

The world is simulated with physical meters and emotional memes. The prose is
generated from the simulated state, not from a frozen template.
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


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little bedroom"
    bedtime: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    twist_zone: str = "neck"
    gender_ok: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Twist:
    id: str
    label: str
    action: str
    cause: str
    fix: str
    untwist_clause: str


@dataclass
class Misunderstanding:
    id: str
    label: str
    worry: str
    correction: str
    resolution: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the little bedroom", bedtime=True),
    "nursery": Setting(place="the nursery", bedtime=True),
}

CHILDREN = {
    "girl": ["Mina", "Luna", "Nora", "Poppy", "Tess"],
    "boy": ["Eli", "Noah", "Finn", "Theo", "Sam"],
}

TRAITS = ["sleepy", "gentle", "curious", "quiet", "small", "brave"]

ITEMS = {
    "nightgown": Item(
        id="nightgown",
        label="nightgown",
        phrase="a soft blue nightgown",
        kind="bedwear",
        twist_zone="neck",
        gender_ok={"girl"},
    ),
    "pajamas": Item(
        id="pajamas",
        label="pajamas",
        phrase="warm striped pajamas",
        kind="bedwear",
        twist_zone="waist",
        gender_ok={"girl", "boy"},
    ),
    "blanket": Item(
        id="blanket",
        label="blanket",
        phrase="a stitched patchwork blanket",
        kind="blanket",
        twist_zone="corner",
        gender_ok={"girl", "boy"},
    ),
}

TWISTS = {
    "ribbon": Twist(
        id="ribbon",
        label="a ribbon twist",
        action="twisted around the collar",
        cause="a sleepy tug",
        fix="smooth it flat with careful fingers",
        untwist_clause="smoothed the ribbon flat",
    ),
    "sleeve": Twist(
        id="sleeve",
        label="a sleeve twist",
        action="got folded the wrong way",
        cause="a quick bedtime spin",
        fix="straighten the sleeve",
        untwist_clause="straightened the sleeve",
    ),
    "blanket_corner": Twist(
        id="blanket_corner",
        label="a blanket twist",
        action="got knotted in one corner",
        cause="too much turning under the quilt",
        fix="loosen the corner knot",
        untwist_clause="loosened the corner knot",
    ),
}

MISUNDERSTANDINGS = {
    "ruined": Misunderstanding(
        id="ruined",
        label="ruined",
        worry="the child thinks the bedtime thing is ruined",
        correction="the seamstress explains that a twist is only a tiny tangle",
        resolution="the child learns that one twist does not spoil the whole night",
    ),
    "stuck": Misunderstanding(
        id="stuck",
        label="stuck",
        worry="the child thinks nothing can be fixed now",
        correction="the seamstress shows how soft hands can guide the fabric free",
        resolution="the child sees that careful hands can untangle almost anything",
    ),
}


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    item: str
    twist: str
    misunderstanding: str
    seamstress_name: str = "Mrs. Willow"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, item: str, twist: str, misunderstanding: str, gender: str) -> bool:
    if setting not in SETTINGS or item not in ITEMS or twist not in TWISTS or misunderstanding not in MISUNDERSTANDINGS:
        return False
    if gender not in ITEMS[item].gender_ok:
        return False
    if item == "blanket" and twist != "blanket_corner":
        return False
    if item != "blanket" and twist == "blanket_corner":
        return False
    if misunderstanding == "ruined" and twist == "ribbon" and item == "blanket":
        return False
    return True


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the chosen twist, item, or misunderstanding does not fit a gentle bedtime fix.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(S,I,T,M,G) :- setting(S), item(I), twist(T), misunderstanding(M), gender(G),
                         gender_ok(I,G),
                         fits(I,T),
                         story_fit(I,T,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, item.kind))
        lines.append(asp.fact("twist_zone", iid, item.twist_zone))
        for g in sorted(item.gender_ok):
            lines.append(asp.fact("gender_ok", iid, g))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        lines.append(asp.fact("fits", "nightgown" if tid == "ribbon" else "pajamas" if tid == "sleeve" else "blanket", tid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for g in CHILDREN:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/5."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set((s, i, t, m, g) for (s, i, t, m, g) in asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if py - asps:
        print(" only in python:", sorted(py - asps))
    if asps - py:
        print(" only in clingo:", sorted(asps - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for i in ITEMS:
            for t in TWISTS:
                for m in MISUNDERSTANDINGS:
                    for g in CHILDREN:
                        if valid_combo(s, i, t, m, g):
                            out.append((s, i, t, m, g))
    return out


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        traits=["little", "sleepy", "gentle"],
    ))
    seamstress = world.add(Entity(
        id="seamstress",
        kind="character",
        type="woman",
        label=params.seamstress_name,
        traits=["careful", "kind"],
    ))
    item = world.add(Entity(
        id="item",
        type="thing",
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=child.id,
        caretaker=seamstress.id,
        worn_by=child.id,
        meters={"twist": 0.0, "neat": 1.0},
        memes={"love": 1.0},
    ))
    world.facts.update(child=child, seamstress=seamstress, item=item, params=params)
    return world


def introduce(world: World) -> None:
    c = world.facts["child"]
    world.say(f"{c.label} was a little {c.traits[0]} {c.type} who loved bedtime.")
    world.say(f"Every night, {c.label} wore {world.facts['item'].phrase} and listened for the soft sounds of the house.")


def twist_occurs(world: World, twist: Twist) -> None:
    item = world.facts["item"]
    item.meters["twist"] += 1.0
    item.meters["neat"] = 0.0
    world.facts["twist_seen"] = True
    world.say(
        f"One night, {twist.label} {twist.action}, because of {twist.cause}."
    )
    world.say(
        f"{world.facts['child'].label} noticed it and felt a small pinch of worry."
    )


def misunderstanding_grows(world: World, mis: Misunderstanding) -> None:
    child = world.facts["child"]
    world.facts["misunderstanding"] = True
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    child.memes["sad"] = child.memes.get("sad", 0.0) + 0.5
    world.say(
        f"{child.label} thought {mis.worry}, so {child.pronoun()} hugged the blanket tighter and frowned."
    )


def seamstress_notices(world: World, twist: Twist, mis: Misunderstanding) -> None:
    seamstress = world.facts["seamstress"]
    child = world.facts["child"]
    world.para()
    world.say(
        f"{seamstress.label} came in with a quiet smile and looked closely."
    )
    world.say(
        f"\"Oh, sweetheart,\" {seamstress.pronoun('subject')} said, \"{mis.correction}, and I can {twist.fix}.\""
    )
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1.0
    world.facts["correction_offered"] = True


def fix_twist(world: World, twist: Twist, mis: Misunderstanding) -> None:
    item = world.facts["item"]
    child = world.facts["child"]
    seamstress = world.facts["seamstress"]
    item.meters["twist"] = 0.0
    item.meters["neat"] = 1.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
    world.say(
        f"With gentle fingers, {seamstress.label} {twist.untwist_clause}, and the bedtime thing looked lovely again."
    )
    world.say(
        f"{child.label} blinked, then smiled, because {mis.resolution}."
    )


def ending(world: World) -> None:
    child = world.facts["child"]
    seamstress = world.facts["seamstress"]
    item = world.facts["item"]
    world.para()
    world.say(
        f"At last, {child.label} tucked under the covers with {item.phrase}, neat and soft."
    )
    world.say(
        f"{seamstress.label} kissed the top of {child.label}'s head, and the room grew still and warm."
    )
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro_twist = TWISTS[params.twist]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    introduce(world)
    world.para()
    twist_occurs(world, intro_twist)
    misunderstanding_grows(world, mis)
    seamstress_notices(world, intro_twist, mis)
    fix_twist(world, intro_twist, mis)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a gentle bedtime story about {p.child_name}, a seamstress, and a small twist that causes a misunderstanding.",
        f"Tell a cozy story where {p.child_name} worries that {ITEMS[p.item].label} is ruined, but a seamstress fixes the problem before sleep.",
        f"Write a child-friendly bedtime tale with the words seamstress, twist, and misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    seamstress = world.facts["seamstress"]
    item = world.facts["item"]
    twist = TWISTS[p.twist]
    mis = MISUNDERSTANDINGS[p.misunderstanding]
    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.label}, who loved bedtime and wore {item.phrase}.",
        ),
        QAItem(
            question=f"What problem happened to {item.label}?",
            answer=f"{twist.label} {twist.action}, so {child.label} thought something was wrong.",
        ),
        QAItem(
            question=f"How did {seamstress.label} help?",
            answer=f"{seamstress.label} gently fixed the twist and showed that {mis.resolution}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.label} calm and cozy in bed, while {item.label} looked neat again.",
        ),
    ]


KNOWLEDGE = {
    "seamstress": [
        QAItem(
            question="What does a seamstress do?",
            answer="A seamstress makes, mends, or adjusts clothes and fabric so they fit and stay nice.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in fabric?",
            answer="A twist is a part that has turned or tangled a little, so it may need to be smoothed out.",
        )
    ],
    "misunderstanding": [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is wrong, but the real meaning is different.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why is bedtime often quiet?",
            answer="Bedtime is often quiet because people are getting ready to sleep and settle down.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    return [q for q in KNOWLEDGE["seamstress"] + KNOWLEDGE["twist"] + KNOWLEDGE["misunderstanding"] + KNOWLEDGE["bedtime"]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: seamstress, twist, misunderstanding.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--twist", choices=list(TWISTS))
    ap.add_argument("--misunderstanding", choices=list(MISUNDERSTANDINGS))
    ap.add_argument("--gender", choices=list(CHILDREN))
    ap.add_argument("--name")
    ap.add_argument("--seamstress-name", default="Mrs. Willow")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    item_choices = [i for i, item in ITEMS.items() if gender in item.gender_ok]
    item = args.item or rng.choice(item_choices)
    twist_choices = [t for t in TWISTS if (item == "blanket" and t == "blanket_corner") or (item != "blanket" and t != "blanket_corner")]
    twist = args.twist or rng.choice(twist_choices)
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    if not valid_combo(setting, item, twist, misunderstanding, gender):
        raise StoryError(explain_invalid(StoryParams(setting, "", gender, item, twist, misunderstanding)))
    name = args.name or rng.choice(CHILDREN[gender])
    return StoryParams(
        setting=setting,
        child_name=name,
        child_gender=gender,
        item=item,
        twist=twist,
        misunderstanding=misunderstanding,
        seamstress_name=args.seamstress_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="bedroom", child_name="Mina", child_gender="girl", item="nightgown", twist="ribbon", misunderstanding="ruined"),
    StoryParams(setting="nursery", child_name="Eli", child_gender="boy", item="pajamas", twist="sleeve", misunderstanding="stuck"),
    StoryParams(setting="bedroom", child_name="Nora", child_gender="girl", item="blanket", twist="blanket_corner", misunderstanding="ruined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/5."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.child_name}: {p.item} / {p.twist} / {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

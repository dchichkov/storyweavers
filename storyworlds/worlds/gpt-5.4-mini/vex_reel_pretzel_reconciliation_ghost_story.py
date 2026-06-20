#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vex_reel_pretzel_reconciliation_ghost_story.py
================================================================================

A small standalone storyworld about a child, a stubborn ghost, a tangled reel,
and a pretzel-shaped peace offering.

Seed premise
------------
A little child gets vexed when a fishing reel keeps tangling in an attic where a
gentle ghost likes to drift around. The ghost isn't trying to scare anyone; it is
lonely and keeps bumping the line. After a frustrated moment, the child notices
what the ghost actually wants, offers a pretzel, and helps wind the reel with a
calm, careful method. They reconcile, and the attic ends in a soft, friendly
glow instead of a spooky mess.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose with a turn and resolution
- QA grounded in world state
- Python reasonableness gate and inline ASP twin
- support for default, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    intangible: bool = False
    edible: bool = False
    mechanical: bool = False
    spectral: bool = False

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tangled": 0.0, "settled": 0.0, "glow": 0.0, "dust": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "vex": 0.0, "care": 0.0, "lonely": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "child": "child"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    ghost_name: str
    reel_kind: str
    pretzel_kind: str
    place: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        if world.get("reel").meters["tangled"] >= THRESHOLD:
            sig = ("tangled",)
            if sig not in world.fired:
                world.fired.add(sig)
                world.get("child").memes["vex"] += 1
                world.get("ghost").memes["lonely"] += 1
                out.append("__tangle__")
                changed = True
        if world.get("ghost").memes["trust"] >= THRESHOLD and world.get("child").memes["care"] >= THRESHOLD:
            sig = ("reconcile",)
            if sig not in world.fired:
                world.fired.add(sig)
                world.get("ghost").meters["glow"] += 1
                world.get("ghost").meters["settled"] += 1
                world.get("child").memes["joy"] += 1
                out.append("__reconcile__")
                changed = True
    if narrate:
        for s in out:
            if s == "__tangle__":
                world.say("The reel kept catching on itself, and the child felt vexed and small.")
            elif s == "__reconcile__":
                world.say("The attic grew softer, like it had found its breath again.")
    return out


def reasonableness_gate(place: str, reel_kind: str, pretzel_kind: str) -> bool:
    return place in PLACES and reel_kind in REELS and pretzel_kind in PRETZELS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, r, z) for p in PLACES for r in REELS for z in PRETZELS]


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    ghost = world.add(Entity("ghost", kind="character", type="ghost", label=params.ghost_name, role="ghost", spectral=True))
    reel = world.add(Entity("reel", type="thing", label=params.reel_kind, mechanical=True))
    pretzel = world.add(Entity("pretzel", type="thing", label=params.pretzel_kind, edible=True))
    place = world.add(Entity("place", type="room", label=params.place))
    ghost.memes["lonely"] = 1.0
    child.memes["care"] = 0.0
    world.say(
        f"At {place.label}, {child.label} found {ghost.label} drifting near a dusty shelf, "
        f"where {reel.label} sat in a knot of old string."
    )
    world.say(f"{child.label} tried to fix it, but each turn made the reel more of a tangle.")
    world.para()
    child.memes["vex"] += 1
    world.say(
        f'"You are really trying my patience," {child.label} muttered, feeling vexed '
        f"as the line slipped away again."
    )
    world.say(
        f"The ghost did not mean to cause trouble. It only hovered close, peeking at "
        f"the {pretzel.label} in the child’s hand as if remembering a kinder night."
    )
    world.para()
    child.memes["care"] += 1
    ghost.memes["trust"] += 1
    world.say(
        f"{child.label} paused, then held out the {pretzel.label}. "
        f'"Maybe you want a snack more than a scare," {child.label} said.'
    )
    world.say(
        f"The ghost brightened. {ghost.label} had been lonely, not mean, and the little "
        f"offering made the whole room feel less cold."
    )
    world.get("reel").meters["tangled"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Together they took the {reel.label}, wound it slowly, and set the line straight. "
        f"The ghost drifted beside them, calm as moonlight, while the {pretzel.label} crumbs "
        f"fell like tiny stars onto the floorboards."
    )
    world.say(
        f"By the end, {child.label} and {ghost.label} were no longer cross with each other. "
        f"They were reconciled, sharing the quiet attic and a warm, friendly glow."
    )
    world.facts.update(child=child, ghost=ghost, reel=reel, pretzel=pretzel, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the words "{f["place"].label}", '
        f'"{f["reel"].label}", "{f["pretzel"].label}", and "vex".',
        f"Tell a small spooky story where {f['child'].label} gets vexed by a tangled reel, "
        f"discovers the ghost is lonely, and reconciliation follows over a pretzel.",
        f"Write a gentle attic ghost story with a turn from frustration to reconciliation."
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    g = world.facts["ghost"]
    r = world.facts["reel"]
    z = world.facts["pretzel"]
    return [
        QAItem(
            question=f"Why did {c.label} feel vexed?",
            answer=f"{c.label} felt vexed because the {r.label} kept tangling again and again. The problem got worse until {c.label} stopped and looked at what the ghost really needed."
        ),
        QAItem(
            question=f"How did {c.label} and {g.label} make peace?",
            answer=f"{c.label} offered the {z.label} and spoke kindly instead of scolding. That helped the ghost trust {c.label}, and they fixed the reel together."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The reel was wound straight, the ghost was no longer lonely, and the attic felt warm and calm. The story ended with reconciliation instead of fear."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does vexed mean?",
            answer="Vexed means feeling bothered, annoyed, or a little frustrated."
        ),
        QAItem(
            question="What is a reel?",
            answer="A reel is a round tool that holds line or string and helps wind it neatly."
        ),
        QAItem(
            question="What is a pretzel?",
            answer="A pretzel is a baked snack, often twisted into a knot shape and sometimes salty."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        mm = {k: v for k, v in e.meters.items() if v}
        me = {k: v for k, v in e.memes.items() if v}
        if mm:
            bits.append(f"meters={mm}")
        if me:
            bits.append(f"memes={me}")
        if e.role:
            bits.append(f"role={e.role}")
        parts.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(parts)


PLACES = ["attic", "boathouse", "basement"]
REELS = ["fishing reel", "toy reel", "old reel"]
PRETZELS = ["salted pretzel", "warm pretzel", "soft pretzel"]


CURATED = [
    StoryParams("attic", "girl", "Mara", "fishing reel", "warm pretzel"),
    StoryParams("boathouse", "boy", "Nico", "toy reel", "soft pretzel"),
    StoryParams("basement", "girl", "Iris", "old reel", "salted pretzel"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination is not reasonable for this little ghost tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny ghost storyworld with reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--reel", choices=REELS)
    ap.add_argument("--pretzel", choices=PRETZELS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(PLACES)
    reel = args.reel or rng.choice(REELS)
    pretzel = args.pretzel or rng.choice(PRETZELS)
    if not reasonableness_gate(place, reel, pretzel):
        raise StoryError(explain_rejection())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Toby", "Lena", "Owen", "Pia", "Arlo"])
    return StoryParams(name, gender, "Pip", reel, pretzel, place)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P,R,Z) :- place(P), reel(R), pretzel(Z).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in REELS:
        lines.append(asp.fact("reel", r))
    for z in PRETZELS:
        lines.append(asp.fact("pretzel", z))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        s = generate(CURATED[0])
        _ = s.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    if rc == 0:
        print("OK: verify passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base + i))
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
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


if __name__ == "__main__":
    main()

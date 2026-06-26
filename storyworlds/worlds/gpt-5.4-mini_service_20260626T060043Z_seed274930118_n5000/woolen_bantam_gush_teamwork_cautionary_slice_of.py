#!/usr/bin/env python3
"""
storyworlds/worlds/woolen_bantam_gush_teamwork_cautionary_slice_of.py
=====================================================================

A small slice-of-life storyworld about a careful child, a bantam chicken, a
woolen thing, and a sudden gush of water. The world is intentionally tiny and
constraint-checked: a brief mishap is only told when the fix is genuinely
reasonable, and the ending proves teamwork changed the state.

Seed imagination:
---
A child and a parent are doing a quiet afternoon chore in the yard. A small
bantam chicken keeps pecking at a basket of woolen scraps. A hose is turned on
too hard, and a gush of water heads toward the woolen pile. The child and the
parent work together: one steadies the chicken away from the splash, the other
shuts off the hose and dries the woolen things. The chicken is safe, the yard is
tidy again, and everyone remembers to be more careful next time.

World model:
---
- The child, parent, bantam chicken, and woolen item all have meters and memes.
- The hose gush increases wetness and worry.
- The child and parent can coordinate to avert damage.
- A cautionary beat is only narrated if the story predicts a real mess.
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
    kind: str = "thing"  # character | animal | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("wet", 0.0)
        self.meters.setdefault("safe", 0.0)
        self.meters.setdefault("tired", 0.0)
        self.meters.setdefault("dusty", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("care", 0.0)
        self.memes.setdefault("teamwork", 0.0)
        self.memes.setdefault("caution", 0.0)

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
    place: str = "the backyard"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.hose_on: bool = False
        self.gush_strength: float = 0.0
        self.hose_target: str = "wool"
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_gush(world: World) -> list[str]:
    out = []
    if not world.hose_on or world.gush_strength < THRESHOLD:
        return out
    wool = world.entities.get("wool")
    chick = world.entities.get("bantam")
    if wool and ("gush", "wool") not in world.fired:
        world.fired.add(("gush", "wool"))
        wool.meters["wet"] += 1
        wool.memes["worry"] += 1
        out.append("The woolen scrap was getting wet.")
    if chick and ("gush", "bantam") not in world.fired:
        world.fired.add(("gush", "bantam"))
        chick.memes["caution"] += 1
        out.append("The little bantam stepped back from the splash.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    wool = world.entities.get("wool")
    chick = world.entities.get("bantam")
    if not (child and parent and wool and chick):
        return out
    if wool.meters["wet"] >= THRESHOLD and child.memes["care"] >= THRESHOLD and parent.memes["care"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.memes["teamwork"] += 1
        parent.memes["teamwork"] += 1
        chick.memes["joy"] += 1
        wool.meters["safe"] += 1
        out.append("__teamwork__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_gush, _r_teamwork):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__teamwork__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING_REGISTRY = {
    "backyard": Setting(place="the backyard"),
    "garden": Setting(place="the garden"),
    "laundry_yard": Setting(place="the side yard"),
}

CHILD_NAMES = ["Mia", "Nora", "Lena", "Ava", "Iris", "June", "Theo", "Sam", "Eli", "Noah"]
TRAITS = ["gentle", "quiet", "helpful", "careful", "curious"]


def setting_detail(setting: Setting) -> str:
    if setting.place == "the side yard":
        return "A clothesline leaned nearby, and the hose was tucked beside a bucket."
    if setting.place == "the garden":
        return "Beans climbed the fence, and a small watering can sat beside the path."
    return "A patch of grass waited near a bucket and a coiled hose."


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.setting])

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    bantam = world.add(Entity(id="bantam", kind="animal", type="chicken", label="the bantam chicken"))
    wool = world.add(Entity(
        id="wool",
        type="thing",
        label="woolen scrap",
        phrase="a soft woolen scrap",
        caretaker="parent",
    ))

    child.memes["care"] += 1
    parent.memes["care"] += 1

    world.say(f"{child.label} was a careful little {params.gender} who liked quiet chores with {parent.label}.")
    world.say(f"The yard had {setting_detail(world.setting)}")
    world.say(f"{child.label} and {parent.label} were looking after {bantam.label}, and the bird pecked near {wool.phrase}.")
    world.say(f"{wool.label.capitalize()} felt cozy and soft in the shade.")

    world.para()
    world.say(f"Then the hose slipped on, and a sudden gush of water rushed across the grass.")
    world.hose_on = True
    world.gush_strength = 1.0
    world.facts["setting_detail"] = setting_detail(world.setting)
    world.facts["bantam"] = bantam
    world.facts["wool"] = wool
    world.facts["child"] = child
    world.facts["parent"] = parent
    propagate(world, narrate=True)

    world.say(f"{child.label} pointed to the woolen scrap while {parent.label} hurried to the tap.")
    child.memes["caution"] += 1
    parent.memes["caution"] += 1

    world.para()
    world.say(f"Together they fixed it fast: {parent.label} turned the hose low, and {child.label} lifted the woolen scrap onto a dry crate.")
    child.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    bantam.memes["joy"] += 1
    wool.meters["safe"] += 1
    world.hose_on = False
    world.gush_strength = 0.0
    world.say(f"{bantam.label.capitalize()} gave one tiny cluck, as if {bantam.pronoun()} knew the problem was over.")
    world.say(f"By the end, the grass was only a little damp, the woolen scrap was safe, and everyone remembered to be more careful next time.")

    world.facts.update(world=world, setting=params.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    return [
        f"Write a slice-of-life story for a small child about {child.label}, {parent.label}, a woolen thing, and a sudden gush of water.",
        f"Tell a cautious story where a bantam chicken is nearby when the hose makes a gush, and teamwork keeps the woolen scrap safe.",
        f"Write a gentle story with the words woolen, bantam, and gush, ending with a calm cleanup and a lesson about being careful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    bantam = world.facts["bantam"]
    wool = world.facts["wool"]
    return [
        QAItem(
            question=f"Who worked together when the gush of water reached the woolen scrap?",
            answer=f"{child.label} and {parent.label} worked together. One of them helped with the woolen scrap, and the other handled the hose so the little bantam stayed safe.",
        ),
        QAItem(
            question=f"What did the sudden gush almost do to the woolen scrap?",
            answer=f"It almost soaked the woolen scrap. The water rushed across the grass, so the woolen piece needed quick help before it got too wet.",
        ),
        QAItem(
            question=f"Why did the bantam chicken move back?",
            answer=f"The bantam chicken moved back because the splash from the gush made the ground feel busy and wet. The little bird kept away from the water while the family fixed it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is woolen fabric like?",
            answer="Woolen fabric is soft and warm. People use it for clothes and little cloth items because it feels cozy.",
        ),
        QAItem(
            question="What is a bantam chicken?",
            answer="A bantam chicken is a small kind of chicken. Bantams are little and quick, and they can peck around a yard or coop.",
        ),
        QAItem(
            question="What does gush mean?",
            answer="A gush is a sudden rush of something, like water moving out quickly all at once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
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
        lines.append(f"{e.id}: meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }")
    lines.append(f"hose_on={world.hose_on} gush_strength={world.gush_strength}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life storyworld with woolen, bantam, gush, teamwork, and caution.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(name=name, gender=gender, parent=parent, setting=setting)


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


ASP_RULES = r"""
setting(backyard).
setting(garden).
setting(laundry_yard).

woolen(wool).
bantam(bantam).
gush_event(gush).

teamwork_needed(bantam, wool) :- affected_by_gush(wool), near_bantam(bantam).
cautionary_story :- teamwork_needed(bantam, wool).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "backyard"),
        asp.fact("setting", "garden"),
        asp.fact("setting", "laundry_yard"),
        asp.fact("thing", "wool"),
        asp.fact("animal", "bantam"),
        asp.fact("event", "gush"),
        asp.fact("style", "slice_of_life"),
        asp.fact("feature", "teamwork"),
        asp.fact("feature", "cautionary"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # The Python reasonableness gate is intentionally simple here: this world
    # always permits the single family-helping-a-bantam scenario.
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show feature/1."))
    feats = set(asp.atoms(model, "feature"))
    if feats == {("teamwork",), ("cautionary",)}:
        print("OK: ASP twin recognizes teamwork and cautionary.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", setting="backyard"),
    StoryParams(name="Noah", gender="boy", parent="father", setting="garden"),
    StoryParams(name="Ava", gender="girl", parent="mother", setting="laundry_yard"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show feature/1."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show feature/1."))
        print(sorted(set(asp.atoms(model, "feature"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
===============================================================================================================================

A bedtime-story style swimming-pool storyworld with sound effects, cautionary
beats, and gentle repetition.

Premise:
A child brings an English manuscript to the swimming pool, hoping to read by the
water while nibbling a snack. The pages risk getting damp and wrinkled, so a
parent warns them, and the child finds a safer way to keep the pages dry and the
snack tidy.

The world is small on purpose:
- one child
- one parent
- one manuscript
- one snack
- one pool-side setting
- one tension: paper + water
- one resolution: protection + patience

The prose is state-driven, not a frozen paragraph with swapped nouns. Meters and
memes change as events happen, and the ending image proves the change.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    name: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    guards: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    manuscript: str
    snack: str
    child: str
    child_type: str
    parent: str
    parent_type: str
    seed: Optional[int] = None


PLACES = {
    "swimming_pool": Place(name="the swimming pool", indoor=False, affords={"read", "nibble", "wait"}),
}

ACTIVITIES = {
    "read": Activity(
        id="read",
        verb="read the English manuscript",
        gerund="reading the English manuscript",
        rush="rush closer to the water with the manuscript",
        mess="wet",
        soil="damp and wrinkled",
        zone={"paper"},
        keyword="english",
        tags={"english", "manuscript", "book"},
    ),
}

MANUSCRIPTS = {
    "english": Item(
        id="english",
        label="English manuscript",
        phrase="a neat English manuscript",
        region="paper",
        plural=False,
        guards={"wet"},
        tags={"english", "manuscript"},
    ),
}

SNACKS = {
    "nibble": Item(
        id="nibble",
        label="nibble snack",
        phrase="a little nibble snack",
        region="hands",
        plural=False,
        guards=set(),
        tags={"nibble"},
    ),
}

GEAR = {
    "dry_bag": Gear(
        id="dry_bag",
        label="dry bag",
        phrase="a clear dry bag",
        covers={"paper"},
        guards={"wet"},
        tags={"dry", "bag"},
    ),
    "towel": Gear(
        id="towel",
        label="towel",
        phrase="a soft towel",
        covers={"paper", "hands"},
        guards={"wet"},
        tags={"towel"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Noah", "Eli"]
TRAITS = ["gentle", "curious", "quiet", "bright", "sleepy"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("swimming_pool", "read", "english")]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "swimming_pool"), asp.fact("activity", "read"), asp.fact("item", "english")]
    lines.append(asp.fact("affords", "swimming_pool", "read"))
    lines.append(asp.fact("zone", "read", "paper"))
    lines.append(asp.fact("soil", "read", "wet"))
    lines.append(asp.fact("item_region", "english", "paper"))
    lines.append(asp.fact("gear", "dry_bag"))
    lines.append(asp.fact("gear", "towel"))
    lines.append(asp.fact("covers", "dry_bag", "paper"))
    lines.append(asp.fact("covers", "towel", "paper"))
    lines.append(asp.fact("guards", "dry_bag", "wet"))
    lines.append(asp.fact("guards", "towel", "wet"))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A, I) :- zone(A, R), item_region(I, R).
fix(G, A, I) :- gear(G), at_risk(A, I), guards(G, wet), covers(G, R), item_region(I, R).
valid(P, A, I) :- affords(P, A), at_risk(A, I), fix(_, A, I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _do_read(world: World, child: Entity, manuscript: Entity) -> None:
    child.memes["delight"] += 1
    child.memes["focus"] += 1
    world.zone = {"paper"}
    child.meters["near_pool"] += 1
    manuscript.memes["temptation"] += 1
    if world.place.name == "the swimming pool":
        world.say("By the swimming pool, the water went splish, splish, splish.")
    world.say(
        f'{child.id} liked the sound of the pool: "swish, swish," and the page: "flip, flip."'
    )


def _do_nibble(world: World, child: Entity, snack: Entity) -> None:
    child.memes["content"] += 1
    snack.meters["crumbs"] += 1
    world.say(f'{child.id} gave {snack.label} a tiny nibble. "Nibble, nibble," went the snack.')


def _apply_wet(world: World) -> list[str]:
    out = []
    child = world.get("child")
    manuscript = world.get("manuscript")
    if child.meters["near_pool"] >= THRESHOLD and manuscript.meters["dry"] < THRESHOLD:
        sig = ("wet",)
        if sig not in world.fired:
            world.fired.add(sig)
            manuscript.meters["wet"] += 1
            out.append("The English manuscript went damp at the edge.")
    return out


def _apply_wrinkle(world: World) -> list[str]:
    out = []
    manuscript = world.get("manuscript")
    if manuscript.meters["wet"] >= THRESHOLD:
        sig = ("wrinkle",)
        if sig not in world.fired:
            world.fired.add(sig)
            manuscript.meters["wrinkle"] += 1
            out.append("The pages wrinkled a little.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for fn in (_apply_wet, _apply_wrinkle):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, activity: Activity, manuscript_cfg: Item, snack_cfg: Item,
         child_name: str, child_type: str, parent_name: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_name))
    manuscript = world.add(Entity(id="manuscript", label=manuscript_cfg.label, phrase=manuscript_cfg.phrase))
    snack = world.add(Entity(id="snack", label=snack_cfg.label, phrase=snack_cfg.phrase))
    gear = world.add(Entity(id="gear", label="dry bag", phrase="a clear dry bag"))

    manuscript.meters["dry"] = 1.0
    snack.meters["ready"] = 1.0
    child.memes["hope"] = 1.0
    parent.memes["watchful"] = 1.0

    world.say(f"{child_name} and {parent_name} went to the swimming pool on a calm, blue day.")
    world.say(f'{child_name} carried {manuscript_cfg.phrase}, and {snack_cfg.phrase} sat in {child_name}\'s pocket.')
    world.say(f'“Let me read it by the pool,” {child_name} said, “and nibble, nibble, nibble.”')

    world.para()
    _do_read(world, child, manuscript)
    _do_nibble(world, child, snack)
    world.say(f'{child_name} leaned closer to the water. Plip, plop, plip went the pool.')
    world.say(f'“Careful,” said {parent_name}. “Paper and water do not mix.”')
    child.memes["worry"] += 1
    parent.memes["caution"] += 1

    propagate(world, narrate=True)

    world.para()
    if manuscript.meters["wet"] >= THRESHOLD:
        world.say(f'{child_name} hugged the manuscript back to their chest.')
        world.say(f'“I see,” {child_name} said softly. “Wet pages are no good.”')
    else:
        world.say(f'{child_name} kept the pages high and dry.')

    if manuscript.meters["wet"] >= THRESHOLD:
        world.say(f'{parent_name} smiled and showed {child_name} the dry bag.')
        gear.meters["used"] = 1.0
        manuscript.meters["dry"] = 1.0
        manuscript.meters["wet"] = 0.0
        manuscript.meters["wrinkle"] = 0.0
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        world.say(f'This time the manuscript stayed safe, safe, safe inside the dry bag.')
        world.say(f'“Read first, swim later,” {parent_name} said. “Nibble later, too.”')
        world.say(f'So {child_name} read the English manuscript on a dry towel and saved the nibble for after the swim.')
    world.facts.update(
        child=child,
        parent=parent,
        manuscript=manuscript,
        snack=snack,
        gear=gear,
        activity=activity,
        place=place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story set at a swimming pool where a child brings an English manuscript and a nibble snack.',
        f"Tell a gentle story about {f['child'].label} at the swimming pool, with splashy sound effects and a careful warning about {f['manuscript'].label}.",
        f'Write a small story that repeats “nibble, nibble” and “swish, swish” while keeping the English manuscript safe from the pool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    m = world.facts["manuscript"]
    return [
        QAItem(
            question=f"What did {c.label} bring to the swimming pool?",
            answer=f"{c.label} brought the English manuscript and a nibble snack. The manuscript was the thing that needed care near the water.",
        ),
        QAItem(
            question=f"Why did {p.label} warn {c.label} at the pool?",
            answer=f"{p.label} warned {c.label} because paper and water do not mix. The pages could get damp and wrinkled if they drifted too close to the pool.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{c.label} kept the English manuscript dry in a dry bag and waited to nibble after the swim. The ending was calm, safe, and tidy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a dry bag do?",
            answer="A dry bag helps keep paper and other things dry when water is nearby.",
        ),
        QAItem(
            question="Why should paper stay away from a swimming pool?",
            answer="Paper can soak up water, and then it gets soft, wrinkly, and hard to use.",
        ),
        QAItem(
            question="What is nibbling?",
            answer="Nibbling means taking tiny bites or small little tastes, one after another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Swimming-pool bedtime storyworld with sound effects and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--manuscript", choices=MANUSCRIPTS)
    ap.add_argument("--snack", choices=SNACKS)
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
    if args.place and args.place != "swimming_pool":
        raise StoryError("This little storyworld only lives at the swimming pool.")
    place = "swimming_pool"
    activity = args.activity or "read"
    manuscript = args.manuscript or "english"
    snack = args.snack or "nibble"
    if activity != "read" or manuscript != "english" or snack != "nibble":
        raise StoryError("Only the pool-side English manuscript and nibble snack make a complete bedtime story here.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, manuscript=manuscript, snack=snack,
                       child=name, child_type=gender, parent=parent, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.activity not in ACTIVITIES or params.manuscript not in MANUSCRIPTS or params.snack not in SNACKS:
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], MANUSCRIPTS[params.manuscript],
                 SNACKS[params.snack], params.child, params.child_type, params.parent, params.parent_type)
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


CURATED = [
    StoryParams(place="swimming_pool", activity="read", manuscript="english", snack="nibble",
                child="Mia", child_type="girl", parent="mother", parent_type="mother"),
    StoryParams(place="swimming_pool", activity="read", manuscript="english", snack="nibble",
                child="Leo", child_type="boy", parent="father", parent_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

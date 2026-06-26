#!/usr/bin/env python3
"""
storyworlds/worlds/thingamajig_savage_suspense_cautionary_curiosity_slice_of.py
================================================================================

A small slice-of-life story world about a curious child, a mysterious
thingamajig, and a cautious grown-up helping them choose the safe way to look.

The seed image:
---
A child notices a strange thingamajig tucked in a sunny corner of the house.
It looks interesting and a little savage around the edges, like it might pinch
or scratch. The child wants to twist it right away, but the grown-up worries
that curiosity could turn into a small mess or a sore finger.

After a careful warning, the child pauses, feels the suspense, and then agrees
to use a cloth, gloves, and the grown-up's help. Together they discover that the
thingamajig is only an old, harmless little gadget. The child gets to satisfy
their curiosity, and the day ends with tidy hands and a calmer heart.
---

Causal state updates:
---
    curious child notices thingamajig   -> child.memes["curiosity"] += 1
                                            child.memes["suspense"] += 1
    child touches sharp old object       -> child.meters["scratch"] += 1
                                            child.memes["worry"] += 1
    unsafe tinkering on a table          -> object.meters["mess"] += 1
                                            child.memes["oops"] += 1
    helper offers a cautious method      -> child.memes["calm"] += 1
                                            child.memes["curiosity"] stays high
    use cloth / gloves                   -> scratch risk removed, resolution possible
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["scratch", "mess"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "suspense", "worry", "calm", "joy", "love", "defiance"]:
            self.memes.setdefault(k, 0.0)

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the kitchen table"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Thingamajig:
    id: str
    label: str
    phrase: str
    danger: str
    risk: str
    action: str
    tag: str = "thingamajig"


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_scratch(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    obj = world.get(world.facts["thing"].id)
    if child.memes["defiance"] >= THRESHOLD and child.memes["curiosity"] >= THRESHOLD:
        sig = ("scratch", child.id, obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["scratch"] += 1
            child.memes["worry"] += 1
            out.append(f"{child.id} got a tiny scratch from the old edge.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    obj = world.get(world.facts["thing"].id)
    if child.memes["defiance"] >= THRESHOLD and child.meters["scratch"] < THRESHOLD:
        sig = ("mess", obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            obj.meters["mess"] += 1
            out.append(f"The thingamajig made a small clatter on the table.")
    return out


CAUSAL_RULES = [Rule("scratch", _r_scratch), Rule("mess", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world about a curious child and a thingamajig."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGAMAJIGS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


@dataclass
class StoryParams:
    place: str
    thing: str
    gear: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"inspect"}),
    "garage": Setting(place="the garage shelf", indoor=True, affords={"inspect"}),
    "porch": Setting(place="the porch step", indoor=False, affords={"inspect"}),
}

THINGAMAJIGS = {
    "clockwork": Thingamajig(
        id="clockwork",
        label="thingamajig",
        phrase="an old clockwork thingamajig with a tiny crank",
        danger="savage-looking edges",
        risk="could pinch fingers",
        action="twist the crank",
        tag="thingamajig",
    ),
    "tinbox": Thingamajig(
        id="tinbox",
        label="thingamajig",
        phrase="a little tin thingamajig that clicked softly",
        danger="savage little latch",
        risk="could snap shut on a thumb",
        action="open the latch",
        tag="thingamajig",
    ),
    "drawerkey": Thingamajig(
        id="drawerkey",
        label="thingamajig",
        phrase="a narrow thingamajig with a hidden drawer",
        danger="savage little corner",
        risk="could scrape skin",
        action="slide the drawer",
        tag="thingamajig",
    ),
}

GEAR = {
    "cloth": Gear(
        id="cloth",
        label="a soft cloth",
        covers={"hands"},
        prep="put a soft cloth under it first",
        tail="laid a soft cloth on the table",
    ),
    "gloves": Gear(
        id="gloves",
        label="little work gloves",
        covers={"hands"},
        prep="put on little work gloves first",
        tail="pulled on the little work gloves",
        plural=True,
    ),
    "tray": Gear(
        id="tray",
        label="a shallow tray",
        covers={"table"},
        prep="set out a shallow tray first",
        tail="set out the shallow tray",
    ),
}

TRAITS = ["curious", "thoughtful", "gentle", "bright-eyed", "patient", "watchful"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Finn", "Max", "Sam"]


def is_reasonable(thing: Thingamajig, gear: Gear) -> bool:
    return gear.id in {"cloth", "gloves"} and "hands" in gear.covers and thing.risk


def select_gear(thing: Thingamajig) -> Optional[Gear]:
    for g in GEAR.values():
        if is_reasonable(thing, g):
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for thing in THINGAMAJIGS:
            for gear in GEAR:
                combos.append((place, thing, gear))
    return combos


def tell(setting: Setting, thing_cfg: Thingamajig, gear_def: Gear,
         hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    thing = world.add(Entity(
        id=thing_cfg.id, type="thingamajig", label="thingamajig",
        phrase=thing_cfg.phrase, owner=parent.id, caretaker=parent.id
    ))

    world.facts.update(child=child, parent=parent, thing=thing, thing_cfg=thing_cfg, gear=gear_def)

    world.say(f"{child.id} was a little {hero_traits[0]} {hero_type} who noticed every interesting corner.")
    world.say(
        f"{child.pronoun().capitalize()} spotted {thing_cfg.phrase} on {setting.place}."
        f" It had {thing_cfg.danger}, and that made {child.id}'s eyes go wide."
    )

    world.para()
    world.say(
        f"{child.id} felt a tug of curiosity and wanted to {thing_cfg.action} right away."
        f" But {child.pronoun('possessive')} {parent.label_word} noticed the {thing_cfg.risk} and lifted a calm hand."
    )
    child.memes["curiosity"] += 1
    child.memes["suspense"] += 1
    world.say(
        f'"Careful," {parent.label_word} said. "That one looks a little savage around the edges."'
    )
    child.memes["defiance"] += 1
    propagate(world, narrate=True)

    world.para()
    if child.meters["scratch"] >= THRESHOLD:
        world.say(f"{child.id} stopped and rubbed {child.pronoun('possessive')} hand, frowning at the stinging spot.")
    else:
        world.say(f"{child.id} paused at the table and took a slow breath, still curious but more careful now.")

    world.say(
        f'{child.pronoun().capitalize()} asked, "Can we look at it together?"'
    )
    child.memes["calm"] += 1
    child.memes["love"] += 1
    world.say(
        f"{parent.label_word} smiled and reached for {gear_def.label}."
        f" {gear_def.prep.capitalize()} so the surprise could stay safe."
    )
    world.say(
        f"Together they {gear_def.tail}, then {thing_cfg.action} slowly."
        f" Inside, the thingamajig was only an old, harmless little gadget."
    )
    child.memes["joy"] += 1
    child.memes["suspense"] = 0.0
    world.say(
        f"{child.id}'s face brightened. The suspense melted away, and the room felt ordinary again,"
        f" with tidy hands, a curious smile, and one solved mystery."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thing_cfg = f["thing_cfg"]
    return [
        f'Write a gentle slice-of-life story for a young child about a {child.type} named {child.id} and a {thing_cfg.tag}.',
        f"Tell a story where {child.id} wants to {thing_cfg.action}, but a grown-up worries it may {thing_cfg.risk}.",
        f'Write a curious but cautionary story that includes the word "thingamajig" and ends with a safe shared discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    thing_cfg = f["thing_cfg"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {child.id} want to do with the thingamajig?",
            answer=f"{child.id} wanted to {thing_cfg.action} because the thingamajig looked interesting and a little mysterious.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} warn {child.id} to be careful?",
            answer=f"{parent.label_word} warned {child.id} because the thingamajig had {thing_cfg.danger} and could {thing_cfg.risk}.",
        ),
        QAItem(
            question=f"How did they look at it more safely?",
            answer=f"They used {gear.label} and worked together, so {child.id} could stay safe while the curiosity was satisfied.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thingamajig?",
            answer="A thingamajig is a funny word for some object when you know it is there, but you do not know what to call it yet.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to learn about something, ask questions, and find out how it works.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a careful warning so someone can avoid getting hurt or making a mess.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the worried, wondering feeling that keeps you curious about what will happen next.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", thing="clockwork", gear="cloth", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garage", thing="tinbox", gear="gloves", name="Leo", gender="boy", parent="father", trait="watchful"),
    StoryParams(place="porch", thing="drawerkey", gear="cloth", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


def explain_rejection(thing: Thingamajig, gear: Gear) -> str:
    return f"(No story: the {gear.label} does not make sense for this thingamajig.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.gear:
        if not is_reasonable(THINGAMAJIGS[args.thing], GEAR[args.gear]):
            raise StoryError(explain_rejection(THINGAMAJIGS[args.thing], GEAR[args.gear]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, thing=thing, gear=gear, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        THINGAMAJIGS[params.thing],
        GEAR[params.gear],
        params.name,
        params.gender,
        [params.trait, "careful"],
        params.parent,
    )
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
thingamajig(T) :- thing(T).
careful_fix(G,T) :- gear(G), thingamajig(T), safe_gear(G).
valid(Place,T,G) :- setting(Place), thingamajig(T), gear(G), reasonable(G,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for tid, t in THINGAMAJIGS.items():
        lines.append(asp.fact("thing", tid))
        if t.tag:
            lines.append(asp.fact("tag", tid, t.tag))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        if gid in {"cloth", "gloves"}:
            lines.append(asp.fact("safe_gear", gid))
        if "hands" in g.covers:
            lines.append(asp.fact("covers", gid, "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
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


def build_full_parser() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_full_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

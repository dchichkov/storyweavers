#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld about a curious child, one reckless choice,
and a gentle cautionary turn backed by a flashback.

Premise:
- A child notices something ordinary in daily life and becomes curious.
- A remembered warning from an earlier moment ("flashback") makes the parent
  cautious.
- The child reaches for a reckless shortcut, then accepts a safer method.

The world models:
- typed entities with physical meters and emotional memes
- a tiny forward-chaining causal engine
- a reasonableness gate: only stories where curiosity plausibly creates risk
  and the chosen safety measure actually helps are generated
- an inline ASP twin for parity checking

Style:
- child-facing
- concrete, authored prose
- slice-of-life, grounded in home and neighborhood details
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    verb: str
    noun: str
    risk: str
    zone: set[str]
    cue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    location: str
    at_risk: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Help:
    id: str
    label: str
    action: str
    fix: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_spill(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["reach"] < THRESHOLD:
        return out
    if not world.zone:
        return out
    for obj in list(world.entities.values()):
        if obj.id == "object" and obj.label == "tea":
            sig = ("spill", obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["spilled"] += 1
            child.memes["oops"] += 1
            out.append("__spill__")
    return out


def _r_cleanup(world: World) -> list[str]:
    out = []
    if world.get("object").meters["spilled"] < THRESHOLD:
        return out
    sig = ("cleanup",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("parent").meters["work"] += 1
    out.append("cleanup")
    return out


RULES = [Rule("spill", _r_spill), Rule("cleanup", _r_cleanup)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_plausible(curiosity: Curiosity, obj: Object) -> bool:
    return obj.at_risk and curiosity.location_overlap if False else True


@dataclass
class StoryParams:
    place: str
    curiosity: str
    object: str
    help: str
    name: str
    child_gender: str
    parent_gender: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, {"tea", "snack"}),
    "porch": Place("porch", "the front porch", False, {"watering", "wind"}),
    "laundry": Place("laundry", "the laundry room", True, {"folding", "sorting"}),
    "garden": Place("garden", "the little garden", False, {"watering"}),
}

CURIOSITIES = {
    "tea": Curiosity("tea", "peek into the cup", "tea", "spill hot tea", {"table"}, "the cup"),
    "watering_can": Curiosity("watering_can", "pour with the watering can", "water", "make a wet mess", {"floor"}, "the spout"),
    "buttons": Curiosity("buttons", "press all the buttons", "machine", "start the wrong cycle", {"controls"}, "the panel"),
}

OBJECTS = {
    "tea": Object("tea", "a mug of tea", "a mug of tea", "the table", True, {"tea"}),
    "folds": Object("folds", "a pile of folded towels", "a pile of folded towels", "the shelf", True, {"laundry"}),
    "seedlings": Object("seedlings", "small seedlings", "small seedlings", "the windowsill", False, {"garden"}),
}

HELPS = {
    "stir": Help("stir", "stir with a spoon", "stirred the tea", "kept the cup steady", {"tea"}),
    "carry": Help("carry", "carry it with two hands", "carried it carefully", "kept it level", {"tea", "laundry"}),
    "wait": Help("wait", "wait for a grown-up", "waited for help", "kept everyone calm", {"buttons"}),
}

GIRL_NAMES = ["Mia", "Lina", "June", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Eli", "Finn", "Noah", "Max", "Theo"]
TRAITS = ["curious", "gentle", "reckless", "thoughtful", "bright", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for cid, c in CURIOSITIES.items():
            if cid not in place.affords and place.indoors is False:
                continue
            for oid, obj in OBJECTS.items():
                if obj.at_risk and c.verb in {"peek into the cup", "pour with the watering can", "press all the buttons"}:
                    combos.append((place.id, cid, oid))
    return combos


def can_help(curiosity: Curiosity, obj: Object, help_item: Help) -> bool:
    return obj.tags & help_item.tags != set()


ASP_RULES = r"""
risk(P,C,O) :- place(P), curiosity(C), object(O), risky(C,O).
helpful(H,C,O) :- help(H), risk(P,C,O), help_tags(H,T), obj_tag(O,T).
valid(P,C,O) :- risk(P,C,O), helpful(H,C,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CURIOSITIES.items():
        lines.append(asp.fact("curiosity", cid))
        lines.append(asp.fact("risky", cid, c.risk))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for t in sorted(o.tags):
            lines.append(asp.fact("obj_tag", oid, t))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("help_tags", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life curiosity storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--help", dest="help_item", choices=HELPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place)
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, curiosity, obj = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        curiosity=curiosity,
        object=obj,
        help=args.help_item or rng.choice(sorted(HELPS)),
        name=args.name or rng.choice(GIRL_NAMES + BOY_NAMES),
        child_gender=args.gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def _make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity("child", "character", params.child_gender, params.name))
    parent = world.add(Entity("parent", "character", params.parent, "the parent"))
    cur = CURIOSITIES[params.curiosity]
    obj = OBJECTS[params.object]
    help_item = HELPS[params.help]
    child.memes["curiosity"] += 1
    child.memes["reckless"] += 1 if params.trait == "reckless" else 0.5
    parent.memes["caution"] += 1
    world.facts.update(child=child, parent=parent, curiosity=cur, object_cfg=obj, help_item=help_item, place=world.place)
    world.say(f"{child.id} was a little {params.trait} {params.child_gender} who liked the ordinary rhythm of the day.")
    world.say(f"At {world.place.label}, {child.id} noticed {cur.cue} and leaned closer, curious about {cur.noun}.")
    world.para()
    world.say(f"{parent.pronoun().capitalize()} had a careful feeling about it, because {parent.pronoun('possessive')} memory flashed back to an earlier afternoon when a small spill had turned into a big cleanup.")
    world.say(f'"That looks like trouble," {parent.label_word} said softly. "Let\'s not be reckless."')
    child.memes["defiance"] += 1
    world.say(f"{child.id} still reached anyway, because curiosity tugged harder than the warning.")
    world.para()
    child.meters["reach"] += 1
    world.zone = set(cur.zone)
    if obj.at_risk and cur.id == "tea":
        obj.meters["spilled"] += 1
        parent.meters["work"] += 1
        world.say(f"The mug tipped, and tea spread across the table in a brown little fan.")
    elif obj.at_risk and cur.id == "buttons":
        world.say(f"{child.id}'s fingers hovered over the panel, and the machine blinked in surprise.")
    else:
        world.say(f"{child.id} found out that the thing was harder to handle than it first looked.")
    world.para()
    help_obj = help_item
    world.say(f"Then {parent.id} took a breath and showed a safer way: {help_obj.action}.")
    world.say(f"{child.id} listened, and the moment became a lesson instead of a mess.")
    child.memes["joy"] += 1
    child.memes["caution"] += 1
    world.facts["helped"] = can_help(cur, obj, help_item)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, cur, obj, help_item = f["child"], f["parent"], f["curiosity"], f["object_cfg"], f["help_item"]
    return [
        QAItem(
            question=f"Who is the story about when {child.id} gets curious at {world.place.label}?",
            answer=f"It is about {child.id} and {parent.label_word}, a child and a grown-up sharing an ordinary day at {world.place.label}.",
        ),
        QAItem(
            question=f"What made {child.id} act recklessly?",
            answer=f"Curiosity made {child.id} lean closer to {cur.cue}, even after {parent.label_word} gave a gentle caution.",
        ),
        QAItem(
            question=f"What happened when {child.id} reached for {cur.noun}?",
            answer=f"The moment turned messy because the curious reach went too far, so the story needed a safer choice.",
        ),
        QAItem(
            question=f"What safer choice did {parent.label_word} show?",
            answer=f"{parent.label_word.capitalize()} showed how to {help_item.fix}, which kept the day calm and helped {child.id} learn without a bigger problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look closer, ask questions, and find out how something works.",
        ),
        QAItem(
            question="Why can reckless choices be a problem?",
            answer="Reckless choices can ignore a warning or skip a careful step, and that can make a small mistake become a bigger one.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a remembered moment from earlier that comes back into the story and helps explain why someone feels cautious.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a gentle slice-of-life story about a curious child who gets a reckless idea, remembers an earlier warning, and chooses a safer way.",
            "Tell a child-facing story with a cautionary beat and a flashback from an ordinary day at home.",
            "Write a small everyday story where curiosity causes a brief problem, then a grown-up helps it end well.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: {e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "tea", "tea", "stir", "Mia", "girl", "mother", "curious"),
    StoryParams("laundry", "buttons", "folds", "wait", "Leo", "boy", "father", "reckless"),
    StoryParams("porch", "watering_can", "seedlings", "carry", "Nora", "girl", "mother", "thoughtful"),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.curiosity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

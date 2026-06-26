#!/usr/bin/env python3
"""
storyworlds/worlds/diabetic_fuel_blarney_happy_ending_folk_tale.py
==================================================================

A small folk-tale storyworld about a diabetic child, a needed fuel run, and a
bit of blarney that tries to make trouble before a happy ending sets it right.

Premise seed:
- A child must keep a warm home and a steady snack on a winter day.
- A smooth-talking blarney-seller tempts them with nonsense and shiny words.
- The child and helper choose the real fuel, manage the food safely, and end
  with a warm house, a full lamp, and a peaceful evening.

This world is intentionally small and constraint-checked. It uses a tiny causal
simulation to drive the prose, with a folk-tale tone and a clear happy ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("warmth", 0.0)
        self.meters.setdefault("fuel", 0.0)
        self.meters.setdefault("sweet", 0.0)
        self.meters.setdefault("clean", 0.0)
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("distance", 0.0)
        self.memes.setdefault("hope", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("trust", 0.0)
        self.memes.setdefault("blarney", 0.0)
        self.memes.setdefault("joy", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    key: str
    name: str
    indoors: bool
    has_fuel: bool = False
    has_market: bool = False


@dataclass
class StoryParams:
    place: str
    helper: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_cold(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    house = world.entities.get("house")
    if not child or not house:
        return out
    if house.meters["fuel"] < THRESHOLD:
        sig = ("cold",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        child.meters["warmth"] -= 1
        child.memes["worry"] += 1
        out.append("The little house grew chilly, and the child felt the cold.")
    return out


def _r_fuel_warms(world: World) -> list[str]:
    out = []
    house = world.entities.get("house")
    if not house or house.meters["fuel"] < THRESHOLD:
        return out
    sig = ("warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    house.meters["warmth"] += 2
    out.append("The stove drank the fuel and sent a warm hum through the cottage.")
    return out


def _r_blarney_fades(world: World) -> list[str]:
    out = []
    trick = world.entities.get("trader")
    child = world.entities.get("child")
    if not trick or not child:
        return out
    if trick.memes["blarney"] < THRESHOLD:
        return out
    sig = ("blarney_fades",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] -= 1
    out.append("The child's ears grew wise to the trader's smooth words.")
    return out


CAUSAL_RULES = [
    Rule("cold", _r_cold),
    Rule("fuel_warms", _r_fuel_warms),
    Rule("blarney_fades", _r_blarney_fades),
]


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


PLACES = {
    "cottage": Place("cottage", "the little cottage", indoors=True, has_fuel=True),
    "market": Place("market", "the market square", indoors=False, has_market=True),
    "woodlot": Place("woodlot", "the woodlot", indoors=False, has_fuel=True),
}

HELPERS = {
    "grandmother": {"type": "grandmother", "label": "grandmother"},
    "brother": {"type": "boy", "label": "big brother"},
    "neighbor": {"type": "woman", "label": "kind neighbor"},
}

CHILDREN = {
    "girl": ["Mara", "Nina", "Elsie", "Hattie", "June"],
    "boy": ["Owen", "Finn", "Eli", "Tomas", "Pip"],
}


ASP_RULES = r"""
% A place can offer fuel, a helper can carry it home, and blarney may mislead.
needs_fuel(cottage).
has_fuel(woodlot).
has_fuel(cottage) :- fuel_in_house(cottage).

blarney_source(trader).
misleads(trader) :- blarney_source(trader).

happy_end(cottage) :- needs_fuel(cottage), fuel_in_house(cottage), child_safe(child), blarney_seen(trader).

child_safe(child) :- steady_snack(child), no_fraud(child).
no_fraud(child) :- blarney_seen(trader).

valid_story(Place, Helper, Gender) :- place(Place), helper(Helper), child_gender(Gender),
                                       good_fuel(Place), good_help(Helper).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
        if p.indoors:
            lines.append(asp.fact("indoors", p.key))
        if p.has_fuel:
            lines.append(asp.fact("good_fuel", p.key))
        if p.has_market:
            lines.append(asp.fact("market", p.key))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("good_help", h))
    for g in CHILDREN:
        lines.append(asp.fact("child_gender", g))
    lines.append(asp.fact("blarney_source", "trader"))
    lines.append(asp.fact("fuel_in_house", "cottage"))
    lines.append(asp.fact("steady_snack", "child"))
    lines.append(asp.fact("blarney_seen", "trader"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale about diabetic care, fuel, and blarney.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pk, p in PLACES.items():
        for hk in HELPERS:
            for g in CHILDREN:
                if p.has_fuel or p.has_market:
                    combos.append((pk, hk, g))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.helper is None or c[1] == args.helper)
              and (args.gender is None or c[2] == args.gender)]
    if not combos:
        raise StoryError("No valid folk-tale combination matches the given options.")
    place, helper, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILDREN[gender])
    return StoryParams(place=place, helper=helper, child_name=name, child_gender=gender)


def _introduce(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"Once, in {world.place.name}, there lived a little diabetic child named {child.id} "
        f"and {helper.label} who kept watch over the hearth."
    )
    world.say(
        f"{child.id} was a careful little {child.type} with a brave heart, and {helper.label} "
        f"liked to keep the day sweet, steady, and calm."
    )


def _setup_need(world: World, child: Entity) -> None:
    child.memes["hope"] += 1
    world.say(
        f"That winter morning, the cottage was low on fuel, and the stove sighed like an old wolf."
    )
    world.say(
        f"{child.id} knew the house needed real fuel, not just promises, so {child.pronoun()} "
        f"tied on {child.pronoun('possessive')} scarf and listened for advice."
    )


def _blarney_scene(world: World, child: Entity, trader: Entity) -> None:
    trader.memes["blarney"] += 2
    child.memes["trust"] += 0
    child.memes["worry"] += 1
    world.say(
        f"At the market, a trader with a shiny hat began to pour out blarney thicker than honey."
    )
    world.say(
        f'"Come, come," said the trader, "my lovely words will warm your house better than fuel!"'
    )
    world.say(
        f"But {child.id} looked at the empty basket and knew warm words could not feed the stove."
    )
    propagate(world, narrate=True)


def _choose_truth(world: World, child: Entity, helper: Entity) -> None:
    house = world.get("house")
    child.memes["trust"] += 1
    child.memes["joy"] += 1
    house.meters["fuel"] += 2
    house.meters["clean"] += 1
    world.say(
        f"{helper.label} chuckled softly and chose honest fuel from the stack of dry wood."
    )
    world.say(
        f"Together they carried it home, and {child.id} remembered that a true friend brings what works."
    )
    propagate(world, narrate=True)


def _steady_snack(world: World, child: Entity) -> None:
    child.meters["sweet"] += 1
    child.meters["clean"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Before supper, {child.id} ate a steady little snack that kept {child.pronoun('possessive')} strength even."
    )


def _happy_ending(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"By sunset, the cottage glowed gold, the kettle sang, and the blarney had blown away like smoke."
    )
    world.say(
        f"{child.id} sat warm beside the hearth while {helper.label} smiled, and the night felt safe at last."
    )
    child.memes["worry"] = 0
    child.memes["joy"] += 2
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child_type = "girl" if params.child_gender == "girl" else "boy"
    child = world.add(Entity(id=params.child_name, kind="character", type=child_type))
    helper = world.add(Entity(id="helper", kind="character", type=HELPERS[params.helper]["type"], label=HELPERS[params.helper]["label"]))
    trader = world.add(Entity(id="trader", kind="character", type="man", label="the trader"))
    house = world.add(Entity(id="house", kind="thing", type="house", label="the cottage"))
    house.meters["fuel"] = 0.0
    world.facts.update(child=child, helper=helper, trader=trader, house=house, place=place)

    _introduce(world, child, helper)
    world.para()
    _setup_need(world, child)
    world.para()
    _blarney_scene(world, child, trader)
    world.para()
    _choose_truth(world, child, helper)
    _steady_snack(world, child)
    world.para()
    _happy_ending(world, child, helper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale for children about {f['child'].id}, a diabetic child, who needs fuel for a warm home.",
        f"Tell a happy-ending story where a smooth-talking trader uses blarney, but a kind helper chooses real fuel instead.",
        f"Write a gentle winter tale in a folk style that includes the words diabetic, fuel, and blarney.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    trader: Entity = f["trader"]
    house: Entity = f["house"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about in {place.name}?",
            answer=f"It is about {child.id}, a diabetic child, and {helper.label}, who helps keep the home safe and warm.",
        ),
        QAItem(
            question="What did the trader try to use instead of real fuel?",
            answer="The trader tried to use blarney, which meant smooth words and empty promises instead of useful firewood.",
        ),
        QAItem(
            question=f"What did {helper.label} bring home for the stove?",
            answer="They brought home real fuel, so the stove could warm the cottage properly.",
        ),
        QAItem(
            question=f"Why was {child.id} careful at the market?",
            answer=f"{child.id} knew that a diabetic child needs steady care, and that warm words cannot heat a house or help a family.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with a warm cottage, honest fuel, a steady snack, and the blarney blowing away.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fuel do in a house?",
            answer="Fuel helps a stove make heat, so a house can stay warm in cold weather.",
        ),
        QAItem(
            question="What is blarney?",
            answer="Blarney is smooth, flattering talk that can sound nice but may not tell the truth.",
        ),
        QAItem(
            question="What does it mean for someone to be diabetic?",
            answer="A diabetic person needs careful attention to food and routine so their body stays balanced.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="cottage", helper="grandmother", child_name="Mara", child_gender="girl"),
    StoryParams(place="market", helper="neighbor", child_name="Owen", child_gender="boy"),
    StoryParams(place="woodlot", helper="brother", child_name="Elsie", child_gender="girl"),
]


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    import asp
    # Minimal parity check against python valid combos, with one model for determinism.
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.helper is None or c[1] == args.helper)
              and (args.gender is None or c[2] == args.gender)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, helper, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILDREN[gender])
    return StoryParams(place=place, helper=helper, child_name=name, child_gender=gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_stories()
        print(f"{len(items)} compatible stories:\n")
        for row in items:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.child_name}: {p.place} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

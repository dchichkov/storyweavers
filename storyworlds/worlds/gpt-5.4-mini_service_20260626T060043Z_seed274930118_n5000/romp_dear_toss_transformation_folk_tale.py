#!/usr/bin/env python3
"""
storyworlds/worlds/romp_dear_toss_transformation_folk_tale.py
==============================================================

A small folk-tale storyworld about a romp, a dear warning, a risky toss,
and a magical transformation that changes the ending image.

Premise seed:
- romp
- dear
- toss
- transformation
- folk tale

The world is built as a simple causal simulation:
- a child or small folk hero romps in a magical place,
- a dear elder warns about tossing a charm,
- the toss can trigger a transformation,
- the ending proves what changed in the world model.

The story quality goal is a complete child-facing tale with a clear setup,
a turn, and a resolution image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    state: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "grandfather", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    moonlit: bool = False
    allows: set[str] = field(default_factory=set)
    magic_kind: str = ""


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    kind: str
    target_form: str
    risk_note: str
    whisper: str


@dataclass
class StoryParams:
    place: str
    charm: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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


PLACES = {
    "meadow": Place(id="meadow", label="the moonlit meadow", moonlit=True, allows={"romp", "toss"}, magic_kind="moon"),
    "brook": Place(id="brook", label="the mossy brook", moonlit=False, allows={"romp", "toss"}, magic_kind="water"),
    "cottage_yard": Place(id="cottage_yard", label="the cottage yard", moonlit=False, allows={"romp", "toss"}, magic_kind="home"),
}

CHARMS = {
    "pebble": Charm(
        id="pebble",
        label="a bright pebble",
        phrase="a bright pebble from the path",
        kind="stone",
        target_form="sparrow",
        risk_note="it could wake the old magic in the brook",
        whisper="When a bright pebble is tossed into magic water, a sleepy spell may wake up.",
    ),
    "ribbon": Charm(
        id="ribbon",
        label="a red ribbon",
        phrase="a red ribbon tied in a bow",
        kind="cloth",
        target_form="white doe",
        risk_note="it could call a kind forest blessing",
        whisper="When a ribbon is tossed into moonlight, old blessings sometimes answer.",
    ),
    "loaf": Charm(
        id="loaf",
        label="a little oat loaf",
        phrase="a little oat loaf wrapped in cloth",
        kind="bread",
        target_form="golden hare",
        risk_note="it could tempt a hungry charm",
        whisper="When a loaf is tossed to the kind spirits, they may return a blessing.",
    ),
}

TRAITS = ["curious", "gentle", "brave", "cheerful", "stubborn", "lively"]
GIRL_NAMES = ["Mira", "Lena", "Ivy", "Tessa", "Nora", "Anya"]
BOY_NAMES = ["Jory", "Bram", "Pell", "Oren", "Milo", "Tarin"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in PLACES for c in CHARMS if p != "cottage_yard" or c != "loaf"]


def prize_at_risk(place: Place, charm: Charm) -> bool:
    return place.id in {"brook", "meadow", "cottage_yard"} and charm.kind in {"stone", "cloth", "bread"}


def select_transform(place: Place, charm: Charm) -> bool:
    return place.allows and prize_at_risk(place, charm)


def explain_rejection(place: Place, charm: Charm) -> str:
    return (
        f"(No story: the {charm.label} doesn't have a sensible magical reaction in "
        f"{place.label}. Try another place or charm.)"
    )


def explain_gender(charm_id: str, gender: str) -> str:
    return f"(No story: try a different name or {gender} choice for this folk-tale setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale storyworld: a romp, a dear warning, a risky toss, and a transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
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
    place = args.place or rng.choice(list(PLACES))
    charm = args.charm or rng.choice(list(CHARMS))
    place_obj, charm_obj = PLACES[place], CHARMS[charm]

    if not select_transform(place_obj, charm_obj):
        raise StoryError(explain_rejection(place_obj, charm_obj))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or ("grandmother" if gender == "girl" else "grandfather")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, charm=charm, name=name, gender=gender, elder=elder, trait=trait)


def _hero_title(hero: Entity) -> str:
    return f"little {hero.pronoun('possessive')} {hero.type}".replace("her girl", "girl").replace("his boy", "boy")


def tell(place: Place, charm: Charm, name: str, gender: str, elder: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={"joy": 0.0}, memes={"curiosity": 0.0}))
    elder_ent = world.add(Entity(id="Elder", kind="character", type=elder, label=f"the {elder}", meters={"worry": 0.0}, memes={"care": 0.0}))
    token = world.add(Entity(id="Charm", kind="thing", type=charm.kind, label=charm.label, phrase=charm.phrase, owner=hero.id, state="held"))

    # Act 1
    world.say(f"{name} was a {trait} child who loved to romp in {place.label}.")
    world.say(f"One bright day, {name}'s {elder} gave {hero.pronoun('object')} {token.phrase} and said, \"Dear {name}, keep it safe.\"")
    world.say(f"{name} smiled, because {hero.pronoun()} liked the little shine of it.")

    # Act 2
    world.para()
    hero.memes["curiosity"] += 1
    hero.meters["motion"] = hero.meters.get("motion", 0.0) + 1
    world.say(f"{name} began to romp, skipping over the grass and spinning around a stone.")
    world.say(f"The {elder} called after {hero.pronoun('object')}, \"Dear one, do not toss it into the magic place; {charm.risk_note}.\"")
    world.say(f"But the charm felt warm in {name}'s hand, and the child could not resist a small toss.")

    # Transformation event
    token.state = "tossed"
    world.facts["tossed"] = True
    world.facts["risk_note"] = charm.risk_note
    hero.meters["motion"] += 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    if place.magic_kind == "water":
        transformed = "sparrow"
        trail = "the brook answered with a silver ripple"
    elif place.magic_kind == "moon":
        transformed = "white doe"
        trail = "the moonlight shivered like a thin bell"
    else:
        transformed = "golden hare"
        trail = "the cottage yard glimmered as if a lantern had opened"

    hero_before = hero.type
    hero.type = transformed
    hero.label = name
    hero.meters["transformed"] = 1.0
    hero.memes["surprise"] = 1.0
    elder_ent.memes["care"] += 1
    world.facts["before_form"] = hero_before
    world.facts["after_form"] = transformed
    world.say(f"{trail}, and the tossed charm turned into a spell of its own.")
    world.say(f"In a blink, {name} was no longer a {hero_before}; {hero.pronoun()} had become {transformed}.")

    # Act 3
    world.para()
    world.say(f"The {elder} did not scold. Instead, {hero.pronoun('subject')} held out kind hands and said, \"Come home, dear {name}.\"")
    world.say(f"{name} learned that a foolish toss could still lead to a gentler ending when love stayed near.")
    world.say(f"At sunset, {name} romped back through {place.label} as {transformed}, small and bright, while the {elder} laughed softly beside {hero.pronoun('object')}.")

    world.facts.update(hero=hero, elder=elder_ent, token=token, place=place, charm=charm, name=name, gender=gender, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child that includes the words "romp", "dear", and "toss".',
        f"Tell a gentle story about {f['name']}, who likes to romp in {f['place'].label}, and whose dear elder warns about a magical toss.",
        f"Write a simple transformation tale where a child tosses {f['charm'].label} and changes form in a magical place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    place: Place = f["place"]
    charm: Charm = f["charm"]
    return [
        QAItem(
            question=f"What did {hero.label} love to do in {place.label}?",
            answer=f"{hero.label} loved to romp in {place.label}. That playful running set up the magical moment later in the tale.",
        ),
        QAItem(
            question=f"Who called {hero.label} dear and warned about the toss?",
            answer=f"The {elder.type} called {hero.label} dear and warned {hero.pronoun('object')} not to toss the charm into the magic place.",
        ),
        QAItem(
            question=f"What happened after {hero.label} tossed {charm.label}?",
            answer=f"The tossed charm woke old magic, and {hero.label} transformed from {f['before_form']} into {f['after_form']}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label}?",
            answer=f"By the end, {hero.label} was still with the {elder.type}, but now {hero.pronoun()} had the new shape of a {f['after_form']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a romp?",
            answer="A romp is lively, happy play with lots of running, skipping, and turning around.",
        ),
        QAItem(
            question="What does toss mean?",
            answer="To toss something is to throw it lightly through the air, usually with a quick hand movement.",
        ),
        QAItem(
            question="What is a transformation in a folk tale?",
            answer="A transformation is a change in form, like a person becoming an animal or a plain thing becoming magical.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.state:
            bits.append(f"state={e.state}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
charm(C) :- charm_def(C).

valid(P,C) :- place(P), charm(C), afford_toss(P), magic_ok(P,C).

afford_toss(meadow).
afford_toss(brook).
afford_toss(cottage_yard).

magic_ok(meadow, ribbon).
magic_ok(brook, pebble).
magic_ok(cottage_yard, loaf).

% A valid folk-tale setup has a place that supports a toss and a charm that can transform there.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.moonlit:
            lines.append(asp.fact("moonlit", pid))
        lines.append(asp.fact("magic_kind", pid, place.magic_kind))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm_def", cid))
        lines.append(asp.fact("charm_kind", cid, charm.kind))
        lines.append(asp.fact("target_form", cid, charm.target_form))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_story_sample(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], CHARMS[params.charm], params.name, params.gender, params.elder, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_sample(params)


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
    StoryParams(place="meadow", charm="ribbon", name="Mira", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="brook", charm="pebble", name="Oren", gender="boy", elder="grandfather", trait="lively"),
    StoryParams(place="cottage_yard", charm="loaf", name="Tessa", gender="girl", elder="grandmother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible folk-tale combos:\n")
        for place, charm in combos:
            print(f"  {place:12} {charm}")
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
            header = f"### {p.name}: {p.charm} at {p.place} ({p.elder})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

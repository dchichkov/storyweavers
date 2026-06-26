#!/usr/bin/env python3
"""
A standalone story world for a small space-adventure tale about a curious crew,
a fragile vase, a saucer-shaped ship, foreshadowed trouble, and a teamwork fix.

The story model is intentionally small:
- a child crew member notices a mysterious vase on a saucer ship,
- curiosity leads them toward a risky choice,
- foreshadowing predicts a wobble, crack, or spill,
- teamwork solves the problem by sharing the task,
- the ending proves the vase is safe and the crew has grown closer.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    sitting_on: Optional[str] = None
    fragile: bool = False
    round: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "risk": 0.0, "safe": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "teamwork": 0.0, "worry": 0.0, "joy": 0.0})

    def pronoun(self) -> str:
        return "they" if self.kind == "crew" else "it"

    def possessive(self) -> str:
        return "their" if self.kind == "crew" else "its"


@dataclass
class Place:
    id: str
    label: str
    sky: str
    has_hatches: bool = False
    has_tables: bool = False
    stars_visible: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    ship: str
    relic: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orbital_garden": Place(id="orbital_garden", label="the orbital garden", sky="purple", has_tables=True),
    "cargo_bay": Place(id="cargo_bay", label="the cargo bay", sky="silver", has_hatches=True, has_tables=True, stars_visible=False),
    "moon_dock": Place(id="moon_dock", label="the moon dock", sky="black", has_hatches=True, stars_visible=True),
}

HEROES = {
    "Mina": "girl",
    "Tobi": "boy",
    "Nova": "child",
    "Rin": "child",
    "Kai": "boy",
}

HELPERS = {
    "Ari": "child",
    "Juno": "girl",
    "Pax": "boy",
    "Sol": "child",
}

SHIPS = {
    "saucer_ship": {
        "label": "a silver saucer ship",
        "phrase": "a little silver saucer ship with a bright round window",
        "round": True,
    },
    "blue_saucer": {
        "label": "a blue saucer",
        "phrase": "a smooth blue saucer ship with tiny lights along the rim",
        "round": True,
    },
}

RELICS = {
    "vase": {
        "label": "vase",
        "phrase": "a tall glass vase with a star painted on it",
        "fragile": True,
        "round": False,
    },
    "saucer": {
        "label": "saucer",
        "phrase": "a small ceramic saucer from the ship's tea set",
        "fragile": True,
        "round": True,
    },
}

TRAIT_WORDS = ["curious", "careful", "eager", "bold", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A relic is at risk when it is fragile and the crew member carrying it explores a place
% where the path is narrow, bumpy, or busy.
at_risk(R) :- relic(R), fragile(R), risky_place(P), carrying(C,R), near(C,P).

% Teamwork is a fix when two crew members share the task and the fragile relic becomes safe.
safe(R) :- at_risk(R), teamwork(T), helps(T,R).

% A valid story needs curiosity, foreshadowing, and a teamwork resolution.
valid_story(P,H,He,R) :- place(P), hero(H), helper(He), relic(R), at_risk(R), safe(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_hatches:
            lines.append(asp.fact("risky_place", pid))
        if p.has_tables:
            lines.append(asp.fact("steady_place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
        if SHIPS[sid]["round"]:
            lines.append(asp.fact("round_ship", sid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r["fragile"]:
            lines.append(asp.fact("fragile", rid))
        if r["round"]:
            lines.append(asp.fact("round_relic", rid))
    # Relations used by the rules
    for pid in PLACES:
        lines.append(asp.fact("near", "crew", pid))
        if pid in {"cargo_bay", "moon_dock"}:
            lines.append(asp.fact("risky_place", pid))
    lines.append(asp.fact("teamwork", "shared_plan"))
    lines.append(asp.fact("helps", "shared_plan", "vase"))
    lines.append(asp.fact("helps", "shared_plan", "saucer"))
    lines.append(asp.fact("carrying", "crew", "vase"))
    lines.append(asp.fact("carrying", "crew", "saucer"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="crew", label=params.hero, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="crew", label=params.helper, role="helper"))
    ship = world.add(Entity(id=params.ship, kind="ship", label=SHIPS[params.ship]["label"], phrase=SHIPS[params.ship]["phrase"], round=True))
    relic = world.add(Entity(
        id=params.relic,
        kind="relic",
        label=RELICS[params.relic]["label"],
        phrase=RELICS[params.relic]["phrase"],
        fragile=RELICS[params.relic]["fragile"],
        round=RELICS[params.relic]["round"],
        carried_by=hero.id,
        sitting_on=ship.id,
    ))

    # setup
    world.say(
        f"{hero.id} and {helper.id} floated through {place.label} beside {ship.phrase}. "
        f"They were on a little space mission, and {hero.id} noticed {relic.phrase}."
    )
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was the curious one, and {hero.id} kept looking at {relic.label} because it gleamed like moonlight."
    )

    # foreshadowing
    world.para()
    world.say(
        f"Near the hatch, the floor made a tiny clink-clink sound. "
        f"{helper.id} glanced over and said the path looked a little wobbly."
    )
    relic.meters["risk"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"That was a hint that the {relic.label} should be handled carefully, because one bump could make it crack."
    )

    # tension
    world.para()
    world.say(
        f"{hero.id} wanted to carry {relic.possessive()} cargo all by {hero.pronoun()}self, "
        f"but the saucer ship rocked softly as the lights flickered."
    )
    world.say(
        f"When {hero.id} reached for the {relic.label}, it tipped a little."
    )
    relic.meters["distance"] += 1
    relic.meters["risk"] += 1

    # teamwork resolution
    world.para()
    helper.memes["teamwork"] += 1
    hero.memes["teamwork"] += 1
    relic.meters["safe"] += 2
    world.say(
        f"{helper.id} rushed in with both hands and said, 'Let's do this together.' "
        f"{hero.id} held one side, and {helper.id} held the other."
    )
    world.say(
        f"Together they carried {relic.possessive()} weight back to the table, "
        f"and the vase stayed steady all the way."
    )
    world.say(
        f"At the end, {relic.label} rested safely on the table, and the saucer ship felt a lot less scary."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        ship=ship,
        relic=relic,
        place=place,
        risk=bool(relic.meters["risk"] > 0),
        teamwork=bool(helper.memes["teamwork"] > 0),
        foreshadowing=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child about {f["hero"].id}, {f["helper"].id}, and a fragile {f["relic"].label}.',
        f'Tell a gentle story set in {f["place"].label} where curiosity leads to a small problem and teamwork fixes it.',
        f'Write a story with a saucer ship, a vase, a little warning sign, and a happy teamwork ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    relic = f["relic"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} notice in {place.label}?",
            answer=f"{hero.id} noticed {relic.phrase} in {place.label} because {hero.id} was very curious.",
        ),
        QAItem(
            question=f"What was the hint that something might go wrong with the {relic.label}?",
            answer="The floor made a tiny clink-clink sound near the hatch, which hinted that the path was wobbly and the fragile object needed care.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} keep the {relic.label} safe?",
            answer=f"They worked together and carried it with both hands so it stayed steady and did not crack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vase?",
            answer="A vase is a container that people often use to hold flowers, and it can be made of glass or ceramic.",
        ),
        QAItem(
            question="What is a saucer?",
            answer="A saucer is a small shallow dish. It can sit under a cup, and in stories it can also mean a round ship.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the job so the work is easier and safer.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something may happen later in the story.",
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.sitting_on:
            bits.append(f"sitting_on={e.sitting_on}")
        if e.fragile:
            bits.append("fragile=True")
        if e.round:
            bits.append("round=True")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for hero in HEROES:
            for helper in HELPERS:
                if hero == helper:
                    continue
                for ship in SHIPS:
                    for relic in RELICS:
                        combos.append((place, hero, helper, ship, relic))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.hero:
        combos = [c for c in combos if c[1] == args.hero]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if args.ship:
        combos = [c for c in combos if c[3] == args.ship]
    if args.relic:
        combos = [c for c in combos if c[4] == args.relic]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")

    place, hero, helper, ship, relic = rng.choice(sorted(combos))
    if hero == helper:
        raise StoryError("Hero and helper must be different crew members.")
    return StoryParams(place=place, hero=hero, helper=helper, ship=ship, relic=relic)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with vase, saucer, curiosity, teamwork, and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, h, he, r) for p, h, he, s, r in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        all_params = [
            StoryParams(place="orbital_garden", hero="Mina", helper="Ari", ship="saucer_ship", relic="vase"),
            StoryParams(place="cargo_bay", hero="Nova", helper="Juno", ship="blue_saucer", relic="saucer"),
            StoryParams(place="moon_dock", hero="Tobi", helper="Sol", ship="saucer_ship", relic="vase"),
        ]
        samples = [generate(p) for p in all_params]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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

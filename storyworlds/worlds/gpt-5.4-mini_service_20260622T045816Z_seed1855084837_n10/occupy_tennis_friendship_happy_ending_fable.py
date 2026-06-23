#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T045816Z_seed1855084837_n10/occupy_tennis_friendship_happy_ending_fable.py
==============================================================================================================

A small fable-style story world about friendship, a tennis court, and a happy ending.

The tale premise:
- Two friends want to occupy the only tennis court for themselves.
- A third friend wants to play tennis too.
- The world tracks whether the court is occupied, whether anyone is waiting, and
  whether the friends choose sharing over selfishness.
- The ending proves the change through state: the court becomes shared, joy rises,
  and friendship deepens.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate and inline ASP twin
- prompts, story QA, and world-knowledge QA
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, is_dataclass, asdict
from typing import Optional

# Robust direct-import support: walk upward until we find a parent containing results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
_SEARCH = _HERE
while True:
    if os.path.exists(os.path.join(_SEARCH, "results.py")):
        if _SEARCH not in sys.path:
            sys.path.insert(0, _SEARCH)
        break
    parent = os.path.dirname(_SEARCH)
    if parent == _SEARCH:
        raise RuntimeError("Could not locate storyworlds/results.py for import")
    _SEARCH = parent

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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "hen", "mare", "queen", "fox"}
        male = {"boy", "father", "dad", "man", "buck", "rooster", "stallion", "king", "hare"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    can_tennis: bool = False
    can_occupy: bool = False


@dataclass
class StoryParams:
    place: str
    first: str
    second: str
    third: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        # Helpful role aliases for causal rules that refer to story roles.
        if ent.role and ent.role not in self.entities:
            self.entities[ent.role] = ent
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_waiting(world: World) -> list[str]:
    out: list[str] = []
    court = world.get("court")
    for kid in world.characters():
        if kid.meters["waiting"] < THRESHOLD:
            continue
        sig = ("waiting", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        court.meters["crowded"] += 1
        out.append(f"{kid.id} stayed on the court too long, and the court felt crowded.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    court = world.get("court")
    for kid in world.characters():
        if kid.memes["sharing"] < THRESHOLD:
            continue
        sig = ("share", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        court.meters["crowded"] = max(0.0, court.meters["crowded"] - 1)
        kid.memes["joy"] += 1
        out.append(f"{kid.id} made room, and the court grew calmer.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("first")
    b = world.get("second")
    c = world.get("third")
    if a.memes["share_with"] >= THRESHOLD and b.memes["share_with"] >= THRESHOLD:
        sig = ("friendship",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        a.memes["friendship"] += 1
        b.memes["friendship"] += 1
        c.memes["joy"] += 1
        out.append("Friendship made the choice easy.")
    return out


CAUSAL_RULES = [_r_waiting, _r_share, _r_friendship]


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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        if not PLACES[place].can_tennis or not PLACES[place].can_occupy:
            continue
        for a in NAMES:
            for b in NAMES:
                for c in NAMES:
                    if len({a, b, c}) == 3:
                        combos.append((place, a, b, c))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if len({params.first, params.second, params.third}) != 3:
        raise StoryError("The three characters must be different.")
    place = PLACES[params.place]
    if not place.can_tennis:
        raise StoryError("This place cannot host tennis.")
    if not place.can_occupy:
        raise StoryError("This place cannot be occupied in the story.")
    if params.first not in NAMES or params.second not in NAMES or params.third not in NAMES:
        raise StoryError("Unknown character name.")


def _make_person(world: World, name: str, animal: str, role: str) -> Entity:
    ent = world.add(Entity(id=name, kind="character", type=animal, role=role))
    ent.meters["occupy"] += 0.0
    ent.meters["waiting"] += 0.0
    ent.memes["friendship"] += 0.0
    ent.memes["joy"] += 0.0
    ent.memes["share_with"] += 0.0
    ent.memes["stubborn"] += 0.0
    return ent


def tell(place: Place, first: str, second: str, third: str) -> World:
    world = World(place)
    world.add(Entity(id="court", kind="thing", type="court", label=place.label, phrase=place.phrase, tags=set(place.tags)))
    a = _make_person(world, first, ANIMALS[first], "first")
    b = _make_person(world, second, ANIMALS[second], "second")
    c = _make_person(world, third, ANIMALS[third], "third")

    # Setup
    a.meters["occupy"] += 1
    b.meters["occupy"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(f"Long ago, {a.id} and {b.id} came to {place.phrase} and decided to occupy the court.")
    world.say(f"They brought a racket, a ball, and a proud wish to play tennis in the sun.")
    world.say(f"But {c.id} arrived too, hoping to join the game.")

    # Turn
    world.para()
    c.meters["waiting"] += 1
    a.memes["stubborn"] += 1
    b.memes["stubborn"] += 1
    world.say(f"At first, {a.id} and {b.id} kept the court to themselves, and {c.id} waited by the line.")
    world.say(f"{c.id} did not complain. {c.id} only asked if friendship could make room for one more player.")

    # Change
    world.para()
    a.memes["share_with"] += 1
    b.memes["share_with"] += 1
    a.meters["occupy"] = 0
    b.meters["occupy"] = 0
    c.meters["waiting"] = 0
    propagate(world, narrate=False)
    world.say(f"{a.id} looked at {b.id}, then at {c.id}, and laughed at their own selfishness.")
    world.say(f"They stepped aside, let {c.id} onto the court, and turned the game into turns instead of pride.")
    world.say(f"Soon the ball flew back and forth, and every stroke felt kinder than the last.")

    # Ending image
    world.para()
    court = world.get("court")
    court.meters["crowded"] = max(0.0, court.meters["crowded"])
    if court.meters["crowded"] > 0:
        world.say("The court stayed crowded.")
    else:
        world.say(f"By sunset the court was shared, the three friends were smiling, and {place.label} felt wide enough for everyone.")
    world.say("Thus the fable ended: a friend who shares the field wins a larger game.")
    world.facts.update(
        place=place,
        first=a,
        second=b,
        third=c,
        court=court,
        shared=a.memes["share_with"] >= THRESHOLD and b.memes["share_with"] >= THRESHOLD,
        waiting=c.meters["waiting"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    a: Entity = f["first"]
    b: Entity = f["second"]
    c: Entity = f["third"]
    return [
        f'Write a short fable for children about friendship at {place.label} that includes the words "occupy" and "tennis".',
        f"Tell a happy-ending story where {a.id} and {b.id} first occupy the court, then make room for {c.id} to play tennis too.",
        f"Write a gentle fable about sharing a tennis court so friendship grows instead of pride.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    a: Entity = f["first"]
    b: Entity = f["second"]
    c: Entity = f["third"]
    return [
        QAItem(
            question=f"Who first wanted to occupy {place.label}?",
            answer=f"{a.id} and {b.id} wanted to occupy {place.label} first. They were excited and a little proud, so they tried to keep the tennis court to themselves.",
        ),
        QAItem(
            question=f"Why did {c.id} wait by the court line?",
            answer=f"{c.id} waited because {a.id} and {b.id} had taken the court. The wait ended when friendship mattered more than keeping the game for only two friends.",
        ),
        QAItem(
            question=f"What changed the ending of the tennis game?",
            answer=f"{a.id} and {b.id} chose to share the court with {c.id}. That choice turned the story into a happy ending, because the game became fair and all three could play.",
        ),
        QAItem(
            question="What did the friends learn from the game?",
            answer="They learned that occupying a good thing does not make it better, but sharing it can make everyone happier. Friendship grows when there is room for another friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does occupy mean?",
            answer="To occupy something means to take up a place or use it for a while, like standing on a court or sitting on a bench.",
        ),
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where players hit a ball with rackets over a net. They try to keep the ball in play and score points.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about one another, take turns, and want to help each other.",
        ),
    ]
    return out


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
        # Skip duplicated role aliases in trace to keep output readable.
        if e.id in {"first", "second", "third"}:
            continue
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing" and e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


PLACES = {
    "sunny_court": Place(id="sunny_court", label="the sunny court", phrase="the sunny court", tags={"tennis", "occupy", "friendship"}, can_tennis=True, can_occupy=True),
    "village_green": Place(id="village_green", label="the village green court", phrase="the village green court", tags={"tennis", "occupy", "friendship"}, can_tennis=True, can_occupy=True),
}

ANIMALS = {
    "Milo": "hare",
    "Tessa": "fox",
    "Nia": "mole",
    "Pip": "squirrel",
    "Oren": "otter",
    "Luna": "deer",
}

NAMES = list(ANIMALS.keys())


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def choose_name(rng: random.Random, avoid: set[str] = set()) -> str:
    pool = [n for n in NAMES if n not in avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.first and args.first not in NAMES:
        raise StoryError("Unknown first character.")
    if args.second and args.second not in NAMES:
        raise StoryError("Unknown second character.")
    if args.third and args.third not in NAMES:
        raise StoryError("Unknown third character.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.first is None or c[1] == args.first)
              and (args.second is None or c[2] == args.second)
              and (args.third is None or c[3] == args.third)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, first, second, third = rng.choice(sorted(combos))
    return StoryParams(place=place, first=first, second=second, third=third)


def generate(params: StoryParams) -> StorySample:
    reasonableness_check(params)
    world = tell(PLACES[params.place], params.first, params.second, params.third)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.can_tennis:
            lines.append(asp.fact("can_tennis", pid))
        if p.can_occupy:
            lines.append(asp.fact("can_occupy", pid))
    for n in NAMES:
        lines.append(asp.fact("name", n))
    for n, animal in ANIMALS.items():
        lines.append(asp.fact("animal", n, animal))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, A, B, C) :- place(P), can_tennis(P), can_occupy(P),
                     name(A), name(B), name(C),
                     A != B, A != C, B != C.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if not ok:
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print("only in python:", sorted(py - cl))
        if cl - py:
            print("only in clingo:", sorted(cl - py))
        return 1
    print(f"OK: ASP matches Python gate ({len(py)} combos).")
    try:
        sample = generate(StoryParams(place="sunny_court", first="Milo", second="Tessa", third="Nia"))
        assert sample.story.strip()
        assert sample.prompts
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate() smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about friendship, occupy, and tennis.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--first", choices=NAMES)
    ap.add_argument("--second", choices=NAMES)
    ap.add_argument("--third", choices=NAMES)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _entity_to_obj(e: Entity) -> dict:
    return {
        "id": e.id,
        "kind": e.kind,
        "type": e.type,
        "label": e.label,
        "phrase": e.phrase,
        "owner": e.owner,
        "role": e.role,
        "attrs": e.attrs,
        "meters": dict(e.meters),
        "memes": dict(e.memes),
        "tags": sorted(e.tags),
        "plural": e.plural,
    }


def _world_to_obj(world: Optional[World]) -> Optional[dict]:
    if world is None:
        return None
    return {
        "place": asdict(world.place) if is_dataclass(world.place) else world.place,
        "entities": [_entity_to_obj(e) for e in world.entities.values() if e.id not in {"first", "second", "third"}],
        "facts": {
            k: (_entity_to_obj(v) if isinstance(v, Entity) else (asdict(v) if is_dataclass(v) else v))
            for k, v in world.facts.items()
        },
        "paragraphs": world.paragraphs,
    }


def sample_to_obj(sample: StorySample) -> dict:
    params = sample.params
    if is_dataclass(params):
        params_obj = asdict(params)
    else:
        params_obj = params
    story_qa = [
        {"question": item.question, "answer": item.answer}
        for item in sample.story_qa
    ]
    world_qa = [
        {"question": item.question, "answer": item.answer}
        for item in sample.world_qa
    ]
    return {
        "params": params_obj,
        "story": sample.story,
        "prompts": list(sample.prompts),
        "story_qa": story_qa,
        "world_qa": world_qa,
        "world": _world_to_obj(sample.world),
    }


CURATED = [
    StoryParams(place="sunny_court", first="Milo", second="Tessa", third="Nia"),
    StoryParams(place="village_green", first="Pip", second="Oren", third="Luna"),
    StoryParams(place="sunny_court", first="Tessa", second="Luna", third="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        payload = sample_to_obj(samples[0]) if len(samples) == 1 else [sample_to_obj(s) for s in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/discover_conserve_dope_mystery_to_solve_animal.py
=================================================================================

A standalone storyworld about a small animal mystery in the forest.

Premise
-------
Tiny animal friends discover that something is missing or wasted in their home.
They follow clues, solve the mystery, and learn to conserve a precious thing:
water, nuts, seeds, berries, or nest fluff.

Style
-----
Animal story, child-facing, concrete, and state-driven. The ending proves what
changed: the mystery is solved, the needed thing is saved, and the animals end
up calm and proud.

Seed words
----------
The storyworld intentionally weaves in the words:
- discover
- conserve
- dope

The word "dope" is used as a child-safe, playful label for a little tool, trinket,
or clue in the animals' world, not as internal jargon.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/discover_conserve_dope_mystery_to_solve_animal.py
    python storyworlds/worlds/gpt-5.4-mini/discover_conserve_dope_mystery_to_solve_animal.py --all
    python storyworlds/worlds/gpt-5.4-mini/discover_conserve_dope_mystery_to_solve_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/discover_conserve_dope_mystery_to_solve_animal.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    setting: str
    clue_spots: list[str]
    resource: str
    resource_plural: bool = False


@dataclass
class Mystery:
    id: str
    question: str
    missing: str
    clue: str
    culprit: str
    solved_by: str
    need: str


@dataclass
class Response:
    id: str
    sense: int
    method: str
    result: str
    fail: str
    qa_text: str


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clue(world: World) -> list[str]:
    out = []
    mystery = world.facts.get("mystery")
    if not mystery:
        return out
    missing = world.get("missing")
    if missing.meters["gone"] >= THRESHOLD and ("clue", missing.id) not in world.fired:
        world.fired.add(("clue", missing.id))
        for c in world.characters():
            c.memes["curiosity"] += 1
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("clue", "social", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(place: Place, mystery: Mystery, response: Response) -> bool:
    return bool(place.clue_spots) and response.sense >= SENSE_MIN and mystery.need in {"water", "nuts", "berries", "seeds", "fluff"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def solve_possible(mystery: Mystery) -> bool:
    return mystery.culprit in {"wind", "squirrel", "bird", "rabbit", "child"} or True


def _find(world: World, hero: Entity, place: Place, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} and {world.get('friend').id} went to {place.setting}. "
        f"They wanted to discover why {mystery.missing} had gone missing."
    )
    world.say(
        f"At first, the place felt quiet, but the little signs around {place.label} looked dope."
    )


def _clue(world: World, hero: Entity, place: Place, mystery: Mystery) -> None:
    spot = random.choice(place.clue_spots)
    world.say(
        f"Near {spot}, {hero.id} spotted {mystery.clue}. "
        f"That clue pointed toward {mystery.culprit}."
    )


def _accuse(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'"{mystery.missing} is gone!" {hero.id} said. "We have to solve the mystery and conserve what is left."'
    )


def _solve(world: World, hero: Entity, response: Response, mystery: Mystery, place: Place) -> None:
    lost = world.get("missing")
    lost.meters["gone"] = 0.0
    world.get("stash").meters["safe"] += 1
    body = response.result.replace("{missing}", mystery.missing)
    world.say(
        f"Then {hero.id} tried {response.method}. {body}."
    )
    world.say(
        f"At last they found the answer: {mystery.culprit} had taken the {mystery.missing}, but only to {mystery.need} it at {place.label}."
    )


def _lesson(world: World, hero: Entity, friend: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} smiled. They agreed to conserve the {mystery.need} from then on, so the whole home would stay ready for tomorrow."
    )
    world.say(
        f"They left the {mystery.missing} in a tidy spot, and the forest felt calm again."
    )


def tell(place: Place, mystery: Mystery, response: Response, hero_name: str, friend_name: str, hero_type: str, friend_type: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["careful"]))
    world.add(Entity(id="missing", kind="thing", type=mystery.need, label=mystery.missing))
    world.add(Entity(id="stash", kind="thing", type="stash", label=place.resource))
    world.facts["mystery"] = mystery

    world.say(
        f"On a bright morning, {hero.id} and {friend.id} lived near {place.setting}. "
        f"They noticed that {mystery.missing} was missing from its usual place."
    )
    world.para()
    _find(world, hero, place, mystery)
    _accuse(world, hero, mystery)
    _clue(world, hero, place, mystery)
    propagate(world, narrate=False)
    world.para()
    _solve(world, hero, response, mystery, place)
    _lesson(world, hero, friend, mystery)

    world.facts.update(
        hero=hero, friend=friend, place=place, response=response, mystery=mystery,
        solved=True, missing=world.get("missing")
    )
    return world


PLACES = {
    "pond": Place("pond", "the pond", "the pond by the reeds", ["the reeds", "the muddy edge", "a fallen log"], "water"),
    "burrow": Place("burrow", "the burrow", "the burrow under the oak", ["the doorway", "a tiny tunnel", "the mossy wall"], "nuts", True),
    "meadow": Place("meadow", "the meadow", "the meadow near the fence", ["the fence post", "a flower patch", "the grass"], "berries", True),
}

MYSTERIES = {
    "water": Mystery("water", "what happened to the water", "water", "wet paw prints", "rabbit", "conserve"),
    "nuts": Mystery("nuts", "where the nuts went", "nuts", "a crumb trail", "squirrel", "conserve"),
    "berries": Mystery("berries", "who took the berries", "berries", "tiny red stains", "bird", "conserve"),
}

RESPONSES = {
    "follow": Response("follow", 3, "followed the clue carefully", "the clue led them right to the answer", "the clue got confused and went nowhere", "followed the clue carefully"),
    "ask": Response("ask", 3, "asked the neighbors kindly", "the neighbors pointed to the answer", "nobody knew, so the mystery stayed foggy", "asked the neighbors kindly"),
    "wait": Response("wait", 2, "waited and listened", "the quiet gave away the answer", "waiting did not help at all", "waited and listened"),
    "shout": Response("shout", 1, "shouted at the wind", "the mystery stayed unsolved", "the shouting made everything worse", "shouted at the wind"),
}

GIRL_NAMES = ["Mina", "Luna", "Rosa", "Tia", "Maya", "Ivy"]
BOY_NAMES = ["Ned", "Pip", "Toby", "Finn", "Ollie", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for mid, m in MYSTERIES.items():
            if mid == "water" and pid != "pond":
                continue
            if mid == "nuts" and pid != "burrow":
                continue
            if mid == "berries" and pid != "meadow":
                continue
            for rid, r in RESPONSES.items():
                if reasonableness_gate(p, m, r):
                    combos.append((pid, mid, rid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    response: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery storyworld with conserve/discover/dope words.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, response = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or (rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES))
    friend = args.friend or (rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero]))
    return StoryParams(place, mystery, response, hero, hero_type, friend, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "discover", "conserve", and "dope".',
        f"Tell a mystery story where {f['hero'].id} and {f['friend'].id} discover what happened to the {f['mystery'].missing} and learn to conserve it.",
        f"Write a gentle forest mystery about {f['place'].label} that ends with the animals solving the clue and keeping things tidy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, place, mystery = f["hero"], f["friend"], f["place"], f["mystery"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two small animals near {place.setting}. They work together to solve a mystery."),
        ("What were they trying to discover?",
         f"They wanted to discover what happened to the {mystery.missing}. The clues showed that the answer was not scary, just unexpected."),
        ("What did they learn to do?",
         f"They learned to conserve the {mystery.need}. That helped keep their home ready for the next day."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    need = f["mystery"].need
    if need == "water":
        return [("Why do animals need water?", "Animals need water to drink and stay healthy.") ]
    if need == "nuts":
        return [("Why do squirrels save nuts?", "Squirrels save nuts so they have food later, especially when it gets cold.") ]
    return [("Why do birds carry berries?", "Birds may carry berries to eat them or move seeds to new places.") ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "water", "follow", "Mina", "girl", "Pip", "boy"),
    StoryParams("burrow", "nuts", "ask", "Toby", "boy", "Luna", "girl"),
    StoryParams("meadow", "berries", "wait", "Ivy", "girl", "Ben", "boy"),
]


def explain_rejection(place: Place, mystery: Mystery, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return "(No story: the response is too weak for a mystery story.)"
    return "(No story: this combination does not fit the animal mystery world.)"


ASP_RULES = r"""
valid(P, M, R) :- place(P), mystery(M), response(R), fit(P, M), sense(R, S), sense_min(Min), S >= Min.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fit", next(pid for pid, mm in PLACES.items() if mm.resource == m.need), mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], RESPONSES[params.response],
                 params.hero, params.friend, params.hero_type, params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

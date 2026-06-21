#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rodent_mystery_to_solve_kindness_bravery_fable.py
==================================================================================

A small fable-like storyworld about a tiny rodent mystery: something goes missing,
the animal characters use kindness and bravery to solve it, and the ending shows
what changed in the little village.

The world is built to stay close to a classic fable tone:
- concrete animals and objects
- a clear mystery
- a cautious, brave search
- kindness that changes the outcome
- a final image proving the fix

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- `StoryParams`, `build_parser`, `resolve_params`, `generate`, `emit`, `main`
- prompts, story-grounded QA, and world-knowledge QA
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
COURAGE_MIN = 2.0


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
        if self.type in {"mouse", "rat", "hamster", "squirrel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    name: str
    cover: str
    hiding_spots: list[str]
    materials: list[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    place_hint: str
    fear_word: str
    recovered_from: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    kindness: str
    bravery: str
    method: str
    tags: set[str] = field(default_factory=set)
    kind_value: int = 0
    brave_value: int = 0


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["missing"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for k in world.entities.values():
            if k.kind == "character":
                k.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("sharing") and "crow" in world.entities:
        crow = world.get("crow")
        if crow.meters["lost"] >= THRESHOLD and ("kindness", "crow") not in world.fired:
            world.fired.add(("kindness", "crow"))
            crow.meters["returned"] += 1
            out.append("The kind act made the little theft matter feel smaller.")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("kindness", "social", _r_kindness)]


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


def mystery_at_risk(mystery: Mystery, helper: Helper) -> bool:
    return mystery.missing and helper.kind_value >= 2 and helper.brave_value >= 2


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.kind_value >= 2 and h.brave_value >= 2]


def best_helper() -> Helper:
    return max(HELPERS.values(), key=lambda h: (h.kind_value + h.brave_value, h.id))


def outcome_of(params: "StoryParams") -> str:
    if params.helper not in HELPERS:
        raise StoryError("unknown helper")
    if params.mystery not in MYSTERIES:
        raise StoryError("unknown mystery")
    return "solved" if params.helper in HELPERS and params.mystery in MYSTERIES else "unknown"


def tell(place: Place, mystery: Mystery, helper: Helper, rodent_name: str = "Milo",
         rodent_type: str = "mouse", friend_name: str = "Pip",
         friend_type: str = "mouse", elder_name: str = "Grandmama",
         elder_type: str = "mouse") -> World:
    world = World()
    rodent = world.add(Entity(id=rodent_name, kind="character", type=rodent_type, role="seeker", traits=["curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="helper", traits=["kind"]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", traits=["wise"]))
    thing = world.add(Entity(id="missing", type="thing", label=mystery.missing))
    crow = world.add(Entity(id="crow", kind="character", type="crow", role="troublemaker", label="crow"))
    crow.meters["lost"] = 1.0

    rodent.memes["curiosity"] = 2.0
    friend.memes["kindness"] = 2.0
    elder.memes["bravery"] = 2.0

    world.say(
        f"In {place.name}, there lived a little {rodent.type} named {rodent.id}. "
        f"{rodent.id} loved {place.cover} and knew the narrow lanes under the roots."
    )
    world.say(
        f"One morning, the village grew uneasy, for {mystery.missing} had gone missing. "
        f"The only clue was this: {mystery.clue}."
    )

    world.para()
    world.say(
        f"{rodent.id} did not laugh at the trouble. {rodent.pronoun().capitalize()} said, "
        f'"I will look. A small heart can still be brave."'
    )
    friend.memes["kindness"] += 1
    world.say(
        f"{friend.id} brought a soft crumb and a calm voice, and {elder.id} nodded. "
        f'"Kindness makes a lantern," {elder.id} said.'
    )

    world.para()
    thing.meters["missing"] = 1.0
    if mystery_at_risk(mystery, helper):
        world.say(
            f"They followed the clue to {mystery.place_hint}, where the air smelled of {place.materials[0]}. "
            f"{rodent.id} found tiny tracks, and {friend.id} noticed a feather caught on a thorn."
        )
    world.say(
        f"{rodent.id} crept past the hiding spots with a steady step, even when {mystery.fear_word} made {rodent.pronoun('object')} tremble."
    )
    world.say(
        f"Then {friend.id} spoke gently to the crow instead of chasing it. "
        f"The crow blinked, listened, and led them to {mystery.recovered_from}."
    )
    crow.meters["lost"] = 0.0
    crow.meters["returned"] = 1.0
    world.facts["sharing"] = True
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"There, hidden under {mystery.recovered_from}, was the missing {mystery.missing}. "
        f"{rodent.id} carried it home while {friend.id} thanked the crow with the crumb."
    )
    world.say(
        f"By sunset, the village was calm again. {mystery.missing} rested back where it belonged, "
        f"and the crow did not steal from that lane anymore."
    )
    world.say(
        f"The little {rodent.type} had solved the mystery with brave steps and a kind heart, "
        f"and the old elder smiled to see how one gentle act had made the whole village safer."
    )

    world.facts.update(
        place=place,
        mystery=mystery,
        helper=helper,
        rodent=rodent,
        friend=friend,
        elder=elder,
        crow=crow,
        outcome="solved",
    )
    return world


PLACES = {
    "barn": Place(
        id="barn",
        name="the warm barn",
        cover="the hay loft",
        hiding_spots=["under the straw", "behind the feed bin", "near the ladder"],
        materials=["hay", "dust", "wood"],
        tags={"barn", "rodent"},
    ),
    "garden": Place(
        id="garden",
        name="the garden wall",
        cover="the bean vines",
        hiding_spots=["under the leaves", "behind the stone pot", "near the gate"],
        materials=["soil", "leaves", "twigs"],
        tags={"garden", "rodent"},
    ),
    "mill": Place(
        id="mill",
        name="the old grain mill",
        cover="the grain sacks",
        hiding_spots=["behind the sacks", "under the wheel", "in the corner"],
        materials=["grain", "flour", "wood"],
        tags={"mill", "rodent"},
    ),
}

MYSTERIES = {
    "cheese": Mystery(
        id="cheese",
        missing="the cheese",
        clue="a few crumbs led toward the loft",
        place_hint="the loft beams",
        fear_word="the dark",
        recovered_from="a loose hay pile",
        tags={"cheese", "rodent"},
    ),
    "key": Mystery(
        id="key",
        missing="the tiny brass key",
        clue="a shining mark pointed near the sacks",
        place_hint="the dusty corner",
        fear_word="the wind",
        recovered_from="a folded cloth",
        tags={"key", "rodent"},
    ),
    "seedbag": Mystery(
        id="seedbag",
        missing="the seed bag",
        clue="a trail of husks led under the vines",
        place_hint="the bean patch",
        fear_word="the buzzing bees",
        recovered_from="a vine basket",
        tags={"seed", "rodent"},
    ),
}

HELPERS = {
    "gentle": Helper(id="gentle", type="mouse", label="gentle", kindness="kind", bravery="brave", method="ask softly", kind_value=3, brave_value=2, tags={"kindness", "bravery"}),
    "steady": Helper(id="steady", type="mouse", label="steady", kindness="kind", bravery="steady", method="search carefully", kind_value=2, brave_value=3, tags={"kindness", "bravery"}),
    "bright": Helper(id="bright", type="mouse", label="bright", kindness="kind", bravery="bold", method="follow clues together", kind_value=3, brave_value=3, tags={"kindness", "bravery"}),
}

NAMES = ["Milo", "Nina", "Toby", "Sana", "Pip", "Luna", "Otto", "Mina"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    rodent_name: str
    friend_name: str
    elder_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for h in HELPERS:
                if mystery_at_risk(MYSTERIES[m], HELPERS[h]):
                    combos.append((p, m, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about a rodent mystery, kindness, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--elder")
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
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, helper = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        helper=helper,
        rodent_name=args.name or rng.choice(NAMES),
        friend_name=args.friend or rng.choice([n for n in NAMES if n != args.name]),
        elder_name=args.elder or "Grandmama",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story about a rodent named {f["rodent"].id} who solves a mystery with kindness and bravery.',
        f'Tell a gentle animal story where {f["rodent"].id} follows a clue about {f["mystery"].missing} and uses kindness instead of force.',
        f'Write a short moral tale about a little rodent, a missing thing, and a brave kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rodent = f["rodent"]
    mystery = f["mystery"]
    friend = f["friend"]
    elder = f["elder"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {rodent.id}, a little {rodent.type}, who wanted to solve the mystery. {friend.id} and {elder.id} helped turn the worry into a kind search.",
        ),
        QAItem(
            question="What was missing?",
            answer=f"{mystery.missing} was missing at the start. That was the mystery everyone wanted to solve.",
        ),
        QAItem(
            question=f"How did {rodent.id} solve the mystery?",
            answer=f"{rodent.id} followed the clue, stayed brave, and let {friend.id} use kindness to calm the crow. Because they were gentle, they found {mystery.missing} and brought it home safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rodent?",
            answer="A rodent is a small animal with teeth that keep growing, like a mouse or a rat. Rodents often live close to the ground and can squeeze into tiny spaces.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring. A kind choice can make fear smaller and help others cooperate.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel scared. A brave creature keeps going and does not run away from every hard moment.",
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="barn", mystery="cheese", helper="bright", rodent_name="Milo", friend_name="Pip", elder_name="Grandmama"),
    StoryParams(place="mill", mystery="key", helper="steady", rodent_name="Nina", friend_name="Toby", elder_name="Old Mouse"),
    StoryParams(place="garden", mystery="seedbag", helper="gentle", rodent_name="Toby", friend_name="Luna", elder_name="Grandmama"),
]


ASP_RULES = r"""
sensible(H) :- helper(H), kind_value(H, K), brave_value(H, B), K >= 2, B >= 2.
valid(P, M, H) :- place(P), mystery(M), helper(H), sensible(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for h, hv in HELPERS.items():
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("kind_value", h, hv.kind_value))
        lines.append(asp.fact("brave_value", h, hv.brave_value))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in combo gate")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, helper=None, name=None, friend=None, elder=None), random.Random(777)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("unknown place")
    if params.mystery not in MYSTERIES:
        raise StoryError("unknown mystery")
    if params.helper not in HELPERS:
        raise StoryError("unknown helper")
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        HELPERS[params.helper],
        rodent_name=params.rodent_name,
        friend_name=params.friend_name,
        elder_name=params.elder_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, mystery, helper) combos:")
        for p, m, h in asp_valid_combos():
            print(f"  {p:8} {m:10} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

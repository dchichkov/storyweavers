#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cud_brace_suspense_whodunit.py
===========================================================================================================

A small whodunit-style story world about a barnyard mystery with cud, a brace,
and a careful little detective. The world is intentionally narrow: it favors
one strong, clue-driven premise over many weak variants.

Seed tale imagined from the prompt:
---
On a windy night, a lantern goes missing from the barn. The little detective
notices a wet patch of cud near the feed trough, a brace propping a side gate
open, and a trail that does not quite match any one animal. By following the
clues, the detective learns who moved the lantern and why.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "detective"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the barn"
    indoors: bool = True
    tags: set[str] = field(default_factory=lambda: {"barn", "night"})


@dataclass
class Clue:
    id: str
    kind: str
    phrase: str
    source: str
    suspicion: float = 1.0


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    clue: str
    motive: str
    innocent: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _puzzle_trace(world: World) -> list[str]:
    out = []
    detective = world.get("detective")
    if detective.memes.get("curious", 0) >= THRESHOLD:
        out.append("The detective kept looking, because the dark barn did not give up its secret at once.")
    if detective.memes.get("suspense", 0) >= THRESHOLD:
        out.append("Every clue felt important.")
    return out


def _clue_suspicion(world: World) -> list[str]:
    out = []
    for clue in world.facts["clues"]:
        sig = ("clue", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{clue.phrase} caught the detective's eye.")
        world.get("detective").memes["suspense"] = world.get("detective").memes.get("suspense", 0) + clue.suspicion
        world.get("detective").meters["evidence"] = world.get("detective").meters.get("evidence", 0) + clue.suspicion
    return out


def _resolve(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meters.get("evidence", 0) < THRESHOLD:
        return []
    if ("solved",) in world.fired:
        return []
    world.fired.add(("solved",))
    culprit = world.facts["culprit"]
    world.facts["solved"] = True
    return [f"At last, {detective.id} knew that {culprit.label} had moved the lantern."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    sentences = []
    for fn in (_clue_suspicion, _resolve):
        sentences.extend(fn(world))
    sentences.extend(_puzzle_trace(world))
    if narrate:
        for s in sentences:
            world.say(s)
    return sentences


@dataclass
class StoryParams:
    name: str
    sidekick: str
    culprit: str
    seed: Optional[int] = None


SETTING = Setting()

SUSPECTS = {
    "goat": Suspect(
        id="goat",
        label="the goat",
        type="goat",
        clue="a clump of cud on the feed trough",
        motive="to reach the warm hay and nibble the salt lick",
    ),
    "dog": Suspect(
        id="dog",
        label="the dog",
        type="dog",
        clue="muddy paw prints by the gate",
        motive="to chase a moth into the dark",
    ),
    "calf": Suspect(
        id="calf",
        label="the calf",
        type="calf",
        clue="a small bell-shaped mark in the dust",
        motive="to look for its mother",
    ),
}

CLUES = {
    "goat": [
        Clue(id="cud", kind="cud", phrase="A smear of cud sat by the trough", source="goat", suspicion=1.0),
        Clue(id="brace", kind="brace", phrase="A loose brace held the side gate open", source="goat", suspicion=1.0),
    ],
    "dog": [
        Clue(id="paw", kind="paw", phrase="Muddy paw prints crossed the aisle", source="dog", suspicion=1.0),
        Clue(id="brace", kind="brace", phrase="A loose brace held the side gate open", source="dog", suspicion=0.5),
    ],
    "calf": [
        Clue(id="milk", kind="milk", phrase="A warm milk pail was tipped beside the stall", source="calf", suspicion=1.0),
        Clue(id="brace", kind="brace", phrase="A loose brace held the side gate open", source="calf", suspicion=0.5),
    ],
}

NAMES = ["Mila", "Toby", "June", "Noah", "Lena", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: cud, brace, and a barn mystery.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=["dog", "cat", "owl"])
    ap.add_argument("--culprit", choices=list(SUSPECTS))
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
    for culprit in SUSPECTS:
        for sidekick in ["dog", "cat", "owl"]:
            combos.append((SETTING.place, culprit, sidekick))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    culprit = args.culprit or rng.choice(list(SUSPECTS))
    sidekick = args.sidekick or rng.choice(["dog", "cat", "owl"])
    name = args.name or rng.choice(NAMES)
    if culprit not in SUSPECTS:
        raise StoryError("Unknown culprit.")
    return StoryParams(name=name, sidekick=sidekick, culprit=culprit)


def generate_world(params: StoryParams) -> World:
    world = World(SETTING)
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick, label=params.sidekick))
    culprit = SUSPECTS[params.culprit]
    world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a small red lantern"))
    world.add(Entity(id="brace", type="thing", label="brace", phrase="a wooden brace"))
    world.add(Entity(id="cud", type="thing", label="cud", phrase="a clump of cud"))
    detective.memes["curious"] = 1.0
    detective.memes["suspense"] = 1.0

    clues = CLUES[culprit.id]
    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        culprit=culprit,
        clues=clues,
    )

    world.say(f"On a windy night in the barn, {params.name} and the little {params.sidekick} stood under the rafters.")
    world.say("The lantern by the feed trough was gone.")
    world.para()
    world.say(f"{params.name} bent down and studied the straw.")
    world.say("A clue waited there, and the barn felt very still.")
    propagate(world)
    world.para()
    if culprit.id == "goat":
        world.say("The goat had nudged the lantern aside while reaching for the salt lick, and the cud by the trough gave it away.")
    elif culprit.id == "dog":
        world.say("The dog had carried the lantern to the door after chasing a moth, but the muddy prints matched the rush.")
    else:
        world.say("The calf had dragged the lantern closer to the milk pail, hoping to find its mother in the dark.")
    world.say(f"{params.name} set the lantern back where it belonged.")
    world.say("Then the barn looked calm again, with the brace fixed and the clues no longer mysterious.")
    world.facts["solved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    culprit = f["culprit"]
    detective = f["detective"]
    return [
        QAItem(
            question=f"What was missing in the barn when {detective.label} started to look around?",
            answer="The small red lantern was missing from its place by the feed trough.",
        ),
        QAItem(
            question="What clue made the detective think carefully about the case?",
            answer=f"{f['clues'][0].phrase}. That clue pointed toward {culprit.label}.",
        ),
        QAItem(
            question="Who moved the lantern?",
            answer=f"{culprit.label} moved the lantern, and the clues made that clear.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cud?",
            answer="Cud is food that a cow or goat chews again after swallowing it the first time.",
        ),
        QAItem(
            question="What is a brace?",
            answer="A brace is something that holds another thing steady or keeps it from falling over.",
        ),
        QAItem(
            question="Why does a mystery story build suspense?",
            answer="A mystery story builds suspense by leaving the answer hidden while the clues slowly appear.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit story for a child about a missing lantern, using the words "cud" and "brace".',
        f"Tell a suspenseful barn mystery where {f['detective'].label} follows clues to discover who moved the lantern.",
        "Write a simple detective story with a calm ending image that proves the clue trail made sense.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A clue is relevant if it raises suspicion.
relevant(C) :- clue(C).

% The case is solved when suspicion is high enough.
solved :- evidence(E), E >= 2.

% The culprit is the one whose clues are present.
culprit(goat) :- clue(cud), clue(brace).
culprit(dog) :- clue(paw), clue(brace).
culprit(calf) :- clue(milk), clue(brace).
"""


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("setting", "barn"))
    for c in ("cud", "brace", "paw", "milk"):
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("evidence", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show solved/0."))
    atoms = [str(a) for a in model]
    ok = "solved" in atoms
    if ok:
        print("OK: ASP gate is reachable.")
        return 0
    print("MISMATCH: ASP gate did not solve as expected.")
    return 1


CURATED = [
    StoryParams(name="Mila", sidekick="dog", culprit="goat"),
    StoryParams(name="Theo", sidekick="owl", culprit="calf"),
    StoryParams(name="June", sidekick="cat", culprit="dog"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.culprit} / {p.sidekick}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small fable-like storyworld about a pecker, a mystery to solve, dialogue,
and reconciliation.

The seed image:
- A pecker hears a strange tapping in the orchard.
- The animals talk, suspect one another, and search for the source.
- The mystery turns out to be a loose lantern chain that has been striking a
  hollow post in the wind.
- The birds and beasts reconcile after understanding the truth.

This script keeps the world deliberately small and constraint-checked.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bird", "pecker", "sparrow", "owl", "finch"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"farmer", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    soundscape: str


@dataclass
class Clue:
    id: str
    source: str
    sound: str
    truth: str
    visible: bool = True


@dataclass
class StoryParams:
    setting: str
    pecker_name: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "orchard": Setting(
        place="the orchard",
        weather="windy",
        soundscape="soft leaves and creaking branches",
    ),
    "meadow": Setting(
        place="the meadow",
        weather="breezy",
        soundscape="grass whispering under a pale sky",
    ),
    "lantern_grove": Setting(
        place="the lantern grove",
        weather="windy",
        soundscape="hanging lanterns and a long wooden path",
    ),
}

COMPANIONS = {
    "squirrel": Entity(id="squirrel", kind="character", type="squirrel", label="squirrel"),
    "mole": Entity(id="mole", kind="character", type="mole", label="mole"),
    "rabbit": Entity(id="rabbit", kind="character", type="rabbit", label="rabbit"),
}

PECKER_TYPES = {
    "pecker": "pecker",
    "woodpecker": "pecker",
}

CLUES = {
    "orchard": Clue(
        id="lantern_chain",
        source="a loose lantern chain",
        sound="a soft clink-clink",
        truth="the chain was tapping against a hollow post in the wind",
    ),
    "meadow": Clue(
        id="tin_cup",
        source="a tin cup on a fence",
        sound="a tiny ding-ding",
        truth="the cup was bumping the fence as the breeze pushed it",
    ),
    "lantern_grove": Clue(
        id="wind_chime",
        source="a wind chime",
        sound="a bright ring-ring",
        truth="the chime was swaying and striking a branch",
    ),
}


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.companion not in COMPANIONS:
        raise StoryError("Unknown companion.")
    world = World(SETTINGS[params.setting])
    pecker = world.add(Entity(
        id=params.pecker_name,
        kind="character",
        type="pecker",
        label="pecker",
        traits=["small", "curious", "patient"],
    ))
    companion = world.add(copy.deepcopy(COMPANIONS[params.companion]))
    clue = CLUES[params.setting]
    world.facts["pecker"] = pecker
    world.facts["companion"] = companion
    world.facts["clue"] = clue
    return world


def _speak_dialogue(world: World, speaker: Entity, line: str) -> None:
    world.say(f'{speaker.id} said, "{line}"')


def tell(world: World) -> World:
    pecker: Entity = world.facts["pecker"]
    companion: Entity = world.facts["companion"]
    clue: Clue = world.facts["clue"]

    pecker.memes["curiosity"] = pecker.memes.get("curiosity", 0.0) + 1
    companion.memes["unease"] = companion.memes.get("unease", 0.0) + 1

    world.say(
        f"In {world.setting.place}, where the air carried {world.setting.soundscape}, "
        f"there lived a little pecker who listened to every sound."
    )
    world.say(
        f"One day the pecker heard {clue.sound} and paused with its beak lifted."
    )
    _speak_dialogue(world, pecker, "Who is making that tapping?")
    world.say(
        f"The pecker and the {companion.id} followed the sound beneath the branches."
    )

    world.para()
    _speak_dialogue(world, companion, "Maybe the old stump is haunted.")
    _speak_dialogue(world, pecker, "Or maybe the wind is carrying something light.")
    world.say(
        f"They searched the ground, the bark, and the roots, but the sound kept coming."
    )
    companion.memes["fear"] = companion.memes.get("fear", 0.0) + 1
    pecker.memes["resolve"] = pecker.memes.get("resolve", 0.0) + 1

    world.para()
    world.say(
        f"At last the pecker noticed a loose chain swaying near a hollow post."
    )
    _speak_dialogue(world, pecker, f"Look closely; {clue.source} is touching the wood.")
    _speak_dialogue(world, companion, "Then the mystery is not a troublemaker at all.")
    world.say(
        f"The wind nudged the chain again, and the pecker saw the truth: {clue.truth}."
    )

    world.para()
    companion.memes["fear"] = 0.0
    companion.memes["trust"] = companion.memes.get("trust", 0.0) + 1
    pecker.memes["contentment"] = pecker.memes.get("contentment", 0.0) + 1
    _speak_dialogue(world, companion, "I was wrong to worry.")
    _speak_dialogue(world, pecker, "We were wise to ask before blaming.")
    world.say(
        f"The pecker and the {companion.id} set the chain straight and tied it fast."
    )
    world.say(
        f"After that, the orchard was calm again, and the little pecker smiled at the clean, quiet post."
    )

    world.facts["solved"] = True
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]
    pecker: Entity = world.facts["pecker"]
    companion: Entity = world.facts["companion"]
    return [
        f'Write a short fable about a pecker in {world.setting.place} who hears "{clue.sound}" and tries to solve a mystery.',
        f"Tell a gentle story where {pecker.id} and a {companion.id} talk through a strange sound, discover the truth, and make peace.",
        f'Write a child-friendly mystery story that includes dialogue, a clue, and a reconciliation at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    pecker: Entity = world.facts["pecker"]
    companion: Entity = world.facts["companion"]
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question=f"What strange sound did {pecker.id} hear in {world.setting.place}?",
            answer=f'{pecker.id} heard {clue.sound}, and it made the pecker stop and listen carefully.',
        ),
        QAItem(
            question=f"Who helped {pecker.id} solve the mystery?",
            answer=f"The {companion.id} helped {pecker.id} search for the source of the sound and talk it through.',
        ),
        QAItem(
            question="What was the real cause of the tapping?",
            answer=f"The tapping came from {clue.truth}, so the mystery was solved without any danger.',
        ),
        QAItem(
            question="How did the story end?",
            answer="The friends fixed the problem, admitted their mistake, and calmed down together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand at first, so you look for clues and ask questions until you find the truth.",
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to become friendly again after a disagreement or worry.",
        ),
        QAItem(
            question="Why do animals listen carefully in a fable?",
            answer="In a fable, listening carefully helps the characters learn a lesson and avoid guessing too fast.",
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
        lines.append(f"  {e.id:12} ({e.type:9}) meters={meters} memes={memes}")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for companion in COMPANIONS:
            combos.append((setting, "pecker", companion))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports a pecker, a small companion, and one of the built-in settings.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a pecker solves a mystery through dialogue and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name", dest="pecker_name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.companion is None or c[2] == args.companion)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, _, companion = rng.choice(sorted(combos))
    pecker_name = args.pecker_name or rng.choice(["Pico", "Bram", "Tico", "Keen"])
    return StoryParams(setting=setting, pecker_name=pecker_name, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
setting(S) :- place(S).
solve(S) :- setting(S), clue(S), dialogue(S), reconcile(S).
"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("dialogue", "yes"))
    lines.append(asp.fact("reconcile", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    py = set((s,) for s in SETTINGS)
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible story combos")
        for s, _, c in valid_combos():
            print(f"  {s:14} pecker   {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for companion in COMPANIONS:
                params = StoryParams(setting=setting, pecker_name="Pico", companion=companion)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.setting} / {p.pecker_name} / {p.companion}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

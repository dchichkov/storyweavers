#!/usr/bin/env python3
"""
storyworlds/worlds/small_conflict_curiosity_rhyme_whodunit.py
=============================================================

A small whodunit storyworld with curiosity, conflict, and a little rhyme.
A child notices a tiny mystery, follows clues, meets a conflict, and solves it
with a careful reveal. The stories are state-driven, not fixed templates.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    clue_spots: list[str]
    witnesses: list[str]


@dataclass
class Mystery:
    id: str
    object_name: str
    object_phrase: str
    hidden_place: str
    rhyme_hint: str
    conflict_word: str
    curiosity_word: str
    resolution: str


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("the small kitchen", ["drawer", "shelf", "table"], ["mom", "dad"]),
    "classroom": Setting("the small classroom", ["desk", "bin", "bookcase"], ["teacher", "friend"]),
    "attic": Setting("the small attic", ["trunk", "box", "beam"], ["grandparent", "cousin"]),
}

MYSTERIES = {
    "missing_cookie": Mystery(
        "missing_cookie", "cookie", "the missing cookie", "under the blue bowl",
        "A crumb by the rug, a spoon gone sly, look low, look near, and then look high.",
        "conflict", "curiosity", "found on the plate",
    ),
    "lost_key": Mystery(
        "lost_key", "key", "the little key", "inside the flower pot",
        "A key can hide where leaves are wet; a plant will keep a tiny secret yet.",
        "conflict", "curiosity", "found in the pot",
    ),
    "vanished_crayon": Mystery(
        "vanished_crayon", "crayon", "the red crayon", "behind the curtain",
        "A red surprise with waxy toes may rest where the folded curtain goes.",
        "conflict", "curiosity", "found behind the curtain",
    ),
}

NAMES = {
    "girl": ["Mia", "Lily", "Nora", "Zoe"],
    "boy": ["Finn", "Leo", "Eli", "Max"],
    "helper": ["mom", "dad", "teacher", "friend", "grandparent", "cousin"],
}


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return bool(setting.clue_spots) and bool(mystery.rhyme_hint)


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: {mystery.id} does not fit {setting.place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Small whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list({h for s in SETTINGS.values() for h in s.witnesses}))
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
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    ms = MYSTERIES[mystery]
    if not reasonableness_gate(SETTINGS[setting], ms):
        raise StoryError(explain_rejection(SETTINGS[setting], ms))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(NAMES["helper"])
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    child = world.add(Entity(params.name, "character", params.gender, params.name,
                             meters={"steps": 0.0}, memes={"curiosity": 0.0, "conflict": 0.0}))
    helper = world.add(Entity("helper", "character", "adult", params.helper,
                              meters={"steps": 0.0}, memes={"calm": 1.0}))
    clue = world.add(Entity("clue", "thing", mystery.object_name, mystery.object_phrase,
                            attrs={"hidden_place": mystery.hidden_place},
                            meters={"noticed": 0.0}, memes={"rhyme": 0.0}))
    world.facts.update(child=child, helper=helper, clue=clue, mystery=mystery, setting=setting)
    child.memes["curiosity"] += 1
    child.meters["steps"] += 1
    world.say(f"{child.id} was a small child in {setting.place}. {child.pronoun().capitalize()} noticed a tiny mystery.")
    world.say(f"{child.id} listened to a rhyme: \"{mystery.rhyme_hint}\"")
    world.para()
    child.memes["curiosity"] += 1
    world.say(f"{child.id} looked under the {setting.clue_spots[0]} and then the {setting.clue_spots[1]}.")
    world.say(f"{helper.label.capitalize()} warned that this could lead to a {mystery.conflict_word}, but {child.id} wanted to know more.")
    child.memes["conflict"] += 1
    world.para()
    clue.meters["noticed"] += 1
    clue.memes["rhyme"] += 1
    world.say(f"At last, {child.id} found {mystery.object_phrase} {mystery.hidden_place}.")
    world.say(f"{child.id} called {helper.label}, and together they checked the clue.")
    world.para()
    child.memes["conflict"] = 0.0
    world.say(f"The answer was simple: {mystery.resolution}. {child.id} smiled, because curiosity had solved the case.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    m = f["mystery"]
    return [
        f"Write a short whodunit for a small child named {c.id} in {world.setting.place}.",
        f"Tell a mystery story where {c.id} follows a rhyme to find {m.object_phrase}.",
        f"Write a gentle story with curiosity, conflict, and a tidy reveal about {m.object_name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, h, m = f["child"], f["helper"], f["mystery"]
    return [
        QAItem(question=f"Who is the story about?", answer=f"It is about {c.id}, a small child who wanted to solve a mystery."),
        QAItem(question=f"What clue did {c.id} follow?", answer=f"{c.id} followed a rhyme that helped point to {m.object_phrase}."),
        QAItem(question=f"Who helped in the end?", answer=f"{h.label.capitalize()} helped {c.id} check the clue and find the answer."),
        QAItem(question=f"What was the answer to the mystery?", answer=f"The answer was that the hidden item was {m.resolution}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a clue?", answer="A clue is a small piece of information that helps solve a mystery."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to learn more and find out what is hidden."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a pattern of words that sound alike at the end."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="] + [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)] + ["", "== Story QA =="]
    for q in sample.story_qa:
        parts += [f"Q: {q.question}", f"A: {q.answer}"]
    parts += ["", "== World QA =="]
    for q in sample.world_qa:
        parts += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M) :- setting(S), mystery(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, m, "Mia", "girl", "mom")) for s, m in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/thing_dim_clue_evaluate_problem_solving_lesson.py
===================================================================

A tiny pirate-tale story world about a crew facing a clue, making an
evaluation, and solving a problem with a lesson learned and a bit of humor.

Premise:
- A small pirate crew wants to find a hidden snack chest.
- A clue points to one of several things around the ship.
- The crew must evaluate the clue carefully instead of rushing.
- The wrong choice causes a funny, harmless mishap.
- The right choice leads to a small victory and a lesson: careful thinking
  beats bluster.

The story is modeled as state changes:
- clue confidence rises or falls based on evaluation,
- the ship's physical state changes when the wrong thing is checked,
- the crew's emotional state shifts from worry to relief and pride,
- the ending proves the change by showing the chest opened and the lesson
  learned.

This world intentionally keeps the cast small and the setting simple so the
turn and resolution are easy to follow for young readers.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pirate", "captain", "mate"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the deck"
    atmosphere: str = "salt-bright"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    hint: str
    weight: str
    is_clue: bool = False


@dataclass
class Challenge:
    id: str
    verb: str
    wrong_verb: str
    mess: str
    result: str
    clue_key: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "deck": Setting(place="the deck", atmosphere="salt-bright", affords={"scan", "dig", "listen"}),
    "cabin": Setting(place="the cabin", atmosphere="lantern-warm", affords={"scan", "peek", "listen"}),
    "beach": Setting(place="the beach", atmosphere="windy", affords={"scan", "dig", "listen"}),
}

CHALLENGES = {
    "find_snack": Challenge(
        id="find_snack",
        verb="find the snack chest",
        wrong_verb="open the squeaky barrel",
        mess="splash",
        result="the snack chest",
        clue_key="banana_peel",
        tags={"clue", "evaluate", "thing-dim"},
    ),
    "find_flag": Challenge(
        id="find_flag",
        verb="find the flag stash",
        wrong_verb="lift the heavy crate",
        mess="clatter",
        result="the flag stash",
        clue_key="red_thread",
        tags={"clue", "evaluate", "thing-dim"},
    ),
}

THINGS = {
    "barrel": Thing("barrel", "barrel", "a squeaky barrel", "It creaks when tapped.", "heavy"),
    "crate": Thing("crate", "crate", "a heavy crate", "It hides a neat corner.", "heavy"),
    "rope": Thing("rope", "rope coil", "a rope coil", "It loops in a tidy circle.", "long"),
    "boot": Thing("boot", "boot", "a lone boot", "It has a sticky leaf on it.", "small"),
    "banana_peel": Thing("banana_peel", "banana peel", "a curled banana peel", "It points toward the chest lid.", "small", True),
    "red_thread": Thing("red_thread", "red thread", "a bright red thread", "It is tied to the right latch.", "small", True),
}

PIRATE_NAMES = ["Mara", "Ned", "Bree", "Finn", "Pip", "Jo", "Tess", "Rook"]
CREW_TYPES = ["captain", "mate", "pirate"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    hero: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def _hero_label(role: str) -> str:
    return {"captain": "captain", "mate": "first mate"}.get(role, "pirate")


def _describe_setting(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was {setting.atmosphere} and busy with sea wind."


def _wrong_choice_item(challenge: Challenge) -> Thing:
    return THINGS["barrel"] if challenge.id == "find_snack" else THINGS["crate"]


def _correct_clue(challenge: Challenge) -> Thing:
    return THINGS[challenge.clue_key]


def _state_line(world: World, actor: Entity) -> str:
    worried = actor.memes.get("worry", 0.0)
    proud = actor.memes.get("pride", 0.0)
    if worried >= THRESHOLD and proud < THRESHOLD:
        return f"{actor.id} looked worried but kept a brave chin."
    if proud >= THRESHOLD:
        return f"{actor.id} stood taller, proud of the careful choice."
    return f"{actor.id} stayed alert, like a gull spotting crumbs."


def _evaluate_clue(world: World, hero: Entity, clue: Thing, challenge: Challenge) -> bool:
    hero.memes["thinking"] = hero.memes.get("thinking", 0.0) + 1
    if clue.is_clue:
        hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
        world.say(f"{hero.id} squinted at the clue and said, \"Aha! This little thing points true.\"")
        return True
    hero.memes["confidence"] = max(0.0, hero.memes.get("confidence", 0.0) - 1)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.id} studied it and grinned, but the clue turned out to be a dud.")
    return False


def _do_wrong_action(world: World, hero: Entity, item: Thing, challenge: Challenge) -> None:
    world.say(f"{hero.id} tried to {challenge.wrong_verb}, and the {item.label} gave a silly squeak.")
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say("A tiny puff of dust popped up like a surprised ghost, and the crew snorted laughing.")


def _solve(world: World, hero: Entity, clue: Thing, challenge: Challenge) -> None:
    world.say(f"{hero.id} followed the {challenge.clue_key.replace('_', ' ')} clue.")
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    hero.memes["worry"] = 0.0
    world.say(f"At last, {challenge.result} opened with a cheerful click, and the snack chest was found.")


def tell(setting: Setting, challenge: Challenge, hero_name: str, role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=role))
    clue = _correct_clue(challenge)
    wrong = _wrong_choice_item(challenge)

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.0
    world.facts["hero"] = hero
    world.facts["challenge"] = challenge
    world.facts["clue"] = clue
    world.facts["wrong"] = wrong

    world.say(f"On {setting.place}, {hero.id} was a {_hero_label(role)} with a sharp eye for trouble.")
    world.say(f"{_describe_setting(setting)}")
    world.say(f"One day, the crew needed to {challenge.verb}, and only a small clue could help.")

    world.para()
    world.say(f"They found a {clue.phrase} near the ropes.")
    if not _evaluate_clue(world, hero, clue, challenge):
        _do_wrong_action(world, hero, wrong, challenge)

    world.para()
    world.say(f"{hero.id} took a breath and decided to evaluate the clue more carefully.")
    _evaluate_clue(world, hero, clue, challenge)
    _solve(world, hero, clue, challenge)
    world.say(f"{hero.id} laughed and said, \"Next time, I check the clue before I chase the squeak!\"")
    world.say(f"That was the lesson learned: a little thinking can save a lot of splashing.")

    world.facts["solved"] = True
    world.facts["humor"] = hero.memes.get("humor", 0.0) >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Q&A and prose helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    chal = f["challenge"]
    clue = f["clue"]
    return [
        f'Write a short pirate tale for a young child about a {hero.type} who must use a clue and evaluate it carefully.',
        f"Tell a funny story where {hero.id} tries to {chal.verb} by following {clue.label}, then learns a lesson about careful thinking.",
        f'Write a tiny pirate adventure that includes the words "thing-dim", "clue", and "evaluate".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    chal = f["challenge"]
    clue = f["clue"]
    wrong = f["wrong"]
    return [
        QAItem(
            question=f"What did {hero.id} need to do in the story?",
            answer=f"{hero.id} needed to {chal.verb}, so they had to look closely at a clue instead of guessing.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the problem?",
            answer=f"The helpful clue was {clue.phrase}, and it pointed toward {chal.result}.",
        ),
        QAItem(
            question=f"What went wrong before {hero.id} got it right?",
            answer=f"{hero.id} first chased {wrong.phrase}, which made a funny mess before they stopped and evaluated the clue properly.",
        ),
        QAItem(
            question="What lesson did the pirate learn?",
            answer="The pirate learned that careful thinking and checking clues can solve problems better than rushing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign or hint that helps someone figure out what to do or where to look.",
        ),
        QAItem(
            question="What does it mean to evaluate something?",
            answer="To evaluate something means to look at it carefully and decide what it means or whether it is useful.",
        ),
        QAItem(
            question="What is a thing-dim clue?",
            answer="A thing-dim clue is a tiny clue that points to the right thing, even when other things are tempting or noisy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    out.append(f"  fired={sorted(world.fired)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
thing(clue).
thing(decoy).
choice(clue) :- clue_item(clue).
choice(decoy) :- decoy_item(decoy).

good_choice(X) :- choice(X), clue_item(X).
bad_choice(X) :- choice(X), decoy_item(X).

solved :- good_choice(X).
humor :- bad_choice(X).
lesson :- solved.

#show good_choice/1.
#show bad_choice/1.
#show solved/0.
#show humor/0.
#show lesson/0.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("clue_item", ch.clue_key))
        wrong = "barrel" if cid == "find_snack" else "crate"
        lines.append(asp.fact("decoy_item", wrong))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show good_choice/1. #show bad_choice/1. #show solved/0. #show humor/0. #show lesson/0."))
    atoms = {(s.name, tuple(a.name if a.type != a.Type.Number else a.number for a in s.arguments)) for s in model}
    expected = {("solved", ()), ("lesson", ())}
    if atoms & {("good_choice", ("banana_peel",)), ("good_choice", ("red_thread",))}:
        expected.add(("solved", ()))
    if atoms & {("bad_choice", ("barrel",)), ("bad_choice", ("crate",))}:
        expected.add(("humor", ()))
    if ("solved", ()) in atoms and ("lesson", ()) in atoms:
        print("OK: ASP gate produced the expected lesson structure.")
        return 0
    print("MISMATCH: ASP did not produce the expected structure.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale about clues, evaluation, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=CREW_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    role = args.role or rng.choice(CREW_TYPES)
    name = args.name or rng.choice(PIRATE_NAMES)
    return StoryParams(setting=setting, challenge=challenge, hero=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge], params.hero, params.role)
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


CURATED = [
    StoryParams(setting="deck", challenge="find_snack", hero="Mara", role="captain"),
    StoryParams(setting="cabin", challenge="find_flag", hero="Ned", role="mate"),
    StoryParams(setting="beach", challenge="find_snack", hero="Bree", role="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_choice/1. #show bad_choice/1. #show solved/0. #show humor/0. #show lesson/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show good_choice/1. #show bad_choice/1. #show solved/0. #show humor/0. #show lesson/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

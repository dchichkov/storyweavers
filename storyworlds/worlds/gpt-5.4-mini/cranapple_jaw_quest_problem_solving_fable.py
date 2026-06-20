#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cranapple_jaw_quest_problem_solving_fable.py
=============================================================================

A small fable-like storyworld about a child creature on a quest for a rare
cranapple, while a sore jaw creates a practical problem that must be solved with
care, patience, and help.

The world is built from a tiny simulation:
- characters have meters and memes
- a quest can be blocked by a jaw problem
- problem solving can resolve the obstacle
- the ending proves what changed in the world state

The seed words "cranapple" and "jaw" are preserved in the domain.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hurt": 0.0, "tired": 0.0, "done": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "rabbit"}
        male = {"boy", "father", "dad", "man", "buck", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    obstacles: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    goal: str
    token: str
    path: str
    reward: str
    danger: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    source: str
    fix: str
    help_from: str
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


PLACES = {
    "orchard": Place("orchard", "the orchard", dark=False, obstacles=["roots"]),
    "hill": Place("hill", "the hill path", dark=True, obstacles=["rocks"]),
    "pond": Place("pond", "the pond bank", dark=False, obstacles=["mud"]),
}

QUESTS = {
    "cranapple": Quest(
        "cranapple",
        goal="find the cranapple",
        token="cranapple",
        path="the mossy path",
        reward="a bright cranapple for the winter shelf",
        danger="a thorny bramble",
        tags={"cranapple", "fruit"},
    ),
    "lost_key": Quest(
        "lost_key",
        goal="find the lost key",
        token="key",
        path="the narrow path",
        reward="the little brass key",
        danger="a deep crack",
        tags={"key"},
    ),
}

PROBLEMS = {
    "jaw": Problem(
        "jaw",
        label="a sore jaw",
        source="a bumped jaw",
        fix="soft berries and a warm cloth",
        help_from="a calm friend",
        sense=3,
        tags={"jaw", "care"},
    ),
    "sprain": Problem(
        "sprain",
        label="a sore foot",
        source="a twisted foot",
        fix="rest and a walking stick",
        help_from="a kind helper",
        sense=2,
        tags={"foot", "care"},
    ),
}

NAMES = ["Milo", "Tess", "Robin", "Pip", "Luna", "Bram"]
KINDS = [("fox", "fox"), ("rabbit", "rabbit"), ("child", "child")]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for quest in QUESTS.values():
            for prob in PROBLEMS.values():
                if quest.id == "cranapple" and prob.id == "jaw":
                    out.append((place.id, quest.id, prob.id))
                if quest.id == "lost_key" and prob.id == "sprain":
                    out.append((place.id, quest.id, prob.id))
    return out


@dataclass
@dataclass
class StoryParams:
    place: str
    quest: str
    problem: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like quest storyworld with a cranapple and a jaw problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=[k for k, _ in KINDS])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=[k for k, _ in KINDS])
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
    combos = valid_combos()
    if args.quest and args.problem:
        if (args.place or "orchard", args.quest, args.problem) not in [(p, q, r) for p, q, r in combos]:
            raise StoryError("That quest and problem do not fit this fable world.")
    valid = [c for c in combos if (args.place is None or c[0] == args.place)
             and (args.quest is None or c[1] == args.quest)
             and (args.problem is None or c[2] == args.problem)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, problem = rng.choice(valid)
    hero_type = args.hero_type or rng.choice([k for k, _ in KINDS])
    helper_type = args.helper_type or rng.choice([k for k, _ in KINDS])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place, quest, problem, hero, hero_type, helper, helper_type)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_type, role="quester"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_type, role="helper"))
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    problem = PROBLEMS[params.problem]
    world.facts.update(place=place, quest=quest, problem=problem, hero=hero, helper=helper)

    hero.memes["hope"] += 1
    world.say(
        f"Once there was {hero.id}, a small {hero.type} with a brave heart, and {helper.id}, "
        f"who liked to think before acting. They lived near {place.label}."
    )
    world.say(
        f"One morning, {hero.id} set out on a quest to {quest.goal}. The story of the "
        f"quest was old, but the need was fresh."
    )
    world.para()
    hero.meters["tired"] += 1
    if problem.id == "jaw":
        hero.meters["hurt"] += 1
        hero.memes["worry"] += 1
        world.say(
            f"But {hero.id} had {problem.label}, and every bite of trail bread made {hero.pronoun('possessive')} jaw ache."
        )
        world.say(
            f"{helper.id} saw the trouble and did not laugh. {helper.id} said that a careful quest could still be won."
        )
        world.say(
            f"So they rested under a tree, used {problem.fix}, and kept the talking small until the pain grew quiet."
        )
    else:
        hero.meters["tired"] += 1
        world.say(
            f"But {hero.id} had {problem.label}, so walking the narrow ground was hard."
        )
        world.say(
            f"{helper.id} found a walking stick and chose the safest stones."
        )
    world.para()
    hero.meters["done"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"At last they reached {place.label} and found {quest.token}. {hero.id} lifted the "
        f"prize with a grin, and {helper.id} smiled because the wiser way had worked."
    )
    world.say(
        f"The little fable ended with {hero.id} carrying {quest.reward}, while {problem.label} "
        f"was only a memory and not a rule."
    )
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short fable about a quest and a problem that gets solved with care.",
        f"Tell a child-friendly story that includes the word '{f['quest'].token}' and the word 'jaw'.",
        f"Write a gentle quest story where {f['hero'].id} solves a problem by thinking first and asking for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.id} going on a quest to find {quest.token}. {helper.id} helped by using a calm, careful plan.",
        ),
        QAItem(
            question="What problem did the hero have?",
            answer=f"{hero.id} had {problem.label}, so even simple trail food made {hero.pronoun('possessive')} jaw hurt. That was why the quest needed a slower, gentler plan.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They rested, used {problem.fix}, and kept going in a careful way. That worked because the helper paid attention to the pain instead of rushing.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They reached {place.label}, found {quest.token}, and the quest was finished safely. The ending shows that thinking first can make a hard path possible.",
        ),
    ]


KNOWLEDGE = [
    QAItem("What is a cranapple?", "A cranapple is a made-up fruit name for a bright, special apple-like prize in this fable world."),
    QAItem("What is a jaw?", "A jaw is the part of your face that helps you bite and chew food."),
    QAItem("Why can a sore jaw make eating hard?", "If your jaw hurts, opening your mouth and chewing can feel painful, so you may need soft food and rest."),
    QAItem("What does a helper do in a fable?", "A helper gives advice, solves problems, and makes the quest safer or wiser."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orchard", "cranapple", "jaw", "Milo", "fox", "Tess", "rabbit"),
    StoryParams("hill", "cranapple", "jaw", "Pip", "child", "Luna", "fox"),
]


ASP_RULES = r"""
valid(P,Q,R) :- place(P), quest(Q), problem(R), cranapple_quest(Q), jaw_problem(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    lines.append(asp.fact("cranapple_quest", "cranapple"))
    lines.append(asp.fact("jaw_problem", "jaw"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python validity differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def explain_rejection() -> str:
    return "(No story: that combination does not fit the fable world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

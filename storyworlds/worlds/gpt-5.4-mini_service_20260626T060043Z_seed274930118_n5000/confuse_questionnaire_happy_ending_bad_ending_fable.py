#!/usr/bin/env python3
"""
storyworlds/worlds/confuse_questionnaire_happy_ending_bad_ending_fable.py
=========================================================================

A small fable-like storyworld about a confused animal, a questionnaire, and
two possible endings: a happy ending when the questions are answered honestly,
or a bad ending when confusion and pride win instead.

The story is a classical simulation with physical meters and emotional memes.
A child-friendly moral emerges from the state changes rather than from a fixed
paragraph template.
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
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "fox", "hare", "deer", "mouse", "turtle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraph: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    creature: str
    setting: str
    question1: str
    question2: str
    answer_style: str
    ending: str
    seed: Optional[int] = None


CREATURES = {
    "fox": {
        "label": "fox",
        "name": "Fenn",
        "traits": ["clever", "proud"],
    },
    "rabbit": {
        "label": "rabbit",
        "name": "Mira",
        "traits": ["quick", "restless"],
    },
    "turtle": {
        "label": "turtle",
        "name": "Timo",
        "traits": ["slow", "careful"],
    },
}

SETTINGS = {
    "meadow": "a sunlit meadow",
    "forest": "a quiet forest",
    "pond": "a small pond",
}

QUESTION_BANK = [
    ("Where did you hide the seed?", "under the old root"),
    ("Who broke the basket?", "the basket tipped by accident"),
    ("Why is the path muddy?", "because it rained last night"),
    ("What made the bell ring?", "the wind touched it"),
    ("Who saw the lantern first?", "the owl saw it first"),
]

ANSWER_STYLES = {
    "honest": "answered honestly",
    "twisty": "answered in a twisty way",
}

ENDINGS = {"happy", "bad"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The questionnaire can be answered in two ways.
good_answer(A) :- answer_style(A, honest).
bad_answer(A) :- answer_style(A, twisty).

% A happy ending happens when the creature answers honestly and the doubt fades.
happy_ending(C) :- creature(C), good_answer(C).

% A bad ending happens when the creature refuses the questions and confusion grows.
bad_ending(C) :- creature(C), bad_answer(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for style in ANSWER_STYLES:
        lines.append(asp.fact("answer_style", style))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1.\n#show bad_ending/1."))
    asp_happy = set(asp.atoms(model, "happy_ending"))
    asp_bad = set(asp.atoms(model, "bad_ending"))
    py_happy = {(c,) for c, s in ((p.creature, p.answer_style) for p in CURATED) if s == "honest"}
    py_bad = {(c,) for c, s in ((p.creature, p.answer_style) for p in CURATED) if s == "twisty"}
    if asp_happy or asp_bad:
        print("OK: ASP rules ground and produce answers.")
        return 0
    print("MISMATCH: ASP produced no shown atoms.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    creature = args.creature or rng.choice(sorted(CREATURES))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    if args.ending and args.ending not in ENDINGS:
        raise StoryError("ending must be happy or bad")
    ending = args.ending or rng.choice(sorted(ENDINGS))
    answer_style = args.answer_style or ("honest" if ending == "happy" else "twisty")
    if answer_style == "honest" and ending == "bad":
        raise StoryError("a bad ending needs a twisty answer style")
    if answer_style == "twisty" and ending == "happy":
        raise StoryError("a happy ending needs an honest answer style")
    q1, a1 = rng.choice(QUESTION_BANK)
    q2, a2 = rng.choice([qa for qa in QUESTION_BANK if qa[0] != q1])
    return StoryParams(
        creature=creature,
        setting=setting,
        question1=q1,
        question2=q2,
        answer_style=answer_style,
        ending=ending,
    )


def generate(params: StoryParams) -> StorySample:
    world = World()
    cre = CREATURES[params.creature]
    hero = world.add(Entity(
        id=cre["name"],
        kind="character",
        type=params.creature,
        label=cre["name"],
        phrase=f"a {cre['traits'][0]} {params.creature}",
        meters={"doubt": 0.0, "mess": 0.0},
        memes={"confusion": 0.0, "hope": 0.0, "pride": 0.0, "kindness": 0.0},
    ))
    elder = world.add(Entity(
        id="OldBee",
        kind="character",
        type="bee",
        label="Old Bee",
        phrase="the old bee",
    ))
    questionnaire = world.add(Entity(
        id="questionnaire",
        kind="thing",
        type="questionnaire",
        label="questionnaire",
        phrase="a neat questionnaire with two clear questions",
    ))

    # Beginning
    world.say(
        f"In {SETTINGS[params.setting]}, there lived {hero.phrase} named {hero.label}."
    )
    world.say(
        f"{hero.label} found {questionnaire.phrase} beside a stump and began to wonder what it was for."
    )
    world.say(
        f"Old Bee said, \"A questionnaire is a little path of questions. It can help a confused heart become clear.\""
    )

    # Middle turn
    world.para()
    hero.memes["confusion"] += 1
    hero.meters["doubt"] += 1
    world.say(f"{hero.label} grew confused and looked at the first question: \"{params.question1}?\"")
    world.say(f"Then came the second: \"{params.question2}?\"")
    if params.answer_style == "honest":
        hero.memes["kindness"] += 1
        hero.memes["hope"] += 1
        hero.meters["doubt"] = max(0.0, hero.meters["doubt"] - 1)
        world.say(
            f"{hero.label} took a slow breath and answered honestly. "
            f"The words were simple, and they did not try to hide anything."
        )
    else:
        hero.memes["pride"] += 1
        hero.memes["confusion"] += 1
        hero.meters["doubt"] += 1
        world.say(
            f"{hero.label} answered in a twisty way, hoping the questions would go away."
        )
        world.say(
            f"But twisty words made the little path of questions feel longer, not shorter."
        )

    # Ending
    world.para()
    if params.ending == "happy":
        hero.memes["confusion"] = 0.0
        hero.meters["mess"] = 0.0
        world.say(
            f"Old Bee smiled. \"That is how a questionnaire works best,\" said the bee."
        )
        world.say(
            f"{hero.label}'s confusion melted away. By the end, {hero.label} was calm, "
            f"and the meadow looked bright around the tidy questionnaire."
        )
        moral = "An honest answer can turn confusion into peace."
    else:
        hero.meters["mess"] += 1
        world.say(
            f"Old Bee sighed softly. The questionnaire stayed unanswered in the grass."
        )
        world.say(
            f"{hero.label} walked away with more confusion than before, and the meadow felt smaller."
        )
        moral = "Twisty answers can make confusion grow."
    world.facts.update(
        hero=hero,
        elder=elder,
        questionnaire=questionnaire,
        setting=params.setting,
        ending=params.ending,
        answer_style=params.answer_style,
        moral=moral,
    )

    prompts = [
        f"Write a short fable about a confused {params.creature} and a questionnaire in {SETTINGS[params.setting]}.",
        f"Tell a gentle story where a {params.creature} learns what to do when a questionnaire asks two hard questions.",
        f"Write a child-friendly fable with a happy ending or a bad ending depending on whether the answers are honest.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {hero.label} find in {SETTINGS[params.setting]}?",
            answer=f"{hero.label} found a questionnaire with two questions.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel confused?",
            answer="The questions were not easy, and the little creature did not know how to answer at first.",
        ),
        QAItem(
            question=f"How did {hero.label} answer the questionnaire?",
            answer=(
                "Honestly, with simple clear words." if params.answer_style == "honest"
                else "In a twisty way, hoping to avoid the hard truth."
            ),
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer=(
                "It had a happy ending, because the honest answer brought calm."
                if params.ending == "happy"
                else "It had a bad ending, because the twisty answer made the confusion grow."
            ),
        ),
        QAItem(
            question="What is the moral of the story?",
            answer=moral,
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a questionnaire?",
            answer="A questionnaire is a list of questions that helps you learn something or collect answers.",
        ),
        QAItem(
            question="What does it mean to answer honestly?",
            answer="It means to tell the truth in clear words instead of hiding or changing the facts.",
        ),
        QAItem(
            question="What does confusion feel like?",
            answer="Confusion feels like not knowing what is true or what to do next.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story q&a ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world q&a ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about confusion and a questionnaire.")
    ap.add_argument("--creature", choices=sorted(CREATURES))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--answer-style", choices=sorted(ANSWER_STYLES))
    ap.add_argument("--ending", choices=sorted(ENDINGS))
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


CURATED = [
    StoryParams("fox", "forest", "Where did you hide the seed?", "Who broke the basket?", "honest", "happy"),
    StoryParams("rabbit", "meadow", "Why is the path muddy?", "What made the bell ring?", "twisty", "bad"),
    StoryParams("turtle", "pond", "Who saw the lantern first?", "Where did you hide the seed?", "honest", "happy"),
]


def asp_valids() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1.\n#show bad_ending/1."))
    out = []
    out.extend(asp.atoms(model, "happy_ending"))
    out.extend(asp.atoms(model, "bad_ending"))
    return sorted(set(out))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show happy_ending/1.\n#show bad_ending/1."))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

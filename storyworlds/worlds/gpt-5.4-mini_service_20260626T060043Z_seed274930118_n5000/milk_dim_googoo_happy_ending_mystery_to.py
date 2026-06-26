#!/usr/bin/env python3
"""
A folk-tale style story world about a dim little milk-carton village, a mystery
to solve, and a choice between a happy ending and a bad ending.
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

try:
    from typing import Literal
except ImportError:  # pragma: no cover
    Literal = str  # type: ignore


@dataclass
class Place:
    id: str
    name: str
    light: str
    sounds: str
    mood: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Character:
    id: str
    kind: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Clue:
    id: str
    thing: str
    hides: str
    reveals: str


@dataclass
class Mystery:
    id: str
    question: str
    answer: str
    solved_by: str
    risk_if_wrong: str


@dataclass
class StoryParams:
    ending: str
    place: str
    hero: str
    sidekick: str
    mystery: str
    seed: Optional[int] = None


PLACES = {
    "milk-dim": Place(
        id="milk-dim",
        name="the milk-dim lane",
        light="soft and pale as spilled cream",
        sounds="the hush of pails and the tiny clink of spoons",
        mood="quiet",
    ),
    "googoo": Place(
        id="googoo",
        name="the googoo grove",
        light="green-shadowed and dappled",
        sounds="the whisper of leaves and the burble of a brook",
        mood="watchful",
    ),
}

HEROES = {
    "pippa": Character(id="pippa", kind="child", name="Pippa", role="a brave little girl"),
    "tom": Character(id="tom", kind="child", name="Tom", role="a curious little boy"),
    "milo": Character(id="milo", kind="child", name="Milo", role="a kind little child"),
}

SIDEKICKS = {
    "old-mouse": Character(id="old-mouse", kind="helper", name="Old Mouse", role="a careful mouse"),
    "owl": Character(id="owl", kind="helper", name="Owl", role="a wise owl"),
    "goat": Character(id="goat", kind="helper", name="Goat", role="a steady goat"),
}

MYSTERIES = {
    "missing-moonmilk": Mystery(
        id="missing-moonmilk",
        question="Who took the moonmilk from the silver pail?",
        answer="a thirsty little fox had only tipped it into the roots for the flowers",
        solved_by="following the milky drops",
        risk_if_wrong="the village would blame the wrong friend and grow cross",
    ),
    "dim-lantern": Mystery(
        id="dim-lantern",
        question="Why did the lamp on the lane grow dim at dusk?",
        answer="a moth had rested over the flame, and the lantern needed a new wick",
        solved_by="peeking inside the lantern glass",
        risk_if_wrong="the children would wander in the dark and feel afraid",
    ),
    "sleepy-stream": Mystery(
        id="sleepy-stream",
        question="Why did the stream stop singing under the reeds?",
        answer="a round stone had lodged in the bend and softened the water's song",
        solved_by="lifting the stone from the bend",
        risk_if_wrong="the fish would lose their bright path and the brook would fret",
    ),
}

CURATED_ENDINGS = ["happy-ending", "bad-ending"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about milk-dim and googoo.")
    ap.add_argument("--ending", choices=["happy-ending", "bad-ending", "mystery-to-solve"])
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def _reasonableness_gate(params: StoryParams) -> None:
    if params.ending not in {"happy-ending", "bad-ending", "mystery-to-solve"}:
        raise StoryError("The ending must be one of the listed tale endings.")
    if params.place not in PLACES or params.hero not in HEROES or params.sidekick not in SIDEKICKS or params.mystery not in MYSTERIES:
        raise StoryError("The chosen characters and place must exist in this world.")
    if params.hero == params.sidekick:
        raise StoryError("The hero and sidekick must be different folk.")
    if params.ending == "mystery-to-solve" and params.mystery == "missing-moonmilk" and params.place == "googoo":
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    endings = ["happy-ending", "bad-ending", "mystery-to-solve"]
    place = args.place or rng.choice(list(PLACES))
    hero = args.hero or rng.choice(list(HEROES))
    sidekick = args.sidekick or rng.choice(list(SIDEKICKS))
    if sidekick == hero:
        sidekick = rng.choice([k for k in SIDEKICKS if k != hero])
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    ending = args.ending or rng.choice(endings)
    params = StoryParams(ending=ending, place=place, hero=hero, sidekick=sidekick, mystery=mystery)
    _reasonableness_gate(params)
    return params


@dataclass
class World:
    place: Place
    hero: Character
    sidekick: Character
    mystery: Mystery
    ending: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    hero = HEROES[params.hero]
    sidekick = SIDEKICKS[params.sidekick]
    mystery = MYSTERIES[params.mystery]
    world = World(place=place, hero=hero, sidekick=sidekick, mystery=mystery, ending=params.ending)

    hero.memes["curious"] = 1
    sidekick.memes["wise"] = 1
    place.meters["quiet"] = 1

    world.say(
        f"Once, in {place.name}, where the air was {place.light} and the folk listened to {place.sounds}, "
        f"there lived {hero.role} named {hero.name}."
    )
    world.say(
        f"{hero.name} walked with {sidekick.name}, {sidekick.role}, because the lane had a mystery to solve: "
        f"{mystery.question}"
    )

    world.para()
    world.say(
        f"They searched by the hedges and the well, and the only answer they found was a trail "
        f"that led them {mystery.solved_by}."
    )
    hero.meters["hope"] = 1
    world.facts["question"] = mystery.question
    world.facts["answer"] = mystery.answer
    world.facts["place"] = place.name

    if params.ending == "bad-ending":
        hero.memes["fear"] = 1
        world.say(
            f"But the child guessed in haste and pointed the wrong finger, and the little village grew heavy-hearted; "
            f"{mystery.risk_if_wrong}."
        )
        world.say(
            f"So the mystery stayed dim, and {hero.name} went home with a stone in the chest and no song in the feet."
        )
        world.facts["resolved"] = False
        world.facts["ending"] = "bad"
        return world

    world.para()
    world.say(
        f"At last {sidekick.name} peered close and found the truth: {mystery.answer}."
    )
    hero.memes["joy"] = 1
    world.say(
        f"The folk laughed softly, the lane looked less dim, and {hero.name} felt as bright as a lamp lit at supper."
    )
    world.facts["resolved"] = True
    world.facts["ending"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a folk tale for small children set in {world.place.name} with the words milk-dim and googoo.",
        f"Tell a gentle mystery story where {world.hero.name} and {world.sidekick.name} solve this question: {world.mystery.question}",
        f"Write a short tale with a happy ending or a bad ending, using the phrase milk-dim and the place {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {world.hero.name}, who is {world.hero.role}, and {world.sidekick.name}, who helps solve the mystery in {world.place.name}.",
        ),
        QAItem(
            question=f"What mystery did they try to solve?",
            answer=f"They tried to solve this mystery: {world.mystery.question}",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {world.mystery.answer}.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended happily, because the mystery was solved and {world.hero.name} went home feeling bright and glad.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended badly, because the mystery stayed unsolved and everyone went home sad and uneasy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mystery need?",
            answer="A mystery needs clues, careful looking, and a question that does not make sense right away.",
        ),
        QAItem(
            question="What does a happy ending mean?",
            answer="A happy ending means the trouble is fixed and the people feel safe, glad, or pleased at the end.",
        ),
        QAItem(
            question="What does bad ending mean?",
            answer="A bad ending means the trouble is not fixed, so the characters end in worry or sadness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"place={world.place.id} meters={world.place.meters} memes={world.place.memes}",
            f"hero={world.hero.id} meters={world.hero.meters} memes={world.hero.memes}",
            f"sidekick={world.sidekick.id} meters={world.sidekick.meters} memes={world.sidekick.memes}",
            f"mystery={world.mystery.id} solved_by={world.mystery.solved_by}",
        ]
    )


ASP_RULES = r"""
place(milk_dim).
place(googoo).

ending(happy).
ending(bad).
ending(mystery).

compatible(P, E, H, S, M) :- place(P), ending(E), hero(H), sidekick(S), mystery(M), H != S.

#show compatible/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid.replace("-", "_")))
    for e in ["happy", "bad", "mystery"]:
        lines.append(asp.fact("ending", e))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for sid in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid.replace("-", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/5."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set()
    for p in PLACES:
        for e in ["happy", "bad", "mystery"]:
            for h in HEROES:
                for s in SIDEKICKS:
                    for m in MYSTERIES:
                        if h != s:
                            py_set.add((p.replace("-", "_"), e, h, s, m.replace("-", "_")))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    if asp_set - py_set:
        print("Only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("Only in Python:", sorted(py_set - asp_set))
    return 1


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/5."))
    return sorted(set(asp.atoms(model, "compatible")))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
    StoryParams(ending="mystery-to-solve", place="milk-dim", hero="pippa", sidekick="old-mouse", mystery="missing-moonmilk"),
    StoryParams(ending="happy-ending", place="googoo", hero="tom", sidekick="owl", mystery="dim-lantern"),
    StoryParams(ending="bad-ending", place="milk-dim", hero="milo", sidekick="goat", mystery="sleepy-stream"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible tales:")
        for c in combos[:50]:
            print(c)
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

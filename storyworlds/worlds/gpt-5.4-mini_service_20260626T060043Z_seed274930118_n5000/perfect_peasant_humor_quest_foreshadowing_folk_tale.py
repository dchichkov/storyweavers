#!/usr/bin/env python3
"""
storyworlds/worlds/perfect_peasant_humor_quest_foreshadowing_folk_tale.py
========================================================================

A small folk-tale story world about a peasant, a humorous quest, and a bit of
foreshadowing that pays off at the end.

Premise:
- A peasant wants something perfect for their village or home.
- A helpful clue hints that the right object is not where it first seems.
- The quest turns into a comic little journey.
- The ending shows how the search changed the world.

The world is intentionally small and constraint-checked: the story only exists
when the quest, the place, and the object fit together in a reasonable way.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "girl", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    mischief: str
    clue: str
    payoff: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    kind: str
    perfect_for: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
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


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    title: str
    seed: Optional[int] = None


PLACES = {
    "village": Place(
        id="village",
        label="the village square",
        mood="cozy",
        affords={"find", "carry", "share"},
        clues={"well", "bell", "sign"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        mood="bright",
        affords={"find", "pick", "carry"},
        clues={"apple", "ladder", "branch"},
    ),
    "brook": Place(
        id="brook",
        label="the brook",
        mood="shiny",
        affords={"find", "carry", "cross"},
        clues={"stone", "bridge", "jar"},
    ),
    "hill": Place(
        id="hill",
        label="the windy hill",
        mood="open",
        affords={"find", "watch", "carry"},
        clues={"kite", "ring", "path"},
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        goal="find the village bell",
        verb="find",
        mischief="keeps wandering after every shiny thing",
        clue="a fox had been seen near the old well",
        payoff="the bell could call everyone home before supper",
        tags={"village", "sound", "fox"},
    ),
    "apple": Quest(
        id="apple",
        goal="pick the perfect apple",
        verb="pick",
        mischief="keeps choosing the roundest fruit and then laughing at the crooked ladder",
        clue="the smallest branch often hides the sweetest fruit",
        payoff="the pie would be sweet enough for the whole table",
        tags={"orchard", "fruit", "sweet"},
    ),
    "jar": Quest(
        id="jar",
        goal="bring home a jar of clear water",
        verb="carry",
        mischief="tips the jar whenever the path gets a little too proud of itself",
        clue="the flattest stones make the calmest steps",
        payoff="the water would stay clear for the grandmother's tea",
        tags={"water", "brook", "stone"},
    ),
    "ring": Quest(
        id="ring",
        goal="find the lost brass ring",
        verb="search for",
        mischief="looks under every bush, even the ones that obviously cannot hide a ring",
        clue="something round rolls downhill before it hides",
        payoff="the ring would be perfect for the market game",
        tags={"hill", "game", "round"},
    ),
}

PRIZES = {
    "bell": Prize(
        id="bell",
        label="bell",
        phrase="the old village bell",
        kind="object",
        perfect_for="the square",
        tags={"sound", "village"},
    ),
    "apple": Prize(
        id="apple",
        label="apple",
        phrase="the perfect red apple",
        kind="fruit",
        perfect_for="the pie",
        tags={"sweet", "orchard"},
    ),
    "jar": Prize(
        id="jar",
        label="jar",
        phrase="a clear glass jar of water",
        kind="container",
        perfect_for="tea",
        tags={"water", "brook"},
    ),
    "ring": Prize(
        id="ring",
        label="ring",
        phrase="a brass ring",
        kind="game piece",
        perfect_for="the market game",
        tags={"round", "hill"},
    ),
}

NAMES = ["Milo", "Poppy", "Tomas", "Anya", "Nell", "Bram", "Lina", "Rory"]
TITLES = ["peasant", "farmer", "village helper", "shepherd", "garden keeper"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for rid, prize in PRIZES.items():
                if qid == rid and pid in prize.tags or qid == rid:
                    out.append((pid, qid, rid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
        for c in sorted(place.clues):
            lines.append(asp.fact("clue_word", pid, c))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("verb", qid, q.verb))
        lines.append(asp.fact("mischief", qid, q.mischief))
    for rid, p in PRIZES.items():
        lines.append(asp.fact("prize", rid))
        lines.append(asp.fact("perfect_for", rid, p.perfect_for))
    return "\n".join(lines)


ASP_RULES = r"""
match(P,Q,R) :- place(P), quest(Q), prize(R), Q = R.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show match/3."))
    return sorted(set(asp.atoms(model, "match")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: perfect peasant quest with humor and foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story fits those choices.")
    place, quest, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    title = args.title or "peasant"
    return StoryParams(place=place, quest=quest, prize=prize, name=name, title=title)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    prize = PRIZES[params.prize]
    world = World(place=place)
    hero = world.add(Entity(id=params.name, kind="character", type="person", label=params.title))
    helper = world.add(Entity(id="helper", kind="character", type="person", label="the old widow"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type=prize.kind, label=prize.label, phrase=prize.phrase, owner=hero.id))

    hero.memes["hope"] = 1
    hero.memes["humor"] = 1
    world.say(f"{hero.id} was a {params.title} who wanted something perfect for the village.")
    world.say(f"Each morning, {hero.id} laughed at the same old hat and said it was too crooked for a hero of any sort.")
    world.say(f"But {helper.label} had a foreshadowing smile and said, \"When the crows point east, look near the {place.clues.pop() if place.clues else 'path'}.\"")
    world.para()
    world.say(f"So {hero.id} set out to {quest.verb} the {prize.label} at {place.label}.")
    world.say(f"{hero.id} {quest.mischief}, which was funny enough to make even the ducks stop and watch.")
    world.say(f"Still, the clue stuck in {hero.pronoun('possessive')} mind like a burr.")
    world.para()
    world.say(f"At last, {hero.id} remembered that the smallest sign can hide the truest road.")
    world.say(f"{hero.id} followed the clue, found the {prize.label}, and brought it home.")
    world.say(f"That was perfect for {prize.perfect_for}, and the whole village smiled as if a song had been mended.")
    world.say(f"And from then on, {hero.id} kept the crooked hat, because even a peasant may wear a funny thing when the work is noble.")

    world.facts.update(hero=hero, helper=helper, prize=prize_ent, quest=quest, place=place, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a short folk tale about a peasant named {params.name} who goes on a humorous quest for the word "perfect".',
            f"Tell a story with foreshadowing where {params.name} follows a small clue and finds what the village needs.",
            f"Write a gentle quest tale about a {params.title} and a lost {prize.label} in {place.label}.",
        ],
        story_qa=[
            QAItem(
                question=f"Who is the story about?",
                answer=f"The story is about {params.name}, a {params.title}, who goes on a quest in {place.label}."
            ),
            QAItem(
                question=f"What did {params.name} want to do?",
                answer=f"{params.name} wanted to {quest.verb} the {prize.label} and bring home something perfect for the village."
            ),
            QAItem(
                question="What helped guide the peasant along the way?",
                answer=f"A small foreshadowing clue from the old widow helped {params.name} know where to look."
            ),
            QAItem(
                question="How did the story end?",
                answer=f"The {prize.label} was found and taken home, and the village was happy because the result was perfect for what it needed."
            ),
        ],
        world_qa=[
            QAItem(
                question="What is a peasant?",
                answer="A peasant is a person who works the land and lives in the countryside or village."
            ),
            QAItem(
                question="What is foreshadowing?",
                answer="Foreshadowing is a small clue or hint that suggests something important will happen later."
            ),
            QAItem(
                question="Why can a quest be funny in a folk tale?",
                answer="A quest can be funny when the hero makes harmless mistakes, meets silly obstacles, or learns in a cheerful way."
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams(place="village", quest="bell", prize="bell", name="Milo", title="peasant"),
    StoryParams(place="orchard", quest="apple", prize="apple", name="Anya", title="peasant"),
    StoryParams(place="brook", quest="jar", prize="jar", name="Bram", title="peasant"),
    StoryParams(place="hill", quest="ring", prize="ring", name="Nell", title="peasant"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show match/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

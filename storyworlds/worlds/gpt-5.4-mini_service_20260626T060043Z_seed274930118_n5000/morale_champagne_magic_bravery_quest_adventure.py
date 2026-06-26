#!/usr/bin/env python3
"""
A small adventure storyworld about a quest, a little burst of magic, and a
rising sense of morale.

The premise:
- A tiny expedition starts with low morale.
- A magical object or place can lift morale.
- The hero may need bravery to complete a quest.
- A celebratory bottle of champagne appears at the end as a victory image.

This world is intentionally compact and constraint-checked:
- The quest must have a clear problem.
- Magic must plausibly change the state.
- Bravery must matter in the turning point.
- Champagne is always non-alcoholic sparkling celebration juice in this child-facing world.

The simulation drives the prose and Q&A.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0}
        if not self.memes:
            self.memes = {"morale": 0.0, "bravery": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    mood: str
    distance: int
    magic_level: int = 0
    quest_danger: int = 0


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    lift: int
    glow: str


@dataclass
class StoryWorld:
    place: Place
    hero: Entity
    companion: Entity
    quest: str
    relic: Relic
    champagne: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in [self.hero, self.companion]:
            lines.append(
                f"  {e.id:10} ({e.type:8}) "
                f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
                f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
            )
        lines.append(
            f"  place={self.place.id} mood={self.place.mood} distance={self.place.distance} "
            f"magic_level={self.place.magic_level} quest_danger={self.place.quest_danger}"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    quest: str
    relic: str
    seed: Optional[int] = None


PLACES = {
    "moon_glen": Place(
        id="moon_glen",
        label="Moon Glen",
        mood="quiet",
        distance=3,
        magic_level=2,
        quest_danger=1,
    ),
    "amber_bridge": Place(
        id="amber_bridge",
        label="Amber Bridge",
        mood="wobbly",
        distance=4,
        magic_level=1,
        quest_danger=2,
    ),
    "old_tower": Place(
        id="old_tower",
        label="the Old Tower",
        mood="echoing",
        distance=5,
        magic_level=3,
        quest_danger=3,
    ),
}

QUESTS = {
    "find_the_lantern": "find the silver lantern",
    "wake_the_garden": "wake the sleeping garden",
    "bring_back_the_song": "bring back the lost song",
}

RELICS = {
    "glowstone": Relic(
        id="glowstone",
        label="glowstone",
        phrase="a small glowstone that warmed the palm",
        lift=2,
        glow="golden",
    ),
    "star_key": Relic(
        id="star_key",
        label="star key",
        phrase="a star key that sparkled like morning",
        lift=3,
        glow="blue",
    ),
    "lantern_spark": Relic(
        id="lantern_spark",
        label="lantern spark",
        phrase="a lantern spark trapped in a glass bead",
        lift=2,
        glow="white",
    ),
}

CHAMPAGNE_LINES = [
    "a bottle of sparkling celebration champagne",
    "a cold bottle of bubbly champagne for the victory picnic",
    "a ribbon-tied bottle of champagne, made for cheering after a quest",
]

HERO_NAMES = ["Mina", "Toby", "Luna", "Rory", "Pia", "Arlo", "Sage", "Niko"]
COMPANION_NAMES = ["June", "Owen", "Iris", "Milo", "Bree", "Finn", "Ada", "Zane"]
HERO_TYPES = ["girl", "boy"]
COMPANION_TYPES = ["girl", "boy"]

TRAITS = ["curious", "gentle", "bold", "careful", "spirited", "brave"]


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------

ASP_RULES = r"""
good_combo(P, Q, R) :- place(P), quest(Q), relic(R), magic(P), danger(P,D), D < 4.
can_lift_morale(P, R) :- place(P), relic(R), lift(R, L), L >= 2.
can_finish(P, Q) :- good_combo(P, Q, R), can_lift_morale(P, R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("magic", pid))
        lines.append(asp.fact("mood", pid, place.mood))
        lines.append(asp.fact("distance", pid, place.distance))
        lines.append(asp.fact("danger", pid, place.quest_danger))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("lift", rid, relic.lift))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: Place, quest: str, relic: Relic) -> bool:
    return place.magic_level >= 1 and place.quest_danger <= 3 and relic.lift >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for qid in QUESTS:
            for rid, relic in RELICS.items():
                if valid_combo(place, qid, relic):
                    out.append((pid, qid, rid))
    return out


def explain_rejection(place: Place, quest: str, relic: Relic) -> str:
    return (
        f"(No story: {place.label} and {QUESTS[quest]} need a relic that can lift morale, "
        f"but {relic.label} would not reasonably change the quest.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> StoryWorld:
    place = PLACES[params.place]
    hero = Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["young"],
        meters={"distance": 0.0},
        memes={"morale": 1.0, "bravery": 0.0, "hope": 1.0},
    )
    companion = Entity(
        id=params.companion_name,
        kind="character",
        type=params.companion_type,
        traits=["young"],
        meters={"distance": 0.0},
        memes={"morale": 1.0, "bravery": 0.0, "hope": 1.0},
    )
    relic = RELICS[params.relic]
    return StoryWorld(
        place=place,
        hero=hero,
        companion=companion,
        quest=QUESTS[params.quest],
        relic=relic,
        champagne=random.choice(CHAMPAGNE_LINES),
    )


def tell(world: StoryWorld) -> None:
    h = world.hero
    c = world.companion
    p = world.place
    r = world.relic

    world.say(
        f"{h.id} and {c.id} reached {p.label} at the start of a long little adventure."
    )
    world.say(
        f"The air felt {p.mood}, and the quest was to {world.quest}, but both children "
        f"could feel their morale droop."
    )

    world.para()
    h.memes["bravery"] += 1
    c.memes["bravery"] += 1
    h.meters["distance"] += p.distance / 2
    c.meters["distance"] += p.distance / 2
    world.say(
        f"Then {h.id} found {r.phrase}. {r.glow.capitalize()} magic glimmered at the edge "
        f"of the path."
    )
    world.say(
        f"When {h.id} held it up, the little glow warmed {h.pronoun('possessive')} hand "
        f"and made both friends stand a little straighter."
    )

    h.memes["morale"] += r.lift
    c.memes["morale"] += r.lift
    h.memes["hope"] += 1
    c.memes["hope"] += 1

    world.para()
    world.say(
        f"Still, the quest had one hard part. A shaky turn in the trail asked for real bravery."
    )
    if p.quest_danger >= 2:
        world.say(
            f"{c.id} hesitated, but {h.id} took a breath and went first, because brave steps "
            f"can be small steps too."
        )
    else:
        world.say(
            f"{h.id} walked on carefully, showing that bravery can look gentle as well as bold."
        )

    h.memes["bravery"] += 1
    c.memes["bravery"] += 1
    h.meters["distance"] += p.distance / 2
    c.meters["distance"] += p.distance / 2

    world.para()
    world.say(
        f"At last, the quest was done: they had gone far enough, solved the problem, and brought back "
        f"the good feeling that everyone had been waiting for."
    )
    world.say(
        f"By the end, their morale rose high and bright. They shared {world.champagne}, "
        f"and the sparkling bubbles looked like tiny stars in a cup."
    )

    world.facts.update(
        place=p,
        hero=h,
        companion=c,
        relic=r,
        quest=world.quest,
        morale_end=max(h.memes["morale"], c.memes["morale"]),
        bravery_end=max(h.memes["bravery"], c.memes["bravery"]),
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        f'Write a short adventure story for a child about a quest at {world.place.label} '
        f"that begins with low morale and ends with magic and celebration.",
        f'Create a gentle quest tale using the words "magic", "bravery", "quest", and '
        f'"champagne" in a child-friendly way.',
        f"Tell an adventure story where {world.hero.id} and {world.companion.id} solve a problem, "
        f"find a magic relic, and lift morale.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    h = world.hero
    c = world.companion
    p = world.place
    r = world.relic
    return [
        QAItem(
            question=f"Where did {h.id} and {c.id} begin their adventure?",
            answer=f"They began at {p.label}, where the path felt {p.mood} and the quest was waiting.",
        ),
        QAItem(
            question=f"What helped raise their morale during the quest?",
            answer=f"{r.label} helped raise their morale. When {h.id} held it up, the magic glow warmed the moment.",
        ),
        QAItem(
            question=f"How did {h.id} show bravery?",
            answer=f"{h.id} showed bravery by taking a breath and going first when the trail turned shaky.",
        ),
        QAItem(
            question=f"What did they share at the end?",
            answer=f"They shared {world.champagne}, a sparkling celebration drink for the happy ending of the quest.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is morale?",
            answer="Morale means how hopeful and encouraged someone feels. High morale helps a team keep trying.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task someone goes on to solve a problem or find something important.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and surprising that can change what happens in a story.",
        ),
        QAItem(
            question="What is champagne in this storyworld?",
            answer="Champagne is a sparkling celebration drink used for a happy victory ending. It is child-friendly here.",
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


# ---------------------------------------------------------------------------
# Sampling and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="moon_glen",
        hero_name="Mina",
        hero_type="girl",
        companion_name="Owen",
        companion_type="boy",
        quest="find_the_lantern",
        relic="glowstone",
    ),
    StoryParams(
        place="amber_bridge",
        hero_name="Toby",
        hero_type="boy",
        companion_name="Iris",
        companion_type="girl",
        quest="wake_the_garden",
        relic="star_key",
    ),
    StoryParams(
        place="old_tower",
        hero_name="Luna",
        hero_type="girl",
        companion_name="Milo",
        companion_type="boy",
        quest="bring_back_the_song",
        relic="lantern_spark",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: morale, magic, bravery, quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and args.relic:
        if not valid_combo(PLACES[args.place], args.quest, RELICS[args.relic]):
            raise StoryError(explain_rejection(PLACES[args.place], args.quest, RELICS[args.relic]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.relic is None or c[2] == args.relic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, relic = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    companion_name = args.companion or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    hero_type = rng.choice(HERO_TYPES)
    companion_type = "boy" if hero_type == "girl" else "girl"
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        quest=quest,
        relic=relic,
        seed=args.seed,
    )


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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, quest, relic) combos:\n")
        for place, quest, relic in triples:
            print(f"  {place:12} {quest:20} {relic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

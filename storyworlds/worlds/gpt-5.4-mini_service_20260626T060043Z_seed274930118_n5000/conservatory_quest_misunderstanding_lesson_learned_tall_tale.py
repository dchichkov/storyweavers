#!/usr/bin/env python3
"""
Standalone storyworld: a tall-tale quest in a conservatory, with a
misunderstanding that turns into a lesson learned.

The seed image is a small, child-facing tall tale:
a brave child goes on a quest inside a conservatory, misunderstands a clue,
causes trouble with plants and echoes, then learns a kinder, wiser way to
solve the problem and finishes the adventure with a changed heart.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Conservatory:
    name: str = "the conservatory"
    has_glass: bool = True
    has_palms: bool = True
    has_echoes: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    wrong_guess: str
    true_meaning: str
    triumph: str
    risk: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CharacterProfile:
    name: str
    type: str
    role: str
    traits: list[str] = field(default_factory=list)
    plural: bool = False


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"shine": 0.0, "scuff": 0.0, "wet": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"wonder": 0.0})


@dataclass
class World:
    conservatory: Conservatory
    characters: dict[str, CharacterProfile] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"noise": 0.0, "broken_plan": 0.0, "repair": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"wonder": 0.0, "worry": 0.0, "confusion": 0.0, "clarity": 0.0, "gratitude": 0.0})
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


QUESTS = {
    "glass-bell": Quest(
        id="glass-bell",
        goal="find the glass bell",
        clue="the bell rings where the palms bow",
        wrong_guess="the bell is hidden inside the biggest flower",
        true_meaning="the clue points to a tiny bell hanging near the palm leaves",
        triumph="the bell is found by listening instead of grabbing",
        risk="a rushed search could knock over delicate pots",
        lesson="listening carefully is often wiser than guessing loudly",
        tags={"conservatory", "bell", "listening", "flowers"},
    ),
    "sun-map": Quest(
        id="sun-map",
        goal="follow the sun map",
        clue="where sunlight makes a silver stripe",
        wrong_guess="the stripe must be a path painted on the floor",
        true_meaning="the stripe is a beam of light showing the next arch",
        triumph="the path is found by watching the light move",
        risk="a stomp through the ferns could flatten the leaves",
        lesson="a careful eye can solve a puzzle a hurried foot cannot",
        tags={"conservatory", "sunlight", "path", "ferns"},
    ),
    "seed-key": Quest(
        id="seed-key",
        goal="bring the seed key home",
        clue="the key sleeps in a cup made by vines",
        wrong_guess="the key must be under the stone bench",
        true_meaning="the key is tucked in a hanging seed pod",
        triumph="the key is taken gently from the vine cup",
        risk="a rough hand could tear the climbing vines",
        lesson="gentle hands protect living things while solving a mystery",
        tags={"conservatory", "seed", "vines", "gentle"},
    ),
}

HEROES = [
    CharacterProfile(name="Nell", type="girl", role="quester", traits=["brave", "lively"]),
    CharacterProfile(name="Milo", type="boy", role="quester", traits=["bold", "curious"]),
    CharacterProfile(name="Pip", type="child", role="quester", traits=["tall-tale", "bright"]),
]

HELPERS = [
    CharacterProfile(name="Aunt Iris", type="woman", role="guide", traits=["patient", "kind"]),
    CharacterProfile(name="Uncle Jun", type="man", role="guide", traits=["steady", "wise"]),
]

PROPS = {
    "bell": Prop(id="bell", label="glass bell", phrase="a tiny glass bell", type="object"),
    "map": Prop(id="map", label="sun map", phrase="a map painted with sunlight", type="paper"),
    "key": Prop(id="key", label="seed key", phrase="a little seed key", type="object"),
    "lantern": Prop(id="lantern", label="lantern", phrase="a brass lantern with a warm shine", type="tool"),
}

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    quest: str
    hero: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest(quest_bell;quest_sun;quest_seed).

goal(quest_bell, bell).
goal(quest_sun, map).
goal(quest_seed, key).

clue_matches(quest_bell, listen).
clue_matches(quest_sun, watch_light).
clue_matches(quest_seed, gentle).

bad_guess(quest_bell, flower).
bad_guess(quest_sun, painted_floor).
bad_guess(quest_seed, bench).

lesson(quest_bell, listening).
lesson(quest_sun, careful_eye).
lesson(quest_seed, gentle_hands).

valid(Q) :- quest(Q), goal(Q,_), clue_matches(Q,_), bad_guess(Q,_), lesson(Q,_).
#show valid/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("goal", qid, q.goal))
        lines.append(asp.fact("clue_matches", qid, q.lesson.split()[0].replace("-", "_")))
        lines.append(asp.fact("bad_guess", qid, q.wrong_guess.split()[0].replace("-", "_")))
        lines.append(asp.fact("lesson", qid, q.lesson.split()[0].replace("-", "_")))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> set[str]:
    import asp

    model = asp.one_model(asp_program())
    return {a[0] for a in asp.atoms(model, "valid")}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    world = World(conservatory=Conservatory())
    q = QUESTS[params.quest]
    hero = next(h for h in HEROES if h.name == params.hero)
    helper = next(h for h in HELPERS if h.name == params.helper)
    world.characters["hero"] = hero
    world.characters["helper"] = helper
    world.props.update(PROPS)

    # start state
    world.memes["wonder"] = 1.0
    world.facts["quest"] = q
    world.facts["hero"] = hero
    world.facts["helper"] = helper

    world.say(
        f"{hero.name} was a {hero.traits[0]} little {hero.type} who loved tall tales "
        f"and brave errands. One bright morning, {hero.name} and {helper.name} went "
        f"into {world.conservatory.name}, where the glass shone like water and the palms "
        f"curled up toward the ceiling."
    )
    world.say(
        f"They were on a quest to {q.goal}, because a soft clue had been found: "
        f"“{q.clue}.”"
    )

    world.para()
    world.memes["confusion"] += 1.0
    world.meters["noise"] += 1.0
    world.say(
        f"But {hero.name} made a misunderstanding. {hero.name} thought the clue meant "
        f"{q.wrong_guess}, so {hero.name} hurried toward the wrong place and spoke in a "
        f"big echoing voice."
    )
    world.say(
        f"The noise bounced off the glass walls, and the fern pots trembled a little. "
        f"{q.risk.capitalize()}."
    )

    world.para()
    world.memes["worry"] += 1.0
    world.say(
        f"{helper.name} touched {hero.name}'s shoulder and smiled. “Wait now,” "
        f"{helper.name} said. “Let’s look again. A good quest needs patient eyes.”"
    )
    world.say(
        f"{hero.name} took a slow breath, listened to the little clinks and leafy whispers, "
        f"and finally understood: {q.true_meaning}."
    )
    world.memes["clarity"] += 1.0
    world.meters["repair"] += 1.0

    world.para()
    world.memes["gratitude"] += 1.0
    world.say(
        f"So {hero.name} moved gently, as careful as a kitten on a piano bench, and "
        f"{q.triumph}. "
        f"{helper.name} laughed softly, and the conservatory seemed to glow brighter "
        f"for having been treated kindly."
    )
    world.say(
        f"{hero.name} learned the lesson: {q.lesson}. By the end of the day, the quest "
        f"was done, the plants were safe, and {hero.name} walked home proud and wiser "
        f"than before."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Registries and parameter resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [(qid, hero.name, helper.name) for qid in QUESTS for hero in HEROES for helper in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale conservatory quest storyworld.")
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--hero", choices=[h.name for h in HEROES])
    ap.add_argument("--helper", choices=[h.name for h in HELPERS])
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
    quest = args.quest or rng.choice(sorted(QUESTS))
    hero = args.hero or rng.choice([h.name for h in HEROES])
    helper = args.helper or rng.choice([h.name for h in HELPERS])
    return StoryParams(quest=quest, hero=hero, helper=helper)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    q: Quest = world.facts["quest"]
    h: CharacterProfile = world.facts["hero"]
    g: CharacterProfile = world.facts["helper"]
    return [
        f"Write a tall tale about {h.name} on a quest in a conservatory with a misunderstanding and a lesson learned.",
        f"Tell a child-sized adventure where {h.name} and {g.name} solve the clue: “{q.clue}.”",
        f"Make a lively story set in a conservatory where a wrong guess turns into wisdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    h: CharacterProfile = world.facts["hero"]
    g: CharacterProfile = world.facts["helper"]
    return [
        QAItem(
            question=f"What was {h.name} trying to do in the conservatory?",
            answer=f"{h.name} was on a quest to {q.goal} with {g.name}.",
        ),
        QAItem(
            question=f"What misunderstanding did {h.name} make?",
            answer=f"{h.name} thought the clue meant {q.wrong_guess}, but it really meant {q.true_meaning}.",
        ),
        QAItem(
            question=f"What lesson did {h.name} learn at the end?",
            answer=q.lesson.capitalize() + ".",
        ),
        QAItem(
            question=f"How did {g.name} help?",
            answer=f"{g.name} told {h.name} to slow down, look again, and listen carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a conservatory?",
            answer="A conservatory is a bright room or building full of glass and plants where flowers can grow in the warm light.",
        ),
        QAItem(
            question="Why can a misunderstanding cause trouble in a quest?",
            answer="A misunderstanding can make someone choose the wrong path or the wrong clue, so they may waste time or bump into things that should be kept safe.",
        ),
        QAItem(
            question="Why is listening useful in a story like this?",
            answer="Listening helps a character notice small clues, hear a kind helper, and learn the smarter way to solve a problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"conservatory: glass={world.conservatory.has_glass} palms={world.conservatory.has_palms} echoes={world.conservatory.has_echoes}")
    for key, c in world.characters.items():
        lines.append(f"{key}: {c.name} ({c.type}) traits={c.traits}")
    lines.append(f"meters={dict(world.meters)}")
    lines.append(f"memes={dict(world.memes)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp

    py = {q for q, _, _ in valid_combos()}
    asp_set = asp_valid()
    if py == asp_set:
        print(f"OK: ASP parity matches Python gate ({len(py)} quests).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in Python:", sorted(py - asp_set))
    print("Only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(quest="glass-bell", hero="Nell", helper="Aunt Iris"),
    StoryParams(quest="sun-map", hero="Milo", helper="Uncle Jun"),
    StoryParams(quest="seed-key", hero="Pip", helper="Aunt Iris"),
]


def asp_program_text(show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program_text("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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

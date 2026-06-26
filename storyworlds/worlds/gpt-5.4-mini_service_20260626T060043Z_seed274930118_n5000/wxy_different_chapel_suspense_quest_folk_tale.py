#!/usr/bin/env python3
"""
A small folk-tale storyworld about a quest to a chapel, with suspense, a
helpful turn, and a different ending than the hero first expected.

The world is intentionally tiny:
- a traveler sets out on a quest
- a guarded chapel is the goal
- a clue named "wxy" matters to the journey
- suspense rises when the way is unclear
- the ending changes the hero's heart and the chapel's meaning
"""

from __future__ import annotations

import argparse
import dataclasses
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    reachable: bool = False
    sacred: bool = False
    clue: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    guide_name: str
    guide_type: str
    chapel_name: str
    clue_word: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    guide: Entity
    chapel: Entity
    clue: Entity
    path_blocked: bool = True
    suspense: float = 0.0
    quest_done: bool = False
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HERO_TYPES = ["girl", "boy"]
HERO_NAMES = {
    "girl": ["Mira", "Tess", "Nia", "Lena", "Rosa"],
    "boy": ["Oren", "Pax", "Finn", "Eli", "Noel"],
}
GUIDE_NAMES = ["Grandma", "Uncle", "Aunt", "Old Tom", "Sister May"]
GUIDE_TYPES = ["mother", "father", "woman", "man"]
CHAPEL_NAMES = ["the little chapel", "the hill chapel", "the chapel by the oak"]
CLUE_WORDS = ["wxy", "riddle", "thread", "stone", "song"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    hero = Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"hope": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "bravery": 0.0},
    )
    guide = Entity(
        id=params.guide_name,
        kind="character",
        type=params.guide_type,
        label=params.guide_name,
        meters={"hope": 0.0},
        memes={"calm": 1.0, "kindness": 1.0},
    )
    chapel = Entity(
        id="chapel",
        kind="place",
        type="chapel",
        label=params.chapel_name,
        phrase=params.chapel_name,
        reachable=False,
        sacred=True,
        meters={"quiet": 1.0},
        memes={"mystery": 1.0},
    )
    clue = Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=params.clue_word,
        phrase=f"a small paper marked {params.clue_word}",
        owner=params.hero_name,
        location="pocket",
        clue=True,
        meters={"weight": 0.0},
        memes={"importance": 1.0},
    )
    return World(hero=hero, guide=guide, chapel=chapel, clue=clue)


def tell(world: World) -> None:
    h, g, c, clue = world.hero, world.guide, world.chapel, world.clue

    world.say(
        f"Once, in a quiet land, {h.id} found a small paper marked {clue.label}."
    )
    world.say(
        f"It was a different kind of sign, the sort that made a child look up and wonder."
    )
    world.say(
        f"{h.id} had heard that {c.label} waited beyond the trees, and the old road was a quest road."
    )

    world.para()
    world.say(
        f"{h.id} wanted to go at once, but the path to {c.label} was blocked by a fallen gate."
    )
    world.path_blocked = True
    world.suspense += 1.0
    h.memes["worry"] += 1.0
    world.say(
        f"The wind went hush-hush through the leaves, and even the birds seemed to hold their breath."
    )
    world.say(
        f"{g.id} said the answer was not to rush, but to listen for what the little clue could mean."
    )

    world.para()
    if clue.label == "wxy":
        world.say(
            f"{h.id} held up the {clue.label} paper and saw that the letters matched marks on a stone near the gate."
        )
        world.say(
            f"Behind the stone was a simple lever, hidden by moss and shadow."
        )
    else:
        world.say(
            f"{h.id} studied the clue and noticed a mark nearby that nobody had seen before."
        )
        world.say(
            f"After a careful look, the hidden way began to make sense."
        )

    world.say(
        f"{g.id} helped {h.id} pull the lever, and the gate creaked open with a long low moan."
    )
    world.path_blocked = False
    world.suspense += 1.0
    h.memes["bravery"] += 1.0
    h.meters["hope"] += 1.0

    world.para()
    world.say(
        f"At last, {h.id} walked into {c.label}, and the quiet there felt warm instead of cold."
    )
    world.say(
        f"{c.label} was not a place of riddles after all, but a place where lost thoughts could rest."
    )
    world.say(
        f"{h.id} left the paper in the chapel book and smiled, because the quest had turned into a blessing."
    )
    h.memes["joy"] += 1.0
    world.quest_done = True

    world.facts.update(
        hero=h,
        guide=g,
        chapel=c,
        clue=clue,
        clue_word=clue.label,
        suspense=world.suspense,
        blocked_before=True,
        blocked_after=world.path_blocked,
        quest_done=world.quest_done,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child about a quest, suspense, and a chapel that includes the word "{f["clue_word"]}".',
        f"Tell a gentle suspense story where {f['hero'].id} must reach {f['chapel'].label} by following a small clue.",
        f"Write a short folk tale in which a hidden gate, a chapel, and the clue {f['clue_word']} change the end of the journey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, g, c = f["hero"], f["guide"], f["chapel"]
    qa = [
        QAItem(
            question=f"What did {h.id} want to do in the story?",
            answer=f"{h.id} wanted to go on a quest to {c.label} and find out what the clue meant.",
        ),
        QAItem(
            question=f"Why was there suspense before {h.id} reached {c.label}?",
            answer=f"There was suspense because the path was blocked, so {h.id} could not get to {c.label} right away.",
        ),
        QAItem(
            question=f"How did {g.id} help {h.id}?",
            answer=f"{g.id} helped by staying calm, telling {h.id} to listen, and helping open the hidden gate.",
        ),
        QAItem(
            question=f"What changed after the gate opened?",
            answer=f"After the gate opened, {h.id} could enter {c.label}, and the quest changed into a peaceful ending.",
        ),
    ]
    if f["clue_word"] == "wxy":
        qa.append(
            QAItem(
                question="Why was the word wxy important?",
                answer="The word wxy mattered because it matched the marks by the gate and pointed to the hidden lever.",
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a chapel?",
        answer="A chapel is a small place where people may pray or sit quietly.",
    ),
    QAItem(
        question="What does suspense mean in a story?",
        answer="Suspense is the feeling that something important may happen soon, but you do not know exactly what yet.",
    ),
    QAItem(
        question="What is a quest?",
        answer="A quest is a journey to find something, solve something, or reach an important goal.",
    ),
    QAItem(
        question="Why do clues matter?",
        answer="Clues matter because they can help someone understand where to go or what to do next.",
    ),
    QAItem(
        question="Why can a blocked path feel tense?",
        answer="A blocked path can feel tense because the hero must find another way instead of going forward right away.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
clue_is(C) :- clue(C).
blocked_path :- gate_blocked.
suspense :- blocked_path.
quest_success :- clue_is("wxy"), gate_opened, chapel_goal.
"""

def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("guide", "guide"),
            asp.fact("chapel_goal"),
            asp.fact("clue", "wxy"),
            asp.fact("gate_blocked"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_model_atoms(symbols, name: str) -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(symbols, name)))


def asp_reasonable() -> bool:
    import asp
    program = asp_program("#show quest_success/0.\n#show suspense/0.\n")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    return "suspense" in atoms


def asp_verify() -> int:
    import asp
    ok = asp_reasonable()
    if not ok:
        print("MISMATCH: ASP gate did not produce the expected suspense atom.")
        return 1
    print("OK: ASP gate is present and reasonableness holds.")
    return 0


# ---------------------------------------------------------------------------
# Parameters and parsing
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale quest to a chapel.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=GUIDE_TYPES)
    ap.add_argument("--chapel-name", choices=CHAPEL_NAMES)
    ap.add_argument("--clue-word", choices=CLUE_WORDS)
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


def valid_combo(params: StoryParams) -> bool:
    return params.clue_word in CLUE_WORDS and params.chapel_name in CHAPEL_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_type])
    guide_type = args.guide_type or rng.choice(GUIDE_TYPES)
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    chapel_name = args.chapel_name or rng.choice(CHAPEL_NAMES)
    clue_word = args.clue_word or rng.choice(CLUE_WORDS)

    params = StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        guide_name=guide_name,
        guide_type=guide_type,
        chapel_name=chapel_name,
        clue_word=clue_word,
    )
    if not valid_combo(params):
        raise StoryError("The chosen chapel and clue do not make a workable folk-tale quest.")
    return params


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


def dump_trace(world: World) -> str:
    h, g, c, clue = world.hero, world.guide, world.chapel, world.clue
    return "\n".join(
        [
            "--- world trace ---",
            f"hero: {h.id} memes={h.memes} meters={h.meters}",
            f"guide: {g.id} memes={g.memes} meters={g.meters}",
            f"chapel: {c.label} sacred={c.sacred} reachable={c.reachable}",
            f"clue: {clue.label} clue={clue.clue} location={clue.location}",
            f"blocked_before=True blocked_after={world.path_blocked}",
            f"suspense={world.suspense} quest_done={world.quest_done}",
        ]
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Mira", "girl", "Grandma", "woman", "the little chapel", "wxy"),
        StoryParams("Oren", "boy", "Old Tom", "man", "the hill chapel", "wxy"),
        StoryParams("Nia", "girl", "Aunt", "woman", "the chapel by the oak", "wxy"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_success/0.\n#show suspense/0.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_success/0.\n#show suspense/0.\n"))
        print("ASP atoms:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

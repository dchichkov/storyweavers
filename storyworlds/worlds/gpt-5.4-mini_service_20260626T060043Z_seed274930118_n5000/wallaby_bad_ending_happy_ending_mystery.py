#!/usr/bin/env python3
"""
storyworlds/worlds/wallaby_bad_ending_happy_ending_mystery.py
=============================================================

A small mystery storyworld about a wallaby, with either a bad ending or a happy
ending depending on what the little detective discovers.

The premise:
- A wallaby notices something missing or strange.
- The wallaby follows clues through a tiny, concrete setting.
- The investigation can end badly if the wrong conclusion sticks.
- Or it can end happily if the real clue is found and the missing thing returns.

This world keeps the prose child-facing and state-driven, with physical meters
and emotional memes influencing what gets narrated.
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

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"wallaby", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    details: str
    hides: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    missing: str
    clue: str
    culprit: str
    false_lead: str
    final_clue: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    ending: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bush": Setting(
        place="the bush path",
        details="The gum leaves were still, and the dusty track curled between the shrubs.",
        hides={"leaf", "shadow", "burrow"},
    ),
    "yard": Setting(
        place="the back yard",
        details="A gum tree cast a neat shadow near the fence, and a tiny gate rattled in the wind.",
        hides={"leaf", "shadow", "bucket"},
    ),
    "creek": Setting(
        place="the dry creek bed",
        details="Smooth stones sat in a line, and a little dip under a rock looked like a good hiding spot.",
        hides={"stone", "shadow", "rock"},
    ),
}

MYSTERIES = {
    "pie": Mystery(
        missing="a blueberry pie",
        clue="a blueberry smear on a flat stone",
        culprit="a hungry cockatoo",
        false_lead="a torn leaf near the fence",
        final_clue="blue crumbs caught in a twig fork",
    ),
    "key": Mystery(
        missing="a little brass key",
        clue="a bright scrape on a rock",
        culprit="a curious lizard",
        false_lead="a shiny bottle cap",
        final_clue="the key-shaped print in the dirt beside a burrow",
    ),
    "ball": Mystery(
        missing="a red ball",
        clue="a round red mark in the dust",
        culprit="a bouncing gust of wind",
        false_lead="a red flower petal",
        final_clue="the ball wedged under a fallen log",
    ),
}

ENDING_CHOICES = {"bad", "happy"}

WALLABY_NAMES = ["Willa", "Nori", "Pip", "Mira", "Juno", "Tali", "Kip", "Arlo"]
TRAITS = ["curious", "quiet", "brave", "careful", "small", "clever"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _new_emotions() -> dict[str, float]:
    return {"worry": 0.0, "hope": 0.0, "relief": 0.0, "confusion": 0.0, "pride": 0.0}


def _new_meters() -> dict[str, float]:
    return {"dusty": 0.0, "tired": 0.0, "lost": 0.0, "found": 0.0}


def _name_or_label(ent: Entity) -> str:
    return ent.label or ent.id


def build_mystery(name: str, mystery_key: str) -> tuple[Setting, Mystery]:
    return SETTINGS[name], MYSTERIES[mystery_key]


def protagonist_line(world: World, hero: Entity) -> None:
    trait = hero.memes.get("trait", "curious")
    world.say(f"{hero.id} was a little {trait} wallaby with soft ears and quick eyes.")
    world.say(f"{hero.pronoun().capitalize()} liked noticing tiny things that other animals missed.")


def setup_line(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"One morning, {hero.id} found that {mystery.missing} was gone from the little ledge."
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked at the empty spot and felt the mystery tug at {hero.pronoun('possessive')} nose."
    )


def clue_line(world: World, mystery: Mystery) -> None:
    world.say(
        f"Near the path, there was {mystery.clue}, and that gave the little wallaby a clue."
    )


def false_lead_line(world: World, mystery: Mystery) -> None:
    world.say(
        f"At first, it seemed like {mystery.false_lead} could explain everything, but it did not fit quite right."
    )


def search_line(world: World, hero: Entity) -> None:
    hero.meters["dusty"] += 1
    hero.memes["worry"] += 1
    world.say(f"{hero.id} hopped along the track and sniffed the ground very carefully.")


def suspect_line(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} wondered if {mystery.culprit} had taken it, because the clue looked strange enough."
    )


def resolve_happy(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["found"] += 1
    hero.memes["hope"] += 1
    hero.memes["relief"] += 2
    hero.memes["pride"] += 1
    world.say(
        f"Then {mystery.final_clue} made the answer plain, and {hero.id} found {mystery.missing} tucked safely away."
    )
    world.say(
        f"It was right where the little wallaby could reach it, so the mystery turned into a happy surprise."
    )
    world.say(
        f"{hero.id} carried {mystery.missing} back with a bright smile, and the morning felt light again."
    )


def resolve_bad(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["lost"] += 1
    hero.memes["worry"] += 2
    world.say(
        f"The wrong guess stayed stuck in the air, and {hero.id} never found {mystery.missing} that day."
    )
    world.say(
        f"{hero.id} sat very still while the light faded, with only the strange clue and a heavy, puzzled feeling for company."
    )


def narrate_story(world: World, hero: Entity, mystery: Mystery, ending: str) -> None:
    protagonist_line(world, hero)
    world.para()
    setup_line(world, hero, mystery)
    clue_line(world, mystery)
    search_line(world, hero)
    false_lead_line(world, mystery)
    suspect_line(world, hero, mystery)
    world.para()
    if ending == "happy":
        resolve_happy(world, hero, mystery)
    else:
        resolve_bad(world, hero, mystery)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    ending = f["ending"]
    return [
        f'Write a short mystery story for a young child about {hero.id} the wallaby in {setting.place}.',
        f"Tell a gentle detective tale where {hero.id} tries to solve why {mystery.missing} is missing.",
        f'Write a small story with a clear clue, a wrong guess, and a {ending} ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    ending = f["ending"]
    qa = [
        QAItem(
            question=f"Who is the little detective in the story?",
            answer=f"The little detective is {hero.id}, a wallaby who likes to notice clues.",
        ),
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer=f"{mystery.missing} was missing from the little ledge at {setting.place}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} look for the missing thing?",
            answer=f"The clue was {mystery.clue}, which helped {hero.id} keep searching.",
        ),
        QAItem(
            question=f"Did the story end badly or happily?",
            answer=(
                "It ended happily because the real clue won in the end."
                if ending == "happy"
                else "It ended badly because the wallaby never found the missing thing."
            ),
        ),
    ]
    if ending == "happy":
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt relieved and proud after finding {mystery.missing}.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt worried and puzzled because the mystery stayed unsolved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a wallaby?",
            answer="A wallaby is a small marsupial that hops on strong back legs and carries its baby in a pouch.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why do detectives pay attention to tiny details?",
            answer="Detectives pay attention to tiny details because little hints can lead them to the answer.",
        ),
    ]
    return out


# ---------------------------------------------------------------------------
# Reasoning / ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is solved when the final clue is seen and the missing thing is found.
solved(M) :- final_clue(M), found(M).

% A bad ending happens when there is a false lead and no solved result.
bad_ending(M) :- false_lead(M), not solved(M).

% A happy ending happens when the mystery is solved.
happy_ending(M) :- solved(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("culprit", mid, m.culprit))
        lines.append(asp.fact("false_lead", mid, m.false_lead))
        lines.append(asp.fact("final_clue", mid, m.final_clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solve(mode: str) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(f"#show {mode}/1."))
    return sorted(set(asp.atoms(model, mode)))


def asp_verify() -> int:
    import asp
    happy_py = {"happy"} if any(p.ending == "happy" for p in CURATED) else set()
    bad_py = {"bad"} if any(p.ending == "bad" for p in CURATED) else set()
    happy_asp = {a[0] for a in asp_solve("happy_ending")}
    bad_asp = {a[0] for a in asp_solve("bad_ending")}
    if bool(happy_asp) and bool(bad_asp):
        print("OK: ASP rules produce both happy and bad ending predicates.")
        return 0
    print("ASP verification failed.")
    print("happy:", happy_asp, "bad:", bad_asp, "py:", happy_py, bad_py)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny wallaby mystery world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--ending", choices=ENDING_CHOICES)
    ap.add_argument("--name", choices=WALLABY_NAMES)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    ending = args.ending or rng.choice(["happy", "bad"])
    name = args.name or rng.choice(WALLABY_NAMES)
    return StoryParams(setting=setting, mystery=mystery, ending=ending, name=name)


def generate(params: StoryParams) -> StorySample:
    setting, mystery = build_mystery(params.setting, params.mystery)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="wallaby",
        label="wallaby",
        meters=_new_meters(),
        memes=_new_emotions() | {"trait": rng_trait(params.name)},
    ))
    world.facts["hero"] = hero
    world.facts["setting"] = setting
    world.facts["mystery"] = mystery
    world.facts["ending"] = params.ending

    narrate_story(world, hero, mystery, params.ending)

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def rng_trait(name: str) -> str:
    return TRAITS[sum(ord(c) for c in name) % len(TRAITS)]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        memes = {k: v for k, v in e.memes.items() if v and k != "trait"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    facts = world.facts
    lines.append(f"  setting={facts.get('setting').place if facts.get('setting') else ''}")
    lines.append(f"  ending={facts.get('ending')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bush", mystery="key", ending="happy", name="Willa"),
    StoryParams(setting="yard", mystery="pie", ending="bad", name="Nori"),
    StoryParams(setting="creek", mystery="ball", ending="happy", name="Pip"),
]


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.mystery} in {p.setting} ({p.ending})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

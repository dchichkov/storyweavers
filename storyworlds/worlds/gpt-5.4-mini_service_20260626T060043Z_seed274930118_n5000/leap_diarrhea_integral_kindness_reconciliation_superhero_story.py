#!/usr/bin/env python3
"""
A small superhero storyworld about a child hero who can leap, faces a messy
diarrhea problem, and learns that kindness is the integral part of
reconciliation.

The world is intentionally small and constraint-driven:
- A hero wants to leap into action.
- Someone nearby has an embarrassing diarrhea accident.
- The hero first feels impatient or embarrassed.
- A kindness-based choice leads to reconciliation.
- The ending shows the repaired relationship and the changed mood.
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city"
    sky: str = "bright"
    afford_leap: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    "city": Setting(place="the city", sky="clear", afford_leap=True),
    "school": Setting(place="the school hall", sky="busy", afford_leap=True),
    "clinic": Setting(place="the clinic hallway", sky="quiet", afford_leap=False),
}

HERO_NAMES = ["Nova", "Mina", "Jett", "Rae", "Tobi", "Lumi"]
SIDEKICK_NAMES = ["Pip", "Sage", "Ari", "Zee", "Milo", "Nia"]

# ---------------------------------------------------------------------------
# Inline ASP twin and facts
# ---------------------------------------------------------------------------
ASP_RULES = r"""
leap_ready(P) :- place(P), afford_leap(P).
messy(A) :- diarrhea_event(A).
helpful(A) :- kindness(A).
fixed(A) :- reconciliation(A), helpful(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.afford_leap:
            lines.append(asp.fact("afford_leap", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("That place is not part of this storyworld.")
    if not SETTINGS[params.place].afford_leap:
        raise StoryError("This story needs a place where a hero can leap into action.")


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} superhero who loved to leap over "
        f"sidewalk cracks and lamp-post shadows. {sidekick.id} was {hero.id}'s "
        f"best sidekick, always ready with a grin and a plan."
    )
    world.say(
        f"On the wall of {world.setting.place}, someone had painted a bright sign: "
        f"'Kindness is the integral part of hero work.'"
    )


def problem(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["eager"] = 1
    sidekick.meters["diarrhea"] = 1
    sidekick.memes["embarrassed"] = 1
    world.say(
        f"One afternoon, {hero.id} wanted to leap straight to the rescue call at "
        f"{world.setting.place}. But then {sidekick.id} turned pale and rushed for "
        f"the nearest bathroom because of diarrhea."
    )
    world.say(
        f"{sidekick.id} looked down at {heroprint(hero)} and whispered, "
        f"'Please don't laugh.'"
    )


def heroprint(hero: Entity) -> str:
    return f"{hero.pronoun('possessive')} cape"


def reaction(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["impatient"] = 1
    world.say(
        f"{hero.id} froze for a second. {hero.pronoun().capitalize()} had wanted "
        f"to race ahead, but the spill and the tears made the hallway feel very small."
    )
    world.say(
        f"Then {hero.id} remembered the sign. Being a hero was not just about a leap; "
        f"it was also about kindness."
    )


def kindness_move(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["kindness"] = 1
    sidekick.memes["calmed"] = 1
    world.say(
        f"{hero.id} held out a hand, guided {sidekick.id} to the clinic sink, and "
        f"went to get clean clothes and water without making a fuss."
    )
    world.say(
        f"{hero.id} said, 'Accidents happen. I'm here.' {sidekick.id} stopped shaking "
        f"and nodded."
    )


def reconciliation(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["reconciliation"] = 1
    sidekick.memes["reconciliation"] = 1
    world.say(
        f"After that, {sidekick.id} apologized for slowing the mission, but {hero.id} "
        f"shook {hero.pronoun('possessive')} head."
    )
    world.say(
        f"'You are integral to the team,' {hero.id} said. 'We keep each other safe.' "
        f"{sidekick.id} smiled, and the two of them walked back together."
    )
    world.say(
        f"At the end, {hero.id} still leaped high, but now {hero.pronoun('possessive')} "
        f"best friend was laughing beside {hero.pronoun('object')}, cleaned up and "
        f"feeling better."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_type))
    world.facts.update(hero=hero, sidekick=sidekick, setting=world.setting)

    intro(world, hero, sidekick)
    world.para()
    problem(world, hero, sidekick)
    reaction(world, hero, sidekick)
    world.para()
    kindness_move(world, hero, sidekick)
    reconciliation(world, hero, sidekick)
    world.facts["kindness"] = True
    world.facts["reconciliation"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    return [
        f"Write a superhero story about {hero.id} learning that kindness is the integral part of a rescue.",
        f"Tell a child-friendly superhero tale where {hero.id} helps {sidekick.id} after an embarrassing diarrhea problem.",
        f"Write a short story with a leap, a messy accident, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    sidekick: Entity = world.facts["sidekick"]  # type: ignore[assignment]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little superhero, and {sidekick.id}, {hero.id}'s best sidekick.",
        ),
        QAItem(
            question=f"What problem happened before the rescue at {place}?",
            answer=f"{sidekick.id} had diarrhea and felt embarrassed, so the mission had to pause for a moment.",
        ),
        QAItem(
            question=f"What did {hero.id} learn was the integral part of being a hero?",
            answer="Kindness was the integral part of being a hero, because helping first mattered more than rushing ahead.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {sidekick.id}?",
            answer=f"They made up, so the story ended with reconciliation and the two friends walking back together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to leap?",
            answer="To leap means to jump quickly and strongly through the air.",
        ),
        QAItem(
            question="What is diarrhea?",
            answer="Diarrhea is when the body has loose, watery poop and a person may need the bathroom fast.",
        ),
        QAItem(
            question="What does integral mean?",
            answer="Integral means something is a very important part of the whole.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making up after a disagreement and becoming friendly again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        raise StoryError(f"ASP verification needs clingo/asp support: {exc}") from exc

    program = asp_program("#show leap_ready/1.\n#show messy/1.\n#show helpful/1.\n#show fixed/1.")
    model = asp.one_model(program)
    shown = sorted((sym.name, tuple(str(a) for a in sym.arguments)) for sym in model)
    expected = [("leap_ready", ("city",)), ("leap_ready", ("school",))]
    if shown != expected:
        print("ASP mismatch:")
        print("got     ", shown)
        print("expected", expected)
        return 1
    print("OK: ASP twin matches the Python gate.")
    return 0


def show_asp() -> str:
    return asp_program("#show leap_ready/1.\n#show messy/1.\n#show helpful/1.\n#show fixed/1.")


# ---------------------------------------------------------------------------
# CLI / interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about leap, diarrhea, integral, kindness, and reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["boy", "girl"])
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
    place = args.place or rng.choice(sorted(SETTINGS))
    reasonableness_gate(StoryParams(place=place, hero_name="x", hero_type="boy", sidekick_name="y", sidekick_type="girl"))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    sidekick_type = args.sidekick_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    if hero_name == sidekick_name:
        sidekick_name = rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
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
    StoryParams(place="city", hero_name="Nova", hero_type="girl", sidekick_name="Milo", sidekick_type="boy"),
    StoryParams(place="school", hero_name="Jett", hero_type="boy", sidekick_name="Nia", sidekick_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(show_asp())
        for sym in model:
            print(sym)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            params.seed = args.seed
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

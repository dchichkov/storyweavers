#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/loss_lesson_learned_dialogue_myth.py
===============================================================================================================

A small myth-like story world about a child who loses a sacred object,
hears wise dialogue, and learns a lesson by making amends.

The world is intentionally compact:
- a hero,
- an elder or spirit helper,
- a sacred object that can be lost,
- a place with a simple loss hazard,
- a turn where the hero searches, speaks, and learns.

The prose is meant to read like a short myth: clear omens, a spoken warning,
a loss, a search, and a final lesson learned.
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
    keeper: Optional[str] = None
    lost: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "elderwoman", "priestess"}
        male = {"boy", "man", "father", "elderman", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    hazard: str
    omen: str
    mood: str
    affords_loss: bool = True


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    significance: str
    loss_kind: str
    hidden_by: str


@dataclass
class StoryParams:
    setting: str
    relic: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


SETTINGS = {
    "hillshrine": Setting(
        place="the hill shrine",
        hazard="the wind",
        omen="the crows circling the stone steps",
        mood="windy and bright",
    ),
    "riverford": Setting(
        place="the river ford",
        hazard="the water",
        omen="the river singing over the rocks",
        mood="cool and shining",
    ),
    "forestgate": Setting(
        place="the old forest gate",
        hazard="the leaves",
        omen="the leaves turning in a sudden swirl",
        mood="green and hushed",
    ),
}

RELICS = {
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="a small bronze lantern",
        type="lantern",
        significance="it was said to keep a path bright in dark hours",
        loss_kind="lost in the wind",
        hidden_by="the tall grass",
    ),
    "bell": Relic(
        id="bell",
        label="bell",
        phrase="a silver bell on a cord",
        type="bell",
        significance="it was said to call friends home by its clear sound",
        loss_kind="dropped into the water",
        hidden_by="the river stones",
    ),
    "feather": Relic(
        id="feather",
        label="feather",
        phrase="a white feather wrapped in red thread",
        type="feather",
        significance="it was said to carry an oath of honesty",
        loss_kind="blown away",
        hidden_by="the fern leaves",
    ),
}

GENDERED_NAMES = {
    "girl": ["Mira", "Lina", "Asha", "Nera", "Tala"],
    "boy": ["Oren", "Kian", "Soren", "Ari", "Milo"],
}

TRAITS = ["careful", "curious", "brave", "proud", "gentle"]

GUIDES = {
    "elder": ("elder", "wise elder"),
    "priestess": ("priestess", "shrine priestess"),
    "hermit": ("hermit", "old hermit"),
}


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    relic = RELICS[params.relic]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"loss": 0.0},
        memes={"worry": 0.0, "lesson": 0.0, "hope": 0.0},
    ))
    guide_kind, guide_label = GUIDES[params.guide]
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_kind,
        label=guide_label,
        meters={"patience": 1.0},
        memes={"wisdom": 1.0},
    ))
    token = world.add(Entity(
        id="Relic",
        type=relic.type,
        label=relic.label,
        phrase=relic.phrase,
        owner=hero.id,
        keeper=guide.id,
        meters={"importance": 1.0},
        memes={"meaning": 1.0},
    ))

    # Act 1: blessing and instruction.
    world.say(
        f"In old days, {hero.id} kept {relic.phrase} as a gift of the shrine."
        f" The gift meant that {relic.significance}."
    )
    world.say(
        f"One morning at {setting.place}, the air was {setting.mood}, and {setting.omen} "
        f"made the day feel watched by unseen eyes."
    )
    world.say(
        f"{guide.label.capitalize()} said, \"Keep the {relic.label} close, for even a sacred thing can be lost if hands grow careless.\""
    )
    world.say(
        f"{hero.id} nodded and said, \"I will be careful.\""
    )

    # Act 2: loss.
    world.para()
    hero.memes["pride"] = 1.0
    world.say(
        f"But when the wind rose, {hero.id} hurried across {setting.place} with the {relic.label} in {hero.pronoun('possessive')} hand."
    )
    if setting.hazard == "the wind":
        token.lost = True
        hero.meters["loss"] += 1.0
        hero.memes["worry"] += 1.0
        world.say(
            f"A sharp gust came at once. The {relic.label} slipped free and was {relic.loss_kind}."
        )
    elif setting.hazard == "the water":
        token.lost = True
        hero.meters["loss"] += 1.0
        hero.memes["worry"] += 1.0
        world.say(
            f"The stone under {hero.pronoun('possessive')} foot was slick. The {relic.label} slipped away and was {relic.loss_kind}."
        )
    else:
        token.lost = True
        hero.meters["loss"] += 1.0
        hero.memes["worry"] += 1.0
        world.say(
            f"A swirl of leaves rushed around {hero.id}. In the blink of an eye, the {relic.label} was {relic.loss_kind}."
        )

    world.say(
        f"{hero.id} froze and whispered, \"Oh no. What have I done?\""
    )
    world.say(
        f"{guide.label.capitalize()} answered, \"A mistake is not the end. A lost thing can still be sought with an honest heart.\""
    )

    # Act 3: search and lesson.
    world.para()
    hero.memes["hope"] += 1.0
    world.say(
        f"{hero.id} looked under {relic.hidden_by}, then searched along the path, calling, \"Little {relic.label}, where are you?\""
    )
    if setting.hazard == "the wind":
        world.say(
            f"The wind answered by rattling the dry reeds, and there, caught beside {relic.hidden_by}, the {relic.label} flashed like a star."
        )
    elif setting.hazard == "the water":
        world.say(
            f"The water answered by tapping on the stones, and there, wedged near {relic.hidden_by}, the {relic.label} shone in the shallows."
        )
    else:
        world.say(
            f"The leaves answered by lifting and settling, and there, tucked beside {relic.hidden_by}, the {relic.label} waited in silence."
        )

    token.lost = False
    token.found = True
    hero.memes["lesson"] += 1.0
    hero.memes["worry"] = 0.0

    world.say(
        f"{hero.id} lifted it with both hands and said, \"I was proud and hurried. Next time I will pause first and keep what matters tied close.\""
    )
    world.say(
        f"{guide.label.capitalize()} smiled and said, \"That is the lesson learned: a careful heart guards what it loves.\""
    )
    world.say(
        f"So {hero.id} returned to {setting.place} with the {relic.label} safe again, and the day felt lighter than before."
    )

    world.facts.update(
        hero=hero,
        guide=guide,
        relic=token,
        setting=setting,
        relic_cfg=relic,
        lost=True,
        found=True,
        lesson=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic_cfg"]
    setting = f["setting"]
    return [
        f"Write a short myth for a child about {hero.id} who loses {relic.phrase} at {setting.place} and learns a lesson.",
        f"Tell a gentle myth with dialogue where {hero.id} says sorry after losing a {relic.label}.",
        f"Write a story about loss and a lesson learned, ending with {relic.label} found again at {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    relic = f["relic_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} lose at {setting.place}?",
            answer=f"{hero.id} lost {relic.phrase} at {setting.place}.",
        ),
        QAItem(
            question=f"Who told {hero.id} that a mistake is not the end?",
            answer=f"{guide.label.capitalize()} told {hero.id} that a mistake is not the end and that a lost thing can still be sought with an honest heart.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to pause first, keep what matters close, and guard precious things with care.",
        ),
        QAItem(
            question=f"How did the story end after the search?",
            answer=f"{hero.id} found the {relic.label} again and returned it safely, so the day felt lighter than before.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    relic = f["relic_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question="What is a lesson?",
            answer="A lesson is something a person learns that helps them make better choices later.",
        ),
        QAItem(
            question=f"What does it mean if something is lost?",
            answer="If something is lost, it is missing and you do not know where it is until you find it again.",
        ),
        QAItem(
            question=f"Why might a careful person keep a {relic.label} tied close?",
            answer=f"A careful person keeps a {relic.label} tied close so wind, water, or rushing feet are less likely to carry it away.",
        ),
        QAItem(
            question=f"What kind of place is {setting.place} in this story?",
            answer=f"{setting.place.capitalize()} is the place where the story happens, and it is described as {setting.mood}.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
lost(H) :- hero(H), lose_event(H).
found(H) :- hero(H), search_event(H), not lost(H).
lesson_learned(H) :- hero(H), lost(H), found(H), apology(H).

valid_story(S, R, G) :- setting(S), relic(R), guide(G), can_lose(S, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("hazard", sid, s.hazard))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("loss_kind", rid, r.loss_kind))
    for g in GUIDES:
        lines.append(asp.fact("guide", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Simple parity check: every setting/relic/guide trio is valid in this tiny world.
    combos = {(s, r, g) for s in SETTINGS for r in RELICS for g in GUIDES}
    asp_set = set(asp_valid_stories())
    python_set = combos
    if asp_set == python_set:
        print(f"OK: clingo gate matches Python registry combinations ({len(asp_set)}).")
        return 0
    print("MISMATCH between clingo and Python registry combinations:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic loss story world with dialogue and a learned lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENDERED_NAMES[gender])
    guide = args.guide or rng.choice(list(GUIDES))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, relic=relic, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(setting="hillshrine", relic="lantern", name="Mira", gender="girl", guide="elder", trait="curious"),
    StoryParams(setting="riverford", relic="bell", name="Oren", gender="boy", guide="priestess", trait="careful"),
    StoryParams(setting="forestgate", relic="feather", name="Asha", gender="girl", guide="hermit", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.relic} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

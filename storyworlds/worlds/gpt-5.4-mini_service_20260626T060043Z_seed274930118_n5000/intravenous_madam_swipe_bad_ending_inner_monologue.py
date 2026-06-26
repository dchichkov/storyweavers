#!/usr/bin/env python3
"""
storyworlds/worlds/intravenous_madam_swipe_bad_ending_inner_monologue.py
=========================================================================

A myth-flavored story world about a sacred vial, a devoted servant, and a
swift theft that leads to a bad ending.

Seed premise:
---
A young attendant carries an intravenous blessing potion to a noble madam
under an old temple's lamp. A sly hand swipes the vial. The attendant's inner
monologue swells with dread, but the stolen cure never returns, and the madam
ends the tale still waiting for relief.

World model:
---
* Physical meters model location, possession, integrity, and sickness.
* Emotional memes model devotion, dread, guilt, and alarm.
* The story is not a frozen template: the simulated state drives what is said,
  what changes, and how the ending is shaped.

The tone leans mythic and child-facing, while the ending is intentionally sad.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "madam", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "priest", "guard", "thief"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    place_note: str


@dataclass
class Rites:
    act: str
    gerund: str
    danger: str
    injury: str
    threat: str
    keyword: str = "intravenous"


@dataclass
class Relic:
    label: str
    phrase: str
    integrity: float = 1.0


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    madam_name: str
    thief_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, rites: Rites) -> None:
        self.setting = setting
        self.rites = rites
        self.entities: dict[str, Entity] = {}
        self.relic: Optional[Relic] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting, self.rites)
        clone.entities = copy.deepcopy(self.entities)
        clone.relic = copy.deepcopy(self.relic)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "temple": Setting(place="the sunlit temple court", place_note="stone pillars and a quiet basin"),
    "grove": Setting(place="the moon-grove", place_note="silver leaves and a spring-fed altar"),
    "sanctum": Setting(place="the inner sanctum", place_note="a lamp, a curtain, and old woven rugs"),
}

RITES = {
    "intravenous": Rites(
        act="deliver the intravenous blessing",
        gerund="delivering the intravenous blessing",
        danger="the vial could be stolen before the cure reached the madam",
        injury="the madam would remain weak and unhealed",
        threat="a swift swipe of the sacred vial",
        keyword="intravenous",
    ),
}

NAMES = {
    "hero": ["Ila", "Nerio", "Sela", "Tavi", "Mira", "Aren"],
    "madam": ["Madam Oline", "Madam Vesta", "Madam Liora", "Madam Seris"],
    "thief": ["Keth", "Ruin", "Spar", "Nox"],
}

TYPES = {
    "hero": ["attendant", "novice", "scribe", "messenger"],
    "madam": ["madam"],
    "thief": ["thief", "boy", "man"],
}

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_is_reasonable(params: StoryParams) -> bool:
    return params.place in SETTINGS and params.hero_name and params.madam_name and params.thief_name


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A rite exists if the setting can host the tale.
place(P) :- setting(P).

% The sacred vial is at risk when the thief is near enough to swipe.
at_risk(S) :- hero(S), thief(T), near(T,S), sacred_vial(S).

% A bad ending happens when the cure is stolen and never restored.
bad_ending(S) :- at_risk(S), stolen(vial), not returned(vial).

% The madam remains sick when the intravenous blessing never arrives.
unhealed(M) :- madam(M), needs_blessing(M), stolen(vial), not delivered(vial).
#show bad_ending/1.
#show unhealed/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    lines.append(asp.fact("rite", "intravenous"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("madam", "madam"))
    lines.append(asp.fact("thief", "thief"))
    lines.append(asp.fact("sacred_vial", "vial"))
    lines.append(asp.fact("needs_blessing", "madam"))
    lines.append(asp.fact("near", "thief", "vial"))
    lines.append(asp.fact("stolen", "vial"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    rites = RITES["intravenous"]
    world = World(setting, rites)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    madam = world.add(Entity(id=params.madam_name, kind="character", type="madam"))
    thief = world.add(Entity(id=params.thief_name, kind="character", type="thief"))

    vial = Relic(label="vial", phrase="a tiny glass vial of intravenous blessing")
    world.relic = vial

    hero.memes["devotion"] = 1.0
    hero.memes["dread"] = 0.0
    hero.memes["guilt"] = 0.0
    madam.meters["sickness"] = 1.0
    madam.meters["hope"] = 0.5
    thief.memes["hunger"] = 1.0
    thief.memes["greed"] = 1.0

    world.facts.update(hero=hero.id, madam=madam.id, thief=thief.id)
    return world


def predict_bad_ending(world: World) -> bool:
    sim = world.copy()
    return True if sim.relic and sim.relic.label == "vial" else False


def opening(world: World) -> None:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    world.say(
        f"In {world.setting.place}, beneath {world.setting.place_note}, {hero.id} knelt "
        f"with the care of a little temple star."
    )
    world.say(
        f"{hero.id} carried {world.relic.phrase} for {madam.id}, who lay pale and still "
        f"like a candle after dawn."
    )


def inner_monologue(world: World) -> None:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    world.say(
        f'Inside {hero.id}\'s mind, a small voice whispered, "Be steady. '
        f'This blessing is for {madam.id}; do not let the hand tremble."'
    )
    hero.memes["dread"] += 1.0
    world.say(
        f'Another thought followed: "If the vial slips away, {madam.id} may remain '
        f'sick, and I will have failed the altar and the day."'
    )


def threat_and_swipe(world: World) -> None:
    hero = world.get(world.facts["hero"])
    thief = world.get(world.facts["thief"])
    madam = world.get(world.facts["madam"])

    world.para()
    world.say(
        f"Then {thief.id} came like a quick shadow through the lampsmoke, and with one "
        f"swift swipe {thief.pronoun('subject')} snatched the vial from {hero.id}'s hands."
    )
    world.relic.integrity = 0.0
    hero.memes["dread"] += 1.0
    hero.memes["guilt"] += 1.0
    madam.meters["hope"] = max(0.0, madam.meters.get("hope", 0.0) - 0.5)
    world.fired.add("swipe")


def aftershock(world: World) -> None:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    thief = world.get(world.facts["thief"])
    world.say(
        f"{hero.id} reached out too late. The air was empty, and the sacred cure was gone."
    )
    world.say(
        f"{hero.id} thought, 'I should have watched closer. I should have held it with both hands.'"
    )
    world.say(
        f"{madam.id} waited in silence, still weak, while {thief.id} vanished beyond the court."
    )
    hero.memes["guilt"] += 1.0
    madam.meters["sickness"] += 1.0


def ending(world: World) -> None:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    world.para()
    world.say(
        f"So the myth closed with no healing song: the vial was stolen, the blessing never "
        f"reached {madam.id}, and {hero.id} stood beneath the temple lamp with an empty pair of hands."
    )
    world.say(
        f"{hero.id}'s heart was heavy, {madam.id}'s fever stayed, and the night remembered the bad ending."
    )


def tell(params: StoryParams) -> World:
    if not story_is_reasonable(params):
        raise StoryError("The chosen story cannot be built from this mythic domain.")

    world = build_world(params)
    opening(world)
    inner_monologue(world)
    threat_and_swipe(world)
    aftershock(world)
    ending(world)

    world.facts.update(
        place=params.place,
        bad_ending=True,
        stolen=True,
        recovered=False,
        madam_sick=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    return [
        f"Write a short myth about {hero.id} carrying an intravenous blessing for {madam.id}, and end it sadly.",
        f"Tell a child-friendly legendary story in which a {hero.type} thinks aloud while a thief swipes a sacred vial.",
        f"Write a simple myth using the word 'intravenous' and the motif of a stolen cure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero"])
    madam = world.get(world.facts["madam"])
    thief = world.get(world.facts["thief"])
    return [
        QAItem(
            question=f"Who carried the sacred vial at the beginning of the story?",
            answer=f"{hero.id} carried the tiny glass vial of intravenous blessing.",
        ),
        QAItem(
            question=f"Who was the blessing meant to help?",
            answer=f"It was meant to help {madam.id}, who was weak and waiting for relief.",
        ),
        QAItem(
            question=f"What happened when the thief came near?",
            answer=f"{thief.id} swiped the vial away in one swift motion, and the cure was lost.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the vial was stolen, the blessing never arrived, and the madam stayed sick.",
        ),
        QAItem(
            question=f"What did {hero.id} think to {hero.pronoun('subject')}self during the story?",
            answer=(
                f"{hero.id} thought to stay steady, but then feared that if the vial slipped away, "
                f"{madam.id} would remain sick."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does intravenous mean?",
            answer=(
                "Intravenous means something is given through a vein, often as a careful medicine or blessing "
                "that is carried to someone who needs help."
            ),
        ),
        QAItem(
            question="What is a madam?",
            answer="A madam is a respectful way to speak about a woman, especially one who is important or noble.",
        ),
        QAItem(
            question="What does swipe mean?",
            answer="To swipe means to move a hand quickly and take something fast, almost like a sudden snatch.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    if world.relic:
        lines.append(f"relic: {world.relic.label}, integrity={world.relic.integrity}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: intravenous, madam, swipe; bad ending, inner monologue.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name", choices=sum([NAMES["hero"]], []))
    ap.add_argument("--madam-name", choices=sum([NAMES["madam"]], []))
    ap.add_argument("--thief-name", choices=sum([NAMES["thief"]], []))
    ap.add_argument("--hero-type", choices=sorted(TYPES["hero"]))
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
    place = args.place or rng.choice(list(SETTINGS))
    hero_name = args.hero_name or rng.choice(NAMES["hero"])
    hero_type = args.hero_type or rng.choice(TYPES["hero"])
    madam_name = args.madam_name or rng.choice(NAMES["madam"])
    thief_name = args.thief_name or rng.choice(NAMES["thief"])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        madam_name=madam_name,
        thief_name=thief_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program()
    models = asp.solve(program, models=1)
    if not models:
        print("ASP verification failed: no model returned.")
        return 1
    print("OK: ASP program grounds and solves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(place=place, hero_name=NAMES["hero"][0], hero_type=TYPES["hero"][0],
                        madam_name=NAMES["madam"][0], thief_name=NAMES["thief"][0])
            for place in SETTINGS
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

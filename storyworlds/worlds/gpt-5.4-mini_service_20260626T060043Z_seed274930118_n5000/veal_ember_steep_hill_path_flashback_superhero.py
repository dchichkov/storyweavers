#!/usr/bin/env python3
"""
A standalone storyworld for a tiny superhero tale with flashback structure.

Premise:
A young superhero carries a lunch parcel of veal up a steep hill path to meet
a friend, but a glowing ember from a picnic fire threatens to ruin the meal.

The story world is modeled as a small simulation:
- physical meters track heat, tiredness, soot, and safety
- emotional memes track confidence, worry, pride, and relief
- a flashback is used to explain why the hero protects the lunch carefully

The story is intentionally compact and child-facing, with a clear turn:
the hero remembers a lesson, changes tactics, and keeps the veal safe while
helping the ember become harmless.
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
# Shared world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"heat": 0.0, "soot": 0.0, "tired": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "pride": 0.0, "relief": 0.0, "memory": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the steep hill path"
    slope: str = "steep"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    trigger: str
    heat_gain: float
    soot_gain: float
    tired_gain: float
    hero_risk: str
    item_risk: str
    flashback_key: str


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    reduces: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting(place="the steep hill path", slope="steep", affords={"carry", "remember"}),
}

CHALLENGES = {
    "ember": Challenge(
        id="ember",
        label="glowing ember",
        trigger="the ember flickered in the wind",
        heat_gain=1.0,
        soot_gain=1.0,
        tired_gain=0.5,
        hero_risk="the hero's hands would get too hot and shaky",
        item_risk="the veal could smoke and smell burnt",
        flashback_key="ember",
    ),
}

AIDS = {
    "cape_shield": Aid(
        id="cape_shield",
        label="a bright cape shield",
        covers={"hands", "chest"},
        reduces={"heat", "soot"},
        prep="wrap the lunch in a bright cape shield and carry it carefully",
        tail="kept the ember out of the lunch",
    ),
    "cool_box": Aid(
        id="cool_box",
        label="a cool lunch box",
        covers={"hands"},
        reduces={"heat"},
        prep="put the veal in a cool lunch box",
        tail="kept the veal safe",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Jett", "Rae", "Piper", "Kira"]
SIDEKICK_NAMES = ["Blink", "Comet", "Sparrow", "Bramble"]
TRAITS = ["brave", "quick", "kind", "lively", "careful"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    hero: str
    hero_kind: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A challenge is at risk on the steep hill path when the ember can heat and soot the lunch.
at_risk(C) :- challenge(C), kind_of(C, ember), place(hill), path(steep).

% Aid is reasonable when it covers the risky hands/chest and reduces the relevant effects.
works(A, C) :- aid(A), at_risk(C), covers(A, hands), reduces(A, heat).
works(A, C) :- aid(A), at_risk(C), covers(A, chest), reduces(A, soot).

valid_story(P, C, A) :- place(P), challenge(C), works(A, C).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("path", s.slope))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("kind_of", cid, "ember"))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", aid, c))
        for r in sorted(a.reduces):
            lines.append(asp.fact("reduces", aid, r))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for challenge_id, challenge in CHALLENGES.items():
            for aid, a in AIDS.items():
                if "hands" in a.covers and "heat" in a.reduces:
                    combos.append((place, challenge_id, aid))
                elif "chest" in a.covers and "soot" in a.reduces:
                    combos.append((place, challenge_id, aid))
    return sorted(set(combos))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def flashback_line(hero: Entity, challenge: Challenge) -> str:
    return (
        f"{hero.ref()} remembered an old lesson: when {challenge.label} glows, "
        f"you do not rush. You steady your hands first."
    )


def setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity]:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, traits=[params.trait]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="boy"))
    lunch = world.add(Entity(
        id="veal",
        type="meal",
        label="veal",
        phrase="a warm veal lunch",
        owner=hero.id,
        caretaker=hero.id,
    ))
    world.facts.update(hero=hero, sidekick=sidekick, lunch=lunch)
    return world, hero, sidekick, lunch


def apply_challenge(world: World, hero: Entity, lunch: Entity, challenge: Challenge) -> None:
    hero.meters["tired"] += challenge.tired_gain
    hero.memes["worry"] += 1.0
    lunch.meters["heat"] += challenge.heat_gain
    lunch.meters["soot"] += challenge.soot_gain
    if lunch.meters["heat"] >= THRESHOLD:
        world.say(f"The {challenge.label} climbed the wind and made the veal worryingly warm.")
    if lunch.meters["soot"] >= THRESHOLD:
        world.say(f"Little dark soot specks tried to land on the lunch.")
    world.say(f"It was the kind of moment that could spoil a hero's careful plan.")


def offer_aid(world: World, hero: Entity, aid: Aid, lunch: Entity) -> None:
    hero.memes["pride"] += 1.0
    lunch.meters["safe"] += 1.0
    world.say(f"{hero.ref()} chose {aid.label}, because the fix had to be as smart as the problem.")
    world.say(f"They decided to {aid.prep}, and {aid.tail}.")


def resolve(world: World, hero: Entity, sidekick: Entity, lunch: Entity, challenge: Challenge, aid: Aid) -> None:
    hero.memes["relief"] += 1.0
    hero.memes["worry"] = 0.0
    lunch.meters["heat"] = max(0.0, lunch.meters["heat"] - 1.0)
    lunch.meters["soot"] = max(0.0, lunch.meters["soot"] - 1.0)
    world.say(
        f"{hero.ref()} carried the lunch the rest of the way without letting the ember touch it."
    )
    world.say(
        f"At the top of the steep hill path, {sidekick.ref()} cheered, and the veal was still ready to eat."
    )


def tell_story(params: StoryParams) -> World:
    world, hero, sidekick, lunch = setup_world(params)
    challenge = CHALLENGES[params.challenge]
    aid = AIDS["cape_shield"]

    world.say(
        f"{hero.ref()} was a {params.trait} young superhero who liked helping on the steep hill path."
    )
    world.say(
        f"One afternoon, {hero.ref()} carried veal in a lunch bundle up {world.setting.place} to meet {sidekick.ref()}."
    )
    world.say(
        f"Near a picnic fire, {challenge.trigger}."
    )

    world.para()
    world.say(flashback_line(hero, challenge))
    world.say(
        f"So {hero.ref()} slowed down, took a breath, and remembered that a hero wins by staying careful."
    )

    world.para()
    apply_challenge(world, hero, lunch, challenge)
    offer_aid(world, hero, aid, lunch)
    resolve(world, hero, sidekick, lunch, challenge, aid)

    world.facts.update(
        challenge=challenge,
        aid=aid,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    challenge: Challenge = world.facts["challenge"]
    return [
        f"Write a short superhero story with a flashback on a {world.setting.place} where {hero.ref()} protects veal from a {challenge.label}.",
        f"Tell a child-friendly story in which a brave hero remembers a lesson and uses a clever aid to keep lunch safe on a steep hill path.",
        f"Create a small superhero tale that includes veal, ember, and a flashback about staying calm and careful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    sidekick: Entity = world.facts["sidekick"]
    lunch: Entity = world.facts["lunch"]
    challenge: Challenge = world.facts["challenge"]
    aid: Aid = world.facts["aid"]

    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.ref()}, a {hero.traits[0] if hero.traits else 'brave'} helper on the steep hill path.",
        ),
        QAItem(
            question=f"What did {hero.ref()} carry up the steep hill path?",
            answer=f"{hero.ref()} carried veal in a lunch bundle so {sidekick.ref()} could share it at the top.",
        ),
        QAItem(
            question=f"What problem did the {challenge.label} cause?",
            answer=f"The glowing ember tried to heat the veal and leave soot on it, which could have ruined the meal.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer=f"The flashback reminded {hero.ref()} to slow down and steady their hands when an ember glows near something important.",
        ),
        QAItem(
            question=f"How did {hero.ref()} keep the lunch safe?",
            answer=f"{hero.ref()} used {aid.label} and carried the veal carefully so the ember stayed away from it.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"At the end, the veal was still ready to eat, and {sidekick.ref()} cheered at the top of the hill.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ember?",
            answer="An ember is a small glowing piece of firewood or coal that can stay hot after a flame dies down.",
        ),
        QAItem(
            question="What is veal?",
            answer="Veal is meat from a young calf, and people may cook it for a meal.",
        ),
        QAItem(
            question="What does a superhero usually do?",
            answer="A superhero usually helps people, protects things that matter, and faces problems with courage.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short memory scene that shows something from earlier time to help explain the present moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a flashback on a steep hill path.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--challenge", choices=CHALLENGES.keys())
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    place = args.place or rng.choice(list(SETTINGS.keys()))
    challenge = args.challenge or "ember"
    hero_kind = args.gender or rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, hero=hero, hero_kind=hero_kind, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for name in HERO_NAMES[:3]:
            params = StoryParams(
                place="hill",
                challenge="ember",
                hero=name,
                hero_kind="girl" if name in {"Nova", "Mira", "Rae", "Kira"} else "boy",
                sidekick="Blink",
                trait="brave",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

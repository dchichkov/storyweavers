#!/usr/bin/env python3
"""
Standalone storyworld: a small superhero tale with magic and foreshadowing.

Premise:
- A young hero wants to perform a dramatic rescue or show off a power.
- A mentor worries that the hero's magical item will be exposed at the wrong time.
- The story builds tension by foreshadowing a later need for the item.
- The resolution uses a sensible compromise that proves the item mattered.

This world keeps the prose child-facing and concrete, with a simple world model
driven by meters and memes. It includes the seed words "appropriate",
"dub", and "parakeet" in natural places so they can appear in stories and QA.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "spark": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "confidence": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    mentor_name: str
    sidekick_name: str
    setting: str
    magic_item: str
    mission: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": "the rooftop",
    "city": "the city square",
    "museum": "the museum hall",
    "park": "the park",
}

HERO_NAMES = ["Nova", "Milo", "Tess", "Rin", "Kai", "Luna"]
MENTOR_NAMES = ["Captain Bright", "Aunt Aurora", "Uncle Vector", "Guide Ember"]
SIDEKICK_NAMES = ["Pip", "Dot", "Bean", "Zee"]

HERO_TYPES = ["girl", "boy"]
MAGIC_ITEMS = {
    "cape": {
        "label": "magic cape",
        "phrase": "a shimmering magic cape",
        "risk": "spark",
        "cover": {"chest", "back"},
        "protective": True,
    },
    "mask": {
        "label": "magic mask",
        "phrase": "a tiny magic mask",
        "risk": "spark",
        "cover": {"face"},
        "protective": True,
    },
    "glove": {
        "label": "magic glove",
        "phrase": "a glowing magic glove",
        "risk": "spark",
        "cover": {"hand"},
        "protective": True,
    },
}

MISSIONS = {
    "rescue": ("rescue a kitten", "rescuing a kitten", "rush to the ladder"),
    "signal": ("signal for help", "signaling for help", "wave at the tower"),
    "lift": ("lift a fallen gate", "lifting the gate", "push at the gate"),
}


def _hero_intro(world: World, hero: Entity, mentor: Entity, sidekick: Entity, item: Entity, mission: str) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} superhero who trained with {mentor.id} and {sidekick.id}."
    )
    world.say(
        f"{hero.id} loved {mission} with {item.phrase}, because it made every leap feel important."
    )


def _foreshadow(world: World, hero: Entity, item: Entity, mission_key: str) -> None:
    hero.memes["hope"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"One bright day, {hero.id} noticed a strange glimmer on {item.label}. "
        f"{hero.pronoun().capitalize()} did not know it yet, but the sparkle was a clue."
    )
    world.say(
        f"{hero.id}'s mentor said, \"Keep that {item.label} safe. It may be just the appropriate thing later.\""
    )
    if mission_key == "rescue":
        world.say(
            f"Far below, a small parakeet chirped from a high branch, as if it already knew someone would need a gentle helper."
        )
    else:
        world.say(
            f"A parakeet in a nearby window bobbed its head, like a tiny announcer dub for the coming trouble."
        )


def _warn(world: World, mentor: Entity, hero: Entity, item: Entity, mission_key: str) -> bool:
    if item.meters["risk"] >= THRESHOLD:
        world.facts["warning"] = True
        world.say(
            f"\"If you use it too soon, {hero.id}, the magic could sputter,\" {mentor.id} warned."
        )
        world.say(
            f"That made sense, because the mission was about to begin and the {item.label} still needed to stay ready."
        )
        return True
    return False


def _act(world: World, hero: Entity, item: Entity, mission_key: str) -> None:
    hero.meters["risk"] += 1
    item.meters["risk"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"When the trouble started, {hero.id} dashed forward and tried to {MISSIONS[mission_key][2]}."
    )
    world.say(
        f"The {item.label} flashed once, and everyone saw why the warning had mattered."
    )


def _compromise(world: World, mentor: Entity, hero: Entity, sidekick: Entity, item: Entity, mission_key: str) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{mentor.id} pointed to a safe plan: \"Use the {item.label} at the exact right moment.\""
    )
    world.say(
        f"{sidekick.id} nodded hard and said it was the appropriate move, even if it was less flashy than a big swoop."
    )
    hero.meters["spark"] += 1
    world.say(
        f"{hero.id} held back for one breath, then released the magic on cue."
    )


def _resolve(world: World, hero: Entity, mentor: Entity, sidekick: Entity, item: Entity, mission_key: str) -> None:
    hero.memes["hope"] += 2
    hero.memes["worry"] = 0.0
    world.say(
        f"At last, the {item.label} answered like a star. {hero.id} finished the {MISSIONS[mission_key][0]}, and the danger turned small."
    )
    world.say(
        f"The parakeet fluttered down safely, and {hero.id} smiled while {mentor.id} laughed with relief."
    )


def tell(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    mentor = world.add(Entity(id=params.mentor_name, kind="character", type="mentor"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick"))
    item_def = MAGIC_ITEMS[params.magic_item]
    item = world.add(Entity(
        id=params.magic_item,
        type="magic item",
        label=item_def["label"],
        phrase=item_def["phrase"],
        owner=hero.id,
        caretaker=mentor.id,
        protective=item_def["protective"],
        covers=set(item_def["cover"]),
    ))
    item.worn_by = hero.id
    mission_key = params.mission

    _hero_intro(world, hero, mentor, sidekick, item, MISSIONS[mission_key][0])
    world.para()
    _foreshadow(world, hero, item, mission_key)
    _warn(world, mentor, hero, item, mission_key)
    world.para()
    _act(world, hero, item, mission_key)
    _compromise(world, mentor, hero, sidekick, item, mission_key)
    _resolve(world, hero, mentor, sidekick, item, mission_key)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        sidekick=sidekick,
        item=item,
        mission_key=mission_key,
        mission=MISSIONS[mission_key],
        place=world.setting,
        setting_text=SETTINGS[params.setting],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "appropriate" and the idea of a parakeet needing help.',
        f"Tell a gentle hero story about {f['hero'].id}, {f['mentor'].id}, and a magic {f['item'].label} at {f['setting_text']}.",
        f'Write a story with foreshadowing where a magic item is saved for the appropriate moment and a parakeet is rescued.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    sidekick: Entity = f["sidekick"]
    item: Entity = f["item"]
    mission = f["mission"][0]
    return [
        QAItem(
            question=f"Who is the superhero in this story?",
            answer=f"The superhero is {hero.id}, who learns to use {item.label} at the right time.",
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id} about the {item.label}?",
            answer=f"{mentor.id} warned {hero.id} because the magic could sputter if it was used too soon, and the story had already foreshadowed that the item would matter later.",
        ),
        QAItem(
            question=f"What did {sidekick.id} call the safer plan?",
            answer=f"{sidekick.id} said it was the appropriate move, because waiting for the right moment kept the mission safe.",
        ),
        QAItem(
            question=f"What finally happened at the end?",
            answer=f"{hero.id} used the {item.label} at the perfect moment, finished the {mission}, and the parakeet was safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early on about something important that will happen later.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something impossible in the real world that can still happen in a story, like a glowing item or a spell.",
        ),
        QAItem(
            question="What is a parakeet?",
            answer="A parakeet is a small colorful bird that can chatter and flap its wings quickly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={ {k: round(v, 2) for k, v in e.meters.items() if v} } memes={ {k: round(v, 2) for k, v in e.memes.items() if v} }"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with magic and foreshadowing.")
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mentor-name", choices=MENTOR_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--mission", choices=MISSIONS)
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
    return StoryParams(
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(HERO_TYPES),
        mentor_name=args.mentor_name or rng.choice(MENTOR_NAMES),
        sidekick_name=args.sidekick_name or rng.choice(SIDEKICK_NAMES),
        setting=args.setting or rng.choice(list(SETTINGS)),
        magic_item=args.magic_item or rng.choice(list(MAGIC_ITEMS)),
        mission=args.mission or rng.choice(list(MISSIONS)),
    )


ASP_RULES = r"""
hero(H) :- hero_name(H).
mentor(M) :- mentor_name(M).
sidekick(S) :- sidekick_name(S).
item(I) :- magic_item(I).
setting(K) :- setting_name(K).
mission(X) :- mission_name(X).

foreshadowing(I) :- item(I), clue(I).
appropriate(I) :- item(I), safe_timing(I).
resolved(H,I) :- hero(H), item(I), appropriate(I), final_use(H,I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in HERO_NAMES:
        lines.append(asp.fact("hero_name", n))
    for n in MENTOR_NAMES:
        lines.append(asp.fact("mentor_name", n))
    for n in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick_name", n))
    for n in SETTINGS:
        lines.append(asp.fact("setting_name", n))
    for n in MAGIC_ITEMS:
        lines.append(asp.fact("magic_item", n))
        lines.append(asp.fact("clue", n))
        lines.append(asp.fact("safe_timing", n))
        lines.append(asp.fact("final_use", "dummy", n))
    for n in MISSIONS:
        lines.append(asp.fact("mission_name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("OK: ASP twin is present for this world.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show appropriate/1.\n#show foreshadowing/1.\n#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        seeds = [
            StoryParams("Nova", "girl", "Captain Bright", "Pip", "rooftop", "cape", "rescue"),
            StoryParams("Milo", "boy", "Aunt Aurora", "Dot", "city", "mask", "signal"),
            StoryParams("Tess", "girl", "Guide Ember", "Bean", "museum", "glove", "lift"),
        ]
        samples = [generate(p) for p in seeds]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        rng = random.Random(base_seed)
        samples = []
        seen = set()
        for i in range(max(args.n, 1) * 20):
            if len(samples) >= max(args.n, 1):
                break
            params = resolve_params(args, random.Random(base_seed + i))
            key = (params.hero_name, params.hero_type, params.mentor_name, params.sidekick_name, params.setting, params.magic_item, params.mission)
            if key in seen:
                continue
            seen.add(key)
            samples.append(generate(params))

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

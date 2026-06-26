#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hate_stranger_rape_friendship_kindness_myth.py
===============================================================================================================

A small mythic storyworld about a village, a stranger, a spreading hate-shadow,
and a friendship-kindness remedy. The seed words are carried as titles, curses,
and tale-ingredients, but the actual story stays child-facing and restorative.

The world is built as a classical simulation:
- people and places are typed entities with meters and memes
- hate can spread as a stormy feeling
- a stranger may arrive with a burden
- friendship and kindness can turn fear into welcome
- a mythic object called the Rape Reed is not a harm, but an old river-name
  for a red reed used to tint festival cloth; its presence matters because the
  stranger guards it and the village mistakes the guarded bundle for trouble

The story premise is:
a village fears a stranger carrying the Rape Reed,
their fear wakes a hate-shadow,
then a child-led act of friendship and kindness reveals the stranger's true need,
and the village helps carry the reed to the river shrine.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dust", "travel", "burden"):
            self.meters.setdefault(k, 0.0)
        for k in ("fear", "hate", "kindness", "friendship", "hope"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the river village"
    village_name: str = "Ember Hollow"
    shrine: str = "the river shrine"


@dataclass
class Relic:
    label: str
    phrase: str
    is_burden: bool = True


@dataclass
class StoryParams:
    place: str
    hero: str
    stranger: str
    relic: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "river": Setting(place="the river village", village_name="Ember Hollow", shrine="the river shrine"),
    "grove": Setting(place="the moon grove", village_name="Willow Crown", shrine="the stone spring"),
    "hill": Setting(place="the hill village", village_name="Bright Cairn", shrine="the old well"),
}

HEROES = [
    ("Ari", "girl"),
    ("Milo", "boy"),
    ("Sana", "girl"),
    ("Tomas", "boy"),
]

STRANGERS = [
    ("the stranger", "wanderer"),
    ("the cloaked stranger", "wanderer"),
    ("the river stranger", "messenger"),
]

RELICS = {
    "rape_reed": Relic(label="Rape Reed", phrase="a red reed from the old river tales"),
    "gold_cord": Relic(label="gold cord", phrase="a bright cord for the shrine bell"),
}

TRAITS = ["kind", "curious", "brave", "gentle", "quick"]


ASP_RULES = r"""
% A stranger is feared when the village hears of the burden and no friendship has yet begun.
feared(S) :- stranger(S), burdened(S), not friendship_started.

% Kindness can soften hate.
softened(S) :- feared(S), kindness_given.
resolved :- softened(S), return_to_shrine.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "village")]
    for sid, _ in STRANGERS:
        lines.append(asp.fact("stranger", sid.replace(" ", "_")))
        lines.append(asp.fact("burdened", sid.replace(" ", "_")))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    lines.append(asp.fact("return_to_shrine"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for hero, _ in HEROES:
            for stranger, _ in STRANGERS:
                for relic in RELICS:
                    out.append((place, hero, relic))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: fear, a stranger, and a kindness-friendship turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[h for h, _ in HEROES])
    ap.add_argument("--stranger", choices=[s for s, _ in STRANGERS])
    ap.add_argument("--relic", choices=RELICS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    stranger = args.stranger or rng.choice([s for s, _ in STRANGERS])
    relic = args.relic or rng.choice(list(RELICS))
    return StoryParams(place=place, hero=hero, stranger=stranger, relic=relic)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_type = next(t for h, t in HEROES if h == params.hero)
    stranger_type = next(t for s, t in STRANGERS if s == params.stranger)
    relic = RELICS[params.relic]

    hero = world.add(Entity(id=params.hero, kind="character", type=hero_type, label=params.hero))
    stranger = world.add(Entity(id=params.stranger, kind="character", type=stranger_type, label=params.stranger))
    reed = world.add(Entity(id="relic", type="relic", label=relic.label, phrase=relic.phrase, owner=stranger.id))
    reed.carried_by = stranger.id

    hero.memes["kindness"] += 1
    hero.memes["hope"] += 1
    stranger.meters["burden"] += 1
    stranger.meters["travel"] += 1

    world.say(
        f"In {setting.village_name}, there lived a {next(t for h, t in HEROES if h == hero.id)} named {hero.id}. "
        f"{hero.id} loved Friendship and Kindness, and the old songs said both could mend a frightened heart."
    )
    world.say(
        f"One dusk, a {stranger.type} came by the gate. {stranger.pronoun().capitalize()} carried "
        f"{relic.phrase} and asked to reach {setting.shrine} before the moon rose."
    )

    world.para()
    hero.memes["fear"] += 1
    if params.relic == "rape_reed":
        world.say(
            f"The villagers whispered about the Rape Reed. They did not like the strange old name, "
            f"and their fear began to harden into hate."
        )
    else:
        world.say(
            f"The villagers did not know why the stranger had come, so their fear grew dark and prickly."
        )
    world.say(
        f"{hero.id} saw the stranger's tired hands and remembered the kindness stories. "
        f"Instead of turning away, {hero.pronoun()} stepped forward with a warm smile."
    )
    hero.memes["friendship"] += 1
    stranger.memes["hope"] += 1
    stranger.memes["hate"] = 0.0

    world.para()
    world.say(
        f"{hero.id} asked the stranger's name and listened closely. "
        f"It turned out the reed was not a threat at all; it was a shrine gift, meant to tint the morning cloth."
    )
    world.say(
        f"{hero.id} called the neighbors back and spoke kindly. The hard feeling of hate loosened, "
        f"and the village remembered how to be a village again."
    )
    hero.memes["kindness"] += 1
    hero.memes["hope"] += 1

    world.para()
    world.say(
        f"Together they walked to {setting.shrine}. {hero.id} carried one end of the bundle, "
        f"and the stranger carried the other. At the shrine, they set down {relic.label}, "
        f"and the moon made it glow like a small red promise."
    )
    world.say(
        f"By dawn, Friendship stood where fear had been, and Kindness had made the path open."
    )

    world.facts.update(
        hero=hero,
        stranger=stranger,
        relic=reed,
        setting=setting,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    stranger = f["stranger"]
    return [
        f"Write a short myth for children about {hero.id}, Friendship, and Kindness, with a stranger at the gate.",
        f"Tell a gentle tale where {hero.id} helps a stranger carrying the Rape Reed reach the shrine.",
        f"Write a village myth where fear turns to friendship after a kind question and a shared walk home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    stranger = f["stranger"]
    relic = f["relic"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a child who cared about Friendship and Kindness in {setting.village_name}.",
        ),
        QAItem(
            question=f"What did the stranger carry?",
            answer=f"The stranger carried {relic.phrase} on the way to {setting.shrine}.",
        ),
        QAItem(
            question="How did the village's hate change?",
            answer="The village's hate faded when the child listened kindly, spoke up, and walked with the stranger instead of fearing them.",
        ),
        QAItem(
            question=f"Why did {hero.id} go with the stranger?",
            answer=f"{hero.id} went with the stranger because Kindness made the child curious, and the child learned the bundle was meant for the shrine.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Friendship?",
            answer="Friendship is the warm bond that helps people trust, share, and walk together instead of being alone.",
        ),
        QAItem(
            question="What is Kindness?",
            answer="Kindness is the choice to help, listen, and speak gently so someone else's hurt feels smaller.",
        ),
        QAItem(
            question="What can happen when fear grows too big?",
            answer="When fear grows too big, it can turn into hate, but careful listening and kindness can calm it down again.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    return 0


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    return [(p, h, r, "all") for p, h, r in valid_combos()]


CURATED = [
    StoryParams(place="river", hero="Ari", stranger="the stranger", relic="rape_reed"),
    StoryParams(place="grove", hero="Sana", stranger="the cloaked stranger", relic="gold_cord"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show feared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos")
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
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

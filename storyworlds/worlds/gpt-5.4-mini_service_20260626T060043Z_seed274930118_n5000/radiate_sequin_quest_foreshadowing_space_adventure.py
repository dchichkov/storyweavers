#!/usr/bin/env python3
"""
storyworlds/worlds/radiate_sequin_quest_foreshadowing_space_adventure.py
=========================================================================

A small classical storyworld in a Space Adventure style.

Seed tale sketch:
---
A young space scout named Nova joined a little quest to deliver a bright star-map
to a far station. Nova loved a sequin patch stitched onto a blue suit because it
radiated like a tiny constellation when the ship lights dimmed. Before the trip,
the patch had flashed at strange times, and an old pilot said it was foreshadowing:
the glittery patch would matter when the route got hard to see.

On the quest, the ship drifted into a shadowy tunnel of dust. The map reader went
dark, and Nova worried the mission would fail. Then the sequin patch radiated a
soft trail of sparkles across the wall, revealing the hidden turn. Nova followed
the light, found the station, and delivered the map just in time.

World model:
---
A child, a quest, a dim route, and a clue that was foreshadowed by something
small and glittering. The sequin patch is physical gear with a light meter;
the story tension is emotional uncertainty that resolves when the patch radiates
and the route becomes visible.
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

SPACEPLACES = {
    "launch_pad": "the launch pad",
    "moon_path": "the moon path",
    "dust_tunnel": "the dust tunnel",
    "orbital_gate": "the orbital gate",
}

QUESTS = {
    "deliver_map": {
        "verb": "deliver the star-map",
        "gerund": "delivering the star-map",
        "object": "star-map",
        "goal": "the far station",
        "risk": "the route could vanish in the dark",
        "turn": "the glitter on the patch would help",
        "tags": {"map", "glow", "space", "quest"},
    },
    "find_beacon": {
        "verb": "find the missing beacon",
        "gerund": "finding the missing beacon",
        "object": "beacon",
        "goal": "the outer dock",
        "risk": "the dust tunnel could hide the turn",
        "turn": "the sequin patch could catch the weak light",
        "tags": {"beacon", "glow", "space", "quest"},
    },
    "bring_kit": {
        "verb": "bring the repair kit",
        "gerund": "bringing the repair kit",
        "object": "repair kit",
        "goal": "the station hatch",
        "risk": "the corridor lights might fail",
        "turn": "the patch could radiate a bright trail",
        "tags": {"kit", "glow", "space", "quest"},
    },
}

GLOW_GEAR = {
    "sequin_patch": {
        "label": "a sequin patch",
        "phrase": "a sequin patch stitched to the sleeve",
        "radiance": "shimmer",
        "covers": {"sleeve"},
        "helps": {"dark", "dust"},
    },
    "helmet_lamp": {
        "label": "a helmet lamp",
        "phrase": "a little helmet lamp",
        "radiance": "beam",
        "covers": {"face"},
        "helps": {"dark"},
    },
    "signal_cloak": {
        "label": "a signal cloak",
        "phrase": "a signal cloak with silver thread",
        "radiance": "glow",
        "covers": {"shoulders", "torso"},
        "helps": {"dark", "dust"},
    },
}

TRAITS = ["brave", "curious", "careful", "lively", "quiet", "hopeful"]
NAMES = ["Nova", "Mika", "Rin", "Tala", "Pip", "Luna"]
CAPTIONS = ["captain", "pilot", "guide"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    quest: str
    gear: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: str, quest: str, gear: str) -> None:
        self.place = place
        self.quest = quest
        self.gear = gear
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with a sequin clue and a quest.")
    ap.add_argument("--place", choices=SPACEPLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gear", choices=GLOW_GEAR)
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
    place = args.place or rng.choice(list(SPACEPLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    gear = args.gear or rng.choice(list(GLOW_GEAR))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, gear=gear, name=name, trait=trait)


def _hero_name(ent: Entity) -> str:
    return ent.id


def tell(params: StoryParams) -> World:
    q = QUESTS[params.quest]
    g = GLOW_GEAR[params.gear]
    w = World(params.place, params.quest, params.gear)

    hero = w.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    mentor = w.add(Entity(id="Captain", kind="character", type="captain", label="the captain"))
    gear = w.add(Entity(
        id=params.gear,
        type="gear",
        label=g["label"],
        phrase=g["phrase"],
        owner=hero.id,
        worn_by=hero.id,
        protective=True,
        covers=set(g["covers"]),
        meters={"radiance": 0.0},
        memes={"hope": 0.0},
    ))
    map_item = w.add(Entity(
        id="map",
        type="map",
        label="star-map",
        phrase="a folded star-map",
        owner=mentor.id,
        meters={"safety": 0.0},
        memes={"importance": 1.0},
    ))

    # Act 1: setup and foreshadowing.
    w.say(
        f"{hero.id} was a {params.trait} child who loved space quests."
    )
    w.say(
        f"{hero.id} liked {gear.phrase} because it seemed to radiate tiny sparks when the ship went dim."
    )
    w.say(
        f"Before the trip, the captain noticed the little shimmer and said it was a foreshadowing sign."
    )
    w.say(
        f"It meant the bright patch might matter when the path got hard to see."
    )

    # Act 2: tension.
    w.para()
    w.say(
        f"That evening, {hero.id} and {hero.pronoun('possessive')} captain started the quest to {q['verb']}."
    )
    w.say(
        f"They crossed {SPACEPLACES[params.place]} and aimed for {q['goal']}."
    )
    w.say(
        f"Then the ship drifted into {SPACEPLACES['dust_tunnel']}, and the map lamp blinked out."
    )
    hero.memes["worry"] = 1.0
    hero.memes["hope"] = 0.2
    w.say(
        f"{hero.id}'s chest tightened because {q['risk']}."
    )

    # The clue pays off.
    w.para()
    gear.meters["radiance"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 1.0
    map_item.meters["safety"] = 1.0
    w.say(
        f"Then {gear.label} began to radiate a soft trail of light across the wall."
    )
    w.say(
        f"The silver shine traced the hidden turn, exactly as the foreshadowing had promised."
    )
    w.say(
        f"{hero.id} followed the glowing line, found {q['goal']}, and finished the quest."
    )
    w.say(
        f"In the end, the small sequin sparkle had become the brightest thing in the dark tunnel."
    )

    w.facts.update(
        hero=hero,
        mentor=mentor,
        gear=gear,
        map=map_item,
        place=params.place,
        quest=params.quest,
        quest_def=q,
        gear_def=g,
    )
    return w


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest_def"]
    g = world.facts["gear_def"]
    hero = world.facts["hero"]
    return [
        f"Write a short Space Adventure story for a child named {hero.id} who goes on a quest to {q['verb']}.",
        f"Tell a gentle story where a sequin-like clue foreshadows how {g['label']} will help in the dark.",
        f"Write a simple quest story that includes radiate and sequin and ends with a hidden path being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q = world.facts["quest_def"]
    hero = world.facts["hero"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question=f"Who went on the quest in the story?",
            answer=f"{hero.id} went on the quest with the captain."
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the trip?",
            answer=f"{hero.id} wanted to {q['verb']}, and the mission led through a dark tunnel."
        ),
        QAItem(
            question=f"How did {gear.label} help at the end?",
            answer=f"It radiated a soft light that showed the hidden turn, so {hero.id} could finish the quest."
        ),
        QAItem(
            question="What earlier clue foreshadowed the solution?",
            answer="The captain noticed the tiny shimmer before the trip and said it was a foreshadowing sign."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is an early clue that hints about something important that will happen later."
        ),
        QAItem(
            question="What does it mean when something radiates light?",
            answer="When something radiates light, it shines out from itself like a tiny lamp or sparkly glow."
        ),
        QAItem(
            question="What is a sequin?",
            answer="A sequin is a tiny shiny disk sewn onto clothes or decorations so they sparkle."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_story(H,Q,G) :- hero(H), quest(Q), gear(G), helpful(G,Q).
helpful(sequin_patch, deliver_map).
helpful(sequin_patch, find_beacon).
helpful(helmet_lamp, deliver_map).
helpful(helmet_lamp, find_beacon).
helpful(signal_cloak, bring_kit).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SPACEPLACES:
        lines.append(asp.fact("place", place))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for g in GLOW_GEAR:
        lines.append(asp.fact("gear", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SPACEPLACES:
        for q in QUESTS:
            for g in GLOW_GEAR:
                combos.append((place, q, g))
    return combos


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="moon_path", quest="deliver_map", gear="sequin_patch", name="Nova", trait="curious"),
    StoryParams(place="dust_tunnel", quest="find_beacon", gear="helmet_lamp", name="Mika", trait="brave"),
    StoryParams(place="orbital_gate", quest="bring_kit", gear="signal_cloak", name="Tala", trait="hopeful"),
]


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
        print(asp_program("#show quest_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

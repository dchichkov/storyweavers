#!/usr/bin/env python3
"""
storyworlds/worlds/nosey_tidy_quadruple_repetition_sharing_quest_superhero.py
===============================================================================

A tiny superhero storyworld about a masked helper, a nosy neighbor, tidy gear,
repetition, sharing, and a quest that can be solved only by cooperation.

Seed tale sketch:
---
A cheerful superhero loved helping the city stay safe. One afternoon, a nosey
neighbor kept peeking into the hero's tidy hideout and asking questions. At the
same time, a quadruple delivery of rescue maps went missing, so the hero had to
begin a quest to find them. The hero could not solve the problem alone, because
the clues were repeated in different places and had to be shared with friends.
In the end, the hero and the neighbor worked together, the maps were found,
and the hideout stayed tidy.

Design notes:
---
- Physical meters include distance, clutter, and the movement of objects.
- Emotional memes include curiosity, worry, pride, trust, and relief.
- Repetition is modeled as an investigation step: the same clue appears in
  multiple places, and the hero must compare them.
- Sharing is modeled as a cooperative transfer of clue cards and tools.
- Quest is modeled as a state-driven search for missing rescue maps.
- The story only resolves when the hero accepts help and uses the repeated
  clues to locate the lost item.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    mood: str
    places: list[str]


@dataclass
class StoryParams:
    setting: str
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
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(name="the city", mood="bright", places=["tower", "library", "rooftop", "alley"]),
    "harbor": Setting(name="the harbor", mood="windy", places=["dock", "warehouse", "lighthouse", "market"]),
    "garden": Setting(name="the rooftop garden", mood="quiet", places=["greenhouse", "bench", "water tank", "path"]),
}

HEROES = ["Nova", "Spark", "Milo", "Ari", "Juno", "Pip"]
SIDEKICKS = ["Bean", "Tess", "Ren", "Dot", "Lumi", "Zed"]
TYPES = ["girl", "boy"]

MISSING_GOODS = {
    "maps": {
        "label": "rescue maps",
        "phrase": "a quadruple stack of rescue maps",
        "plural": True,
        "count": 4,
    }
}

CLUES = [
    "chalk arrow",
    "blue ribbon",
    "lamp blink",
    "door hum",
]

# ---------------------------------------------------------------------------
# Reasoning helpers
# ---------------------------------------------------------------------------
def valid_setting(name: str) -> bool:
    return name in SETTINGS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld about a nosy interruption, a tidy hideout, and a quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--sidekick-type", choices=TYPES)
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
    hero_name = args.name or rng.choice(HEROES)
    hero_type = args.hero_type or rng.choice(TYPES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICKS)
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    if hero_name == sidekick_name:
        raise StoryError("The hero and sidekick must be different characters.")
    if not valid_setting(setting):
        raise StoryError("That setting is not available.")
    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
    )


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={"distance": 0}, memes={"pride": 1, "trust": 1}))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_type, meters={"distance": 0}, memes={"curiosity": 1, "help": 1}))
    neighbor = world.add(Entity(id="Neighbor", kind="character", type="woman", label="the nosey neighbor", meters={"distance": 0}, memes={"curiosity": 3, "worry": 0}))
    maps = world.add(Entity(id="Maps", type="maps", label="rescue maps", phrase="a quadruple stack of rescue maps", plural=True, owner=hero.id, carried_by=hero.id, location="hideout", meters={"clutter": 0}))
    world.facts.update(hero=hero, sidekick=sidekick, neighbor=neighbor, maps=maps)
    return world


def _intro(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    maps = world.facts["maps"]
    world.say(
        f"{hero.id} was a little superhero who kept a tidy hideout and liked to help the city."
        f" {hero.pronoun().capitalize()} and {sidekick.id} sorted every tool by color, because a tidy room made quick rescues easier."
    )
    world.say(
        f"On the shelf sat {maps.phrase}, a quadruple set of rescue maps that showed where people might need help."
    )


def _nosy_interrupt(world: World) -> None:
    hero = world.facts["hero"]
    neighbor = world.facts["neighbor"]
    world.para()
    neighbor.memes["curiosity"] += 1
    world.say(
        f"Then {neighbor.label} peered into the hideout with nosey little questions."
        f' "What is under that cloth? Why is everything so tidy? Where do the maps go?"'
    )
    hero.memes["unease"] = hero.memes.get("unease", 0) + 1
    world.say(
        f"{hero.id} felt a tiny pinch of worry, because even a superhero does not like secrets being poked at all day."
    )


def _quest_begins(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    maps = world.facts["maps"]
    world.para()
    maps.carried_by = None
    maps.location = "missing"
    hero.memes["worry"] = hero.memes.get("worry", 0) + 2
    world.say(
        f"Just then, the quadruple stack of rescue maps went missing, and the room stopped feeling tidy."
    )
    world.say(
        f"{hero.id} and {sidekick.id} had to start a quest right away, because the city needed those maps before sunset."
    )


def _repetition_clue(world: World, place: str, clue: str) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    world.say(
        f"At the {place}, they found the same {clue} again."
        f" The repetition mattered: one clue appeared in more than one spot, so the heroes knew the trail was real."
    )
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    sidekick.memes["focus"] = sidekick.memes.get("focus", 0) + 1


def _share_tools(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    neighbor = world.facts["neighbor"]
    hero.memes["trust"] += 1
    sidekick.memes["trust"] = sidekick.memes.get("trust", 0) + 1
    neighbor.memes["help"] = neighbor.memes.get("help", 0) + 1
    world.say(
        f"{hero.id} finally shared the clue cards with {sidekick.id}, and even the nosey neighbor offered a flashlight and a map pin."
    )
    world.say(
        f"With shared tools, they could compare the repeated signs instead of guessing alone."
    )


def _find_maps(world: World) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    neighbor = world.facts["neighbor"]
    maps = world.facts["maps"]
    maps.location = "lighthouse shelf"
    maps.carried_by = hero.id
    hero.memes["relief"] = hero.memes.get("relief", 0) + 2
    sidekick.memes["relief"] = sidekick.memes.get("relief", 0) + 2
    neighbor.memes["worry"] = max(0, neighbor.memes.get("worry", 0) - 1)
    world.say(
        f"They followed the repeated clues all the way to the lighthouse shelf, where the rescue maps were tucked behind a red box."
    )
    world.say(
        f"{hero.id} lifted the maps, and the room felt tidy again because everything was back where it belonged."
    )
    world.say(
        f"The nosey neighbor smiled, not so nosey anymore, because helping had been better than peeking."
    )


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _intro(world)
    _nosy_interrupt(world)
    _quest_begins(world)
    world.para()
    places = SETTINGS[params.setting].places
    for place, clue in zip(places[:2], CLUES[:2]):
        _repetition_clue(world, place, clue)
    _share_tools(world)
    world.para()
    for place, clue in zip(places[2:], CLUES[2:]):
        _repetition_clue(world, place, clue)
    _find_maps(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    setting = world.setting.name
    return [
        f"Write a superhero story for young children about {hero.id}, a tidy hero, and a nosey interruption in {setting}.",
        f"Tell a quest story where {hero.id} and {sidekick.id} must share clues to find missing rescue maps.",
        f"Make a short child-friendly superhero tale that uses the words nosey, tidy, quadruple, repetition, sharing, and quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    maps = f["maps"]
    return [
        QAItem(
            question=f"Who went on the quest to find the missing maps?",
            answer=f"{hero.id} and {sidekick.id} went on the quest together.",
        ),
        QAItem(
            question="Why did the hero care about the missing rescue maps?",
            answer="The rescue maps were needed to help the city before sunset, so losing them was a real problem.",
        ),
        QAItem(
            question="What did the hero share during the search?",
            answer="The hero shared clue cards and worked with the sidekick instead of searching alone.",
        ),
        QAItem(
            question="What proved that the clues were useful?",
            answer="The same clue showed up in more than one place, and that repetition helped them trust the trail.",
        ),
        QAItem(
            question="Where were the maps found at the end?",
            answer=f"They were found on a lighthouse shelf, and {hero.id} carried them back to the tidy hideout.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special courage, skill, or tools to help other people.",
        ),
        QAItem(
            question="What does tidy mean?",
            answer="Tidy means neat, clean, and put in the right place.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or have part of something, like a tool or a clue.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important that may take some work to find.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).

needs_quest(H) :- missing(maps), hero(H).
repetition_helpful :- clue_seen(C,P1), clue_seen(C,P2), P1 != P2.
sharing_helpful :- shared_clue_cards(H,S), hero(H), sidekick(S).

resolved :- needs_quest(_), repetition_helpful, sharing_helpful, found(maps).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for setting in SETTINGS:
        lines.append(asp.fact("setting", setting))
        for place in SETTINGS[setting].places:
            lines.append(asp.fact("place", setting, place))
    lines.append(asp.fact("missing", "maps"))
    lines.append(asp.fact("hero_name", "hero"))
    lines.append(asp.fact("sidekick_name", "sidekick"))
    lines.append(asp.fact("shared_clue_cards", "hero", "sidekick"))
    lines.append(asp.fact("found", "maps"))
    for clue in CLUES:
        lines.append(asp.fact("clue", clue))
    lines.append(asp.fact("repetition_seed", "quadruple"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> bool:
    return True


def asp_verify() -> int:
    if not asp_reasonable():
        print("Python reasonableness gate failed.")
        return 1
    try:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        atoms = {str(a) for a in model}
        ok = any("resolved" in a for a in atoms)
        if ok:
            print("OK: ASP twin resolves the shared quest story.")
            return 0
        print("MISMATCH: ASP did not derive resolved.")
        return 1
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable or failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "character":
            bits.append("character")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="city", hero_name="Nova", hero_type="girl", sidekick_name="Bean", sidekick_type="boy"),
    StoryParams(setting="harbor", hero_name="Spark", hero_type="boy", sidekick_name="Dot", sidekick_type="girl"),
    StoryParams(setting="garden", hero_name="Ari", hero_type="girl", sidekick_name="Ren", sidekick_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show resolved/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

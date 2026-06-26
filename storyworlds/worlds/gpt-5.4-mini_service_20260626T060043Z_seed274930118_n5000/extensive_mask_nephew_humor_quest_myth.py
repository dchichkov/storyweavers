#!/usr/bin/env python3
"""
A small myth-style storyworld about an extensive quest, a strange mask, and a
nephew who learns to laugh wisely.

The seed image:
---
A village keeps an extensive old mask in a shrine. A proud uncle sends his
nephew to fetch it from a cliff cave so the spring festival can begin. The cave
is tricky, but the boy has humor, and the quest turns on whether he can use
laughter without mocking the sacred thing. He returns changed: less boastful,
more humble, and the mask is delivered safely.

This world models:
- a hero, an elder, a sacred mask, a shrine, a cave, and a festival
- physical meters such as distance, weight, height, and damage
- emotional memes such as courage, awe, humor, pride, trust, and relief
- causal steps: receive quest -> travel -> face riddle/trick -> solve with wit
  -> return with the mask -> festival begins

The world has a Python reasonableness gate and an inline ASP twin.
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
# Core entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place | event
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    journey: str
    challenge: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    weight: str
    is_mask: bool = False
    sacred: bool = False
    risk: str = "damage"
    tags: set[str] = field(default_factory=set)


@dataclass
class Talisman:
    id: str
    label: str
    aid: str
    joke_style: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    quest: str
    relic: str
    hero_name: str
    hero_type: str
    elder_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shrine": Setting(
        name="the shrine",
        place="the shrine of river stones",
        mood="awe",
        affords={"quest"},
    ),
    "mountain": Setting(
        name="the mountain",
        place="the mountain path",
        mood="wonder",
        affords={"quest"},
    ),
    "forest": Setting(
        name="the forest",
        place="the whispering forest",
        mood="wonder",
        affords={"quest"},
    ),
}

QUESTS = {
    "fetch_mask": Quest(
        id="fetch_mask",
        verb="fetch the mask",
        journey="climb to the cave",
        challenge="answer the stone guardian",
        resolution="return with the mask",
        tags={"mask", "quest", "humor"},
    ),
    "bring_mask": Quest(
        id="bring_mask",
        verb="bring back the mask",
        journey="go into the old cave",
        challenge="please the laughing echo",
        resolution="come home with the mask",
        tags={"mask", "quest", "humor"},
    ),
}

RELICS = {
    "mask": Relic(
        id="mask",
        label="mask",
        phrase="an extensive old mask with painted leaves and a long nose",
        weight="heavy",
        is_mask=True,
        sacred=True,
        risk="scrape",
        tags={"mask", "sacred"},
    ),
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="a bronze lantern with a bright glass eye",
        weight="medium",
        is_mask=False,
        sacred=False,
        risk="fade",
        tags={"light"},
    ),
}

TALISMANS = {
    "humor": Talisman(
        id="humor",
        label="a joke pebble",
        aid="keeps the hero from shaking with fear",
        joke_style="a tiny, respectful joke",
        protects={"fear"},
        tags={"humor"},
    ),
    "rope": Talisman(
        id="rope",
        label="a climbing rope",
        aid="helps the hero cross steep places",
        joke_style="a clever knot trick",
        protects={"fall"},
        tags={"quest"},
    ),
}

NAMES = ["Oren", "Milo", "Nia", "Tara", "Ivo", "Lina", "Arin", "Mara"]
HERO_TYPES = ["boy", "girl"]
ELDER_TYPES = ["uncle", "aunt", "father", "mother"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_needs_mask(quest: Quest, relic: Relic) -> bool:
    return quest.id in {"fetch_mask", "bring_mask"} and relic.is_mask


def compatible_talisman(quest: Quest, relic: Relic) -> Optional[Talisman]:
    if relic.is_mask:
        return TALISMANS["humor"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for qid, q in QUESTS.items():
            for rid, r in RELICS.items():
                if quest_needs_mask(q, r) and compatible_talisman(q, r):
                    out.append((s, qid, rid))
    return out


def explain_rejection(quest: Quest, relic: Relic) -> str:
    if not quest_needs_mask(quest, relic):
        return "(No story: this quest does not honestly require the relic in the seed image.)"
    return "(No story: the tale needs a sacred mask, and this relic does not fit that role.)"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def build_hero(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity, Talisman]:
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"distance": 0.0, "weariness": 0.0},
        memes={"humor": 1.0, "courage": 0.0, "awe": 0.0, "pride": 0.0, "trust": 0.0, "relief": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder_type,
        label=f"the {params.elder_type}",
        meters={"patience": 1.0},
        memes={"pride": 1.0, "trust": 0.0, "worry": 0.0},
    ))
    relic_cfg = RELICS[params.relic]
    relic = world.add(Entity(
        id=relic_cfg.id,
        kind="thing",
        type="relic",
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        keeper="elder",
        location="shrine",
        sacred=relic_cfg.sacred,
        meters={"damage": 0.0, "weight": 2.0 if relic_cfg.weight == "heavy" else 1.0},
        memes={"awe": 1.0},
    ))
    quest_cfg = QUESTS[params.quest]
    quest = world.add(Entity(
        id=quest_cfg.id,
        kind="event",
        type="quest",
        label=quest_cfg.id,
        phrase=quest_cfg.verb,
    ))
    talisman = TALISMANS["humor"]
    world.add(Entity(
        id=talisman.id,
        kind="thing",
        type="talismans",
        label=talisman.label,
        phrase=talisman.aid,
        meters={"lightness": 1.0},
        memes={"humor": 1.0},
    ))
    return hero, elder, relic, quest, talisman


def tell_story(world: World, hero: Entity, elder: Entity, relic: Entity, quest: Quest, talisman: Talisman) -> None:
    world.say(f"Long ago, {hero.label} lived near {world.setting.place}, where even the stones seemed to listen.")
    world.say(
        f"One day, {elder.label} gave {hero.label} an extensive quest: to {quest.verb} "
        f"from the cave and carry it home before sunset."
    )
    hero.memes["courage"] += 1.0
    elder.memes["trust"] += 1.0
    world.say(
        f"{hero.label} held the request like a lantern in the chest. "
        f"{hero.pronoun().capitalize()} loved the idea of a quest, and {hero.pronoun('possessive')} humor kept {hero.pronoun('object')} from trembling."
    )

    world.para()
    hero.meters["distance"] += 1.0
    hero.meters["weariness"] += 0.5
    world.say(
        f"{hero.label} climbed the {world.setting.place.split()[-1]} path and reached the cave mouth, where the air was cool and shy."
    )
    world.say(
        f"Inside, a stone guardian asked for a smile that did not break the sacredness of the place."
    )

    hero.memes["awe"] += 1.0
    world.facts["challenged"] = True
    world.facts["guardian"] = "stone guardian"
    world.say(
        f"{hero.label} remembered the joke pebble and the rule of the old tales: humor should open a door, not slam one."
    )
    hero.memes["humor"] += 1.0
    if hero.memes["humor"] >= 2.0:
        world.say(
            f"So {hero.label} told a tiny, respectful joke about a mouse who wanted to borrow the moon, and even the cave seemed to grin."
        )
    hero.memes["trust"] += 1.0
    world.say(
        f"The guardian stepped aside, and the mask waited on a shelf of black stone, looking older than summer rain."
    )

    world.para()
    relic.meters["damage"] += 0.0
    hero.meters["distance"] += 1.0
    hero.meters["weariness"] += 0.5
    world.say(
        f"{hero.label} lifted the mask carefully with both hands. It was heavier than it looked, and the weight made {hero.pronoun('object')} humble."
    )
    world.say(
        f"{hero.label} wrapped it in cloth, turned back down the path, and carried it home without a scratch."
    )
    relic.location = "shrine"
    relic.carried_by = hero.id
    world.facts["returned"] = True
    hero.memes["relief"] += 1.0
    elder.memes["worry"] += 0.0
    world.say(
        f"When {hero.label} returned, {elder.label} bowed and smiled, for the quest had been done with wit, care, and a steady heart."
    )
    world.say(
        f"That night the village lit lamps, the mask stood safe again, and {hero.label} laughed softly at the feast, wiser than when the day began."
    )


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    relic = f["relic"]
    return [
        f"Write a short myth for children about {hero.label}, an extensive quest, and {relic.label}.",
        f"Tell a gentle story where a {hero.type} named {hero.label} must {quest.verb} and use humor wisely.",
        f"Write a mythic tale with a sacred mask, a cave, and a nephew or niece who brings the relic home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    elder: Entity = f["elder"]
    relic: Entity = f["relic"]
    quest: Quest = f["quest"]

    qa = [
        QAItem(
            question=f"Who was sent on the quest to get the mask?",
            answer=f"{hero.label} was sent by {elder.label} to {quest.verb}.",
        ),
        QAItem(
            question=f"What made {hero.label} brave enough to face the cave guardian?",
            answer=f"{hero.label}'s humor and awe helped {hero.pronoun('object')} stay brave without being rude.",
        ),
        QAItem(
            question=f"What did the hero carry home at the end?",
            answer=f"{hero.label} carried home {relic.phrase}, and the mask stayed safe.",
        ),
    ]
    if world.facts.get("challenged"):
        qa.append(
            QAItem(
                question=f"How did the hero answer the stone guardian?",
                answer=(
                    f"{hero.label} answered with a tiny, respectful joke that opened the way "
                    f"without mocking the sacred place."
                ),
            )
        )
    if world.facts.get("returned"):
        qa.append(
            QAItem(
                question=f"How was {hero.label} changed by the quest?",
                answer=(
                    f"{hero.label} came back more humble and careful, with more trust and relief "
                    f"than pride."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mask?",
            answer="A mask is something you can wear over the face, often to change how you look or to honor a story, festival, or ritual.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey with a goal, often one that asks for courage, wit, or patience.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can help because it lightens fear, helps people think, and can make a tense situation softer.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(shrine).
setting(mountain).
setting(forest).

quest(fetch_mask).
quest(bring_mask).

relic(mask).
relic(lantern).

mask_relic(mask).

needs_mask(fetch_mask, mask).
needs_mask(bring_mask, mask).

valid(Setting, Quest, Relic) :- setting(Setting), quest(Quest), relic(Relic), needs_mask(Quest, Relic).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    for qid, q in QUESTS.items():
        for rid, r in RELICS.items():
            if quest_needs_mask(q, r):
                lines.append(asp.fact("needs_mask", qid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(python_set - asp_set))
    print("only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("No valid combination matches the chosen options.")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting, quest, relic = select_combo(args, rng)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    hero_name = args.hero_name or rng.choice(NAMES)
    if args.hero_name and args.hero_name == "nephew" and hero_type != "boy":
        raise StoryError("If the hero is a nephew, the hero type must be boy.")
    if args.elder_type == "uncle" and hero_type == "girl":
        # Still possible in natural language, but the seed image says nephew.
        pass
    return StoryParams(
        setting=setting,
        quest=quest,
        relic=relic,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero, elder, relic, quest, talisman = build_hero(world, params)
    world.facts.update(hero=hero, elder=elder, relic=relic, quest=QUESTS[params.quest], talisman=talisman)
    tell_story(world, hero, elder, relic, QUESTS[params.quest], talisman)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-style storyworld about a mask quest with humor.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--relic", choices=RELICS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--elder-type", choices=ELDER_TYPES)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:\n")
        for setting, quest, relic in combos:
            print(f"  {setting:10} {quest:12} {relic}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(setting="shrine", quest="fetch_mask", relic="mask", hero_name="Oren", hero_type="boy", elder_type="uncle"),
        StoryParams(setting="mountain", quest="bring_mask", relic="mask", hero_name="Milo", hero_type="boy", elder_type="uncle"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

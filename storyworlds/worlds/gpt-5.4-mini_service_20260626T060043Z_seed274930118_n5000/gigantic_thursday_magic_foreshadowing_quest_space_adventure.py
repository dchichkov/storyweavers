#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gigantic_thursday_magic_foreshadowing_quest_space_adventure.py
=================================================================================================

A small standalone story world: a space-adventure quest with a little magic and
a foreshadowing clue that helps the hero solve a problem on Thursday.

Premise:
- A child astronaut wants to complete a quest aboard a spaceship or on a moon.
- A magical helper object can reveal a foreshadowing sign before the final turn.
- The story is driven by world state: tension comes from a blocked route or
  missing item; resolution comes from using the clue and the magic in a concrete
  way.

The seed words "gigantic" and "thursday" are baked into the vocab, and the
style aims for child-facing space adventure prose.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    hinting: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "astronaut-girl", "captain-girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "astronaut-boy", "captain-boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    missing: str
    obstacle: str
    fix: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    reveal: str
    clue_sign: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.day: str = "thursday"
        self.clue_seen: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.day = self.day
        clone.clue_seen = self.clue_seen
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_station": Setting(
        place="the orbital station",
        mood="bright and humming",
        affords={"repair", "scan", "launch"},
    ),
    "moon_base": Setting(
        place="the moon base",
        mood="quiet and silvery",
        affords={"repair", "scan"},
    ),
    "starport": Setting(
        place="the starport",
        mood="busy and shiny",
        affords={"repair", "launch"},
    ),
}

QUESTS = {
    "signal": Quest(
        id="signal",
        goal="follow the missing signal",
        missing="the lost signal map",
        obstacle="the corridor lights go dark",
        fix="use the foreshadowing clue to find the hidden switch",
        clue="a tiny sparkle on the wall points to the side panel",
        keyword="signal",
        tags={"signal", "scan"},
    ),
    "crystal": Quest(
        id="crystal",
        goal="bring the crystal home",
        missing="the moon crystal",
        obstacle="a hatch is sealed shut",
        fix="use magic to open the hatch gently",
        clue="the crystal hums before the hatch opens",
        keyword="crystal",
        tags={"crystal", "magic"},
    ),
    "garden": Quest(
        id="garden",
        goal="reach the sky garden",
        missing="the garden seed pod",
        obstacle="a huge cargo crate blocks the lift",
        fix="move the crate with a clever machine and a magic spark",
        clue="the crate has claw marks that point toward the wheel",
        keyword="garden",
        tags={"garden", "repair"},
    ),
}

MAGICS = {
    "lamp": MagicItem(
        id="lamp",
        label="a tiny moon-lamp",
        phrase="a tiny moon-lamp with a warm glow",
        effect="it lights the dark path",
        reveal="its glow makes the hidden switch easy to see",
        clue_sign="the lamp flickers toward the correct panel",
        tags={"magic", "light"},
    ),
    "wand": MagicItem(
        id="wand",
        label="a star wand",
        phrase="a star wand with a silver tip",
        effect="it opens sealed things softly",
        reveal="its sparkle loosens the stuck hatch",
        clue_sign="the wand points at the seam in the hatch",
        tags={"magic", "open"},
    ),
    "compass": MagicItem(
        id="compass",
        label="a singing compass",
        phrase="a singing compass that buzzes like a bee",
        effect="it hums when the right way is near",
        reveal="its song grows loud beside the cargo wheel",
        clue_sign="the compass tilts toward the hidden path",
        tags={"magic", "guide"},
    ),
}

HERO_NAMES = ["Nina", "Toby", "Mila", "Arlo", "June", "Kai", "Pia", "Ezra"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "brave", "gentle", "cheerful", "bold"]


# ---------------------------------------------------------------------------
# Reasonableness checks
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if qid not in setting.affords and quest.id != "signal":
                # signal fits anywhere; other quests need a place that plausibly
                # supports their action.
                continue
            for mid, magic in MAGICS.items():
                if quest.id == "signal" and mid == "lamp":
                    combos.append((place, qid, mid))
                elif quest.id == "crystal" and mid == "wand":
                    combos.append((place, qid, mid))
                elif quest.id == "garden" and mid == "compass":
                    combos.append((place, qid, mid))
    return combos


def explain_rejection(quest: Quest, magic: MagicItem) -> str:
    return (
        f"(No story: {magic.label} does not make a believable fix for the {quest.keyword} quest. "
        f"Try the matching magical helper instead.)"
    )


# ---------------------------------------------------------------------------
# Story state / rules
# ---------------------------------------------------------------------------
def _do_quest(world: World, hero: Entity, quest: Quest, magic: MagicItem, narrate: bool = True) -> None:
    hero.meters[quest.id] = hero.meters.get(quest.id, 0.0) + 1.0
    if magic.id == "lamp":
        world.clue_seen = True
    if narrate:
        world.say(f"{hero.id} moved forward on the quest.")


def predict_outcome(world: World, hero: Entity, quest: Quest, magic: MagicItem) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, magic, narrate=False)
    obstacle_cleared = quest.id in {"signal", "crystal", "garden"}
    clue = sim.clue_seen
    return {"obstacle_cleared": obstacle_cleared, "clue_seen": clue}


def intro(world: World, hero: Entity, quest: Quest, magic: MagicItem) -> None:
    world.say(
        f"On {world.day}, {hero.id} was a little {hero.type} astronaut who loved a gigantic quest."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {magic.phrase} because {magic.effect}."
    )
    world.say(
        f"The ship felt {world.setting.mood}, and the {quest.keyword} mission waited like a shiny promise."
    )


def foreshadow(world: World, hero: Entity, quest: Quest, magic: MagicItem) -> None:
    world.say(
        f"Before the trouble started, {magic.clue_sign}."
    )
    world.say(
        f"{quest.clue}"
    )
    world.clue_seen = True
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0


def trouble(world: World, hero: Entity, quest: Quest, magic: MagicItem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Then the problem arrived: {quest.obstacle}."
    )
    world.say(
        f"{hero.id} paused, but {hero.pronoun('possessive')} {magic.label} began to glow anyway."
    )


def resolve(world: World, hero: Entity, quest: Quest, magic: MagicItem) -> None:
    _do_quest(world, hero, quest, magic, narrate=False)
    if magic.id == "lamp":
        world.say(
            f"{hero.id} followed the glow, found the hidden switch, and the corridor lights blinked back on."
        )
    elif magic.id == "wand":
        world.say(
            f"{hero.id} raised the star wand, and the sealed hatch opened with a soft sigh."
        )
    else:
        world.say(
            f"{hero.id} listened to the singing compass, rolled the crate aside, and found the way through."
        )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["worry"] = 0.0
    world.say(
        f"At the end, the quest was finished, and {hero.id} smiled at the gigantic space beyond."
    )


# ---------------------------------------------------------------------------
# Simulate a complete tale
# ---------------------------------------------------------------------------
def tell(setting: Setting, quest: Quest, magic: MagicItem, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=trait))
    item = world.add(Entity(
        id=magic.id,
        kind="thing",
        type="magic-item",
        label=magic.label,
        phrase=magic.phrase,
        magical=True,
        hinting=True,
        owner=hero.id,
        carried_by=hero.id,
    ))
    world.facts.update(hero=hero, item=item, quest=quest, magic=magic, setting=setting)

    intro(world, hero, quest, magic)
    world.para()
    foreshadow(world, hero, quest, magic)
    world.para()
    trouble(world, hero, quest, magic)
    resolve(world, hero, quest, magic)
    return world


# ---------------------------------------------------------------------------
# Params and QA
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    magic: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story about a "{f["quest"].keyword}" quest on {world.day}.',
        f"Tell a story where {f['hero'].id}, a little {f['hero'].type} astronaut, uses {f['magic'].label} and a foreshadowing clue to solve a problem.",
        f"Write a short magical spaceship story that includes the word '{world.day}' and ends with the quest finished.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    magic: MagicItem = f["magic"]
    place: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who went on the gigantic {quest.keyword} quest at {place.place}?",
            answer=f"{hero.id}, a little {hero.type} astronaut, went on the gigantic {quest.keyword} quest at {place.place}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the trouble in the story?",
            answer=f"The story foreshadowed trouble with this clue: {quest.clue}",
        ),
        QAItem(
            question=f"How did {magic.label} help with the problem?",
            answer=f"{magic.label} helped because {magic.reveal}.",
        ),
        QAItem(
            question=f"What happened at the end of the quest?",
            answer=f"{hero.id} solved the problem, finished the quest, and looked out at the huge space beyond.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special pretend power that can do amazing things, like lighting dark places or opening sealed doors.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue near the start of a story that hints at what will matter later.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find, fix, or deliver something important.",
        )
    ],
    "space": [
        QAItem(
            question="What is a spaceship?",
            answer="A spaceship is a vehicle that travels through space.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [q for key in ("space", "magic", "foreshadowing", "quest") for q in WORLD_KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_fix(P,Q,M) :- place(P), quest(Q), magic(M), compatible(P,Q,M).

compatible(P,signal,lamp) :- place(P).
compatible(P,crystal,wand) :- place(P), supports_magic(P).
compatible(P,garden,compass) :- place(P), supports_repair(P).

valid_story(P,Q,M) :- quest_fix(P,Q,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if "repair" in SETTINGS[pid].affords:
            lines.append(asp.fact("supports_repair", pid))
        if "scan" in SETTINGS[pid].affords or "launch" in SETTINGS[pid].affords:
            lines.append(asp.fact("supports_magic", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_fix/3."))
    return sorted(set(asp.atoms(model, "quest_fix")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with magic, foreshadowing, and a quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    if args.quest and args.magic:
        if (args.place, args.quest, args.magic) not in valid_combos():
            raise StoryError(explain_rejection(QUESTS[args.quest], MAGICS[args.magic]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.magic is None or c[2] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, magic = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, magic=magic, name=name, gender=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], MAGICS[params.magic], params.name, params.gender, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.magical:
            bits.append("magical=True")
        if e.hinting:
            bits.append("hinting=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  clue_seen={world.clue_seen}")
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
    StoryParams(place="orbital_station", quest="signal", magic="lamp", name="Nina", gender="girl", trait="curious"),
    StoryParams(place="moon_base", quest="crystal", magic="wand", name="Kai", gender="boy", trait="brave"),
    StoryParams(place="starport", quest="garden", magic="compass", name="Mila", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_fix/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, magic) combos:\n")
        for row in combos:
            print("  ", row)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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

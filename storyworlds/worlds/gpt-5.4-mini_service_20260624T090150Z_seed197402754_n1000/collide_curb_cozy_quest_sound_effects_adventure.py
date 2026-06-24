#!/usr/bin/env python3
"""
A small adventure storyworld about a quest, sound effects, and a curb mishap
that leads to a cozy fix.

A child goes on a quest with a little cart or bike, collides with a curb, hears
a dramatic sound effect, then finds a cozy, safer way to continue.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the neighborhood curb"
    soundy: bool = True
    cozy_spot: str = "a cozy porch"
    afford: set[str] = field(default_factory=lambda: {"quest"})


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    risk: str
    allows_curb_collision: bool
    fix: str
    sound: str


@dataclass
class ComfortGear:
    id: str
    label: str
    covers: str
    cozy_phrase: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "sidewalk": Setting(place="the sidewalk", cozy_spot="a cozy porch", afford={"quest"}),
    "yard": Setting(place="the front yard path", cozy_spot="the warm doorstep", afford={"quest"}),
    "lane": Setting(place="the lane by the curb", cozy_spot="a cozy bench", afford={"quest"}),
}

QUESTS = {
    "map": QuestItem(
        id="map",
        label="quest map",
        phrase="a folded quest map",
        risk="slipped off course",
        allows_curb_collision=True,
        fix="walk carefully around the curb",
        sound="tap-tap",
    ),
    "toycart": QuestItem(
        id="toycart",
        label="little cart",
        phrase="a little cart for the quest",
        risk="bumped hard",
        allows_curb_collision=True,
        fix="lift the front wheels over the curb",
        sound="clatter-clack",
    ),
    "bike": QuestItem(
        id="bike",
        label="small bike",
        phrase="a small bike with bright spokes",
        risk="wobbled",
        allows_curb_collision=True,
        fix="slow down before the curb",
        sound="whirr-bump",
    ),
}

COMFORT = {
    "blanket": ComfortGear(
        id="blanket",
        label="a soft blanket",
        covers="shoulders",
        cozy_phrase="wrapped up warm",
        fixes={"shiver", "scared"},
    ),
    "hoodie": ComfortGear(
        id="hoodie",
        label="a cozy hoodie",
        covers="back",
        cozy_phrase="snug as a kitten",
        fixes={"shiver", "scared"},
    ),
    "cushion": ComfortGear(
        id="cushion",
        label="a puffy cushion",
        covers="seat",
        cozy_phrase="comfortable and calm",
        fixes={"bump", "ache"},
    ),
}

NAMES = ["Mila", "Noah", "Zoe", "Leo", "Ava", "Maya", "Theo", "Finn"]
GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["brave", "curious", "lively", "cheerful", "spirited"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    comfort: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def quest_at_risk(q: QuestItem) -> bool:
    return q.allows_curb_collision


def select_comfort(q: QuestItem) -> Optional[ComfortGear]:
    if q.id == "toycart":
        return COMFORT["cushion"]
    if q.id == "bike":
        return COMFORT["hoodie"]
    if q.id == "map":
        return COMFORT["blanket"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for qid, q in QUESTS.items():
            for gid, g in COMFORT.items():
                if quest_at_risk(q) and select_comfort(q) and select_comfort(q).id == gid:
                    out.append((s, qid, gid))
    return out


class WorldRun:
    def __init__(self, world: World) -> None:
        self.world = world

    def act_begin(self, hero: Entity, parent: Entity, q: QuestItem, item: Entity) -> None:
        self.world.say(
            f"{hero.id} was on a quest with {hero.pronoun('possessive')} {q.label}. "
            f"{hero.pronoun().capitalize()} and {hero.pronoun('possessive')} {parent.type} were ready for adventure."
        )
        self.world.say(
            f"Along the way, {hero.id} heard {q.sound}! The little quest felt exciting and new."
        )

    def act_collision(self, hero: Entity, q: QuestItem, item: Entity) -> None:
        hero.meters["stopped"] = 1
        hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        self.world.say(
            f"Then, {hero.id} tried to keep going, but {hero.pronoun('possessive')} {q.label} collided with the curb. "
            f"Thunk! The little {q.label} gave a {q.sound} and wobbled to a stop."
        )
        self.world.say(
            f"{hero.id} felt a tiny jolt and looked at the curb, suddenly not so cozy anymore."
        )

    def act_fix(self, hero: Entity, parent: Entity, q: QuestItem, comfort: ComfortGear) -> None:
        hero.memes["worry"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        self.world.say(
            f"{parent.pronoun().capitalize()} smiled and offered {comfort.label}. "
            f"\"Let's make this cozy and try {q.fix},\" {parent.pronoun()} said."
        )
        self.world.say(
            f"{hero.id} nodded, got {comfort.cozy_phrase}, and followed the plan. "
            f"Soon the curb was no problem at all."
        )

    def act_ending(self, hero: Entity, parent: Entity, q: QuestItem, comfort: ComfortGear, setting: Setting) -> None:
        self.world.say(
            f"In the end, {hero.id} kept going on the quest near {setting.place}, "
            f"{hero.pronoun('possessive')} {q.label} safe and steady. "
            f"{hero.id} and {parent.pronoun('possessive')} {parent.type} laughed as the day felt cozy again."
        )
        self.world.say(
            f"Every step sounded soft and happy now, like the adventure had found its warm ending."
        )


def tell(setting: Setting, q: QuestItem, comfort: ComfortGear, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    item = world.add(Entity(id="quest_item", type=q.label, label=q.label, phrase=q.phrase, owner=hero.id))
    run = WorldRun(world)

    world.say(
        f"{name} was a {trait} {gender} who loved adventure quests."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {hero.pronoun('possessive')} {q.phrase} and set out toward {setting.place}."
    )
    world.para()
    run.act_begin(hero, parent, q, item)
    run.act_collision(hero, q, item)
    world.para()
    run.act_fix(hero, parent, q, comfort)
    run.act_ending(hero, parent, q, comfort, setting)

    world.facts.update(hero=hero, parent=parent, quest=q, comfort=comfort, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, q, comfort = f["hero"], f["parent"], f["quest"], f["comfort"]
    return [
        'Write a short adventure story for a child that includes a quest, a curb, and a cozy fix.',
        f"Tell a gentle adventure about {hero.id} and {hero.pronoun('possessive')} {q.label} when they collide with a curb and then get help from {parent.pronoun('possessive')} {comfort.label}.",
        f"Write a cozy quest story that uses the sound effect {q.sound} and ends with the curb no longer causing trouble.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, q, comfort = f["hero"], f["parent"], f["quest"], f["comfort"]
    return [
        QAItem(
            question=f"What was {hero.id} doing at the start of the story?",
            answer=f"{hero.id} was on a quest with {hero.pronoun('possessive')} {q.label}.",
        ),
        QAItem(
            question=f"What happened when {hero.id} reached the curb?",
            answer=f"{hero.id}'s {q.label} collided with the curb, making a loud {q.sound} sound.",
        ),
        QAItem(
            question=f"How did {parent.id} help make the adventure cozy again?",
            answer=f"{parent.pronoun().capitalize()} offered {comfort.label} and helped {hero.id} keep going safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curb?",
            answer="A curb is the raised edge beside a road or sidewalk that helps mark the boundary of the street.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like bang, clatter, or whoosh that help you imagine the noise something makes.",
        ),
        QAItem(
            question="What does cozy mean?",
            answer="Cozy means warm, comfortable, and pleasant in a way that makes someone feel safe and snug.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or mission where someone goes looking for something or trying to do an important task.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
quest(Q) :- quest_fact(Q).
comfort(C) :- comfort_fact(C).

valid(S,Q,C) :- setting_fact(S), quest_fact(Q), comfort_fact(C), curb_risk(Q), fix_for(Q,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for qid in QUESTS:
        lines.append(asp.fact("quest_fact", qid))
        lines.append(asp.fact("curb_risk", qid))
    for cid in COMFORT:
        lines.append(asp.fact("comfort_fact", cid))
    lines.append(asp.fact("fix_for", "map", "blanket"))
    lines.append(asp.fact("fix_for", "toycart", "cushion"))
    lines.append(asp.fact("fix_for", "bike", "hoodie"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: quest, curb, cozy, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--comfort", choices=COMFORT)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting and args.quest and args.comfort:
        if (args.setting, args.quest, args.comfort) not in combos:
            raise StoryError("That quest and cozy fix do not fit together in this storyworld.")
    combos = [c for c in combos
              if (not args.setting or c[0] == args.setting)
              and (not args.quest or c[1] == args.quest)
              and (not args.comfort or c[2] == args.comfort)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, quest, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, comfort=comfort, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], COMFORT[params.comfort], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(setting="sidewalk", quest="map", comfort="blanket", name="Mila", gender="girl", parent="mother", trait="brave"),
    StoryParams(setting="yard", quest="toycart", comfort="cushion", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(setting="lane", quest="bike", comfort="hoodie", name="Ava", gender="girl", parent="mother", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

#!/usr/bin/env python3
"""
storyworlds/worlds/ramble_eieio_chalk_petting_zoo_quest_reconciliation.py
==========================================================================

A small comedy storyworld set at a petting zoo.

Seed tale sketch:
---
A child arrives at a petting zoo for a silly little quest: make a chalk path that
helps visitors find the gentlest goat. The child keeps rambling, because the quest
sounds serious and the child is not serious at all. Then a goat eats the chalk,
which makes the sign impossible, and everybody must pause for an awkward inner
monologue. In the end, the child and the keeper reconcile by turning the mistake
into a joke and drawing a new sign together.

World model:
---
- Physical meters track chalk pieces, smeared fur, and completed signs.
- Emotional memes track excitement, embarrassment, annoyance, laughter, and
  reconciliation.
- The story turns on a quest item, a misunderstanding, and a repaired friendship.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "keeper"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the petting zoo"
    afford: set[str] = field(default_factory=lambda: {"ramble", "eieio", "chalk"})


@dataclass
class QuestItem:
    label: str
    phrase: str
    risk: str
    remedy: str
    difficulty: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    child_name: str
    child_type: str
    keeper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes)}) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def gget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def set_meme(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def narrate_ramble(world: World, child: Entity, quest: QuestItem) -> None:
    add_meme(child, "excitement", 1)
    world.say(
        f"{child.id} rambled across the petting zoo path, trying to sound brave about the quest. "
        f"“I can do this, I can do this, I can totally do this,” {child.pronoun()} said, "
        f"which was exactly the kind of speech that made little goats stare."
    )
    world.say(
        f"The quest was simple in theory: use chalk to make a bright trail, follow the clue, "
        f"and find the gentlest goat near the hay bale."
    )


def narrate_setup(world: World, child: Entity, keeper: Entity, quest: QuestItem) -> None:
    world.say(
        f"At {world.setting.place}, {keeper.id} handed {child.pronoun('object')} a small box of {quest.label}. "
        f"It was meant for a neat trail, but {child.id} treated it like treasure."
    )
    world.say(
        f"{child.id} stared at the {quest.label} and had an inner monologue that was mostly just, "
        f"“Eieio, chalk, quest, do not drop the chalk, do not drop the chalk.”"
    )


def goat_eats_chalk(world: World, child: Entity, goat: Entity, quest: QuestItem) -> None:
    if goat.pronoun() != "it":
        pass
    add_meter(goat, "chalk", 1)
    add_meter(child, "lost_chalk", 1)
    add_meme(child, "embarrassment", 1)
    add_meme(goat, "satisfaction", 1)
    world.say(
        f"Then a goat with the confidence of a tiny comedian leaned over and ate a piece of {quest.label}. "
        f"The chalk snapped, the trail wobbled, and the quest looked ridiculous in one second flat."
    )
    world.say(
        f"{child.id} froze and had a louder inner monologue this time: "
        f"“Oh no. Oh no. The goat chose the chalk. The goat has made a terrible but impressive decision.”"
    )


def narrate_conflict(world: World, child: Entity, keeper: Entity, quest: QuestItem) -> None:
    add_meme(keeper, "annoyance", 1)
    world.say(
        f"{keeper.id} tried very hard not to laugh, which made {keeper.pronoun()} look even more serious. "
        f"“We needed the chalk for the quest,” {keeper.pronoun()} said, though {keeper.pronoun()} was blinking like {keeper.pronoun()} wanted to smile."
    )
    world.say(
        f"{child.id} felt small and silly. The trail was ruined, the clue was blurry, and the petting zoo seemed to be giggling at the whole problem."
    )


def reconcile(world: World, child: Entity, keeper: Entity, goat: Entity, quest: QuestItem) -> None:
    add_meme(child, "embarrassment", -1)
    add_meme(child, "laughter", 1)
    add_meme(keeper, "annoyance", -1)
    add_meme(keeper, "laughter", 1)
    add_meme(child, "reconciliation", 1)
    add_meme(keeper, "reconciliation", 1)
    add_meter(child, "quest_progress", 1)
    add_meter(keeper, "quest_progress", 1)
    world.say(
        f"Then {child.id} took a breath and said, “Maybe the goat is part of the quest now.”"
    )
    world.say(
        f"{keeper.id} snorted. {keeper.pronoun().capitalize()} looked at the goat, then at the broken chalk, and finally laughed."
    )
    world.say(
        f"Together they drew a new sign with the last crumbs of chalk: a silly arrow, a smiling goat, and the words 'This way for the gentlest goat.' "
        f"The goat stood beside them like a proud little guard."
    )
    world.say(
        f"By the end, {child.id} and {keeper.id} were smiling again, and even the goat looked pleased with its part in the comedy."
    )


def tell(setting: Setting, quest: QuestItem, child_name: str, child_type: str, keeper_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        meters={"quest_progress": 0.0},
        memes={"excitement": 1.0},
    ))
    keeper = world.add(Entity(
        id=keeper_name,
        kind="character",
        type="keeper",
        label="the keeper",
        memes={"patience": 1.0},
    ))
    goat = world.add(Entity(
        id="Goat",
        kind="character",
        type="goat",
        label="the goat",
        memes={"curiosity": 1.0},
    ))
    chalk = world.add(Entity(
        id="Chalk",
        type="chalk",
        label="chalk",
        phrase="a box of chalk",
        owner=child.id,
        caretaker=keeper.id,
        meters={"pieces": 3.0},
    ))

    world.facts.update(child=child, keeper=keeper, goat=goat, chalk=chalk, quest=quest)

    narrate_setup(world, child, keeper, quest)
    world.para()
    narrate_ramble(world, child, quest)
    goat_eats_chalk(world, child, goat, quest)
    narrate_conflict(world, child, keeper, quest)
    world.para()
    reconcile(world, child, keeper, goat, quest)
    return world


SETTING = Setting()

QUESTS = {
    "sign": QuestItem(
        label="chalk",
        phrase="a chalk trail",
        risk="the trail could vanish",
        remedy="make a new sign",
        difficulty="small",
        clue="follow the smiling goat",
        tags={"chalk", "quest", "eieio"},
    )
}

CHILD_NAMES = ["Mina", "Theo", "Luca", "Piper", "Nora", "Ben"]
KEEPER_NAMES = ["Alex", "Riley", "Sam", "Jordan"]


def valid_combos() -> list[tuple[str, str]]:
    return [(SETTING.place, q) for q in QUESTS]


@dataclass
class _AspFact:
    pass


ASP_RULES = r"""
quest(Quest) :- quest_item(Quest).
can_run(Place, Quest) :- setting(Place), quest_item(Quest), place_supports(Place, Quest).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", SETTING.place))
    for quest_id, quest in QUESTS.items():
        lines.append(asp.fact("quest_item", quest_id))
        lines.append(asp.fact("quest_label", quest_id, quest.label))
        for tag in sorted(quest.tags):
            lines.append(asp.fact("tag", quest_id, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_run/2."))
    return sorted(set(asp.atoms(model, "can_run")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld at a petting zoo with a quest, chalk, and reconciliation.")
    ap.add_argument("--place", choices=[SETTING.place], default=None)
    ap.add_argument("--quest", choices=QUESTS, default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--keeper", default=None)
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
    if args.place and args.place != SETTING.place:
        raise StoryError("This world only takes place at the petting zoo.")
    quest_id = args.quest or rng.choice(list(QUESTS))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    keeper_name = args.keeper or rng.choice(KEEPER_NAMES)
    return StoryParams(
        place=SETTING.place,
        quest=quest_id,
        child_name=child_name,
        child_type=child_type,
        keeper_name=keeper_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    return [
        f'Write a funny story for young children set at a petting zoo about {child.id}, a rambling quest, and chalk.',
        f"Tell a comedy where {child.id} tries to finish a chalk quest, a goat eats the chalk, and everyone reconciles.",
        f'Write a short petting-zoo adventure that includes the words "ramble", "eieio", and "chalk".',
        f"Show an inner monologue where {child.id} worries about the chalk and then laughs at the goat's timing.",
        f"Make the ending a reconciliation with a silly sign for the quest {quest.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    goat = f["goat"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"What was {child.id} trying to do at {world.setting.place}?",
            answer=f"{child.id} was trying to finish a chalk quest at the petting zoo and make a path that would help visitors find the gentlest goat.",
        ),
        QAItem(
            question=f"Why did {child.id} keep talking to {self_name(child)}self in an inner monologue?",
            answer=f"{child.id} felt excited and nervous about the quest, so the inner monologue helped {child.pronoun('object')} keep track of the chalk and the steps.",
        ),
        QAItem(
            question=f"What ruined the first chalk trail?",
            answer=f"A goat ate a piece of chalk, which made the trail break apart and turned the quest into a funny mess.",
        ),
        QAItem(
            question=f"How did {child.id} and {keeper.id} fix the problem?",
            answer=f"They reconciled by laughing, using the last chalk crumbs, and drawing a new sign together for the quest.",
        ),
    ]


def self_name(ent: Entity) -> str:
    return ent.id


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chalk used for?",
            answer="Chalk is used to draw or write on boards, sidewalks, and signs, and it can make bright, dusty lines.",
        ),
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where children can gently visit and sometimes pet friendly animals.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop being upset and start feeling friendly again.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    quest = QUESTS[params.quest]
    world = tell(SETTING, quest, params.child_name, params.child_type, params.keeper_name)
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
    StoryParams(place="the petting zoo", quest="sign", child_name="Mina", child_type="girl", keeper_name="Alex"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show can_run/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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

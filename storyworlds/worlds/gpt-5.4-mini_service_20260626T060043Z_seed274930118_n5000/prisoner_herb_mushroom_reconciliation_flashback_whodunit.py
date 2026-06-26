#!/usr/bin/env python3
"""
A small whodunit storyworld about a prisoner, an herb, and a mushroom.

Premise:
- A prisoner in a little garden courtyard loses a prized herb.
- A mushroom stain, cap, or basket becomes an early clue.
- The story turns on a flashback that reveals who moved what and why.
- A reconciliation closes the mystery when the misunderstanding is repaired.

The world model tracks physical state in meters and social state in memes.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "warden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "guard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    setting: str
    prisoner_name: str
    prisoner_type: str
    keeper_name: str
    herb: str
    mushroom: str
    seed: Optional[int] = None


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    scent: str
    color: str
    fragile: bool = False


SETTINGS = {
    "courtyard": Setting(place="the courtyard", detail="The courtyard had stone tiles, a tiny herb bed, and one old bench."),
    "greenhouse": Setting(place="the greenhouse", detail="The greenhouse was warm and bright, with mist on the glass and pots on every shelf."),
    "cellar": Setting(place="the cellar garden", detail="The cellar garden was dim, but jars, baskets, and plant beds lined the walls."),
}

HERBS = {
    "basil": ObjectSpec(id="basil", label="basil", phrase="a small pot of fresh basil", scent="sweet", color="green"),
    "mint": ObjectSpec(id="mint", label="mint", phrase="a clipped bunch of mint", scent="cool", color="bright green"),
    "thyme": ObjectSpec(id="thyme", label="thyme", phrase="a tidy sprig of thyme", scent="earthy", color="soft green"),
}

MUSHROOMS = {
    "button": ObjectSpec(id="button", label="button mushroom", phrase="a pale button mushroom", scent="damp", color="white"),
    "morel": ObjectSpec(id="morel", label="morel mushroom", phrase="a wrinkled morel mushroom", scent="nutty", color="tan"),
    "oyster": ObjectSpec(id="oyster", label="oyster mushroom", phrase="a fan-shaped oyster mushroom", scent="woodsy", color="gray"),
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _bump_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = _meter(entity, key) + amount


def _bump_mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = _mem(entity, key) + amount


def _do_theft(world: World, prisoner: Entity, herb: Entity, mushroom: Entity) -> None:
    _bump_meter(herb, "missing")
    _bump_mem(prisoner, "fear")
    _bump_mem(prisoner, "guilt")
    _bump_meter(mushroom, "seen")
    world.say(
        f"At first, the {prisoner.type} named {prisoner.id} noticed that {herb.phrase} was missing from the shelf."
    )
    world.say(
        f"Near the pot, there was only {mushroom.phrase}, and that odd little clue made the whole room feel quiet."
    )


def _flashback(world: World, prisoner: Entity, keeper: Entity, herb: Entity, mushroom: Entity) -> None:
    _bump_mem(prisoner, "memory")
    _bump_mem(keeper, "memory")
    world.say(
        f"Then a flashback came back to {prisoner.id}."
    )
    world.say(
        f"Earlier, {prisoner.id} had seen {keeper.id} carry {mushroom.phrase} from the damp crate because the mushroom shelf was tipping."
    )
    world.say(
        f"The same hands had moved {herb.phrase} only to keep it from getting crushed, not to take it away."
    )


def _mystery_turn(world: World, prisoner: Entity, keeper: Entity, herb: Entity, mushroom: Entity) -> None:
    _bump_mem(prisoner, "curiosity")
    _bump_mem(prisoner, "understanding")
    world.say(
        f"{prisoner.id} looked again and noticed a smear of soil on the crate and a clean ring where the pot had been."
    )
    world.say(
        f"The clues fit together: the mushroom had been the reason for the move, and the herb had only been tucked aside for safety."
    )


def _reconciliation(world: World, prisoner: Entity, keeper: Entity, herb: Entity, mushroom: Entity) -> None:
    _bump_mem(prisoner, "relief")
    _bump_mem(prisoner, "reconciliation")
    _bump_mem(keeper, "reconciliation")
    herb.meters["missing"] = 0.0
    world.say(
        f"{prisoner.id} apologized for the sharp look."
    )
    world.say(
        f"{keeper.id} smiled, set {herb.phrase} back in place, and said the truth out loud so there would be no more guesswork."
    )
    world.say(
        f"By the end, the mystery was solved, the herb was safe, and the prisoner and the keeper were friends again."
    )


def tell_story(setting: Setting, prisoner: Entity, keeper: Entity, herb: Entity, mushroom: Entity) -> World:
    world = World(setting)
    world.add(prisoner)
    world.add(keeper)
    world.add(herb)
    world.add(mushroom)

    world.say(
        f"{setting.detail} There lived a {prisoner.type} named {prisoner.id}, a careful keeper named {keeper.id}, and one precious pot of {herb.label}."
    )
    world.say(
        f"{prisoner.id} loved the sharp smell of {herb.label}, so when it vanished, {prisoner.pronoun('subject')} felt sure somebody had taken it."
    )

    world.para()
    _do_theft(world, prisoner, herb, mushroom)

    world.para()
    _flashback(world, prisoner, keeper, herb, mushroom)

    world.para()
    _mystery_turn(world, prisoner, keeper, herb, mushroom)

    world.para()
    _reconciliation(world, prisoner, keeper, herb, mushroom)

    world.facts.update(
        setting=setting,
        prisoner=prisoner,
        keeper=keeper,
        herb=herb,
        mushroom=mushroom,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prisoner: Entity = f["prisoner"]
    herb: Entity = f["herb"]
    mushroom: Entity = f["mushroom"]
    return [
        f"Write a short whodunit for a child about {prisoner.id}, {herb.label}, and {mushroom.label}.",
        f"Tell a mystery story where a prisoner thinks {herb.phrase} was stolen, but a flashback explains the mushroom clue.",
        f"Write a gentle detective story that ends with reconciliation after the herb is returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    prisoner: Entity = f["prisoner"]
    keeper: Entity = f["keeper"]
    herb: Entity = f["herb"]
    mushroom: Entity = f["mushroom"]
    return [
        QAItem(
            question=f"Who thought {herb.phrase} had been taken?",
            answer=f"{prisoner.id} thought {herb.label} had been taken because it was missing from the shelf.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was {mushroom.phrase}, which showed that the strange move had something to do with the mushroom shelf.",
        ),
        QAItem(
            question="What did the flashback reveal?",
            answer=f"The flashback revealed that {keeper.id} moved the herb and the mushroom to keep them safe, not to steal them.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The story ended with reconciliation: {prisoner.id} apologized, {keeper.id} explained the truth, and the herb went back in place.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What is an herb?",
        answer="An herb is a plant with a strong smell or taste that people often use in cooking.",
    ),
    QAItem(
        question="What is a mushroom?",
        answer="A mushroom is a kind of fungus that can grow in damp places and often looks like a small umbrella or cap.",
    ),
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is when a story briefly shows something that happened earlier so the reader can understand the present better.",
    ),
    QAItem(
        question="What does reconciliation mean?",
        answer="Reconciliation means people stop being upset and make peace again.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HERBS:
        lines.append(asp.fact("herb", hid))
    for mid in MUSHROOMS:
        lines.append(asp.fact("mushroom", mid))
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting(S).
herb(H) :- herb(H).
mushroom(M) :- mushroom(M).

mystery(H, M) :- herb(H), mushroom(M).
reconcile(H) :- herb(H).
#show mystery/2.
#show reconcile/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mystery/2.\n#show reconcile/1."))
    if model is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP program parsed and solved.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit storyworld with prisoner, herb, mushroom, flashback, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prisoner-name")
    ap.add_argument("--prisoner-type", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("--keeper-name")
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--mushroom", choices=MUSHROOMS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    herb = args.herb or rng.choice(list(HERBS))
    mushroom = args.mushroom or rng.choice(list(MUSHROOMS))
    prisoner_type = args.prisoner_type or rng.choice(["boy", "girl", "man", "woman"])
    prisoner_name = args.prisoner_name or rng.choice(["Ivy", "Milo", "Nina", "Otto", "Pia", "Rae", "Tess", "Uma"])
    keeper_name = args.keeper_name or rng.choice(["Mara", "Evan", "Jules", "Sana", "Noel", "Rin"])
    return StoryParams(
        setting=setting,
        prisoner_name=prisoner_name,
        prisoner_type=prisoner_type,
        keeper_name=keeper_name,
        herb=herb,
        mushroom=mushroom,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    prisoner = Entity(id=params.prisoner_name, kind="character", type=params.prisoner_type)
    keeper = Entity(id=params.keeper_name, kind="character", type="warden")
    herb_spec = HERBS[params.herb]
    mushroom_spec = MUSHROOMS[params.mushroom]
    herb = Entity(id=herb_spec.id, type="herb", label=herb_spec.label, phrase=herb_spec.phrase, owner=keeper.id)
    mushroom = Entity(id=mushroom_spec.id, type="mushroom", label=mushroom_spec.label, phrase=mushroom_spec.phrase)

    world = tell_story(setting, prisoner, keeper, herb, mushroom)
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
        print(asp_program("#show mystery/2.\n#show reconcile/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery/2.\n#show reconcile/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("courtyard", "Ivy", "girl", "Mara", "basil", "button"),
            StoryParams("greenhouse", "Milo", "boy", "Evan", "mint", "morel"),
            StoryParams("cellar", "Nina", "woman", "Sana", "thyme", "oyster"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.prisoner_name}: {p.herb} / {p.mushroom} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

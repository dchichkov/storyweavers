#!/usr/bin/env python3
"""
A small folk-tale storyworld about a lifter, a taco, a quest, and a humorous fix.

Seed tale:
---
In a little village, a strong lifter named Pip loved carrying heavy things and showing
off for the townsfolk. One morning, Pip found a tiny taco on a stone bench. The taco
belonged to the village feast, and the baker said it had to stay whole until supper.

Pip wanted to carry the taco to the hilltop shrine as an offering for a quest, but
the taco was delicate and could fall apart. Pip bragged that strong hands could fix
everything, yet the baker warned that the shells were thin and the filling would spill.

So Pip tried to march up the hill at once, but the taco tipped in the basket and
made a silly mess. Pip laughed, the baker laughed too, and then the clever fox said
to wrap the taco in a warm cloth and carry it in a shallow tray. Pip did that, and
the taco arrived safe, making the whole village cheer.

This script models that tale as a tiny causal world: desire, warning, mishap,
humor, and a quest-completing compromise.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the village green"


@dataclass
class Quest:
    id: str
    goal: str
    climb: str
    surprise: str
    ending: str
    tag: str = "quest"


@dataclass
class Cover:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


QUESTS = {
    "hill_shrine": Quest(
        id="hill_shrine",
        goal="carry the taco to the hilltop shrine",
        climb="climb the winding hill",
        surprise="a gust of wind",
        ending="the shrine bell rang for a happy thanks",
        tag="quest",
    ),
}

COVERS = {
    "cloth_tray": Cover(
        id="cloth_tray",
        label="a warm cloth and a shallow tray",
        prep="wrap the taco in a warm cloth and set it in a shallow tray",
        tail="wrapped the taco in a warm cloth and carried it in a shallow tray",
        guards={"spill"},
    ),
}

GIRL_NAMES = ["Mina", "Tula", "Nora", "Ivy", "Lina"]
BOY_NAMES = ["Pip", "Taro", "Bram", "Otto", "Rumi"]
TRAITS = ["strong", "cheerful", "curious", "boastful", "lively"]


def story_intro(hero: Entity, taco: Entity, quest: Quest) -> list[str]:
    return [
        f"{hero.id} was a {hero.traits[0]} lifter who loved to carry heavy things around {WORLD_PLACE}.",
        f"One morning, {hero.id} found {hero.pronoun('possessive')} taco on a stone bench and decided it should help with a {quest.goal}.",
        f"{hero.id} liked the taco because it smelled good and made the day feel funny and bright.",
    ]


def predict_spill(world: World, hero: Entity, taco: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["rush"] = sim.get(hero.id).memes.get("rush", 0) + 1
    sim.get(taco.id).meters["fragile"] = sim.get(taco.id).meters.get("fragile", 0) + 1
    return sim.get(taco.id).meters.get("spill", 0) >= THRESHOLD


def narrate_warning(world: World, hero: Entity, taco: Entity, quest: Quest) -> None:
    world.say(
        f'"If you hurry up the {quest.climb}, your taco may tumble apart," said the baker.'
    )
    world.facts["warning"] = True


def narrate_misstep(world: World, hero: Entity, taco: Entity, quest: Quest) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    taco.meters["spill"] = taco.meters.get("spill", 0) + 1
    world.say(
        f"But {hero.id} laughed and said strong hands could fix everything, then marched toward the hill."
    )
    world.say(
        f"At the first bend, {quest.surprise} puffed by, and the taco tipped right over with a silly splat."
    )
    taco.meters["messy"] = taco.meters.get("messy", 0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1


def narrate_fix(world: World, hero: Entity, taco: Entity, quest: Quest) -> Optional[Cover]:
    cover = COVERS["cloth_tray"]
    tray = world.add(Entity(id=cover.id, type="tray", label=cover.label, kind="thing"))
    taco.carried_by = hero.id
    world.say(
        f"The clever fox gave a wise grin and said, '{cover.prep}.'"
    )
    world.say(
        f"{hero.id} did that, and soon {cover.tail} instead of dropping it."
    )
    taco.meters["spill"] = 0
    taco.meters["messy"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    world.facts["cover"] = tray
    return tray


def narrate_resolution(world: World, hero: Entity, taco: Entity, quest: Quest) -> None:
    world.say(
        f"By the time {hero.id} reached the hilltop, the taco stayed whole, the village cheered, and {quest.ending}."
    )
    hero.memes["pride"] = 0
    hero.memes["stubborn"] = 0
    hero.memes["resolved"] = 1


def tell_story(hero_name: str, hero_type: str, trait: str, parent_type: str = "baker") -> World:
    world = World(Setting())
    taco = world.add(Entity(
        id="Taco",
        kind="thing",
        type="taco",
        label="taco",
        phrase="a tiny taco",
        owner=hero_name,
        caretaker=parent_type,
        meters={"spill": 0.0, "messy": 0.0},
    ))
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=[trait, "stubborn"],
        memes={"joy": 0.0, "pride": 0.0, "stubborn": 0.0, "humor": 0.0},
    ))
    baker = world.add(Entity(id="Baker", kind="character", type=parent_type, label="the baker"))

    quest = QUESTS["hill_shrine"]

    world.say(f"{hero.id} was a {trait} lifter in {WORLD_PLACE}.")
    world.say(f"{hero.id} loved to carry big crates, but one day {hero.pronoun('possessive')} attention fell on a tiny taco.")
    world.say(f"The taco belonged to the feast, yet it also seemed perfect for a {quest.goal}.")

    world.para()
    world.say(f"That morning, {hero.id} went to {WORLD_PLACE} with {baker.label}.")
    world.say(f"{hero.id} wanted to {quest.goal}, but the baker worried the taco would not survive the climb.")
    narrate_warning(world, hero, taco, quest)
    narrate_misstep(world, hero, taco, quest)

    world.para()
    narrate_fix(world, hero, taco, quest)
    narrate_resolution(world, hero, taco, quest)

    world.facts.update(
        hero=hero,
        taco=taco,
        baker=baker,
        quest=quest,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f"Write a short folk tale for children about a lifter named {hero.id}, a taco, and a quest.",
        f"Tell a humorous story where {hero.id} tries to {quest.goal} but learns a safer way.",
        f"Write a simple folk tale with a small mistake, a funny moment, and a happy ending involving a taco.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, taco, baker, quest = f["hero"], f["taco"], f["baker"], f["quest"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.traits[0]} lifter who tried to take the taco on a quest.",
        ),
        QAItem(
            question=f"Why did the baker warn {hero.id}?",
            answer=f"The baker warned {hero.id} because the taco was delicate and might spill on the hill climb.",
        ),
        QAItem(
            question=f"What funny thing happened on the way to the hill?",
            answer=f"A gust of wind tipped the taco over, and it made a silly mess that made everyone laugh.",
        ),
        QAItem(
            question=f"How did {hero.id} finish the quest safely?",
            answer="The fox suggested wrapping the taco in a warm cloth and carrying it in a shallow tray, and that kept it whole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a taco?",
            answer="A taco is a folded food with filling inside a shell or soft bread, and it can be tasty but a little messy.",
        ),
        QAItem(
            question="What does a lifter do?",
            answer="A lifter is a strong person who picks up and carries heavy things.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task someone does to reach a goal or bring back something important.",
        ),
        QAItem(
            question="Why can warm cloth help carry food?",
            answer="A warm cloth can help hold something gently so it does not slip or break apart as easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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


WORLD_PLACE = "the village green"


ASP_RULES = r"""
hero(X) :- hero_name(X).
taco(T) :- taco_id(T).
quest(Q) :- quest_id(Q).

at_risk(T,Q) :- taco(T), quest(Q), fragile(T), hill_quest(Q).
needs_cover(T,Q) :- at_risk(T,Q), spill_risk(T).
has_fix(T,Q) :- needs_cover(T,Q), cover(C), guards(C, spill).

valid_story(H,T,Q) :- hero(H), taco(T), quest(Q), at_risk(T,Q), has_fix(T,Q).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero_name", "Pip"),
        asp.fact("taco_id", "Taco"),
        asp.fact("quest_id", "hill_shrine"),
        asp.fact("fragile", "Taco"),
        asp.fact("hill_quest", "hill_shrine"),
        asp.fact("spill_risk", "Taco"),
        asp.fact("cover", "cloth_tray"),
        asp.fact("guards", "cloth_tray", "spill"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("Pip", "Taco", "hill_shrine")}
    clingo = set(asp_valid_stories())
    if py == clingo:
        print("OK: ASP and Python parity match.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(clingo))
    return 1


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about a lifter, a taco, and a quest.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    hero_type = "boy" if params.gender == "boy" else "girl"
    world = tell_story(params.name, hero_type, params.trait)
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
    StoryParams(name="Pip", gender="boy", trait="strong"),
    StoryParams(name="Mina", gender="girl", trait="curious"),
    StoryParams(name="Bram", gender="boy", trait="boastful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

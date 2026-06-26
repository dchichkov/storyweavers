#!/usr/bin/env python3
"""
A folk-tale storyworld about a small quest, a drawer, and a child who sobs
until a wise helper turns the search into a gentle puzzle.
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
    caretakers: list[str] = field(default_factory=list)
    in_drawer: Optional[str] = None
    openable: bool = False
    opened: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0, "tidy": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "sob": 0.0, "fear": 0.0, "relief": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage"
    ambience: str = "warm"
    hides: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    object_label: str
    object_phrase: str
    search_place: str
    clue: str
    turn: str
    resolution: str
    risk: str
    has_drawer: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    name: str
    gender: str
    helper: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.events = list(self.events)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


SETTINGS = {
    "cottage": Setting(place="the little cottage", ambience="warm", hides={"drawer"}),
    "forest_hut": Setting(place="the forest hut", ambience="shadowed", hides={"drawer"}),
    "granary": Setting(place="the old granary", ambience="dusty", hides={"drawer"}),
}

QUESTS = {
    "lost_ribbon": Quest(
        id="lost_ribbon",
        title="The Lost Ribbon",
        object_label="ribbon",
        object_phrase="a blue ribbon with a silver thread",
        search_place="drawer",
        clue="the ribbon had been tucked in the top drawer",
        turn="the child stopped sobbing long enough to listen",
        resolution="the ribbon was found beneath a folded scarf",
        risk="the child feared it was gone forever",
        tags={"drawer", "sob", "quest"},
    ),
    "lamp_key": Quest(
        id="lamp_key",
        title="The Lamp Key",
        object_label="key",
        object_phrase="a small brass key for the lamp chest",
        search_place="drawer",
        clue="the key had been hidden in a drawer behind an old comb",
        turn="the helper asked a careful question",
        resolution="the key glittered under a handkerchief",
        risk="the family could not light the lamp without it",
        tags={"drawer", "sob", "quest"},
    ),
    "seed_pouch": Quest(
        id="seed_pouch",
        title="The Seed Pouch",
        object_label="pouch",
        object_phrase="a little pouch of garden seeds",
        search_place="drawer",
        clue="the pouch had fallen to the back of the drawer",
        turn="the child wiped tears and looked again",
        resolution="the pouch lay safe beside a wooden spoon",
        risk="the spring garden would not begin without it",
        tags={"drawer", "sob", "quest"},
    ),
}

NAMES_GIRL = ["Mira", "Lina", "Nora", "Elsa", "Ivy", "Tessa"]
NAMES_BOY = ["Oren", "Pavel", "Bram", "Jonah", "Soren", "Milo"]
HELPERS = ["grandmother", "mother", "father", "old wise woman", "old wise man"]


def can_drawer_hide(quest: Quest) -> bool:
    return quest.search_place == "drawer"


def reasonableness_gate(quest: Quest) -> bool:
    return can_drawer_hide(quest) and "drawer" in quest.tags and "quest" in quest.tags


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    qid = args.quest or rng.choice(list(QUESTS))
    quest = QUESTS[qid]
    if not reasonableness_gate(quest):
        raise StoryError("That quest does not fit this drawer tale.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(quest=qid, name=name, gender=gender, helper=helper, setting=setting)


def _intro(world: World, hero: Entity, helper: Entity, quest: Quest, drawer: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there lived a little {hero.type} named {hero.id}, "
        f"who loved the old family things and the stories they held."
    )
    world.say(
        f"One day, {hero.id} longed for {quest.object_phrase}, but it could not be found."
    )
    world.say(
        f"The {helper.label} said, 'There is a quest for us now. Let us search the drawer with patient hands.'"
    )
    drawer.opened = True
    world.facts["opened_drawer"] = True


def _sob(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["sob"] += 1.0
    hero.memes["fear"] += 1.0
    world.say(
        f"{hero.id} began to sob, because {quest.risk}."
    )
    world.say(
        f"The tears were small, but they made the room feel heavy."
    )


def _search(world: World, hero: Entity, helper: Entity, drawer: Entity, quest: Quest) -> None:
    world.para()
    world.say(
        f"The {helper.label} knelt beside {hero.id} and said, 'First we look where little things like to hide: in the drawer.'"
    )
    world.say(
        f"{hero.id} wiped {hero.pronoun('possessive')} cheeks and peered inside."
    )
    world.say(
        f"{quest.clue.capitalize()}."
    )
    hero.memes["hope"] += 1.0


def _turn(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    world.para()
    hero.memes["sob"] = 0.0
    hero.memes["hope"] += 1.0
    world.say(
        f"{quest.turn.capitalize()}, and the search became a true quest."
    )
    world.say(
        f"Under a folded cloth and behind an old trinket, the {quest.object_label} waited quietly."
    )
    world.say(
        f"{helper.label.capitalize()} smiled, for the answer had been hiding in plain sight."
    )


def _resolve(world: World, hero: Entity, helper: Entity, quest: Quest) -> None:
    hero.memes["relief"] += 1.0
    hero.meters["tidy"] += 1.0
    world.para()
    world.say(
        f"{quest.resolution.capitalize()}, and {hero.id} laughed through the last wet shine of tears."
    )
    world.say(
        f"{hero.id} hugged the {helper.label}, and the little house felt bright again."
    )
    world.say(
        f"By evening, the drawer was shut neatly, the treasure was safe, and the quest was done."
    )


def tell(setting: Setting, quest: Quest, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_type))
    drawer = world.add(Entity(id="Drawer", kind="thing", type="drawer", label="drawer", openable=True))

    drawer.opened = False
    world.facts.update(hero=hero, helper=helper, quest=quest, drawer=drawer, setting=setting)

    world.say(f"Once upon a time, in {setting.place}, there was a quest hidden among the ordinary things.")
    _intro(world, hero, helper, quest, drawer)
    _sob(world, hero, quest)
    _search(world, hero, helper, drawer, quest)
    _turn(world, hero, helper, quest)
    _resolve(world, hero, helper, quest)
    return world


def generation_prompts(world: World) -> list[str]:
    q = world.facts["quest"]
    hero = world.facts["hero"]
    return [
        f"Write a folk tale about {hero.id}, a drawer, and a small quest for {q.object_label}.",
        f"Tell a gentle story where someone sobs at the loss of {q.object_phrase} and a wise helper finds it in a drawer.",
        f"Create a simple quest story in a cottage where tears turn into relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and the wise {helper.label} who helped with the quest.",
        ),
        QAItem(
            question=f"Why did {hero.id} sob?",
            answer=f"{hero.id} sobbed because {quest.risk}, and the lost {quest.object_label} could not be found at first.",
        ),
        QAItem(
            question=f"Where was the treasure found?",
            answer=f"It was found in the drawer, just where the helper said to look.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The tears turned into relief, the quest was finished, and the lost {quest.object_label} was safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a drawer?",
            answer="A drawer is a sliding box in a table, desk, or chest where people keep small things.",
        ),
        QAItem(
            question="What does it mean to sob?",
            answer="To sob means to cry hard, with shaky breaths and tears that come again and again.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or journey to find something or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} opened={e.opened} in_drawer={e.in_drawer} meters={e.meters} memes={e.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(quest="lost_ribbon", name="Mira", gender="girl", helper="grandmother", setting="cottage"),
    StoryParams(quest="lamp_key", name="Oren", gender="boy", helper="mother", setting="forest_hut"),
    StoryParams(quest="seed_pouch", name="Lina", gender="girl", helper="old wise woman", setting="granary"),
]


ASP_RULES = r"""
quest(q) :- quest_id(q).
drawer_story(q) :- quest(q), search_place(q, drawer).
valid(q) :- drawer_story(q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hide in sorted(setting.hides):
            lines.append(asp.fact("hides", sid, hide))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_id", qid))
        lines.append(asp.fact("search_place", qid, q.search_place))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", qid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_quests() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((qid,) for qid, q in QUESTS.items() if reasonableness_gate(q))
    cl = asp_valid_quests()
    if py == cl:
        print(f"OK: ASP gate matches Python gate ({len(py)} quests).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", py)
    print("asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale quest in a drawer, with sobs and a wise helper.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--setting", choices=SETTINGS)
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


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    hero_type = "girl" if params.gender == "girl" else "boy"
    helper_type = params.helper
    hero_name = params.name
    world = tell(setting, quest, hero_name, hero_type, helper_type)
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
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

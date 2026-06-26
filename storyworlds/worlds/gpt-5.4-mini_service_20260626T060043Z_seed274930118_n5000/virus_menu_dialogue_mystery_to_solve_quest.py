#!/usr/bin/env python3
"""
storyworlds/worlds/virus_menu_dialogue_mystery_to_solve_quest.py
=================================================================

A small pirate-tale story world about a shipboard mystery: someone on the crew
is getting sick, the menu is involved, and the pirates have to solve the clue
before the voyage can continue.

Premise seed:
- virus
- menu
- Dialogue
- Mystery to Solve
- Quest
- Pirate Tale style

The story is built from a live world model with physical meters and emotional
memes. The world is intentionally small and constraint-checked: the menu must
actually be relevant to the sickness mystery, and the quest must end in a
reasonable fix.

The narration style stays child-facing, concrete, and pirate-like.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["sick", "clean", "clue", "solution", "fresh"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "bravery", "hope", "fear", "relief", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
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
    place: str = "the ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    symptom: str
    culprit: str
    clue: str
    spread: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestGear:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    symptom = world.facts["mystery"].symptom
    for c in world.characters():
        if c.meters["sick"] < THRESHOLD:
            continue
        sig = ("spread", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["worry"] += 1
        out.append(f"{c.id} sniffled and looked pale.")
        for other in world.characters():
            if other.id == c.id:
                continue
            other.memes["fear"] += 0.2
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    menu = world.get("menu")
    if menu.meters["clue"] >= THRESHOLD and ("clue", menu.id) not in world.fired:
        world.fired.add(("clue", menu.id))
        out.append("The menu looked like an important clue.")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.get("menu").meters["clean"] >= THRESHOLD and ("solution", "menu") not in world.fired:
        world.fired.add(("solution", "menu"))
        for c in world.characters():
            c.memes["hope"] += 1
        out.append("The crew felt hopeful once the menu was clean and safe.")
    return out


RULES = [_r_spread, _r_clue, _r_solution]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_reasonable_mystery() -> tuple[Setting, Mystery, QuestGear]:
    setting = Setting(place="the pirate ship", affords={"search", "wash", "share"})
    mystery = Mystery(
        id="menu_virus",
        symptom="sniffles",
        culprit="virus",
        clue="menu",
        spread="touching the menu",
        fix="wash the menu and keep sick hands away from the galley",
        tags={"virus", "menu", "mystery", "quest"},
    )
    gear = QuestGear(
        id="soap_and_rag",
        label="a bowl of warm water, soap, and a clean rag",
        prep="bring a bowl of warm water, soap, and a clean rag to the galley",
        tail="washed the menu until it shone",
        helps={"clean", "fresh"},
    )
    return setting, mystery, gear


def valid_combos() -> list[tuple[str, str]]:
    return [("the pirate ship", "menu_virus")]


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    hero_type: str
    captain: str
    seed: Optional[int] = None


def pirate_name(gender: str, rng: random.Random) -> str:
    girls = ["Mira", "Nell", "Rosa", "Poppy", "Lila", "Ava"]
    boys = ["Finn", "Jace", "Toby", "Milo", "Finnian", "Beck"]
    return rng.choice(girls if gender == "girl" else boys)


def reasonableness_gate(place: str, mystery_id: str) -> None:
    if (place, mystery_id) not in valid_combos():
        raise StoryError("This pirate tale only works when the virus mystery is tied to the ship's menu.")


def select_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "the pirate ship"
    mystery = args.mystery or "menu_virus"
    reasonableness_gate(place, mystery)
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    hero = args.hero or pirate_name("girl" if hero_type == "girl" else "boy", rng)
    captain = args.captain or rng.choice(["Captain Maris", "Captain Brawn", "Captain Pearl"])
    return StoryParams(place=place, mystery=mystery, hero=hero, hero_type=hero_type, captain=captain)


def introduce(world: World, hero: Entity, captain: Entity, menu: Entity, mystery: Mystery) -> None:
    world.say(
        f"On the pirate ship, {hero.id} was a small but sharp-eyed crew mate who loved a good quest."
    )
    world.say(
        f"{hero.pronoun().capitalize()} followed {captain.id} to the galley, where the dinner menu lay on the table like a clue."
    )
    world.say(
        f"Then the crew began to sneeze. The strange sickness had the same pesky mark as a sea-borne {mystery.culprit}."
    )


def dialogue_mystery(world: World, hero: Entity, captain: Entity, menu: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    captain.memes["worry"] += 1
    menu.meters["clue"] += 1
    world.say(
        f'"Why is everyone sniffly?" asked {hero.id}.'
        f' "And why is the menu the only thing nobody wants to touch?"'
    )
    world.say(
        f'"Because something hidden in this tale is making the crew ill," said {captain.id}. '
        f'"Find the clue, matey."'
    )
    world.say(
        f'{hero.id} peered at the menu and whispered, "If the sickness started after we shared the menu, that menu must be part of the mystery."'
    )
    propagate(world)


def quest_search(world: World, hero: Entity, captain: Entity, menu: Entity, mystery: Mystery) -> None:
    hero.memes["bravery"] += 1
    world.para()
    world.say(
        f"{hero.id} set off on a little quest through the ship, asking questions the pirate way."
    )
    world.say(
        f'"Who held the menu first?" asked {hero.id}. "Who coughed into it? Who washed their hands after the docks?"'
    )
    world.say(
        f"{captain.id} pointed to the smudges. \"There! The clue is on the paper. The sickness likes sticky hands and shared things.\""
    )
    menu.meters["clue"] += 1
    world.say(
        f"{hero.id} nodded. \"So the menu is not the enemy. It is the trail!\"'
    )
    menu.memes["fear"] += 0.5
    propagate(world)


def resolve(world: World, hero: Entity, captain: Entity, menu: Entity, gear: QuestGear, mystery: Mystery) -> None:
    world.para()
    world.say(
        f"{hero.id} came back with {gear.label}, just as brave as a mouse with a sword."
    )
    world.say(
        f'"First we clean the clue," said {hero.id}. "Then we keep the virus from hopping to new hands."'
    )
    world.say(
        f"{captain.id} smiled. \"Aye. That is a fine pirate fix.\""
    )
    world.say(f"They {gear.prep}.")
    menu.meters["clean"] += 1
    menu.meters["fresh"] += 1
    menu.meters["clue"] = 0.0
    for c in world.characters():
        if c.id != hero.id:
            c.memes["fear"] = max(0.0, c.memes["fear"] - 0.2)
            c.memes["relief"] += 1
    world.say(
        f"At last they {gear.tail}. The crew washed their hands, the sniffles quieted, and the galley smelled fresh again."
    )
    world.say(
        f"The menu stayed on the table, clean and harmless, and {hero.id} stood tall as the ship sailed on to the next harbor."
    )
    hero.memes["hope"] += 1
    captain.memes["hope"] += 1
    propagate(world)


def tell(params: StoryParams) -> World:
    setting, mystery, gear = build_reasonable_mystery()
    world = World(setting)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain"))
    menu = world.add(Entity(id="menu", type="thing", label="menu", phrase="the ship's dinner menu"))
    menu.owner = captain.id
    menu.caretaker = captain.id

    world.facts.update(mystery=mystery, gear=gear, hero=hero, captain=captain, menu=menu)

    introduce(world, hero, captain, menu, mystery)
    dialogue_mystery(world, hero, captain, menu, mystery)
    quest_search(world, hero, captain, menu, mystery)
    resolve(world, hero, captain, menu, gear, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    return [
        "Write a pirate tale for a little child about a sickness mystery on a ship, and let the menu be the clue.",
        f"Tell a dialogue-heavy quest story where {hero.id} asks why the crew is sneezing and {captain.id} helps solve it.",
        "Write a short pirate mystery with a safe ending where the crew cleans the clue and the voyage continues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    menu: Entity = f["menu"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"What was the mystery in the pirate ship story?",
            answer=f"The mystery was why the crew were getting sick, and the menu was part of the clue."
        ),
        QAItem(
            question=f"Who asked questions to solve the sickness on the ship?",
            answer=f"{hero.id} asked questions, listened to {captain.id}, and followed the clues."
        ),
        QAItem(
            question=f"What did they do to make the menu safe again?",
            answer=f"They washed the menu with warm water, soap, and a clean rag so the ship could keep sailing safely."
        ),
        QAItem(
            question=f"Why did the captain worry about the menu?",
            answer=f"{captain.id} worried because the sickness could spread when the crew kept touching the same shared menu."
        ),
        QAItem(
            question=f"What ended the quest in a happy way?",
            answer=f"The happy ending came when the menu was clean, the crew felt better, and the ship sailed on."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a virus?",
            answer="A virus is a tiny germ that can make people or animals sick and spread from one person to another."
        ),
        QAItem(
            question="What is a menu?",
            answer="A menu is a list of foods or drinks people can choose from."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, solve a problem, or help someone."
        ),
        QAItem(
            question="What does a pirate captain do?",
            answer="A pirate captain leads the crew, makes plans, and helps the ship work together."
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, mystery in valid_combos():
        lines.append(asp.fact("setting", place))
        lines.append(asp.fact("mystery", mystery))
        lines.append(asp.fact("needs_menu", mystery))
    lines.append(asp.fact("gear", "soap_and_rag"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- setting(P), mystery(M), needs_menu(M).
fix(M) :- mystery(M), needs_menu(M), gear(soap_and_rag).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld: a virus mystery, a menu clue, and a quest to solve it."
    )
    ap.add_argument("--place")
    ap.add_argument("--mystery")
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--captain")
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


CURATED = [
    StoryParams(place="the pirate ship", mystery="menu_virus", hero="Mira", hero_type="girl", captain="Captain Pearl"),
    StoryParams(place="the pirate ship", mystery="menu_virus", hero="Finn", hero_type="boy", captain="Captain Maris"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return select_params(args, rng)


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible mystery combos:\n")
        for place, mystery in vals:
            print(f"  {place:18} {mystery}")
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
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

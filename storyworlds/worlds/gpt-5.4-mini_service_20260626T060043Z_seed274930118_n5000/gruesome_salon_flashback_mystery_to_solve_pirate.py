#!/usr/bin/env python3
"""
A pirate-tale story world with a salon on a ship, a flashback, and a mystery to solve.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["mess", "shine", "fear", "joy", "curiosity", "resolve", "memory"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    piratey: bool = True


@dataclass
class Mystery:
    id: str
    thing: str
    clue: str
    culprit: str
    flashback_line: str
    solve_method: str
    result_line: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "ship_salon": Setting(place="the ship's salon", affords={"braid", "powder", "polish"}),
    "harbor_salon": Setting(place="the harbor salon", affords={"braid", "powder"}),
}

MYSTERIES = {
    "missing_combs": Mystery(
        id="missing_combs",
        thing="the silver comb",
        clue="a trail of glittering powder",
        culprit="a cheeky parrot",
        flashback_line="Earlier, the parrot had swooped through the salon and pecked at the comb basket.",
        solve_method="follow the powder trail",
        result_line="They found the comb tucked under a rope coil, where the parrot had hidden it.",
    ),
    "sour_scent": Mystery(
        id="sour_scent",
        thing="the jasmine oil",
        clue="a sticky brown drip near the chair",
        culprit="a spilled barrel of molasses",
        flashback_line="Earlier, a crate had tipped in a rocking wave, and a little molasses leaked across the floor.",
        solve_method="check the crate marks",
        result_line="They found the oil safe on a shelf, and the brown drip was only molasses from the crate.",
    ),
    "gruesome_spot": Mystery(
        id="gruesome_spot",
        thing="the white barber cape",
        clue="a dark red stain",
        culprit="a smashed pomegranate",
        flashback_line="Earlier, the captain had bitten a pomegranate in a hurry, and the juice had splashed the cape.",
        solve_method="ask who ate fruit",
        result_line="They cleaned the cape, and the stain turned out to be harmless pomegranate juice.",
    ),
}

GIRL_NAMES = ["Mina", "Tia", "Ruby", "Nell", "Zara"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Oren", "Kai"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if "salon" in place and m.thing:
                out.append((place, mid))
    return out


@dataclass
class ClueGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


GEAR = [
    ClueGear("gloves", "clean gloves", {"hands"}, {"mess"}, "put on clean gloves", "slipped on clean gloves"),
    ClueGear("cloth", "a damp cloth", {"hands"}, {"mess"}, "take a damp cloth", "used a damp cloth"),
    ClueGear("brush", "a soft brush", {"hands"}, {"mess"}, "pick up a soft brush", "used a soft brush"),
]


def prize_at_risk(mystery: Mystery) -> bool:
    return True


def select_gear(mystery: Mystery) -> Optional[ClueGear]:
    return GEAR[0]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate salon mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["pirate", "woman", "man"])
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
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or "pirate"
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_type=gender, captain_type=captain)


def _solve_mystery(world: World, hero: Entity, captain: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} stepped into {world.setting.place}, where the air smelled of soap, salt, and sea rope."
    )
    world.say(
        f"{hero.id} wanted to solve a mystery for the captain, because something in the salon looked {('gruesome' if mystery.id == 'gruesome_spot' else 'odd')}."
    )
    world.say(
        f"They noticed {mystery.clue} near the chair."
    )
    hero.memes["memory"] += 1
    world.say(
        f"That made {hero.id} think of a flashback: {mystery.flashback_line}"
    )
    gear = select_gear(mystery)
    if gear:
        hero.memes["resolve"] += 1
        world.say(
            f"{hero.id} decided to {mystery.solve_method}. {hero.pronoun().capitalize()} {gear.prep} and looked carefully."
        )
    world.say(mystery.result_line)
    hero.memes["joy"] += 1
    captain.memes["joy"] += 1
    world.say(
        f"{hero.id} grinned, and the captain laughed, because the salon mystery was solved at last."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str, captain_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = w.add(Entity(id="Captain", kind="character", type=captain_type, label="the captain"))
    comb = w.add(Entity(id="comb", type="thing", label="silver comb", phrase="a silver comb"))
    cape = w.add(Entity(id="cape", type="thing", label="barber cape", phrase="a white barber cape", caretaker="Captain"))
    comb.meters["shine"] = 1
    w.facts.update(hero=hero, captain=captain, mystery=mystery, setting=setting, comb=comb, cape=cape)
    w.say(
        f"{hero.id} was a little {hero_type} who loved pirate tales and strange rooms."
    )
    w.say(
        f"One morning, {hero.id} and {captain.label} came to {setting.place}, a salon aboard a ship."
    )
    w.para()
    _solve_mystery(w, hero, captain, mystery)
    w.para()
    w.say(
        f"In the end, the salon was neat again, the air smelled sweet, and the captain's chair stood ready for the next sailor."
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate story set in {world.setting.place} where {f['hero'].id} solves a mystery with a flashback.",
        f"Tell a child-friendly tale about a salon on a ship, a clue, and a careful search.",
        f"Write a short pirate tale that includes the words gruesome and salon and ends with the mystery being solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"Where does {hero.id} solve the mystery?",
            answer=f"{hero.id} solves it in {world.setting.place}, a salon on a ship.",
        ),
        QAItem(
            question=f"What clue helps {hero.id} notice the problem?",
            answer=f"The clue was {mystery.clue}. It made {hero.id} think about what happened before.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed that {mystery.flashback_line}",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They solved it by {mystery.solve_method}, and then found that {mystery.result_line.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salon?",
            answer="A salon is a place where hair can be washed, brushed, cut, or styled.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something that happened earlier.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle where someone needs to look for clues to find the answer.",
        ),
        QAItem(
            question="What does a pirate tale usually include?",
            answer="A pirate tale often includes a ship, a captain, brave helpers, and a sea adventure.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
valid_story(P,M) :- place(P), mystery(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.hero_name, params.hero_type, params.captain_type)
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
    StoryParams(place="ship_salon", mystery="missing_combs", hero_name="Mina", hero_type="girl", captain_type="pirate"),
    StoryParams(place="harbor_salon", mystery="sour_scent", hero_name="Pip", hero_type="boy", captain_type="pirate"),
    StoryParams(place="ship_salon", mystery="gruesome_spot", hero_name="Kai", hero_type="boy", captain_type="pirate"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

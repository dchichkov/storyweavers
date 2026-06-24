#!/usr/bin/env python3
"""
A tiny fairy-tale kitchen world about wobble and an agenda.

A source tale imagined from the seed:
---
Once upon a time, in a kitchen that smelled like warm bread and apple peels, a
little cook named Pippa wanted the soup pot to wobble just so. Her agenda for
the day was to make the royal lunch feel magical. But the spoon kept slipping,
the lid kept tilting, and a cranky whisk kept making the whole affair feel like
a joke.

Then Pippa noticed that the kitchen cat was batting at the ladle, which was why
everything kept wobbling. She laughed, gave the cat a ribbon toy, and set the
ladle in a bowl. The pot stood steady at last, the soup stopped sloshing, and
the royal lunch became merry instead of messy.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "maid", "cook"}
        male = {"boy", "man", "father", "king", "baker", "cook"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    cause: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    surface: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    steadies: set[str]
    plural: bool = False


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"wobble", "humor"}),
}

ACTIONS = {
    "wobble": Action(
        id="wobble",
        verb="make the pot wobble",
        gerund="wobbling the pot",
        rush="rush to steady the pot",
        mess="spill",
        soil="spilled",
        cause="the spoon keeps slipping",
        keyword="wobble",
        tags={"wobble", "humor"},
    ),
    "agenda": Action(
        id="agenda",
        verb="follow the agenda",
        gerund="keeping the agenda",
        rush="hurry to check the list",
        mess="spill",
        soil="spilled",
        cause="the cat keeps bumping the table",
        keyword="agenda",
        tags={"agenda", "humor"},
    ),
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a neat blue apron",
        type="apron",
        surface="torso",
    ),
    "soup": Prize(
        label="soup",
        phrase="a pot of royal soup",
        type="soup",
        surface="table",
        plural=False,
    ),
    "spoon": Prize(
        label="spoon",
        phrase="a silver spoon",
        type="spoon",
        surface="hand",
    ),
}

REMEDIES = [
    Remedy(
        id="cloth",
        label="a folded cloth",
        prep="set the pot on a folded cloth",
        tail="placed the pot on the folded cloth",
        guards={"spill"},
        steadies={"wobble"},
    ),
    Remedy(
        id="tray",
        label="a wooden tray",
        prep="move the bowl onto a wooden tray",
        tail="moved the bowl onto the wooden tray",
        guards={"spill"},
        steadies={"wobble"},
    ),
    Remedy(
        id="stool",
        label="a small stool",
        prep="put the stirring bowl on a small stool",
        tail="put the stirring bowl on a small stool",
        guards={"spill"},
        steadies={"wobble", "agenda"},
    ),
]

NAMES_GIRL = ["Pippa", "Mina", "Tilly", "Nora", "Lila"]
NAMES_BOY = ["Owen", "Robin", "Finn", "Milo", "Theo"]
TRAITS = ["cheerful", "curious", "spry", "gentle", "merry"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def can_story(action: Action, prize: Prize) -> bool:
    return True


def select_remedy(action: Action, prize: Prize) -> Optional[Remedy]:
    for rem in REMEDIES:
        if action.id in rem.steadies or action.mess in rem.guards:
            return rem
    return None


def predict(world: World, hero: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return {"spilled": prize.meters.get("spilled", 0) >= THRESHOLD}


def _do_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    hero.memes[action.id] = hero.memes.get(action.id, 0) + 1
    if action.id == "wobble":
        hero.meters["wobble"] = hero.meters.get("wobble", 0) + 1
    if action.id == "agenda":
        hero.meters["agenda"] = hero.meters.get("agenda", 0) + 1
    # The cat's nudges and the slipping spoon create spill pressure.
    if action.cause:
        hero.meters["spill"] = hero.meters.get("spill", 0) + 1
    if narrate:
        world.say(f"{hero.id} tried to {action.verb}, but {action.cause}.")


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="Cook", kind="character", type="woman", label="the cook"))
    cat = world.add(Entity(id="Cat", kind="character", type="thing", label="the kitchen cat"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id))

    world.say(f"{hero.id} was a little {trait} {gender} who lived near {setting.place}.")
    world.say(f"{hero.pronoun('subject').capitalize()} loved the kitchen because {action.keyword} made the day feel funny and bright.")
    world.say(f"One day, {parent.label} handed {hero.pronoun('object')} {prize.phrase} for the royal lunch.")
    world.say(f"{hero.id} wanted to {action.verb}, and the tiny agenda on the table said this was the hour for it.")

    world.para()
    world.say(f"At {setting.place}, the spoon kept slipping and the little cat bumped the table.")
    _do_action(world, hero, action)
    if predict(world, hero, action, prize.id)["spilled"]:
        world.say(f"That could make {prize.label} {action.soil}, which would spoil the merry plan.")
        world.say(f"{parent.label} frowned in a kindly way and held up {prize.phrase} before it tipped.")
        world.say(f"{hero.id} laughed, because the wobble looked almost like a joke.")

    world.para()
    rem = select_remedy(action, prize)
    if rem:
        world.say(f"Then {parent.label} suggested {rem.prep}.")
        world.say(f"They {rem.tail}, and at once the wobble grew smaller.")
        world.say(f"{hero.id} tapped the spoon softly, and the cat sat down as if it had remembered the agenda too.")
        prize.meters["spilled"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.say(f"In the end, {prize.label} stayed neat, the soup did not spill, and the kitchen felt like a smiling storybook.")
    else:
        raise StoryError("No reasonable remedy fits this kitchen tale.")

    world.facts.update(hero=hero, parent=parent, cat=cat, prize=prize, action=action, setting=setting, remedy=rem)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a short fairy tale for children set in a kitchen that uses the word "{action.keyword}".',
        f"Tell a humorous story about {hero.id} and a kitchen agenda that goes wobble-wobble before turning out well.",
        f"Write a gentle fairy tale where a little helper laughs, steadies the kitchen, and keeps the soup from spilling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    action = f["action"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the kitchen?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the royal soup?",
            answer=f"{parent.label} worried because the wobble could make {prize.label} {action.soil}.",
        ),
        QAItem(
            question="What made the kitchen feel funny at first?",
            answer=f"The spoon kept slipping and the cat kept bumping the table, so everything felt like a joke.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The {prize.label} stayed neat, the spill was stopped, and the kitchen felt merry at the end.",
        ),
    ]
    if f.get("remedy"):
        rem = f["remedy"]
        qa.append(
            QAItem(
                question=f"What helped steady the wobble?",
                answer=f"{rem.label.capitalize()} helped steady the wobble and kept the kitchen safe for the plan.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an agenda?",
            answer="An agenda is a plan or list of things to do, often in order.",
        ),
        QAItem(
            question="What does wobble mean?",
            answer="To wobble means to move unsteadily, as if something might tip or shake.",
        ),
        QAItem(
            question="Why are kitchens busy places?",
            answer="Kitchens are busy because people cook, stir, wash, and carry food there.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts -- asks that would produce this story ==")
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", action="wobble", prize="soup", name="Pippa", gender="girl", trait="cheerful"),
    StoryParams(place="kitchen", action="agenda", prize="apron", name="Milo", gender="boy", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale kitchen world about wobble and agenda.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    if args.action and args.prize and not can_story(ACTIONS[args.action], PRIZES[args.prize]):
        raise StoryError("No valid story for the chosen action and prize.")
    action = args.action or rng.choice(list(ACTIONS))
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=args.place or "kitchen", action=action, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.trait)
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


ASP_RULES = r"""
place(kitchen).
action(wobble).
action(agenda).
prize(apron).
prize(soup).
prize(spoon).

wobbly(wobble).
humorous(wobble).
humorous(agenda).

valid_story(P,A,R) :- place(P), action(A), prize(R), humorous(A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "kitchen")]
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        if "humor" in ACTIONS[a].tags:
            lines.append(asp.fact("humorous", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("kitchen", "wobble", "soup"), ("kitchen", "wobble", "apron"), ("kitchen", "wobble", "spoon"),
          ("kitchen", "agenda", "soup"), ("kitchen", "agenda", "apron"), ("kitchen", "agenda", "spoon")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print("\n".join(map(str, combos)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

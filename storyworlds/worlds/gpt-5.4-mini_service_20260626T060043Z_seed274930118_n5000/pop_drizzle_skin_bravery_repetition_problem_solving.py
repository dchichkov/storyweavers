#!/usr/bin/env python3
"""
A small animal-story world about a brave little creature, a stubborn problem,
and a repeated try that finally solves it.

Seed words: pop, drizzle, skin
Features: bravery, repetition, problem solving
Style: Animal Story
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "mouse", "hedgehog", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    attempt: str
    trouble: str
    fix_hint: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    protects: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    animal: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.weather: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        chunk = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.weather = self.weather
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "pond": Place("the pond", False, {"drizzle", "pop"}),
    "garden": Place("the garden", False, {"drizzle", "pop"}),
    "burrow": Place("the burrow", True, {"pop"}),
}

ACTIONS = {
    "pop": Action(
        id="pop",
        verb="pop the bubble wrap",
        gerund="popping bubble wrap",
        attempt="try to pop the last bubble",
        trouble="made too much noise and scared the little nest nearby",
        fix_hint="use a soft paw and pop only one bubble at a time",
        keyword="pop",
        tags={"pop"},
    ),
    "drizzle": Action(
        id="drizzle",
        verb="walk in the drizzle",
        gerund="walking in drizzle",
        attempt="try to keep walking under the drizzle",
        trouble="made the fur damp and the skin chilly",
        fix_hint="find a leaf shelter and walk in little steps",
        keyword="drizzle",
        tags={"drizzle"},
    ),
    "skin": Action(
        id="skin",
        verb="help a friend soothe scratched skin",
        gerund="caring for skin",
        attempt="try to clean the scratch again",
        trouble="made the fox worry because the skin still looked tender",
        fix_hint="wash gently, pat dry, and ask the helper to check again",
        keyword="skin",
        tags={"skin"},
    ),
}

ITEMS = {
    "shell": Item("shell", "little shell cap", "a little shell cap", "head", {"drizzle"}),
    "leafcloak": Item("leafcloak", "leaf cloak", "a leaf cloak", "back", {"drizzle"}),
    "featherpad": Item("featherpad", "feather pad", "a feather pad", "paws", {"pop"}),
}

ANIMALS = {
    "fox": {"name": "Fenn", "kind": "fox"},
    "rabbit": {"name": "Pip", "kind": "rabbit"},
    "mouse": {"name": "Milo", "kind": "mouse"},
    "hedgehog": {"name": "Holly", "kind": "hedgehog"},
    "squirrel": {"name": "Suri", "kind": "squirrel"},
}

HELPERS = ["mother", "father", "grandmother", "grandfather", "older sister", "older brother"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for action_id in place.afford:
            action = ACTIONS[action_id]
            for item_id, item in ITEMS.items():
                if action.id in item.protects or (action.id == "pop" and item_id == "featherpad"):
                    out.append((place_id, action_id, item_id))
    return out


def choose_item(action: Action) -> Optional[Item]:
    for item in ITEMS.values():
        if action.id in item.protects or (action.id == "pop" and item.id == "featherpad"):
            return item
    return None


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.memes[action.id] = actor.memes.get(action.id, 0) + 1
    if action.id == "drizzle":
        actor.meters["wet"] = actor.meters.get("wet", 0) + 1
        actor.meters["chill"] = actor.meters.get("chill", 0) + 1
    if action.id == "pop":
        actor.meters["noise"] = actor.meters.get("noise", 0) + 1
    if action.id == "skin":
        actor.memes["care"] = actor.memes.get("care", 0) + 1
    if narrate:
        if action.id == "pop":
            world.say("Pop! The soft bubble went away with a tiny snap.")
        elif action.id == "drizzle":
            world.say("The drizzle landed on the fur like tiny silver pins.")
        elif action.id == "skin":
            world.say("The little skin scratch was washed very gently and checked again.")
    if action.id == "drizzle" and actor.meters.get("wet", 0) >= THRESHOLD:
        world.say("That made the little animal look damp and uncomfortable.")


def predict_trouble(world: World, actor: Entity, action: Action) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    return bool(sim.get(actor.id).meters.get("wet", 0) >= THRESHOLD or sim.get(actor.id).meters.get("noise", 0) >= THRESHOLD)


def introduce(world: World, animal: Entity, helper: Entity, item: Item, action: Action) -> None:
    world.say(f"{animal.id} was a small {animal.type} who noticed every curious thing.")
    world.say(f"{animal.id} loved {action.gerund}, and {animal.id}'s {helper.type} had brought {item.phrase}.")
    world.say(f"{animal.id} liked how the day could change with one little {action.keyword}.")


def setup(world: World, animal: Entity, helper: Entity, action: Action, item: Item) -> None:
    world.para()
    world.say(f"One day, {animal.id} and {animal.pronoun('possessive')} {helper.type} went to {world.place.name}.")
    if action.id == "drizzle":
        world.weather = "drizzle"
        world.say("A soft drizzle was falling, and the air felt cool.")
    elif action.id == "pop":
        world.say("A pile of bubble wrap sat nearby, waiting for tiny paws.")
    else:
        world.say("A little scrape had made the skin sting, and everyone wanted to help.")


def problem(world: World, animal: Entity, helper: Entity, action: Action, item: Item) -> None:
    world.say(f"{animal.id} wanted to {action.verb}, but {animal.pronoun('possessive')} {helper.type} worried about the little problem.")
    if action.id == "drizzle":
        world.say(f"If {animal.id} stayed out, the wet drizzle would reach the skin and make it chilly.")
    elif action.id == "pop":
        world.say(f"If {animal.id} popped every bubble at once, the sharp pop-pop-pop would scare the birds.")
    else:
        world.say(f"If the skin was rubbed too hard, the scratch might sting even more.")


def repeated_try(world: World, animal: Entity, action: Action) -> None:
    world.say(f"{animal.id} took a brave breath and tried again.")
    _do_action(world, animal, action, narrate=True)
    world.say(f"Then {animal.id} tried once more, because bravery can mean not giving up.")
    _do_action(world, animal, action, narrate=False)


def solve(world: World, animal: Entity, helper: Entity, action: Action, item: Item) -> None:
    world.para()
    world.say(f"After that, {animal.id} and {animal.pronoun('possessive')} {helper.type} used a clever plan.")
    if action.id == "drizzle":
        world.say(f"They put on the {item.label} and walked in small careful steps under a leafy branch.")
        world.say(f"The skin stayed dry enough, and the drizzle turned into a shiny, happy sparkle.")
    elif action.id == "pop":
        world.say(f"They used the {item.label} so the bubbles could pop one by one without a fright.")
        world.say(f"The soft pop became friendly, and the nest nearby stayed calm.")
    else:
        world.say(f"They washed the skin gently, patted it dry, and checked it again with care.")
        world.say(f"The scratch looked better, and the worried face relaxed.")
    world.say(f"In the end, {animal.id} kept going, and the little problem was solved.")


def tell_story(world: World, animal: Entity, helper: Entity, action: Action, item: Item) -> None:
    introduce(world, animal, helper, item, action)
    setup(world, animal, helper, action, item)
    world.para()
    problem(world, animal, helper, action, item)
    repeated_try(world, animal, action)
    solve(world, animal, helper, action, item)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story with the words "{f["action"].keyword}", "brave", and "problem".',
        f"Tell a gentle story where {f['animal'].id} faces a small trouble at {world.place.name} and solves it with help.",
        f"Write a child-friendly story about repeated tries, a brave animal, and a clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    animal: Entity = f["animal"]
    helper: Entity = f["helper"]
    action: Action = f["action"]
    item: Item = f["item"]
    return [
        QAItem(
            question=f"Who is the brave animal in the story?",
            answer=f"The brave animal is {animal.id}, a little {animal.type} who keeps trying.",
        ),
        QAItem(
            question=f"What little problem did {animal.id} have with {action.keyword}?",
            answer=f"{animal.id} had to handle {action.gerund}, and the tricky part was that {action.trouble}.",
        ),
        QAItem(
            question=f"How did {animal.id} and the {helper.type} solve the problem?",
            answer=f"They used {item.label} and a careful plan, so {animal.id} could keep going without making things worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is drizzle?",
            answer="Drizzle is a very light rain with tiny drops.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully and finding a good way to fix a trouble.",
        ),
        QAItem(
            question="What does pop sound like?",
            answer="Pop is a quick, tiny snapping sound.",
        ),
        QAItem(
            question="What is skin?",
            answer="Skin is the thin outer layer that covers a person's or animal's body.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.indoors:
            lines.append(asp.fact("indoors", place_id))
        for a in sorted(place.afford):
            lines.append(asp.fact("affords", place_id, a))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(action.tags):
            lines.append(asp.fact("tagged", aid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for p in sorted(item.protects):
            lines.append(asp.fact("protects", iid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,A,I) :- affords(Place,A), action(A), item(I), can_use(A,I).
can_use(drizzle,I) :- protects(I,drizzle).
can_use(pop,I) :- protects(I,pop).
can_use(skin,I) :- protects(I,skin).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: bravery, repetition, problem solving.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--action", choices=ACTIONS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--animal", choices=ANIMALS.keys())
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place or args.action or args.item:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.action is None or c[1] == args.action)
            and (args.item is None or c[2] == args.item)
        ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, item = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, action=action, item=item, animal=animal, helper=helper)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    item = ITEMS[params.item]
    animal_info = ANIMALS[params.animal]
    world = World(place)
    animal = world.add(Entity(id=animal_info["name"], kind="character", type=animal_info["kind"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper))
    world.facts.update(animal=animal, helper=helper, action=action, item=item)
    tell_story(world, animal, helper, action, item)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="pond", action="drizzle", item="shell", animal="fox", helper="mother"),
    StoryParams(place="garden", action="pop", item="featherpad", animal="rabbit", helper="father"),
    StoryParams(place="burrow", action="skin", item="leafcloak", animal="hedgehog", helper="grandmother"),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        raise StoryError(f"ASP mode requires clingo: {e}")
    program = asp_program()
    model = asp.one_model(program)
    asp_vals = set(asp.atoms(model, "valid"))
    py_vals = set(valid_combos())
    if asp_vals == py_vals:
        print(f"OK: ASP and Python agree on {len(py_vals)} valid combos.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only ASP:", sorted(asp_vals - py_vals))
    print("Only Python:", sorted(py_vals - asp_vals))
    return 1


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_list()
        for t in vals:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

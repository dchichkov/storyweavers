#!/usr/bin/env python3
"""
A small heartwarming storyworld about a child, a disagreement, and learning to
share while burying a time capsule in the yard.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    afford_bury: bool = True
    soil: str = "soft dirt"


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "backyard": Place(name="the backyard", afford_bury=True, soil="soft dirt"),
    "garden": Place(name="the garden", afford_bury=True, soil="loose soil"),
    "beach": Place(name="the beach", afford_bury=False, soil="sand"),
}

ITEMS = {
    "time_capsule": Item(
        id="time_capsule",
        label="time capsule",
        phrase="a small tin time capsule",
        type="container",
    ),
    "seed_box": Item(
        id="seed_box",
        label="seed box",
        phrase="a little box of flower seeds",
        type="container",
    ),
    "toy": Item(
        id="toy",
        label="toy box",
        phrase="a favorite toy in a bright box",
        type="container",
    ),
}

NAMES = {
    "girl": ["Mia", "Luna", "Ada", "Nora", "Zoe", "Maya"],
    "boy": ["Noah", "Leo", "Eli", "Finn", "Owen", "Theo"],
}
TRAITS = ["gentle", "curious", "kind", "brave", "patient"]


@dataclass
class StoryModel:
    hero: Entity
    parent: Entity
    item: Entity
    place: Place
    conflict: bool = False
    shared: bool = False
    buried: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming bury/share dialogue storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.place == "beach" and args.item == "time_capsule":
        raise StoryError("(No story: the beach is sandy and not a good place to bury a time capsule.)")
    place = args.place or rng.choice(["backyard", "garden"])
    item = args.item or rng.choice(["time_capsule", "seed_box"])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent)


def _do_bury(world: World, model: StoryModel) -> None:
    model.hero.memes["hope"] = model.hero.memes.get("hope", 0) + 1
    model.hero.meters["busy"] = model.hero.meters.get("busy", 0) + 1
    model.buried = True


def tell(place: Place, item_cfg: Item, hero_name: str, hero_gender: str, parent_type: str) -> StoryModel:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase))

    model = StoryModel(hero=hero, parent=parent, item=item, place=place)

    world.say(f"{hero.id} loved being outside in {place.name}.")
    world.say(f"{hero.pronoun().capitalize()} had an idea: {hero.pronoun('subject')} wanted to bury {hero.pronoun('possessive')} {item.label} in the ground.")
    world.say(f"{hero.pronoun('subject').capitalize()} told {parent.label}: \"Can we bury {hero.pronoun('possessive')} {item.label} here?\"")
    world.say(f"{parent.label.capitalize()} looked at the little box and asked, \"Why do you want to bury it?\"")
    world.say(f"\"So we can keep a surprise safe for later,\" {hero.id} said. \"And I want you to help me.\"")

    if not place.afford_bury:
        world.say(f"{parent.label.capitalize()} shook {parent.pronoun('possessive')} head. \"This place is too sandy. The box might get lost.\"")
        world.say(f"{hero.id} frowned for a moment, but then {hero.pronoun()} listened.")
        world.say(f"\"Then let’s go home,\" {hero.id} said. \"I still want to share the job.\"")
        model.conflict = True
    else:
        world.say(f"{parent.label.capitalize()} smiled. \"That sounds special.\"")
        model.shared = True

    if not model.shared:
        world.para()
        world.say(f"{hero.id} and {parent.label} carried the {item.label} to the backyard together.")
        world.say(f"{hero.id} held the tiny shovel, but {parent.label} held the marker so they could both take part.")
        world.say(f"\"I can dig,\" {hero.id} said, \"and you can place the stone on top.\"")
        world.say(f"\"That is sharing,\" {parent.label} said warmly. \"We both help.\"")
        model.shared = True

    world.para()
    if place.afford_bury:
        _do_bury(world, model)
        world.say(f"They dug a small hole in the {place.soil}, tucked the {item.label} inside, and covered it with earth.")
        world.say(f"{hero.id} pressed a flat stone on top and drew a tiny heart in the dirt.")
        world.say(f"At the end, {hero.id} smiled at {parent.label} and said, \"Now our surprise is safe until we come back.\"")
    else:
        _do_bury(world, model)
        world.say(f"Back home, they dug a neat little hole in the soft dirt.")
        world.say(f"They buried the {item.label} together, and {hero.id} shared the last scoop of soil with {parent.label}.")
        world.say(f"The ground looked simple, but the moment felt special and warm.")

    world.facts.update(hero=hero, parent=parent, item=item, place=place, model=model)
    model.world = world  # type: ignore[attr-defined]
    return model


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    item: Entity = f["item"]
    return [
        f"Write a heartwarming story about {hero.id} wanting to bury a {item.label} and learning to share the work.",
        f"Tell a gentle dialogue story where a child asks a parent to bury something special together.",
        f"Write a short story for young children about a disagreement that turns into sharing while burying a treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    place: Place = f["place"]
    model: StoryModel = f["model"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to bury the {item.label} in {place.name} so it could stay safe for later.",
        ),
        QAItem(
            question=f"Why did {parent.label} say no at first if the story was set at {place.name}?",
            answer=f"{parent.label.capitalize()} said no at first because {place.name} was not the right place for that plan, so the box might not stay safe there.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} solve the problem?",
            answer=f"They talked about it, shared the job, and then buried the {item.label} together in a better spot.",
        ),
    ]
    if model.shared:
        qa.append(QAItem(
            question=f"What did sharing look like in the story?",
            answer=f"Sharing looked like {hero.id} and {parent.label} both helping: one dug, and the other held the marker and helped cover the hole.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to bury something?",
            answer="To bury something means to put it under the ground and cover it with dirt or sand.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people join in, use something, or help with a job together.",
        ),
        QAItem(
            question="Why can talking help during a conflict?",
            answer="Talking helps because people can explain their feelings, listen to each other, and find a kinder plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    model = tell(SETTINGS[params.place], ITEMS[params.item], params.name, params.gender, params.parent)
    world = model.world  # type: ignore[attr-defined]
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
place(backyard). place(garden). place(beach).
bury_ok(backyard). bury_ok(garden).
item(time_capsule). item(seed_box).
conflict(P, I) :- place(P), item(I), P = beach, I = time_capsule.
shared(P, I) :- bury_ok(P), item(I), not conflict(P, I).
resolved(P, I) :- shared(P, I).
#show conflict/2.
#show shared/2.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        if SETTINGS[pid].afford_bury:
            lines.append(asp.fact("bury_ok", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shared/2.\n#show resolved/2.\n"))
    return sorted(set(asp.atoms(model, "shared")))


def asp_verify() -> int:
    python_set = {(p, i) for p in SETTINGS for i in ITEMS if SETTINGS[p].afford_bury}
    clingo_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_storysample(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place == "beach" and args.item == "time_capsule":
        raise StoryError("(No story: a time capsule is not a good thing to bury on the beach.)")
    place = args.place or rng.choice(["backyard", "garden"])
    item = args.item or rng.choice(["time_capsule", "seed_box"])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, name=name, gender=gender, parent=parent)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show conflict/2.\n#show shared/2.\n#show resolved/2.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(asp_program("#show conflict/2.\n#show shared/2.\n#show resolved/2.\n"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="backyard", item="time_capsule", name="Mia", gender="girl", parent="mother"),
            StoryParams(place="garden", item="seed_box", name="Noah", gender="boy", parent="father"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: bury {p.item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

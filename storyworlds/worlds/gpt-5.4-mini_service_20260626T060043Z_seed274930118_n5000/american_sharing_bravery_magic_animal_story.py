#!/usr/bin/env python3
"""
A small animal-story world about sharing, bravery, and a little magic.

Premise:
- An animal hero keeps a magical thing or trick all to itself.
- A smaller friend wants to join in.
- The hero feels scared to share.
- Bravery helps the hero make a kind choice.
- Magic makes the ending feel bright and earned.

This script is self-contained and follows the Storyweavers world contract.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"rabbit", "fox", "deer", "bird", "squirrel", "cat"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Animal:
    type: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    kind: str
    glow: str
    shares: bool
    helps: set[str] = field(default_factory=set)
    story_tag: str = ""


@dataclass
class Companion:
    type: str
    label: str
    phrase: str
    size: str = "small"
    tags: set[str] = field(default_factory=set)


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _emotions(ent: Entity) -> dict[str, float]:
    return ent.memes


def _meters(ent: Entity) -> dict[str, float]:
    return ent.meters


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for actor in world.characters():
            if _emotions(actor).get("fear", 0.0) >= THRESHOLD and _emotions(actor).get("brave", 0.0) < THRESHOLD:
                sig = ("brave_up", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _emotions(actor)["brave"] = 1.0
                    out.append(f"{actor.id} took a slow breath and stood a little taller.")
                    changed = True
            if _emotions(actor).get("brave", 0.0) >= THRESHOLD and _emotions(actor).get("share", 0.0) >= THRESHOLD:
                sig = ("joy_share", actor.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    _emotions(actor)["joy"] = _emotions(actor).get("joy", 0.0) + 1.0
                    out.append(f"{actor.id} felt warm and proud after choosing to share.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.phrase} who loved bright days and small surprises.")


def loves_magic(world: World, hero: Entity, item: Entity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {item.phrase}, because it glowed with a soft {item.label}.")
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0


def meet_friend(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"Near {world.setting.place}, {friend.id} came over and looked at the glow with wide eyes.")
    friend.memes["hope"] = friend.memes.get("hope", 0.0) + 1.0


def wants_to_share(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    world.say(f"{hero.id} wanted to keep the magic all to itself, but {friend.id} asked, \"Can I see {item.it()} too?\"")
    world.say(f"{hero.id}'s paws went still. Sharing felt a little scary.")


def brave_choice(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["share"] = hero.memes.get("share", 0.0) + 1.0
    propagate(world, narrate=True)
    world.say(f"Then {hero.id} chose to be brave. {hero.pronoun().capitalize()} held out {item.it()} so {friend.id} could come closer.")


def magic_blooms(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    item.meters["glow"] = item.meters.get("glow", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(f"When they touched {item.it()} together, the magic sparkled brighter than before.")
    world.say(f"Little lights drifted around them, and {friend.id} laughed with delight.")
    world.say(f"By the end, {hero.id} was happy to share, and the magic felt bigger because it was shared.")


def tell(setting: Setting, animal: Animal, companion: Companion, item: MagicItem) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=animal.type, label=animal.label, phrase=animal.phrase))
    friend = world.add(Entity(id="friend", kind="character", type=companion.type, label=companion.label, phrase=companion.phrase))
    magic = world.add(Entity(id="magic", type=item.kind, label=item.label, phrase=item.phrase, owner=hero.id))

    hero.memes["curious"] = 1.0
    world.say(f"In {setting.place}, an {animal.phrase} named {hero.id} found a little {item.label}.")
    world.say(f"{hero.id} kept it tucked under one wing, paw, or hoof and watched the {item.label} glow.")

    world.para()
    meet_friend(world, hero, friend)
    loves_magic(world, hero, magic)
    wants_to_share(world, hero, friend, magic)

    world.para()
    brave_choice(world, hero, friend, magic)
    magic_blooms(world, hero, friend, magic)

    world.facts.update(hero=hero, friend=friend, item=magic, setting=setting, animal=animal, companion=companion)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"sharing", "bravery", "magic"}),
    "pond": Setting(place="the pond", affords={"sharing", "bravery", "magic"}),
    "oak_tree": Setting(place="the old oak tree", affords={"sharing", "bravery", "magic"}),
    "porch": Setting(place="the porch by the farm", affords={"sharing", "bravery", "magic"}),
}

ANIMALS = {
    "american_robin": Animal(
        type="bird",
        label="american robin",
        phrase="american robin",
        tags={"american", "bird"},
    ),
    "rabbit": Animal(type="rabbit", label="rabbit", phrase="curious rabbit", tags={"animal"}),
    "squirrel": Animal(type="squirrel", label="squirrel", phrase="busy squirrel", tags={"animal"}),
    "deer": Animal(type="deer", label="deer", phrase="gentle deer", tags={"animal"}),
    "fox": Animal(type="fox", label="fox", phrase="small fox", tags={"animal"}),
}

COMPANIONS = {
    "mole": Companion(type="mole", label="mole", phrase="tiny mole", tags={"animal"}),
    "mouse": Companion(type="mouse", label="mouse", phrase="small mouse", tags={"animal"}),
    "chipmunk": Companion(type="chipmunk", label="chipmunk", phrase="little chipmunk", tags={"animal"}),
    "duckling": Companion(type="duckling", label="duckling", phrase="yellow duckling", tags={"animal"}),
}

MAGIC_ITEMS = {
    "lantern": MagicItem(
        id="lantern",
        label="lantern light",
        phrase="a lantern that glowed like moon milk",
        kind="lantern",
        glow="soft gold",
        shares=True,
        helps={"sharing", "bravery", "magic"},
        story_tag="light",
    ),
    "berries": MagicItem(
        id="berries",
        label="berry magic",
        phrase="a bowl of berries that shimmered purple",
        kind="berries",
        glow="purple",
        shares=True,
        helps={"sharing", "magic"},
        story_tag="berries",
    ),
    "ribbon": MagicItem(
        id="ribbon",
        label="magic ribbon",
        phrase="a ribbon that sparkled like pond ripples",
        kind="ribbon",
        glow="silver",
        shares=True,
        helps={"sharing", "bravery", "magic"},
        story_tag="ribbon",
    ),
}

GENDERS = ["girl", "boy"]
TRAITS = ["gentle", "curious", "brave", "shy", "lively"]


@dataclass
class StoryParams:
    place: str
    animal: str
    companion: str
    item: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for animal in ANIMALS:
            for item in MAGIC_ITEMS:
                combos.append((place, animal, item))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen animal, place, or magic item does not make a gentle sharing story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world about sharing, bravery, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.animal is None or c[1] == args.animal)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError(explain_rejection())
    place, animal, item = rng.choice(sorted(combos))
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    gender = args.gender or rng.choice(GENDERS)
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(["Ava", "Milo", "Nia", "Theo", "Zoe", "Jude"])
    return StoryParams(place=place, animal=animal, companion=companion, item=item, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for children about "{f["animal"].label}" sharing a magical thing.',
        f"Tell a gentle story where {f['hero'].id} learns bravery and shares the {f['item'].label} with a smaller friend.",
        f'Write a simple story that includes the word "american" and ends with a happy shared magic moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, an {hero.phrase}, in {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep at first?",
            answer=f"{hero.id} kept {item.phrase} all to itself before choosing to share it.",
        ),
        QAItem(
            question=f"Why was {hero.id} scared?",
            answer=f"{hero.id} felt scared because sharing the magic seemed risky at first, but being brave helped.",
        ),
        QAItem(
            question=f"Who got to see the magic in the end?",
            answer=f"{friend.id} got to see it too, and both friends enjoyed the brighter magic together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to share?", answer="To share means to let someone else use or enjoy something with you."),
        QAItem(question="What is bravery?", answer="Bravery means doing something even when you feel a little scared."),
        QAItem(question="What is magic in a story?", answer="Magic is something special and impossible in real life that makes a story feel wonder-filled."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
    for iid, i in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic_item", iid))
        for h in sorted(i.helps):
            lines.append(asp.fact("helps", iid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,I) :- setting(P), animal(A), magic_item(I), affords(P, sharing), affords(P, bravery), affords(P, magic).
featured(american_robin) :- animal(american_robin).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def tell_from_params(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ANIMALS[params.animal],
        COMPANIONS[params.companion],
        MAGIC_ITEMS[params.item],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return tell_from_params(params)


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
    StoryParams(place="meadow", animal="american_robin", companion="mole", item="lantern", name="Ruby", gender="girl", trait="brave"),
    StoryParams(place="pond", animal="rabbit", companion="duckling", item="berries", name="Nico", gender="boy", trait="curious"),
    StoryParams(place="oak_tree", animal="squirrel", companion="mouse", item="ribbon", name="Mina", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.animal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

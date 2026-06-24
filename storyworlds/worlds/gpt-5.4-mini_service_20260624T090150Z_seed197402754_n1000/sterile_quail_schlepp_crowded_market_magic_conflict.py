#!/usr/bin/env python3
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the crowded market"
    crowd: str = "crowded"
    affords: set[str] = field(default_factory=set)


@dataclass
class Agent:
    name: str
    gender: str
    trait: str
    parent: str


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    kind: str = "thing"
    plural: bool = False
    sterile: bool = False


@dataclass
class Spell:
    id: str
    label: str
    action: str
    consequence: str
    caution: str
    turn: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    spell: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "market": Setting(place="the crowded market", crowd="crowded", affords={"magic"}),
}

SPELLS = {
    "magic": Spell(
        id="magic",
        label="a little market charm",
        action="stir a magic breeze through the stalls",
        consequence="the ribboned baskets began to wobble",
        caution="the old sellers warned that magic should be used with care",
        turn="the charm could calm the crowd if it was spoken softly",
        tags={"magic", "cautionary"},
    ),
    "quail": Spell(
        id="quail",
        label="a shy quail song",
        action="call a quail from under the cart",
        consequence="the quail fluttered and startled the shoppers",
        caution="the feathered bird would flee if chased",
        turn="the song could quiet the bird if the child knelt still",
        tags={"quail", "cautionary"},
    ),
    "schlepp": Spell(
        id="schlepp",
        label="a long schlepp of sacks",
        action="schlepp the heavy sacks across the stones",
        consequence="the sacks bumped into cabbage and apples",
        caution="the wise aunt said not to schlepp without help",
        turn="the load could be shared and carried safely",
        tags={"schlepp", "conflict", "cautionary"},
    ),
}

ITEMS = {
    "basket": Item(id="basket", label="sterile basket", phrase="a sterile white basket", region="hands", sterile=True),
    "cloak": Item(id="cloak", label="clean cloak", phrase="a clean cloak with bright thread", region="torso"),
    "quail": Item(id="quail", label="quail", phrase="a small quail with soft feathers", region="hands", kind="animal"),
    "sacks": Item(id="sacks", label="sacks", phrase="three heavy market sacks", region="back", plural=True),
}

TRAITS = ["curious", "gentle", "bold", "careful", "cheerful", "spirited"]
GIRL_NAMES = ["Mina", "Tala", "Nora", "Lina", "Suri", "Asha"]
BOY_NAMES = ["Taro", "Milo", "Ravi", "Jon", "Pavel", "Ivo"]
PARENTS = ["mother", "father"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, sp in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        for t in sorted(sp.tags):
            lines.append(asp.fact("tag", sid, t))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.sterile:
            lines.append(asp.fact("sterile", iid))
        lines.append(asp.fact("on_region", iid, it.region))
    return "\n".join(lines)


ASP_RULES = r"""
allowed(P,S,I) :- affords(P,S), spell(S), item(I), not blocked(S,I).
blocked(magic, sacks) :- sterile(basket).
blocked(schlepp, basket) :- sterile(basket).
needs_caution(S) :- tag(S, cautionary).
usable(P,S,I) :- allowed(P,S,I), needs_caution(S).
#show allowed/3.
#show usable/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for s in SPELLS:
            for i in ITEMS:
                if p == "market" and not (s == "schlepp" and i == "basket"):
                    combos.append((p, s, i))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show allowed/3."))
    return sorted(set(asp.atoms(model, "allowed")))


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
    ap = argparse.ArgumentParser(description="Folk-tale market story world with magic, conflict, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.spell and args.item and args.spell == "schlepp" and args.item == "basket":
        raise StoryError("The sterile basket cannot sensibly be schlepped as the central conflict.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.spell is None or c[1] == args.spell)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, spell, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, spell=spell, item=item, name=name, gender=gender, parent=parent, trait=trait)


def setup_world(params: StoryParams) -> World:
    w = World(SETTINGS[params.place])
    hero = w.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = w.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = ITEMS[params.item]
    held = w.add(Entity(id=item.id, type=item.kind, label=item.label, phrase=item.phrase, owner=hero.id))
    held.worn_by = hero.id
    w.facts = {"hero": hero, "parent": parent, "item": held, "spell": SPELLS[params.spell], "params": params}
    return w


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    spell: Spell = f["spell"]

    world.say(f"At {world.setting.place}, {hero.id} was a {f['params'].trait} child who carried {item.phrase}.")
    world.say(f"The folk in the market called the charm {spell.label}, and they said it belonged to the old songs.")
    world.para()
    world.say(f"One busy morning, {hero.id} wanted to {spell.action}.")
    world.say(f"But {spell.caution}, and {parent.label} frowned at the noise and the pushing crowd.")
    world.say(f"Then {spell.consequence}, and a seller cried out that the aisle was too narrow for such a thing.")
    world.para()

    if spell.id == "magic":
        world.say(f"{hero.id} nearly made a scene, but {parent.label} lifted a hand and asked for a softer word.")
        world.say(f"{hero.id} whispered the charm again, and the market breeze calmed the hanging cloths.")
        world.say(f"The sterile basket stayed steady, and no stall was upset.")
    elif spell.id == "quail":
        world.say(f"{hero.id} saw the quail trembling beneath a cart and stopped at once.")
        world.say(f"{hero.id} knelt still, and the quail settled beside {hero.pronoun('object')} as gentle as a shawl.")
        world.say(f"The crowd laughed kindly, because caution made the little bird safe.")
    else:
        world.say(f"{hero.id} tried to schlepp the sacks alone, but they slipped and bumped a stack of pears.")
        world.say(f"{parent.label} hurried over, and together they shared the load instead of pushing through the crowd.")
        world.say(f"Once the sacks were balanced, the sterile basket and the market wares stayed safe.")
    world.say(f"In the end, {hero.id} left the crowded market wiser, and the folk tale ended with care instead of trouble.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    spell: Spell = f["spell"]
    return [
        QAItem(
            question=f"Who is the story about at the crowded market?",
            answer=f"It is about {hero.id}, a {f['params'].trait} {hero.type}, and {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {spell.label}?",
            answer=f"{hero.id} wanted to {spell.action}, but the {spell.caution.lower()}.",
        ),
        QAItem(
            question=f"What was special about the item {hero.id} carried?",
            answer=f"It was {item.phrase}, so the story kept it safe and clean in the market crowd.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a crowded market?", answer="A crowded market is a busy place where many people sell and buy things close together."),
        QAItem(question="What does caution mean?", answer="Caution means being careful so nobody gets hurt or causes trouble."),
        QAItem(question="What is a folk tale?", answer="A folk tale is an old story told from person to person, usually with a lesson or a wise ending."),
        QAItem(question="What is magic in stories?", answer="Magic in stories is a special power that can change how things happen, often in surprising ways."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale set in {world.setting.place} about {f['hero'].id}, a child with a {f['item'].label}, who meets a little problem and learns caution.",
        f"Tell a child-friendly story with magic, conflict, and a careful ending that uses the words sterile, quail, and schlepp.",
        f"Write a short story about a crowded market where someone must choose a safer way after a magical idea goes wrong.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} ({e.type:7}) owner={e.owner} worn_by={e.worn_by}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"WQ: {item.question}")
            print(f"WA: {item.answer}")


CURATED = [
    StoryParams(place="market", spell="magic", item="basket", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="market", spell="quail", item="quail", name="Ravi", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="market", spell="schlepp", item="sacks", name="Tala", gender="girl", parent="mother", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show allowed/3.\n#show usable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show allowed/3."))
        combos = sorted(set(asp.atoms(model, "allowed")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

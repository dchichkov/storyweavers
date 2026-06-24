#!/usr/bin/env python3
"""
A small ghost-story world built from the seed: believe, spill-gerund, rhyme,
foreshadowing. A child notices a spooky rumor, something spills, and the truth
turns out kinder than feared.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    mess: str


@dataclass
class Gloom:
    id: str
    label: str
    foreshadow: str
    rhyme: str
    twist: str


@dataclass
class StoryParams:
    place: str
    item: str
    gloom: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting("the attic", True),
    "hall": Setting("the old hall", True),
    "basement": Setting("the basement", True),
    "garden": Setting("the moonlit garden", False),
}

ITEMS = {
    "lantern": Item("lantern", "lantern", "a little lantern with a glass door", "hand", "spilled"),
    "tea": Item("tea", "tea cup", "a warm teacup", "hand", "spilled"),
    "book": Item("book", "story book", "a thin story book", "hand", "spilled"),
}

GLOOMS = {
    "whisper": Gloom(
        "whisper",
        "whisper",
        "a soft whisper that said, 'Don't go near the stairs.'",
        "tap and flap and little clap",
        "The whisper sounded spooky, but it was only the wind in a loose sash.",
    ),
    "shadow": Gloom(
        "shadow",
        "shadow",
        "a dark shadow by the door that seemed to lean and sway",
        "sway and play and drift away",
        "The shadow looked tall, but it was only a coat on a hook.",
    ),
    "bump": Gloom(
        "bump",
        "bump",
        "a bump-bump sound under the floorboards",
        "bump and thump and soft little lump",
        "The bump was a sleepy mouse moving crumbs under a board.",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Mia"]
BOY_NAMES = ["Theo", "Finn", "Noah", "Eli", "Ben"]
TRAITS = ["curious", "careful", "brave", "gentle", "sly"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


def rhyme_line(gloom: Gloom) -> str:
    return f"Tap and flap, then hush and nap; {gloom.rhyme}."


def foreshadow_line(gloom: Gloom, item: Item) -> str:
    return f"Even before anyone touched {item.label}, {gloom.foreshadow}"


def spill_effect(item: Entity, amount: float = 1.0) -> None:
    item.meters["spilled"] = item.meters.get("spilled", 0.0) + amount


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    item = ITEMS[params.item]
    gloom = GLOOMS[params.gloom]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"fear": 0.0, "believe": 0.0, "calm": 0.0},
        memes={"curiosity": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="Mom" if params.parent == "mother" else "Dad",
        meters={"care": 1.0},
    ))
    thing = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.id,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"spilled": 0.0},
    ))

    world.say(f"{hero.id} was a {params.gender} who liked quiet places and small mysteries.")
    world.say(f"{hero.id} loved to believe the old stories, because believing made the dark feel less empty.")
    world.say(f"One evening, in {setting.place}, {foreshadow_line(gloom, thing)}")
    world.say(rhyme_line(gloom))

    world.para()
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {thing.label} close and listened again.")
    world.say(f"Then {hero.id} heard the {gloom.label}. It sounded like a ghostly warning.")
    hero.meters["fear"] += 1
    hero.meters["believe"] += 1

    world.para()
    world.say(f"{hero.id} tried to walk past the dark corner, but {thing.label} tipped and spilled.")
    spill_effect(thing)
    world.say(f"That made a shiny little mess, and the tiny spill glittered like a pale moon on the floor.")
    world.say(f"{parent.label} came near with a calm smile, not a scary face.")
    world.say(f"Together they looked at the spooky sign and found the truth behind it.")
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - 1)
    hero.meters["calm"] += 1

    world.para()
    world.say(f"{gloom.twist}")
    world.say(f"{hero.id} laughed softly, because the ghost story was only a wrong guess.")
    world.say(f"After that, {hero.id} believed a kinder thing: every strange sound has a reason, and the dark can be understood.")
    world.say(f"The spill was wiped away, and the room felt warm and still.")
    world.facts.update(hero=hero, parent=parent, item=thing, gloom=gloom)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            for gloom in GLOOMS:
                combos.append((place, item, gloom))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("spills_on", iid, item.region))
    for gid in GLOOMS:
        lines.append(asp.fact("gloom", gid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,G) :- setting(P), item(I), gloom(G).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child that includes the word "believe" and a small spill.',
        f"Tell a gentle spooky story set in {world.setting.place} where {f['hero'].id} hears {f['gloom'].label} and learns not to be afraid.",
        f"Write a rhyme-filled story about a child named {f['hero'].id} and a harmless ghostly misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    gloom: Gloom = f["gloom"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a curious little child who heard a spooky sound in {world.setting.place}.",
        ),
        QAItem(
            question=f"What made {hero.id} feel scared at first?",
            answer=f"The {gloom.label} made {hero.id} think a ghost might be near, so the dark felt spooky for a moment.",
        ),
        QAItem(
            question=f"What spilled in the story?",
            answer=f"{hero.id}'s {item.label} spilled, making a small shiny mess on the floor.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling calm again after learning the scary sound had a simple reason.",
        ),
        QAItem(
            question=f"Who helped {hero.id} feel better?",
            answer=f"{parent.label} helped by staying calm and looking at the problem with {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shadow?",
            answer="A shadow is a dark shape made when something blocks the light.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues to figure out what is really happening.",
        ),
        QAItem(
            question="What does it mean to believe something?",
            answer="To believe something means to think it is true.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story world with rhyme and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gloom", choices=GLOOMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    pick = (
        args.place or None,
        args.item or None,
        args.gloom or None,
    )
    if all(pick):
        return StoryParams(place=pick[0], item=pick[1], gloom=pick[2], name=args.name or "Mina",
                           gender=args.gender or "girl", parent=args.parent or "mother")
    place, item, gloom = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, gloom=gloom, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="attic", item="lantern", gloom="whisper", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="hall", item="book", gloom="shadow", name="Theo", gender="boy", parent="father"),
    StoryParams(place="basement", item="tea", gloom="bump", name="Ivy", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### {p.name}: {p.place}, {p.item}, {p.gloom}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

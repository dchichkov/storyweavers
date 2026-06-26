#!/usr/bin/env python3
"""
storyworlds/worlds/taffy_baton_olympian_moral_value_animal_story.py
====================================================================

A small animal-story world about a proud little olympian, a baton, and a piece
of taffy, built around a simple moral value: share what helps, and keep a promise.

The seed idea:
---
A little animal hero wants to shine in a little race. The hero loves a bright
baton and gets a piece of taffy as a treat. Then a mistake or a selfish choice
puts the baton or the taffy at risk. A friend or elder points out the harm,
the hero learns a moral lesson, and the story ends with a better choice:
returning, sharing, or apologizing.

World model:
---
Characters have physical meters and emotional memes. The physical state tracks
holding, mess, and whether an object is lost or used up. The emotional state
tracks pride, worry, guilt, generosity, and friendship. The narration is driven
by those state changes, not by a frozen template.

The ASP twin mirrors the Python reasonableness gate:
---
A story is valid only when the chosen object can honestly be at risk and a
reasonable resolution exists in the supported moral-action catalog.
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
    held_by: Optional[str] = None
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
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    risk_kind: str
    risk_place: str
    plural: bool = False


@dataclass
class MoralMove:
    id: str
    label: str
    verb: str
    promise: str
    fix: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


SETTINGS = {
    "meadow": Place("the meadow", False, {"race", "share"}),
    "barnyard": Place("the barnyard", False, {"race", "share"}),
    "playroom": Place("the playroom", True, {"share"}),
}

TRAITS = ["brave", "cheerful", "quick", "proud", "curious", "gentle"]
ANIMAL_TYPES = ["rabbit", "fox", "bear", "mouse", "puppy", "kitten"]
NAMES = {
    "rabbit": ["Milo", "Nina", "Pip", "Luna"],
    "fox": ["Fenn", "Tara", "Sly", "Rita"],
    "bear": ["Ollie", "Bruno", "Mina", "Bess"],
    "mouse": ["Toby", "Poppy", "Jinx", "Mara"],
    "puppy": ["Buddy", "Kiki", "Nori", "Zed"],
    "kitten": ["Tilly", "Momo", "Lila", "Pax"],
}


TREASURES = {
    "baton": Treasure(
        id="baton",
        label="baton",
        phrase="a shiny baton",
        type="baton",
        risk_kind="lost",
        risk_place="track",
        plural=False,
    ),
    "taffy": Treasure(
        id="taffy",
        label="taffy",
        phrase="a sweet stick of taffy",
        type="taffy",
        risk_kind="eaten",
        risk_place="mouth",
        plural=False,
    ),
}

MOVES = {
    "share_taffy": MoralMove(
        id="share_taffy",
        label="sharing the taffy",
        verb="share the taffy",
        promise="if you have two treats, you can give one away",
        fix="shared it with a friend",
        helps={"taffy"},
    ),
    "return_baton": MoralMove(
        id="return_baton",
        label="returning the baton",
        verb="bring back the baton",
        promise="if something belongs to someone else, you should return it",
        fix="gave the baton back",
        helps={"baton"},
    ),
    "apologize": MoralMove(
        id="apologize",
        label="apologizing",
        verb="say sorry",
        promise="when you make a mistake, saying sorry helps mend the hurt",
        fix="said sorry and made it right",
        helps={"baton", "taffy"},
    ),
}

CURATED = [
    ("meadow", "baton"),
    ("barnyard", "taffy"),
    ("playroom", "taffy"),
]


@dataclass
class StoryParams:
    place: str
    treasure: str
    animal: str
    name: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(treasure: Treasure, place: Place) -> bool:
    return treasure.risk_place in {"track", "mouth"} and place.affords


def choose_move(treasure: Treasure) -> MoralMove:
    if treasure.id == "baton":
        return MOVES["return_baton"]
    return MOVES["share_taffy"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place_id, place in SETTINGS.items():
        for treasure_id, treasure in TREASURES.items():
            if treasure.id == "baton" and "race" in place.affords:
                out.append((place_id, treasure_id))
            if treasure.id == "taffy" and "share" in place.affords:
                out.append((place_id, treasure_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: a baton, taffy, and a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--name")
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
    if args.place and args.treasure:
        if (args.place, args.treasure) not in valid_combos():
            raise StoryError("No valid story matches that place and treasure.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treasure is None or c[1] == args.treasure)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, treasure = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(NAMES[animal])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, treasure=treasure, animal=animal, name=name, trait=trait)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("risk_place", tid, t.risk_place))
        lines.append(asp.fact("risk_kind", tid, t.risk_kind))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        for h in sorted(m.helps):
            lines.append(asp.fact("helps", mid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Treasure) :- affords(Place, race), risk_place(Treasure, track).
valid(Place, Treasure) :- affords(Place, share), risk_place(Treasure, mouth).
moral_fix(Treasure, Move) :- move(Move), helps(Move, Treasure).
valid_story(Place, Treasure) :- valid(Place, Treasure), moral_fix(Treasure, _).
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def _hero_line(world: World, hero: Entity) -> str:
    return f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} {hero.type} who loved to help."


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    treasure = TREASURES[params.treasure]
    move = choose_move(treasure)
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.animal,
        meters={},
        memes={"trait_word": params.trait, "pride": 1.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type="animal",
        label="a small friend",
        memes={"kindness": 1.0},
    ))
    item = world.add(Entity(
        id=treasure.id,
        type=treasure.type,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=hero.id,
        caretaker=friend.id,
        held_by=hero.id,
        plural=treasure.plural,
        meters={"safe": 1.0},
    ))

    world.say(f"{hero.id} was a little {params.trait} {params.animal} who loved to run and help.")
    world.say(f"{hero.pronoun().capitalize()} had {item.phrase} and felt proud of it.")
    world.para()
    if treasure.id == "baton":
        world.say(f"One bright day at {place.name}, {hero.id} wanted to race with the shiny baton.")
        world.say(f"{hero.id} ran too fast and the baton slipped from {hero.pronoun('possessive')} paws.")
        hero.memes["worry"] = 1.0
        item.meters["lost"] = 1.0
        world.say(f"{friend.id} looked around and said, \"If something belongs to someone, it should go back.\"")
        hero.memes["guilt"] = 1.0
        world.para()
        world.say(f"{hero.id} took a slow breath, found the baton, and gave it back.")
        world.say(f"That was the right thing to do, and {hero.id} felt lighter inside.")
        hero.memes["pride"] = 0.0
        hero.memes["kindness"] = 1.0
        item.held_by = None
    else:
        world.say(f"One warm day in {place.name}, {hero.id} found a sweet stick of taffy.")
        world.say(f"{hero.id} wanted to keep it all, but {friend.id} watched with sad eyes.")
        hero.memes["greedy"] = 1.0
        world.say(f"{friend.id} said, \"If you have enough, sharing can make two hearts happy.\"")
        hero.memes["guilt"] = 1.0
        world.para()
        world.say(f"{hero.id} broke the taffy in two and shared it with {friend.id}.")
        world.say(f"The treat was smaller, but the kindness felt bigger.")
        item.meters["eaten"] = 1.0
        item.held_by = None
        hero.memes["generous"] = 1.0

    world.facts.update(
        hero=hero,
        friend=friend,
        treasure=item,
        place=place,
        move=move,
        moral=move.promise,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for young children about {f["hero"].id}, {f["treasure"].label}, and a moral choice.',
        f"Tell a gentle story where a {f['hero'].type} named {f['hero'].id} learns to {f['move'].verb}.",
        f'Write a simple story that includes "{f["treasure"].label}" and ends with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    treasure = f["treasure"]
    place = f["place"]
    if treasure.id == "baton":
        return [
            QAItem(
                question=f"What did {hero.id} lose at {place.name}?",
                answer=f"{hero.id} lost the baton, but then {hero.pronoun()} gave it back.",
            ),
            QAItem(
                question=f"What moral did {hero.id} learn about the baton?",
                answer="The story teaches that if something belongs to someone, you should return it.",
            ),
            QAItem(
                question=f"How did {hero.id} feel after doing the right thing?",
                answer=f"{hero.id} felt lighter and happier after returning the baton.",
            ),
        ]
    return [
        QAItem(
            question=f"What sweet thing did {hero.id} have?",
            answer=f"{hero.id} had taffy.",
        ),
        QAItem(
            question=f"What good choice did {hero.id} make with the taffy?",
            answer=f"{hero.id} shared the taffy with a friend.",
        ),
        QAItem(
            question=f"What moral did {hero.id} learn from the taffy story?",
            answer="The story teaches that sharing can make everyone happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is taffy?",
            answer="Taffy is a chewy sweet candy that people often stretch or pull before eating.",
        ),
        QAItem(
            question="What is a baton?",
            answer="A baton is a short stick that can be passed in a race or used to lead a parade.",
        ),
        QAItem(
            question="Who is an olympian?",
            answer="An olympian is an athlete who takes part in the Olympic Games or trains very hard like one.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, treasure) combos:\n")
        for place, treasure in triples:
            print(f"  {place:9} {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, treasure) in enumerate(CURATED):
            params = StoryParams(
                place=place,
                treasure=treasure,
                animal="rabbit",
                name=f"Hero{i+1}",
                trait="brave",
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
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
            header = f"### {p.name}: {p.treasure} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

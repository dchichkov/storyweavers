#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story style domain about
hassocks, style, conflict, transformation, and a bad ending.

The premise is simple: a careful animal wants to arrange a cozy room in a
certain style, but another animal keeps using the hassock for a different
purpose. Their conflict changes the room, and the ending lands badly.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    style: str = "cottage"
    setting: str = "lantern room"
    hero: str = "Milo"
    rival: str = "Tansy"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    species: str
    role: str
    meters: dict[str, float]
    memes: dict[str, float]


@dataclass
class Room:
    style: str
    setting: str
    hassock_color: str
    hassock_use: str
    transformed: bool = False
    damaged: bool = False
    conflict: bool = False
    ending: str = ""
    facts: dict = None

    def __post_init__(self):
        if self.facts is None:
            self.facts = {}


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.room = Room(
            style=params.style,
            setting=params.setting,
            hassock_color="red",
            hassock_use="footrest",
        )
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.world_log: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


STYLE_DETAILS = {
    "cottage": {
        "look": "soft checkered cloth and warm little shelves",
        "wish": "make the room feel snug and tidy",
        "shift": "look less cozy and more crowded",
        "ending": "the room ended up lopsided and gloomy",
    },
    "garden": {
        "look": "leaf-green ribbons and sunny basket colors",
        "wish": "make the room feel bright and fresh",
        "shift": "look less bright and more muddy",
        "ending": "the room ended up messy and sorry-looking",
    },
    "storybook": {
        "look": "painted stars and curly golden trim",
        "wish": "make the room feel magical and neat",
        "shift": "look less magical and more plain",
        "ending": "the room ended up dull and unfinished",
    },
}

ANIMALS = {
    "Milo": ("rabbit", "careful"),
    "Tansy": ("fox", "restless"),
    "Pip": ("mouse", "proud"),
    "Mara": ("cat", "tidy"),
    "Bram": ("bear", "sturdy"),
}

ASP_RULES = r"""
style_room(Style) :- style(Style).
has_hassock(Room) :- room(Room), hassock(Room).
wants_style(Hero, Style) :- animal(Hero), prefers(Hero, Style).
conflict(Hero, Rival) :- wants_style(Hero, Style), uses(Rival, hassock, DifferentWay), not same_way(Style, DifferentWay).
transform(Room) :- conflict(Hero, Rival), room(Room).
bad_ending(Room) :- transform(Room), damaged(Room).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for style in STYLE_DETAILS:
        lines.append(asp.fact("style", style))
    for name, (species, trait) in ANIMALS.items():
        lines.append(asp.fact("animal", name))
        lines.append(asp.fact("species", name, species))
        lines.append(asp.fact("trait", name, trait))
    lines.append(asp.fact("room", "room"))
    lines.append(asp.fact("hassock", "room"))
    lines.append(asp.fact("prefers", "Milo", "cottage"))
    lines.append(asp.fact("prefers", "Milo", "storybook"))
    lines.append(asp.fact("uses", "Tansy", "hassock", "nap"))
    lines.append(asp.fact("same_way", "cottage", "rest"))
    lines.append(asp.fact("same_way", "storybook", "display"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show conflict/2.\n#show bad_ending/1.\n"), models=1)
    if not models:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program grounds and solves.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with hassock-style conflict and a bad ending.")
    ap.add_argument("--style", choices=sorted(STYLE_DETAILS))
    ap.add_argument("--setting", choices=["lantern room", "window nook", "quiet den"])
    ap.add_argument("--hero", choices=sorted(ANIMALS))
    ap.add_argument("--rival", choices=sorted(ANIMALS))
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
    style = args.style or rng.choice(list(STYLE_DETAILS))
    setting = args.setting or rng.choice(["lantern room", "window nook", "quiet den"])
    hero = args.hero or rng.choice(["Milo", "Pip", "Mara"])
    rival = args.rival or rng.choice([n for n in ANIMALS if n != hero])
    if hero == rival:
        raise StoryError("Hero and rival must be different animals.")
    return StoryParams(style=style, setting=setting, hero=hero, rival=rival)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    hero_species, hero_trait = ANIMALS[params.hero]
    rival_species, rival_trait = ANIMALS[params.rival]
    detail = STYLE_DETAILS[params.style]

    hero = world.add(Entity(params.hero, hero_species, hero_trait, {"order": 1.0}, {"hope": 1.0, "worry": 0.0}))
    rival = world.add(Entity(params.rival, rival_species, rival_trait, {"order": 0.2}, {"mischief": 1.0, "pride": 1.0}))

    world.room.facts = {
        "hero": hero,
        "rival": rival,
        "style": params.style,
        "setting": params.setting,
    }

    world.say(f"In {params.setting}, {params.hero} the {hero_species} cared about style.")
    world.say(f"{hero.name} wanted the room to {detail['wish']}, with {detail['look']}.")
    world.say(f"But {rival.name} the {rival_species} kept dragging the hassock around like it was a toy.")

    world.room.conflict = True
    hero.memes["worry"] += 1.0
    rival.memes["mischief"] += 1.0
    world.room.transformed = True
    world.room.hassock_use = "perch"
    world.room.hassock_color = "scratched"
    world.room.damaged = True

    world.say(f"{hero.name} asked for care, but {rival.name} would not stop.")
    world.say(f"The hassock got turned into a wobbling perch, and the room began to {detail['shift']}.")
    world.say(f"At last, the whole place could not be saved, and {detail['ending']}.")

    world.room.ending = detail["ending"]
    world.room.facts["conflict"] = True
    world.room.facts["transformed"] = True
    world.room.facts["damaged"] = True

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.room.facts
    return [
        f"Write an Animal Story about {f['hero'].name} and {f['rival'].name} where a hassock changes the room's style.",
        f"Tell a short story for children with conflict, transformation, and a bad ending in a {f['setting']}.",
        f"Create a gentle animal tale where the word 'hassock' matters and the room style cannot be kept.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.room.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    return [
        QAItem(
            question=f"Who wanted the room to keep its {f['style']} style?",
            answer=f"{hero.name} the {hero.species} wanted the room to keep its {f['style']} style.",
        ),
        QAItem(
            question="What did the other animal keep doing with the hassock?",
            answer=f"{rival.name} kept dragging the hassock around and using it like a toy instead of leaving it alone.",
        ),
        QAItem(
            question="What changed in the room during the story?",
            answer=f"The hassock changed from a footrest into a wobbling perch, and the room lost the neat {f['style']} feel.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the room could not be fixed in time, and {world.room.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    style = world.room.style
    return [
        QAItem(
            question="What is a hassock?",
            answer="A hassock is a soft low seat or footrest, often used to rest your feet or sit near a chair.",
        ),
        QAItem(
            question="What does style mean in a room?",
            answer="Style means the way a room looks and feels, such as cozy, bright, fancy, or simple.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or disagreement that makes the characters struggle before the story can end.",
        ),
        QAItem(
            question="What is transformation in a story?",
            answer="Transformation means something changes into a new form or becomes different during the story.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when things do not get fixed and the characters do not get the happy result they wanted.",
        ),
        QAItem(
            question=f"Why might a room be called {style}?",
            answer=f"A room might be called {style} if its colors, cloth, and objects all fit that {style} feeling.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"style={world.room.style}")
    lines.append(f"setting={world.room.setting}")
    lines.append(f"hassock_color={world.room.hassock_color}")
    lines.append(f"hassock_use={world.room.hassock_use}")
    lines.append(f"conflict={world.room.conflict}")
    lines.append(f"transformed={world.room.transformed}")
    lines.append(f"damaged={world.room.damaged}")
    for ent in world.entities.values():
        lines.append(f"{ent.name}: species={ent.species}, role={ent.role}, meters={ent.meters}, memes={ent.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
    StoryParams(style="cottage", setting="lantern room", hero="Milo", rival="Tansy"),
    StoryParams(style="storybook", setting="window nook", hero="Mara", rival="Pip"),
    StoryParams(style="garden", setting="quiet den", hero="Pip", rival="Milo"),
]


def valid_story(params: StoryParams) -> bool:
    return params.hero != params.rival and params.style in STYLE_DETAILS


def asp_valid_story_tuples() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4.\n"))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_parity() -> int:
    py = {(p.style, p.setting, p.hero, p.rival) for p in CURATED if valid_story(p)}
    asp_set = set(asp_valid_story_tuples())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} curated story tuples.")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print(" only in python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only in asp:", sorted(asp_set - py))
    return 1


def asp_story_program(show: str) -> str:
    return f"""
style(cottage).
style(garden).
style(storybook).
room(room).
hassock(room).
animal(Milo). animal(Tansy). animal(Pip). animal(Mara). animal(Bram).
prefers(Milo,cottage). prefers(Milo,storybook). prefers(Mara,garden).
uses(Tansy,hassock,perch).
uses(Pip,hassock,toy).
same_way(cottage,order).
same_way(storybook,order).
same_way(garden,order).

conflict(H,R) :- prefers(H,S), uses(R,hassock,D), not same_way(S,D).
transform(room) :- conflict(H,R), room(room).
damaged(room) :- transform(room), hassock(room).

valid(S,Room,H,R) :- style(S), room(Room), animal(H), animal(R), H != R, conflict(H,R).

#show valid/4.
#show conflict/2.
#show transform/1.
#show damaged/1.
{show}
"""


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_story_program(""))
        return
    if args.verify:
        sys.exit(asp_verify_parity())
    if args.asp:
        import asp
        model = asp.one_model(asp_story_program(""))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid story tuples:")
        for t in vals:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.rival} / {p.style}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

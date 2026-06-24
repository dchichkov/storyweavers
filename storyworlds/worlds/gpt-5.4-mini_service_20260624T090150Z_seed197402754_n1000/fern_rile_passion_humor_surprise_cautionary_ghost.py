#!/usr/bin/env python3
"""
A tiny ghost-story world with humor, surprise, and a cautionary turn.

Seed tale:
A child named Fern, a sibling named Rile, and a friend named Passion visit a
creaky old house. They expect a spooky ghost, but the ghost turns out funny,
then startling, and finally helpful: it warns them away from a brittle floorboard
and from waking the sleeping cat. The ending proves they listened and left with
a safer, warmer feeling.

This world keeps the story grounded in simulated state:
- characters have meters (physical) and memes (emotional)
- a ghost can spook, joke, and warn
- a risky choice can raise caution and be resolved by a safer action
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
    kind: str = "thing"   # character | ghost | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    risky: bool = False
    soothed_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    thing: str
    name: str
    sibling: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "old_house": Setting(place="the old house", mood="creaky", affords={"attic", "hallway"}),
    "garden_shed": Setting(place="the garden shed", mood="moonlit", affords={"shed", "hallway"}),
}

THINGS = {
    "lantern": Thing(id="lantern", label="lantern", phrase="a small lantern", risky=False),
    "fern": Thing(id="fernplant", label="fern", phrase="a potted fern", risky=True, soothed_by="water"),
    "bell": Thing(id="bell", label="bell", phrase="a shiny hand bell", risky=True, soothed_by="silence"),
}

ACTIVITIES = {
    "attic": {
        "verb": "peek into the attic",
        "gerund": "peeking into the attic",
        "risk": "dust",
        "turn": "a mouse wearing a ribbon",
        "caution": "the floorboard near the window was loose",
        "fix": "hold the lantern and step around the loose board",
    },
    "shed": {
        "verb": "look inside the shed",
        "gerund": "looking inside the shed",
        "risk": "shadows",
        "turn": "a cricket orchestra",
        "caution": "the paint can was wobbling on a shelf",
        "fix": "open the door slowly and leave the wobbly can alone",
    },
    "hallway": {
        "verb": "follow the creaking hallway",
        "gerund": "following the creaking hallway",
        "risk": "spooks",
        "turn": "a tiny ghost in striped slippers",
        "caution": "the rug hid a slippery edge",
        "fix": "walk near the wall and watch the rug edge",
    },
}


GIRL_NAMES = ["Fern", "Mina", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Rile", "Otis", "Milo", "Theo", "Eli"]
SIBLING_NAMES = ["Passion", "Pip", "Wren", "Juniper", "Bram"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with humor, surprise, and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
    place = args.place or rng.choice(list(SETTINGS))
    thing = args.thing or rng.choice(list(THINGS))
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.thing and args.thing not in THINGS:
        raise StoryError("Unknown thing.")
    if not SETTINGS[place].affords:
        raise StoryError("(No story: that place has no usable ghost-story path.)")
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sibling = args.sibling or rng.choice(SIBLING_NAMES)
    return StoryParams(place=place, thing=thing, name=name, sibling=sibling)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    thing = THINGS[params.thing]
    act = ACTIVITIES["attic" if params.place == "old_house" else "shed"]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="girl" if params.sibling in SIBLING_NAMES else "boy"))
    ghost = world.add(Entity(id="Ghost", kind="ghost", type="ghost", label="a little ghost"))
    item = world.add(Entity(id=thing.id, type="thing", label=thing.label, phrase=thing.phrase, owner=hero.id))

    hero.memes["curiosity"] = 1
    sibling.memes["humor"] = 1
    ghost.memes["playful"] = 1

    world.say(
        f"{hero.id} and {sibling.id} went to {setting.place} on a {setting.mood} evening, "
        f"with {item.phrase} tucked under {hero.pronoun('possessive')} arm."
    )
    world.say(
        f"{hero.id} wanted to {act['verb']}, because the house felt mysterious and a little funny."
    )
    world.para()
    world.say(
        f"At the door, {sibling.id} whispered that a ghost might jump out, and {hero.id} tried not to laugh."
    )

    # humor
    ghost.memes["humor"] = 1
    world.say(
        f"Then {ghost.pronoun().capitalize()} popped from behind a curtain and said, "
        f'"Boo," but {ghost.pronoun()} sounded like a squeaky teacup.'
    )
    world.say(
        f"{sibling.id} snorted, and even {hero.id} giggled, because the ghost had a sticker on its forehead."
    )

    # surprise
    world.para()
    ghost.memes["surprise"] = 1
    hero.memes["surprise"] = 1
    world.say(
        f"The ghost spun around and showed them something surprising: a tiny mouse wearing a ribbon, "
        f"which had been hiding under an old chair."
    )
    world.say(
        f"{hero.id} blinked, then smiled, because the scariest thing in the room was only a small, busy mouse."
    )

    # cautionary turn
    hero.memes["caution"] = 1
    sibling.memes["caution"] = 1
    world.say(
        f"Then the ghost pointed with one pale finger and warned, "
        f'"Careful. {act["caution"].capitalize()}."'
    )
    world.say(
        f"{hero.id} looked where {ghost.pronoun()} pointed and stepped back fast, "
        f"so nobody disturbed the risky spot."
    )
    world.say(
        f"After that, {hero.id} chose to {act['fix']}, and {sibling.id} held the lantern steady."
    )

    # resolution
    hero.memes["relief"] = 1
    sibling.memes["relief"] = 1
    ghost.memes["kindness"] = 1
    world.para()
    world.say(
        f"Inside the quiet room, the spooky feeling melted into a silly one, and the house seemed less lonely."
    )
    world.say(
        f"{hero.id} left with {item.phrase} still safe, {sibling.id} still laughing, and the ghost waving from the dark."
    )

    world.facts.update(
        hero=hero,
        sibling=sibling,
        ghost=ghost,
        item=item,
        thing=thing,
        act=act,
        setting=setting,
        caution=act["caution"],
        fix=act["fix"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for children that includes the word "{f["hero"].id}".',
        f"Tell a funny spooky story where {f['hero'].id} and {f['sibling'].id} meet a ghost in {f['setting'].place}.",
        f"Write a cautionary tale with humor and surprise about {f['hero'].id} keeping {f['item'].label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sib, ghost, item, act = f["hero"], f["sibling"], f["ghost"], f["item"], f["act"]
    return [
        QAItem(
            question=f"Who went to {f['setting'].place} with the {item.label}?",
            answer=f"{hero.id} went with {sib.id}, and {item.phrase} stayed with {hero.id} the whole time.",
        ),
        QAItem(
            question="Why did the story feel funny instead of truly scary?",
            answer=f"The ghost said boo in a squeaky way, had a sticker on its forehead, and made the whole scene feel silly.",
        ),
        QAItem(
            question="What made the surprise in the middle of the story?",
            answer=f"The ghost suddenly showed a tiny mouse wearing a ribbon, which surprised {hero.id} and {sib.id}.",
        ),
        QAItem(
            question=f"What caution did the ghost give before {hero.id} kept going?",
            answer=f"The ghost warned them that {act['caution']} and told them to be careful.",
        ),
        QAItem(
            question=f"How did {hero.id} avoid trouble?",
            answer=f"{hero.id} stepped back, then chose to {act['fix']}, while {sib.id} held the lantern steady.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is usually a spooky character from a story, often shown as a pale figure that can surprise people.",
        ),
        QAItem(
            question="Why should you be careful around a loose floorboard?",
            answer="A loose floorboard can shift or tip, so being careful helps keep feet safe and keeps the board from making a bigger problem.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives off light, which helps people see better in dark places.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.kind} {bits}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- hero_name(X).
sibling(X) :- sibling_name(X).
ghost(g).
humor(g) :- ghost(g), funny(g).
surprise(g) :- ghost(g), pops_out(g).
caution(P) :- risky(P), warned(P).
safe(P) :- caution(P), chose_carefully(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in THINGS:
        lines.append(asp.fact("thing", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    places = set(asp.atoms(model, "place"))
    py = set((p,) for p in SETTINGS)
    if places == py:
        print("OK: ASP matches Python registries.")
        return 0
    print("MISMATCH between ASP and Python registries.")
    return 1


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


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        out = []
        for p in SETTINGS:
            for t in THINGS:
                out.append(StoryParams(place=p, thing=t, name="Fern", sibling="Rile"))
        return out
    return [resolve_params(args, rng)]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show place/1. #show thing/1."))
        print("ASP model:", asp.atoms(model, "place"), asp.atoms(model, "thing"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, params in enumerate(resolve_all(args, random.Random(base_seed))):
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        rng = random.Random(base_seed)
        try:
            params = resolve_params(args, rng)
        except StoryError as err:
            print(err)
            return
        params.seed = base_seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### {i + 1}: {p.name} at {p.place} with {p.thing}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

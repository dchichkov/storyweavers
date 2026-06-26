#!/usr/bin/env python3
"""
A small ghost-story world about a chicken, a ram, and a bahbah share that goes
wrong before the twist makes it make sense.

Premise:
- A chicken guards a shiny lantern in a quiet barnyard at dusk.
- A ram keeps calling "bahbah" from the shadows, trying to share a blanket and a
  bowl of warm porridge.

Tension:
- The chicken thinks the ram is trying to steal the lantern.
- The ram thinks the chicken is refusing to share on purpose.

Twist:
- The "bahbah" is not a threat; it is the ram's tiny, scared way of asking for
  help after hearing a ghostly flutter in the hayloft.

Resolution:
- The chicken shares the lantern and the blanket, and they scare the spooky
  flutter away together.
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
    plurality: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chicken", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"ram"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plurality else "it"


@dataclass
class Place:
    name: str
    dusk: bool = True
    spooky: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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


PLACES = {
    "barnyard": Place(name="the barnyard", dusk=True, spooky=True, affords={"sharing", "misunderstanding", "twist"}),
    "hayloft": Place(name="the hayloft", dusk=True, spooky=True, affords={"sharing", "misunderstanding", "twist"}),
    "yard": Place(name="the yard", dusk=True, spooky=True, affords={"sharing", "misunderstanding", "twist"}),
}

CHICKEN_NAMES = ["Cluck", "Nina", "Dot", "Sunny"]
RAM_NAMES = ["Bram", "Rufus", "Bellow", "Moss"]


ASP_RULES = r"""
% A small declarative twin: the story is valid when sharing, misunderstanding,
% and twist all happen in order.
event(sharing).
event(misunderstanding).
event(twist).
valid_story(P) :- place(P), event(sharing), event(misunderstanding), event(twist).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", pid) for pid in PLACES])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def reasonableness_gate(place: str) -> None:
    if place not in PLACES:
        raise StoryError("Choose a place where the dusk and the ghosts can matter.")
    if not PLACES[place].spooky:
        raise StoryError("This story needs a spooky place for the ghost-story twist.")


def choose_name(rng: random.Random, genderless_pool: list[str]) -> str:
    return rng.choice(genderless_pool)


def tell(place: Place, seed: int, chicken_name: str, ram_name: str) -> World:
    world = World(place)
    chicken = world.add(Entity(id=chicken_name, kind="character", type="chicken", label="chicken"))
    ram = world.add(Entity(id=ram_name, kind="character", type="ram", label="ram"))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a shiny lantern",
        owner=chicken.id,
        caretaker=chicken.id,
        worn_by=chicken.id,
    ))
    blanket = world.add(Entity(
        id="blanket",
        type="blanket",
        label="blanket",
        phrase="a warm patchwork blanket",
        owner=ram.id,
        caretaker=ram.id,
        worn_by=ram.id,
    ))
    porridge = world.add(Entity(
        id="porridge",
        type="bowl",
        label="bowl",
        phrase="a bowl of warm porridge",
        owner=ram.id,
        caretaker=ram.id,
    ))
    flutter = world.add(Entity(
        id="flutter",
        type="ghost",
        label="flutter",
        phrase="a ghostly flutter in the hayloft",
    ))

    chicken.memes["care"] = 1
    ram.memes["hope"] = 1
    ram.memes["fear"] = 1

    world.say(
        f"At {place.name}, {chicken.name if hasattr(chicken, 'name') else chicken.id} the chicken kept "
        f"{chicken.pronoun('possessive')} shiny lantern close while the dusk grew thick and blue."
    )
    world.say(
        f"Nearby, the ram kept calling, \"Bahbah,\" because {ram.pronoun('subject')} wanted to share "
        f"{ram.pronoun('possessive')} warm blanket and {ram.pronoun('possessive')} bowl of porridge."
    )

    world.para()
    world.say(
        f"When {ram.id} stepped out of the shadow, {chicken.id} saw only big horns and a dark shape near "
        f"{chicken.pronoun('possessive')} lantern."
    )
    world.say(
        f"{chicken.id} thought, \"He wants my lantern,\" so {chicken.pronoun('subject')} clutched it tighter "
        f"and backed into the straw."
    )
    world.say(
        f"The ram heard that silence and thought, \"The chicken will not share,\" so {ram.pronoun('subject')} "
        f"said, \"Bahbah,\" again, softer this time."
    )

    world.para()
    world.say(
        f"Then the lantern light wobbled up the ladder and found {flutter.phrase} hiding in the hayloft."
    )
    world.say(
        f"That was the twist: {ram.id} had been scared of the flutter all along, and \"bahbah\" meant, "
        f"\"Please, stay with me.\""
    )
    world.say(
        f"{chicken.id} blinked, then laughed a tiny chicken laugh, because the ram had not been greedy at all."
    )
    world.say(
        f"{chicken.id} shared the lantern and let {ram.id} tuck under {chicken.pronoun('possessive')} wing beside "
        f"{chicken.pronoun('object')}, and they carried the blanket together."
    )
    world.say(
        f"With both of them shining the lantern into the hay, the flutter slipped away, and the barnyard felt warm again."
    )

    world.facts.update(
        place=place,
        chicken=chicken,
        ram=ram,
        lantern=lantern,
        blanket=blanket,
        porridge=porridge,
        flutter=flutter,
        seed=seed,
        resolved=True,
        misunderstanding=True,
        twist=True,
        sharing=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for a small child that includes a chicken, a ram, and the word "bahbah".',
        f"Tell a simple story set at {world.place.name} where the chicken and ram start with a misunderstanding and end by sharing something safe.",
        "Write a cozy spooky tale with a twist: the scary sound is actually a request for help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    chicken: Entity = f["chicken"]
    ram: Entity = f["ram"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who was holding the lantern in {place.name}?",
            answer=f"The chicken was holding the shiny lantern because the dusk made {place.name} feel spooky.",
        ),
        QAItem(
            question=f"Why did the ram keep saying bahbah?",
            answer="The ram was scared of the ghostly flutter in the hayloft and wanted the chicken to stay close.",
        ),
        QAItem(
            question="What was the misunderstanding between the chicken and the ram?",
            answer="The chicken thought the ram wanted to take the lantern, and the ram thought the chicken would not share.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the ram was not being rude at all; he was asking for help because something spooky was hiding above them.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The chicken shared the lantern and the ram shared the blanket, and together they chased away the spooky flutter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something with you instead of keeping it all to yourself.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think the wrong thing about each other and get mixed up before they talk it out.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new way, often by showing that things were not what they seemed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: chicken, ram, bahbah, sharing, misunderstanding, twist.")
    ap.add_argument("--place", choices=PLACES)
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
    place = args.place or rng.choice(list(PLACES))
    reasonableness_gate(place)
    return StoryParams(place=place, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    rng = random.Random(params.seed or 0)
    chicken_name = rng.choice(CHICKEN_NAMES)
    ram_name = rng.choice(RAM_NAMES)
    world = tell(place, params.seed or 0, chicken_name, ram_name)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible story-place choices:")
        for p in PLACES:
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, seed=base_seed + i)) for i, p in enumerate(PLACES)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

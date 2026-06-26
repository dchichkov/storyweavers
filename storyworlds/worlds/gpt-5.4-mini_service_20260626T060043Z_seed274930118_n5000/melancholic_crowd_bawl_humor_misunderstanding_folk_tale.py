#!/usr/bin/env python3
"""
A small folk-tale story world about a melancholic crow, a curious crowd, and a
funny misunderstanding that turns into a kinder ending.

The story model follows a tiny simulation:
- a crow can become lonely, noisy, and misunderstood
- a crowd can gather and grow uneasy or amused
- a child or villager can notice the mistake, help, and soften the scene

The prose is authored from the state changes, not a frozen template.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "crow": {"subject": "it", "object": "it", "possessive": "its"},
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "woman": {"subject": "she", "object": "her", "possessive": "her"},
            "man": {"subject": "he", "object": "him", "possessive": "his"},
            "crowd": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    noise: str
    meaning: str
    helps: str
    risk: str
    resolves_with: str


@dataclass
class StoryParams:
    place: str
    cause: str
    hero_name: str
    child_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, cause: Cause) -> None:
        self.place = place
        self.cause = cause
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "market": Place(
        id="market",
        label="the market square",
        kind="square",
        detail="Stalls leaned in a ring, and the old well sat in the middle like a quiet eye.",
        affords={"bawl", "gather"},
    ),
    "green": Place(
        id="green",
        label="the village green",
        kind="green",
        detail="The grass was soft, and the oak tree cast a round shade for the townsfolk.",
        affords={"bawl", "gather"},
    ),
    "bridge": Place(
        id="bridge",
        label="the stone bridge",
        kind="bridge",
        detail="The river ran below in a silver ribbon, and footsteps echoed on the stones.",
        affords={"bawl", "gather"},
    ),
}

CAUSES = {
    "lost_ring": Cause(
        id="lost_ring",
        label="a lost ring",
        noise="bawling",
        meaning="crying out loudly",
        helps="a little humor and a careful look",
        risk="the crowd thinks the crow has stolen something",
        resolves_with="the child finds the ring in the well grass",
    ),
    "stuck_bone": Cause(
        id="stuck_bone",
        label="a stuck fish bone",
        noise="bawling",
        meaning="making a loud, rough cry",
        helps="a sip of water and a crumb of bread",
        risk="the crowd thinks the crow is casting a gloomy spell",
        resolves_with="the child eases the bone free",
    ),
    "rain_badge": Cause(
        id="rain_badge",
        label="a rain-beaded ribbon",
        noise="bawling",
        meaning="calling out with a long, wobbling cry",
        helps="a laugh and a towel",
        risk="the crowd thinks the crow is warning of bad luck",
        resolves_with="the ribbon is only snagged on a thorn",
    ),
}

NAMES = ["Milo", "Tessa", "Anya", "Pip", "Jon", "Wren", "Lena", "Olin"]
CHILDREN = ["Ayla", "Ned", "Bram", "Mira", "Elsa", "Toby", "Sana", "Ivo"]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place], CAUSES[params.cause])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="crow",
        label="the crow",
        phrase="a melancholic crow with a bright black eye",
        memes={"melancholy": 2.0, "trust": 0.0, "relief": 0.0, "humor": 0.0, "misunderstanding": 0.0},
        meters={"hunger": 0.0, "noise": 0.0},
    ))
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type="girl",
        label="the child",
        phrase="a small village child with quick feet",
        memes={"curiosity": 1.0, "kindness": 0.0},
        meters={},
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="group",
        type="crowd",
        label="the crowd",
        phrase="the market folk",
        plural=True,
        memes={"unease": 0.0, "amusement": 0.0, "kindness": 0.0, "misunderstanding": 0.0},
        meters={"size": 12.0},
    ))
    return world


def tell(world: World) -> World:
    hero = world.get(next(k for k, e in world.entities.items() if e.type == "crow"))
    child = world.get(next(k for k, e in world.entities.items() if e.type == "girl"))
    crowd = world.get("crowd")
    cause = world.cause
    place = world.place

    world.say(f"Once, by {place.label}, there lived {hero.phrase}.")
    world.say(
        f"{hero.id} was melancholy in the morning, for the crow had seen too many gray days and too few kind ones."
    )
    world.say(
        f"Still, {hero.id} had a voice like a cracked kettle, and when the crow began to {cause.noise}, the sound carried far."
    )

    world.para()
    hero.meters["noise"] += 1.0
    crowd.memes["misunderstanding"] += 1.0
    crowd.memes["unease"] += 1.0
    world.say(f"A crowd gathered at once, as crowds do when one strange sound crosses a square.")
    world.say(
        f"The folk heard the {cause.noise} and did not know {cause.meaning}; so they whispered that {cause.risk}."
    )
    world.say(
        f"Some crossed their arms. Some stepped back. A few laughed the nervous sort of laugh that makes a child glance over a shoulder."
    )

    world.para()
    child.memes["curiosity"] += 1.0
    child.meters["steps"] = 1.0
    world.say(
        f"But {child.id}, being small and brave in the way of children, walked closer and looked up."
    )
    world.say(
        f'"Why are you crying so loudly?" {child.id} asked the crow, and the question was gentle enough to be a blanket.'
    )
    hero.memes["misunderstanding"] = 1.0
    world.say(
        f"{hero.id} flapped once, then twice, and the crowd leaned in to see whether the bird was angry or only lonely."
    )
    world.say(
        f"At last the truth came out: the crow was not cursing anyone at all; the crow was troubled by {cause.label}."
    )

    world.para()
    if cause.id == "lost_ring":
        world.say(
            f"The child laughed, not unkindly, because the ring had slipped from a ribbon and rolled near the well grass."
        )
        world.say(
            f"Together they found it, shiny as a fish scale, and the crowd laughed too, this time with relief."
        )
    elif cause.id == "stuck_bone":
        world.say(
            f"The child fetched water in a small cup and offered a crumb of bread, and the crow took both with great care."
        )
        world.say(
            f"After a swallow and a cough, the bone came free, and the whole square seemed to breathe again."
        )
    else:
        world.say(
            f"The child saw that the ribbon was caught on a thorn, and with one careful tug the snare was undone."
        )
        world.say(
            f"The crow gave a rough little bow, and the crowd, seeing how plain the trouble was, began to smile."
        )

    hero.memes["relief"] += 2.0
    hero.memes["melancholy"] = max(0.0, hero.memes["melancholy"] - 1.0)
    crowd.memes["amusement"] += 1.0
    crowd.memes["kindness"] += 1.0
    crowd.memes["misunderstanding"] = 0.0
    crowd.memes["unease"] = 0.0
    child.memes["kindness"] += 1.0
    hero.meters["noise"] = 0.0

    world.para()
    world.say(
        f"Then {hero.id} hopped to the edge of the well, bowed to {child.id}, and gave one final croaky call, less a bawl than a joke."
    )
    world.say(
        f"The folk laughed because they understood it now, and {place.label} felt lighter than it had at dawn."
    )
    world.say(
        f"From that day on, when the {cause.noise} rose from the stones, the villagers looked first for a small trouble before they looked for a large fear."
    )

    world.facts = {
        "hero": hero,
        "child": child,
        "crowd": crowd,
        "place": place,
        "cause": cause,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short folk tale about a melancholic crow whose bawling is misunderstood by a crowd.",
        f"Tell a gentle village story set at {world.place.label} where humor helps clear a misunderstanding.",
        f"Write a child-friendly tale in which {world.get(next(k for k, e in world.entities.items() if e.type == 'girl')).id} helps a crow and the crowd learns the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    child = world.facts["child"]
    crowd = world.facts["crowd"]
    place = world.facts["place"]
    cause = world.facts["cause"]

    return [
        QAItem(
            question="Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a melancholy crow who lived near {place.label}.",
        ),
        QAItem(
            question="Why did the crowd get confused?",
            answer=f"The crowd heard {hero.id} {cause.noise} and did not understand that the bird was upset about {cause.label}.",
        ),
        QAItem(
            question="Who helped clear up the mistake?",
            answer=f"{child.id} helped by looking closely, asking a kind question, and finding the real trouble.",
        ),
        QAItem(
            question="How did the ending change the crowd?",
            answer=f"At the end, the crowd was no longer uneasy; it was amused, kinder, and smiling instead of whispering.",
        ),
        QAItem(
            question="What made the story funny as well as gentle?",
            answer="The joke was that everyone expected a grand mystery, but the trouble was only a small, ordinary problem that the child could solve.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crowd?",
            answer="A crowd is a group of people gathered in one place.",
        ),
        QAItem(
            question="What does it mean to misunderstand something?",
            answer="To misunderstand something means to think it means one thing when it really means another.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is a way of being funny that can make a hard moment feel lighter.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that is often simple, memorable, and full of lessons or surprises.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_id(P).
cause(C) :- cause_id(C).

compatible(P, C) :- affords(P, bawl), affords(P, gather), cause_id(C), place_id(P).
valid_story(P, C) :- compatible(P, C).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_id", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid in CAUSES:
        lines.append(asp.fact("cause_id", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    out = []
    for pid, place in PLACES.items():
        if "bawl" in place.affords and "gather" in place.affords:
            for cid in CAUSES:
                out.append((pid, cid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP/Python parity matches ({len(a)} valid story combos).")
        return 0
    print("Mismatch between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale world about a melancholic crow, a crowd, and a misunderstanding.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--cause", choices=sorted(CAUSES))
    ap.add_argument("--name")
    ap.add_argument("--child")
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
    place = args.place or rng.choice(sorted(PLACES))
    cause = args.cause or rng.choice(sorted(CAUSES))
    name = args.name or rng.choice(NAMES)
    child = args.child or rng.choice(CHILDREN)
    return StoryParams(place=place, cause=cause, hero_name=name, child_name=child, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell(world)
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
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print()
        print("== world qa ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible story combos:")
        for p, c in combos:
            print(f"  {p} / {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            for cause in sorted(CAUSES):
                params = StoryParams(place=place, cause=cause, hero_name=NAMES[0], child_name=CHILDREN[0], seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

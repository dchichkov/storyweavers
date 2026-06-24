#!/usr/bin/env python3
"""
A small mythic storyworld about a gob, a cup of cappuccino, and a sacred test of symmetry.
The world is built around three narrative instruments: Curiosity, Bad Ending, and Surprise.

The tale premise:
A gob hears of a warm cappuccino offered at a temple table. The gob is curious about the
cup's foam and the mirrored lines of its surface. The gob's curiosity tempts it into a
choice that may spoil the ritual. A surprise can turn the story toward wisdom, but not every
choice permits a happy ending.

This file is self-contained and follows the Storyweavers storyworld contract.
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
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "gob":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    sacred: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    requires_symmetry: bool = True
    warm: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    gob_name: str
    seed: Optional[int] = None


SETTINGS = {
    "temple": Place(id="temple", label="the temple of steam", sacred=True, affords={"cappuccino", "symmetry", "surprise"}),
    "garden": Place(id="garden", label="the moon garden", sacred=True, affords={"symmetry", "surprise"}),
    "kitchen": Place(id="kitchen", label="the warm kitchen", sacred=False, affords={"cappuccino", "surprise"}),
}


RELICS = {
    "cappuccino": Relic(
        id="cappuccino",
        label="cappuccino",
        phrase="a cup of cappuccino crowned with foam",
        kind="drink",
        requires_symmetry=True,
        warm=True,
    ),
    "mirror_tile": Relic(
        id="mirror_tile",
        label="mirror tile",
        phrase="a polished mirror tile",
        kind="token",
        requires_symmetry=False,
        warm=False,
    ),
}


GOB_NAMES = ["Grimble", "Mog", "Brok", "Snip", "Varn", "Glub"]


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = world.place.label
    g = world.facts["gob"].id
    return [
        f'Write a short mythic story for a child about a gob named {g} in {p}, with cappuccino and symmetry.',
        f"Tell a gentle legend where {g} is curious about cappuccino and must face a bad ending or a surprise.",
        f'Write a story that includes the words "cappuccino", "symmetry", and "gob" in a myth style.',
    ]


def story_qa(world: World) -> list[QAItem]:
    gob = world.facts["gob"]
    relic = world.facts["relic"]
    place = world.place.label
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a gob named {gob.id} who went to {place} and became curious about {relic.label}.",
        ),
        QAItem(
            question=f"What made the gob curious?",
            answer=f"The gob was curious about the cappuccino's foam and the way its top could show symmetry like a sacred sign.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=world.facts["ending"],
        ),
    ]
    if world.facts.get("surprise"):
        qa.append(QAItem(
            question="How did surprise change the story?",
            answer="Surprise arrived like a bright little omen and changed the gob's choice before the bad ending could settle forever.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cappuccino?",
            answer="Cappuccino is a warm coffee drink with milk and foam on top.",
        ),
        QAItem(
            question="What is symmetry?",
            answer="Symmetry means two sides or shapes match in a balanced way, like a mirrored pattern.",
        ),
        QAItem(
            question="What is a gob?",
            answer="A gob is a small mythic creature, often imagined as tricky, strange, or curious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(temple). place(garden). place(kitchen).
affords(temple,cappuccino). affords(temple,symmetry). affords(temple,surprise).
affords(garden,symmetry). affords(garden,surprise).
affords(kitchen,cappuccino). affords(kitchen,surprise).

relic(cappuccino).

curious_story(P) :- place(P), affords(P,cappuccino), affords(P,symmetry).
surprise_possible(P) :- place(P), affords(P,surprise).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show curious_story/1."))
    return sorted(set(asp.atoms(model, "curious_story")))


def asp_verify() -> int:
    py = {p for p in SETTINGS if "cappuccino" in SETTINGS[p].affords and "symmetry" in SETTINGS[p].affords}
    asp_set = {t[0] for t in asp_valid_places()}
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} places).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - asp_set))
    print(" clingo only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate and story engine
# ---------------------------------------------------------------------------
def reasonable(place: Place) -> bool:
    return "cappuccino" in place.affords and "symmetry" in place.affords


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice([p for p in SETTINGS if reasonable(SETTINGS[p])])
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    if not reasonable(SETTINGS[place]):
        raise StoryError("This place cannot host both cappuccino and symmetry, so no myth can begin there.")
    gob_name = args.gob_name or rng.choice(GOB_NAMES)
    return StoryParams(place=place, gob_name=gob_name)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic gob storyworld: cappuccino, symmetry, and surprise.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--gob-name")
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


@dataclass
class SceneState:
    curiosity: float = 0.0
    surprise: float = 0.0
    bad_ending: bool = False
    drank: bool = False
    spilled: bool = False


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.place]
    world = World(place)
    gob = world.add(Entity(id=params.gob_name, kind="character", type="gob", label="gob"))
    relic = world.add(Entity(id="cappuccino", kind="thing", type="cappuccino", label="cappuccino", phrase=RELICS["cappuccino"].phrase))
    sigil = world.add(Entity(id="mirror_tile", kind="thing", type="mirror_tile", label="mirror tile", phrase=RELICS["mirror_tile"].phrase))
    state = SceneState()

    world.facts["gob"] = gob
    world.facts["relic"] = relic

    world.say(f"Long ago, in {place.label}, there lived a gob named {gob.id}.")
    world.say(f"The gob had a restless curiosity and watched the steam rise above {relic.phrase}.")
    world.say("On the cup's bright foam, the gob saw a pale pattern of symmetry, like moonlight split in two.")

    world.para()
    state.curiosity += 1
    world.say(f"Curiosity stepped into the gob's heart, and it leaned closer to study the symmetry.")
    if place.sacred:
        world.say(f"But {place.label} was sacred, and the cup was meant to be admired before it was touched.")

    # Choice and consequence
    world.para()
    if params.place == "garden":
        state.surprise = 1.0
        world.say("A surprise came first: a breeze rang the mirror tile like a little bell.")
        world.say("The gob saw its own crooked grin reflected beside the cup, and it laughed softly.")
        world.say("Remembering the temple rule, the gob bowed instead of grabbing the drink.")
        state.bad_ending = False
    else:
        world.say("The gob could not resist its curiosity.")
        state.spilled = True
        world.say(f"It nudged the cup, and the cappuccino tipped over the stone.")
        if place.sacred:
            state.bad_ending = True
            world.say("That was the bad ending: the symmetry broke, the foam vanished, and the silent hall grew sad.")
        else:
            state.bad_ending = True
            world.say("That was a bad ending for the little table, though the room itself only sighed.")

    # Surprise ending, if allowed by setting and not already in a clean ending
    world.para()
    if not state.bad_ending:
        state.surprise = 1.0
        world.say("Then came the surprise: the keeper of the hall placed a second cup beside the first.")
        world.say("It was a smaller cappuccino, and its foam held a perfect line of symmetry.")
        world.say(f"The gob thanked the keeper and left the first cup untouched, wiser than before.")
        ending = f"In the end, {gob.id} kept the cappuccino safe, honored the symmetry, and carried home a quiet joy."
    else:
        if place.sacred:
            world.say("Yet the myth did not end in ruin alone.")
            world.say("A surprise seed had fallen into the foam before the spill, and from it grew a tiny white flower.")
            ending = f"In the end, {gob.id} learned that curiosity must bow before sacred symmetry, even after a bad ending."
        else:
            ending = f"In the end, {gob.id} learned that too-hasty curiosity can turn sweetness into a bad ending."

    world.say(ending)
    world.facts.update(
        state=state,
        ending=ending,
        surprise=bool(state.surprise),
    )
    return world


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.id} ({world.place.label}) sacred={world.place.sacred}")
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")
    lines.append(f"facts: ending={world.facts.get('ending')}")
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
    StoryParams(place="temple", gob_name="Grimble"),
    StoryParams(place="garden", gob_name="Mog"),
    StoryParams(place="kitchen", gob_name="Brok"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show curious_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show curious_story/1."))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.gob_name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

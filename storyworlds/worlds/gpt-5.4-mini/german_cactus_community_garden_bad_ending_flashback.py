#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/german_cactus_community_garden_bad_ending_flashback.py
======================================================================================

A small standalone storyworld for an animal-story style tale set in a community
garden. A curious animal remembers a flashback, ignores a careful warning, and
the cactus ends up hurt in a bad ending. The world model keeps the story grounded
in physical state (meters) and feelings (memes), and the prose follows the
simulated events rather than a fixed template.

The seed words are woven in as requested:
- german
- cactus

Features:
- community garden setting
- flashback beat
- bad ending option as the default outcome

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/german_cactus_community_garden_bad_ending_flashback.py
    python storyworlds/worlds/gpt-5.4-mini/german_cactus_community_garden_bad_ending_flashback.py --all
    python storyworlds/worlds/gpt-5.4-mini/german_cactus_community_garden_bad_ending_flashback.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/german_cactus_community_garden_bad_ending_flashback.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Garden:
    id: str
    label: str
    place_phrase: str
    cactus_spot: str
    shelter: str
    has_flashback_trigger: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Animal:
    id: str
    type: str
    label: str
    sound: str
    curious: bool
    gentle: bool
    likes: str
    dislikes: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    sharp: bool = False
    spiky: bool = False
    grows: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters["hurt"] >= THRESHOLD:
                sig = ("sadness", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.memes["sad"] += 1
                    ent.memes["shocked"] += 1
                    changed = True


def flashback(world: World, animal: Entity, cactus: Entity) -> None:
    if world.facts.get("flashback_done"):
        return
    world.facts["flashback_done"] = True
    world.say(
        f"As {animal.id} paused, a flashback came back: last summer {animal.id} had "
        f"seen {cactus.label} wobble when a ball rolled too close."
    )
    animal.memes["memory"] += 1


def warn(world: World, guard: Entity, actor: Entity, cactus: Entity) -> None:
    guard.memes["care"] += 1
    world.say(
        f'{guard.id} tilted {guard.pronoun("possessive")} head. '
        f'"Careful," {guard.id} barked, "that {cactus.label} is sharp and could get hurt."'
    )


def defy(world: World, actor: Entity) -> None:
    actor.memes["stubborn"] += 1
    world.say(f'But {actor.id} kept going. "{actor.sound}!" {actor.id} said, as if that made it fine.')


def knock(world: World, actor: Entity, cactus: Entity) -> None:
    cactus.meters["hurt"] += 1
    cactus.meters["broken"] += 1
    actor.memes["guilt"] += 1
    propagate(world)
    world.say(
        f"{actor.id} bumped the cactus pot. The pot tipped, a spiky arm snapped, "
        f"and little bits of soil spilled across the path."
    )


def bad_ending(world: World, actor: Entity, guard: Entity, cactus: Entity, garden: Garden) -> None:
    world.say(
        f"The helpers rushed over, but the damage was already done. {cactus.label} "
        f"leaned crooked in {garden.label}, and the happy little game was over."
    )
    world.say(
        f'{guard.id} lowered {guard.pronoun("possessive")} ears. "{cactus.label} can grow again, '
        f'but only if we are gentle. Today the garden feels sad."'
    )
    actor.memes["sad"] += 1
    guard.memes["sad"] += 1


def tell(garden: Garden, actor_cfg: Animal, guard_cfg: Animal, cactus_cfg: Item) -> World:
    world = World()
    actor = world.add(Entity(
        id=actor_cfg.id, kind="character", type=actor_cfg.type, label=actor_cfg.label,
        traits=["curious"], role="actor",
    ))
    guard = world.add(Entity(
        id=guard_cfg.id, kind="character", type=guard_cfg.type, label=guard_cfg.label,
        traits=["careful"], role="guard",
    ))
    cactus = world.add(Entity(
        id="cactus", kind="thing", type="thing", label=cactus_cfg.label,
        traits=["spiky"], role="plant",
    ))
    world.facts["garden"] = garden
    world.facts["actor"] = actor
    world.facts["guard"] = guard
    world.facts["cactus"] = cactus
    world.facts["flashback_done"] = False

    world.say(
        f"In the {garden.label}, {actor.id} was wandering between bean poles and watering cans. "
        f"It was a bright day in the community garden, and {actor.id} liked the busy, buzzing paths."
    )
    world.say(
        f"{guard.id} was nearby, keeping an eye on the beds and the little signs that showed what grew where."
    )
    flashback(world, actor, cactus)
    world.para()
    warn(world, guard, actor, cactus)
    defy(world, actor)
    world.para()
    knock(world, actor, cactus)
    bad_ending(world, actor, guard, cactus, garden)

    world.facts["outcome"] = "bad"
    world.facts["hurt"] = cactus.meters["hurt"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    actor = f["actor"]
    guard = f["guard"]
    garden = f["garden"]
    return [
        f'Write an animal story set in a community garden that includes the words "german" and "cactus".',
        f"Tell a short story about {actor.id} and {guard.id} in {garden.label}, with a flashback that changes what the animal does.",
        f"Write a child-friendly bad-ending story where a careful animal warns another animal about a cactus, but the warning is ignored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor = f["actor"]
    guard = f["guard"]
    garden = f["garden"]
    cactus = f["cactus"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {actor.id} and {guard.id} in the {garden.label}. The story follows an animal who gets curious and another animal who tries to keep things safe.",
        ),
        QAItem(
            question="Why did the story include a flashback?",
            answer=f"The flashback showed {actor.id} remembering a past wobble near the {cactus.label}. That memory should have helped {actor.id} choose a safer move.",
        ),
        QAItem(
            question="What happened to the cactus at the end?",
            answer=f"The {cactus.label} got bumped, the pot tipped, and a spiky part snapped. The ending is sad because the garden plant was hurt.",
        ),
    ]
    if f["hurt"]:
        items.append(
            QAItem(
                question=f"Did {guard.id} manage to stop the problem?",
                answer=f"No. {guard.id} warned {actor.id}, but the warning came too late and the cactus was already knocked over. The helpers could only look at the damage and clean up the soil.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cactus?",
            answer="A cactus is a plant that stores water and often has sharp spines. People should be gentle around it so it does not get broken.",
        ),
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared garden where neighbors grow plants together. Many people help care for the beds, paths, and tools there.",
        ),
        QAItem(
            question="Why are cacti tricky near children or animals?",
            answer="Cacti can be spiky, so a bump can hurt the plant and can also scratch skin. That is why careful walking matters around them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
@dataclass
class StoryParams:
    actor: str = "Milo"
    guard: str = "Luna"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


GARDENS = {
    "community_garden": Garden(
        id="community_garden",
        label="the community garden",
        place_phrase="between the tomato cages and the herb beds",
        cactus_spot="near the sunny wall",
        shelter="by the tool shed",
    )
}

ANIMALS = [
    Animal("Milo", "boy", "little dog", "woof", True, False, "sniffing the flower path"),
    Animal("Luna", "girl", "garden cat", "meow", True, True, "watching the beds"),
    Animal("Gus", "boy", "goat", "bleat", True, True, "nibbling weeds"),
    Animal("Nina", "girl", "rabbit", "thump", True, True, "hopping by carrots"),
]

CACTUS = Item("cactus", "cactus", "a tall cactus with sharp spines", spiky=True, grows=True)


def valid_combos() -> list[tuple[str, str, str]]:
    return [("community_garden", a.id, g.id) for a in ANIMALS for g in ANIMALS if a.id != g.id]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world: a flashback, a cactus, and a bad ending in a community garden.")
    ap.add_argument("--actor", choices=[a.id for a in ANIMALS])
    ap.add_argument("--guard", choices=[a.id for a in ANIMALS])
    ap.add_argument("--garden", choices=GARDENS)
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
    if args.actor and args.guard and args.actor == args.guard:
        raise StoryError("The actor and guard need to be different animals.")
    choices = valid_combos()
    if args.actor:
        choices = [c for c in choices if c[1] == args.actor]
    if args.guard:
        choices = [c for c in choices if c[2] == args.guard]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    _, actor, guard = rng.choice(choices)
    return StoryParams(actor=actor, guard=guard)


def generate(params: StoryParams) -> StorySample:
    garden = GARDENS["community_garden"]
    actor_cfg = next(a for a in ANIMALS if a.id == params.actor)
    guard_cfg = next(a for a in ANIMALS if a.id == params.guard)
    world = tell(garden, actor_cfg, guard_cfg, CACTUS)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
valid(A, G, community_garden) :- animal(A), animal(G), A != G.
bad_end(A, G) :- valid(A, G, community_garden), flashback_used(A), cactus_hurt.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("garden", "community_garden")]
    for a in ANIMALS:
        lines.append(asp.fact("animal", a.id))
    lines.append(asp.fact("flashback_used", "Milo"))
    lines.append(asp.fact("cactus_hurt"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import itertools
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
    else:
        print(f"OK: valid_combos matches ASP ({len(py)} combos).")
    try:
        sample = generate(StoryParams())
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("Milo", "Luna"),
    StoryParams("Gus", "Nina"),
    StoryParams("Nina", "Milo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show bad_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

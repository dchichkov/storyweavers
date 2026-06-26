#!/usr/bin/env python3
"""
storyworlds/worlds/anaconda_pact_quadruple_inner_monologue_kindness_adventure.py
===============================================================================

A small adventure storyworld about a jungle trek, a startling anaconda,
a promise made in kindness, and a four-step rescue pact.

Premise:
- A curious child explorer wants to cross a vine bridge and reach a hidden
  grove.
- A giant anaconda blocks the path and makes the child think of backing away.
- A kind companion proposes a pact: four careful steps that keep everyone safe.
- The child listens to an inner monologue, chooses kindness, and the trek
  continues with a new bond of trust.

This world keeps one compact, state-driven adventure with a clear turn:
fear is answered by a pact, and the pact is carried out as a quadruple of
actions.

The story uses two linked dimensions for every entity:
- meters: physical quantities like danger, distance, trust, and readiness
- memes: emotional quantities like fear, calm, kindness, and resolve
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    anaconda_size: str
    seed: Optional[int] = None


PLACES = {
    "jungle_path": "the jungle path",
    "riverbank": "the riverbank",
    "canopy_bridge": "the vine bridge",
    "hidden_grove": "the hidden grove",
}

HERO_NAMES = ["Mira", "Niko", "Lani", "Tobi", "Iris", "Rafi"]
COMPANION_NAMES = ["Pia", "Joss", "Kellan", "Sana", "Orin"]
SIZES = {
    "huge": "huge",
    "long": "long",
    "towering": "towering",
}


def _setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        meters={"distance": 0.0, "readiness": 0.0, "danger": 0.0},
        memes={"curiosity": 1.0, "fear": 0.0, "calm": 0.0, "resolve": 0.0, "kindness": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=params.companion_type,
        label=params.companion_name,
        meters={"distance": 0.0, "readiness": 0.0},
        memes={"kindness": 1.0, "calm": 1.0, "trust": 1.0},
    ))
    anaconda = world.add(Entity(
        id="anaconda",
        kind="animal",
        type="snake",
        label=f"{params.anaconda_size} anaconda",
        phrase=f"a {params.anaconda_size} anaconda coiled beside the path",
        meters={"blocking": 1.0, "distance": 1.0},
        memes={"stillness": 1.0, "alertness": 1.0},
    ))
    pact = world.add(Entity(
        id="pact",
        kind="thing",
        type="pact",
        label="pact",
        phrase="a careful pact",
        meters={"steps": 0.0, "kept": 0.0},
        memes={"promise": 1.0, "trust": 0.0},
        props={"shape": "quadruple"},
    ))
    world.facts.update(hero=hero, companion=companion, anaconda=anaconda, pact=pact)
    return world


def _inner_monologue(world: World, hero: Entity) -> str:
    if hero.memes["fear"] >= THRESHOLD:
        return (
            f"{hero.label} thought, \"If I rush, I might scare the anaconda. "
            f"If I stay calm, I can choose a kinder path.\""
        )
    return (
        f"{hero.label} thought, \"This path is strange, but I can keep going "
        f"if I listen carefully.\""
    )


def _introduce(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    anaconda = world.facts["anaconda"]
    world.say(
        f"{hero.label} was a little {hero.type} adventurer who loved bright leaves, "
        f"muddy boots, and the feeling of a trail that led somewhere secret."
    )
    world.say(
        f"On {world.place}, {companion.label} walked beside {hero.label} with a warm smile, "
        f"and together they hoped to reach the hidden grove."
    )
    world.say(
        f"Then they saw {anaconda.phrase}, and the whole path seemed to hold its breath."
    )


def _threat(world: World) -> None:
    hero = world.facts["hero"]
    anaconda = world.facts["anaconda"]
    hero.meters["danger"] += 1.0
    hero.memes["fear"] += 1.0
    world.say(
        f"{hero.label}'s stomach fluttered. {hero.pronoun().capitalize()} did not want to startle "
        f"{anaconda.label} or get trapped on the narrow trail."
    )
    world.say(_inner_monologue(world, hero))


def _offer_pact(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    pact = world.facts["pact"]
    pact.meters["steps"] = 4.0
    pact.meters["kept"] = 0.0
    pact.memes["trust"] = 1.0
    hero.memes["calm"] += 1.0
    companion.memes["trust"] += 1.0
    world.say(
        f"{companion.label} lifted a hand and spoke kindly: "
        f"\"Let's make a pact. We will take four quiet steps, one by one, and stay low.\""
    )
    world.say(
        f"The promise felt small and strong at the same time, like a lantern in the dark."
    )


def _quadruple_steps(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    pact = world.facts["pact"]
    anaconda = world.facts["anaconda"]

    steps = [
        "first, they froze and let the leaves stop shaking",
        "second, they backed up slowly so the snake had space",
        "third, they placed a smooth branch across a muddy patch",
        "fourth, they crossed in single file, quiet as sand slipping through fingers",
    ]
    for i, line in enumerate(steps, 1):
        sig = ("step", i)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        pact.meters["kept"] += 1.0
        hero.meters["readiness"] += 0.25
        companion.meters["readiness"] += 0.25
        hero.memes["kindness"] += 0.25
        world.say(f"Together, {line}.")
    if pact.meters["kept"] >= 4.0:
        anaconda.meters["blocking"] = 0.0
        anaconda.meters["distance"] = 2.0
        world.say(
            f"The {anaconda.label} stayed calm and uncoiled just enough to let them pass."
        )


def _resolution(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    pact = world.facts["pact"]
    world.para()
    hero.memes["fear"] = 0.0
    hero.memes["resolve"] += 1.0
    companion.memes["kindness"] += 1.0
    world.say(
        f"{hero.label} felt brave now, not because the path was easy, but because kindness "
        f"had given the fear a place to sit down."
    )
    world.say(
        f"Their pact held, the four steps were finished, and the two adventurers went on "
        f"toward the grove with lighter hearts."
    )
    world.say(
        f"Behind them, the trail was quiet again, and {pact.label} had become a story "
        f"they would remember whenever the jungle looked strange."
    )


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    _introduce(world)
    world.para()
    _threat(world)
    world.para()
    _offer_pact(world)
    _quadruple_steps(world)
    _resolution(world)
    world.facts["resolved"] = True
    return world


def _reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_name == params.companion_name:
        raise StoryError("The hero and companion need different names.")
    if params.anaconda_size not in SIZES:
        raise StoryError("Unknown anaconda size.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world: an anaconda, a pact, and a quadruple of careful steps.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name", choices=COMPANION_NAMES)
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--anaconda-size", choices=SIZES)
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    companion_name = args.companion_name or rng.choice([n for n in COMPANION_NAMES if n != hero_name])
    anaconda_size = args.anaconda_size or rng.choice(list(SIZES))
    params = StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        anaconda_size=anaconda_size,
    )
    _reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    return [
        f"Write a short adventure story for a young child about {hero.label}, {companion.label}, an anaconda, and a pact.",
        f"Tell a gentle jungle tale where kindness helps {hero.label} keep going after seeing an anaconda.",
        "Write a child-friendly adventure that includes an inner monologue and a quadruple of careful steps.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    anaconda = world.facts["anaconda"]
    pact = world.facts["pact"]
    return [
        QAItem(
            question=f"Why did {hero.label} feel nervous when the anaconda appeared?",
            answer=f"{hero.label} felt nervous because the {anaconda.label} blocked the trail and the path seemed narrow and risky.",
        ),
        QAItem(
            question=f"What did {companion.label} suggest to help {hero.label} move safely?",
            answer=f"{companion.label} suggested a pact: four quiet steps taken slowly and kindly so they could pass without startling the snake.",
        ),
        QAItem(
            question="How many careful steps were in the pact?",
            answer="There were four careful steps, so the pact was a quadruple of actions.",
        ),
        QAItem(
            question=f"What did {hero.label} think in the inner monologue?",
            answer=f"{hero.label} thought about not rushing, not startling the anaconda, and choosing the kinder, calmer path.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {companion.label}?",
            answer=f"They crossed safely, kept the pact, and continued toward the hidden grove with lighter hearts.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an anaconda?",
            answer="An anaconda is a very large snake that can coil quietly and move slowly through warm places.",
        ),
        QAItem(
            question="What is a pact?",
            answer="A pact is a promise people make to each other about what they will do.",
        ),
        QAItem(
            question="What does quadruple mean?",
            answer="Quadruple means four times or a group of four things.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how someone else feels.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking inside a person's mind, like words they say to themselves.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.props:
            bits.append(f"props={e.props}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A pact is valid when the story has exactly one anaconda, one hero, one companion,
% and the pact includes four steps.
quadruple(pact) :- pact(pact), steps(pact, 4).

% Kindness and calm make the pact workable.
can_cross(hero) :- kindness(hero), calm(hero), quadruple(pact), kept(pact, 4).

% The anaconda blocks the path at first, but a kept pact resolves the block.
resolved_story :- blocks(anaconda), can_cross(hero).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("storyworld", "anaconda_pact_quadruple"))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for size in SIZES:
        lines.append(asp.fact("anaconda_size", size))
    lines.append(asp.fact("steps", "pact", 4))
    lines.append(asp.fact("pact", "pact"))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("calm", "hero"))
    lines.append(asp.fact("blocks", "anaconda"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show quadruple/1.\n#show can_cross/1.\n#show resolved_story/0.")
    model = asp.one_model(program)
    atoms = set((a.name, len(a.arguments), tuple(arg.name if arg.type != arg.type.Number else arg.number for arg in a.arguments)) for a in model)
    expected = {("quadruple", 1, ("pact",)), ("can_cross", 1, ("hero",)), ("resolved_story", 0, ())}
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH: ASP result did not match expected story logic.")
    print("Got:", sorted(atoms))
    print("Expected:", sorted(expected))
    return 1


CURATED = [
    StoryParams(place="jungle_path", hero_name="Mira", hero_type="girl", companion_name="Pia", companion_type="girl", anaconda_size="huge"),
    StoryParams(place="riverbank", hero_name="Niko", hero_type="boy", companion_name="Sana", companion_type="girl", anaconda_size="long"),
    StoryParams(place="canopy_bridge", hero_name="Lani", hero_type="girl", companion_name="Orin", companion_type="boy", anaconda_size="towering"),
]


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show quadruple/1.\n#show can_cross/1.\n#show resolved_story/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quadruple/1.\n#show can_cross/1.\n#show resolved_story/0."))
        for atom in model:
            print(atom)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

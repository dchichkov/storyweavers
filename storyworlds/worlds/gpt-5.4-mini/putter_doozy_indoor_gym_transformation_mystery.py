#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/putter_doozy_indoor_gym_transformation_mystery.py
=================================================================================

A small standalone story world for an indoor-gym mystery with a transformation
turn. The seed words are "putter" and "doozy"; the story premise is that a child
or small group enters an indoor gym, notices strange clues, and discovers that a
plain object has transformed into something surprising. The mystery is solved by
observing state changes in the room, not by swapping nouns in a frozen paragraph.

Core shape:
- typed entities with physical meters and emotional memes
- a forward-chained causal rule engine
- a reasonableness gate plus inline ASP twin
- three QA sets grounded in world state
- child-facing prose with a clear beginning, middle turn, and ending image

This world favors gentle mystery: odd footprints, a hidden mechanism, a curious
shift in form, and a final reveal that makes the transformed object useful.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
STATE_LOW = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Gym:
    id: str
    place: str
    echo: str
    lockers: str
    floor: str
    mystery_spot: str
    tags: set[str] = field(default_factory=set)

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
class ObjectCfg:
    id: str
    label: str
    form: str
    transformed_form: str
    clue: str
    reveal: str
    can_transform: bool = True
    tags: set[str] = field(default_factory=set)

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
class Catalyst:
    id: str
    label: str
    method: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)

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
    def __init__(self, gym: Gym) -> None:
        self.gym = gym
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        c = World(self.gym)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("mystery")
    if item.meters["odd"] >= THRESHOLD and ("clue", "odd") not in world.fired:
        world.fired.add(("clue", "odd"))
        seeker = world.get("child")
        seeker.memes["curiosity"] += 1
        out.append("__clue__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("mystery")
    if item.meters["ready"] >= THRESHOLD and item.meters["transformed"] < THRESHOLD:
        sig = ("transform", item.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        item.meters["transformed"] += 1
        item.meters["surprise"] += 1
        world.get("child").memes["wonder"] += 1
        out.append("__transform__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("mystery")
    child = world.get("child")
    if item.meters["transformed"] >= THRESHOLD and ("settle", item.id) not in world.fired:
        world.fired.add(("settle", item.id))
        child.memes["relief"] += 1
        out.append("__settle__")
    return out


CAUSAL_RULES = [
    Rule("clue", "social", _r_clue),
    Rule("transform", "physical", _r_transform),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mystery_safe(cfg: ObjectCfg) -> bool:
    return cfg.can_transform


def reasonableness_gate(obj: ObjectCfg, cat: Catalyst) -> bool:
    return mystery_safe(obj) and cat.power >= 1


def predict_transformation(world: World, cat: Catalyst) -> bool:
    sim = world.copy()
    simulate_use(sim, sim.get("child"), cat, narrate=False)
    return sim.get("mystery").meters["transformed"] >= THRESHOLD


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"On a quiet afternoon in the indoor gym, {child.id} walked past the mats, "
        f"the mirrors, and the shiny lockers."
    )
    world.say(
        f"Something about {world.gym.mystery_spot} felt strange, as if the room were "
        f"holding its breath."
    )


def clue_scene(world: World, child: Entity, obj: ObjectCfg) -> None:
    world.get("mystery").meters["odd"] += 1
    world.say(
        f"{child.id} noticed {obj.clue} near {world.gym.mystery_spot}. "
        f"The clue looked small, but it felt like the start of a doozy."
    )
    propagate(world, narrate=True)


def suspect(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} leaned closer. \"A putter could have left this,\" "
        f"{child.pronoun()} whispered, as if saying the word might wake the mystery."
    )


def simulate_use(world: World, child: Entity, cat: Catalyst, narrate: bool = True) -> None:
    obj = world.get("mystery")
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} pressed the {cat.label} to the strange spot and tried "
        f"{cat.method}."
    )
    obj.meters["ready"] += 1
    if cat.effect:
        world.say(cat.effect)
    propagate(world, narrate=narrate)


def reveal(world: World, child: Entity, obj: ObjectCfg) -> None:
    item = world.get("mystery")
    child.memes["joy"] += 1
    world.say(
        f"Then, with a soft click, the strange thing changed shape. It was no longer "
        f"{obj.form}; it had become {obj.transformed_form}."
    )
    world.say(
        f"Now the mystery made sense: {obj.reveal}. {child.id} smiled, because the "
        f"doozy had turned into something useful."
    )
    world.say(
        f"The indoor gym felt bright again, and the odd little clue was gone."
    )


def tell(gym: Gym, obj: ObjectCfg, cat: Catalyst, child_name: str = "Mia",
         child_gender: str = "girl") -> World:
    world = World(gym)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seer"))
    mystery = world.add(Entity(id="mystery", type="thing", label=obj.label))
    world.facts["object"] = obj
    world.facts["catalyst"] = cat

    introduce(world, child)
    world.para()
    clue_scene(world, child, obj)
    suspect(world, child, obj)

    world.para()
    if not reasonableness_gate(obj, cat):
        raise StoryError("This mystery has no honest transformation path.")
    if not predict_transformation(world, cat):
        raise StoryError("The chosen catalyst cannot complete the transformation.")

    simulate_use(world, child, cat, narrate=True)
    world.para()
    reveal(world, child, obj)

    world.facts.update(child=child, mystery=mystery, outcome="transformed")
    return world


GYMS = {
    "indoor_gym": Gym(
        id="indoor_gym",
        place="the indoor gym",
        echo="The high ceiling made every whisper bounce softly.",
        lockers="Row after row of lockers lined one wall.",
        floor="The floor was polished and bright.",
        mystery_spot="the far corner by the climbing rope",
        tags={"gym", "indoor"},
    )
}

OBJECTS = {
    "putter": ObjectCfg(
        id="putter",
        label="a putter",
        form="a plain putter",
        transformed_form="a tiny key",
        clue="a round shadow shaped like a coin",
        reveal="the putter had hidden a secret latch, and the latch opened a tiny key",
        can_transform=True,
        tags={"putter", "mystery"},
    ),
    "doozy": ObjectCfg(
        id="doozy",
        label="a doozy",
        form="a dull doozy",
        transformed_form="a bright compass",
        clue="a strange humming sound from under the bench",
        reveal="the doozy had been a puzzle box all along, and its answer was a bright compass",
        can_transform=True,
        tags={"doozy", "mystery"},
    ),
}

CATALYSTS = {
    "tap": Catalyst(
        id="tap",
        label="tap",
        method="tapping the hidden panel three times",
        effect="The tapping made a little click echo through the gym.",
        power=1,
        tags={"tap", "mystery"},
    ),
    "turn": Catalyst(
        id="turn",
        label="turn",
        method="turning the putter like a key",
        effect="The metal gave a neat, neat turn.",
        power=2,
        tags={"turn", "putter", "mystery"},
    ),
}

NAMES = ["Mia", "Lily", "Theo", "Sam", "Nora", "Finn"]


@dataclass
@dataclass
class StoryParams:
    gym: str
    object: str
    catalyst: str
    name: str
    gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for gid in GYMS:
        for oid, obj in OBJECTS.items():
            for cid, cat in CATALYSTS.items():
                if reasonableness_gate(obj, cat):
                    out.append((gid, oid, cid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an indoor-gym mystery with a transformation."
    )
    ap.add_argument("--gym", choices=GYMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--catalyst", choices=CATALYSTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.object and args.catalyst:
        if not reasonableness_gate(OBJECTS[args.object], CATALYSTS[args.catalyst]):
            raise StoryError("This transformation setup is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.gym is None or c[0] == args.gym)
              and (args.object is None or c[1] == args.object)
              and (args.catalyst is None or c[2] == args.catalyst)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    gym, obj, cat = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(gym, obj, cat, name, gender)


def generation_prompts(world: World) -> list[str]:
    obj = world.facts["object"]
    return [
        f'Write a short mystery story for a young child in an indoor gym that includes the words "putter" and "doozy".',
        f"Tell a gentle mystery where {world.facts['child'].id} finds {obj.clue} and discovers that a plain object transforms into something useful.",
        f'Write a child-friendly story set in a gym where a transformation solves the puzzle and the ending proves what changed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    obj = world.facts["object"]
    child = world.facts["child"]
    return [
        QAItem(
            question="What kind of place is the story set in?",
            answer=f"It takes place in an indoor gym with mats, lockers, and a quiet echo. That setting makes the mystery feel secret and small.",
        ),
        QAItem(
            question="What clue did the child notice?",
            answer=f"{child.id} noticed {obj.clue}. The clue made the child look closer and think the odd thing might be important.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{obj.form} transformed into {obj.transformed_form}. That change solved the mystery and turned the doozy into something useful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a putter?",
            answer="A putter is a golf club made for smooth, careful hits. In this story world, it also serves as the clue that starts the mystery.",
        ),
        QAItem(
            question="What does doozy mean?",
            answer="A doozy is something surprising, strange, or extra big. Here it means the mystery is a real surprise.",
        ),
        QAItem(
            question="Why does a mystery story need clues?",
            answer="Clues help the reader and the character notice what is really happening. A good clue points toward the answer before the reveal.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in GYMS:
        lines.append(asp.fact("gym", gid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("can_transform", oid))
    for cid, cat in CATALYSTS.items():
        lines.append(asp.fact("catalyst", cid))
        lines.append(asp.fact("power", cid, cat.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(G,O,C) :- gym(G), object(O), catalyst(C), can_transform(O), power(C,P), P >= 1.
transforms(O,C) :- object(O), catalyst(C), can_transform(O), power(C,P), P >= 1.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(gym=None, object=None, catalyst=None, name=None, gender=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(GYMS[params.gym], OBJECTS[params.object], CATALYSTS[params.catalyst], params.name, params.gender)
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
    StoryParams("indoor_gym", "putter", "turn", "Mia", "girl"),
    StoryParams("indoor_gym", "doozy", "tap", "Theo", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.object} in the {p.gym}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

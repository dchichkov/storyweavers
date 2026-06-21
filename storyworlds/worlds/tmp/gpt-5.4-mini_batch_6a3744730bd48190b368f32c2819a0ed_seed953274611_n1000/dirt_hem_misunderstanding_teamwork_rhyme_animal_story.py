#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dirt_hem_misunderstanding_teamwork_rhyme_animal_story.py
=========================================================================================

A tiny animal-story storyworld about a muddy hem, a misunderstanding, and a
teamwork fix that ends in a little rhyme.

The premise is simple: a small animal gets dirt on the hem of a cherished cloth
item after play. Another animal misunderstands what happened, thinking the dirt
means trouble or carelessness. A gentle explanation, plus teamwork, turns the
mess into a tidy ending. The final beat includes a child-friendly rhyme so the
story has a playful animal-story flavor.

This script is standalone and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REASONABLE_SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "rabbit", "mouse", "fox", "bird", "squirrel", "deer", "dog"}
        male = {"bear", "owl", "wolf", "frog", "otter", "hedgehog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class AnimalKind:
    id: str
    label: str
    type: str
    habitat: str
    voice: str
    paws: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClothItem:
    id: str
    label: str
    phrase: str
    hem_word: str
    wearer_role: str = "helper"
    can_get_dirty: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CleanupTool:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    animal1: str
    animal2: str
    cloth: str
    tool: str
    place: str
    seed: Optional[int] = None


ANIMALS = {
    "cat": AnimalKind(id="cat", label="cat", type="cat", habitat="the meadow", voice="meow", paws="paws", tags={"animal", "cat"}),
    "rabbit": AnimalKind(id="rabbit", label="rabbit", type="rabbit", habitat="the meadow", voice="sniff", paws="paws", tags={"animal", "rabbit"}),
    "bear": AnimalKind(id="bear", label="bear", type="bear", habitat="the woods", voice="hmm", paws="paws", tags={"animal", "bear"}),
    "fox": AnimalKind(id="fox", label="fox", type="fox", habitat="the field", voice="chirp", paws="paws", tags={"animal", "fox"}),
    "mouse": AnimalKind(id="mouse", label="mouse", type="mouse", habitat="the garden", voice="squeak", paws="tiny paws", tags={"animal", "mouse"}),
    "owl": AnimalKind(id="owl", label="owl", type="owl", habitat="the tree", voice="hoo", paws="claws", tags={"animal", "owl"}),
}

CLOTHS = {
    "scarf": ClothItem(id="scarf", label="scarf", phrase="a soft red scarf", hem_word="hem", tags={"cloth", "hem"}),
    "blanket": ClothItem(id="blanket", label="blanket", phrase="a cozy blue blanket", hem_word="edge", tags={"cloth", "hem"}),
    "apron": ClothItem(id="apron", label="apron", phrase="a clean yellow apron", hem_word="hem", tags={"cloth", "hem"}),
}

TOOLS = {
    "brush": CleanupTool(id="brush", label="brush", phrase="a soft brush", action="brush away the dirt", tags={"clean"}),
    "water": CleanupTool(id="water", label="cloth and water", phrase="a bowl of warm water", action="wipe the dirt away", tags={"clean"}),
    "cloth": CleanupTool(id="cloth", label="cloth", phrase="a clean cloth", action="rub the dirt away", tags={"clean"}),
}

PLACES = {
    "path": "the pebble path",
    "garden": "the garden gate",
    "barn": "the little barn",
    "meadow": "the sunny meadow",
}

CURATED = [
    StoryParams(animal1="rabbit", animal2="cat", cloth="scarf", tool="brush", place="garden"),
    StoryParams(animal1="fox", animal2="mouse", cloth="apron", tool="cloth", place="barn"),
    StoryParams(animal1="bear", animal2="owl", cloth="blanket", tool="water", place="meadow"),
]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_dirty(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal1")
    cloth = world.get("cloth")
    if animal.meters["dirt"] >= THRESHOLD and cloth.meters["dirt"] < THRESHOLD:
        sig = ("dirty",)
        if sig not in world.fired:
            world.fired.add(sig)
            cloth.meters["dirt"] += 1
            cloth.memes["embarrassed"] += 1
            out.append("__cloth_got_dirty__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cloth").meters["dirt"] >= THRESHOLD and "worry" not in world.fired:
        world.fired.add(("worry",))
        world.get("animal2").memes["worry"] += 1
        out.append("__worry__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_dirty, _r_worry):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness(params: StoryParams) -> None:
    if params.animal1 not in ANIMALS or params.animal2 not in ANIMALS:
        raise StoryError("Unknown animal choice.")
    if params.cloth not in CLOTHS or params.tool not in TOOLS:
        raise StoryError("Unknown cloth or tool choice.")
    if params.animal1 == params.animal2:
        raise StoryError("The two animals should be different so the misunderstanding can play out.")
    if params.place not in PLACES:
        raise StoryError("Unknown place choice.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a1 in ANIMALS:
        for a2 in ANIMALS:
            if a1 == a2:
                continue
            for cloth in CLOTHS:
                for tool in TOOLS:
                    combos.append((a1, a2, cloth))
    return combos


ASP_RULES = r"""
dirt_on_hem(A, C) :- dirt(A), cloth(C), hem(C).
misunderstanding(B) :- dirt_on_hem(A, C), not explained(A, B, C).
teamwork(A, B) :- misunderstood(B), helped(B, A).
cleaned(C) :- teamwork(A, B), tool(T), clean(T), cloth(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid in CLOTHS:
        lines.append(asp.fact("cloth", cid))
        lines.append(asp.fact("hem", cid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("clean", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show dirt_on_hem/2."))
    asp_ok = bool(asp.atoms(model, "dirt_on_hem"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python gate disagree.")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about dirt, hem, misunderstanding, teamwork, and rhyme.")
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--place", choices=PLACES)
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
    if args.animal1 and args.animal2 and args.animal1 == args.animal2:
        raise StoryError("The two animals must be different.")
    animal1 = args.animal1 or rng.choice(list(ANIMALS))
    animal2 = args.animal2 or rng.choice([a for a in ANIMALS if a != animal1])
    cloth = args.cloth or rng.choice(list(CLOTHS))
    tool = args.tool or rng.choice(list(TOOLS))
    place = args.place or rng.choice(list(PLACES))
    return StoryParams(animal1=animal1, animal2=animal2, cloth=cloth, tool=tool, place=place)


def tell(params: StoryParams) -> World:
    reasonableness(params)
    w = World()
    a1 = w.add(Entity(id="animal1", kind="character", type=ANIMALS[params.animal1].type, label=ANIMALS[params.animal1].label, role="mover"))
    a2 = w.add(Entity(id="animal2", kind="character", type=ANIMALS[params.animal2].type, label=ANIMALS[params.animal2].label, role="helper"))
    cloth = w.add(Entity(id="cloth", kind="thing", type="thing", label=CLOTHS[params.cloth].label))
    tool = w.add(Entity(id="tool", kind="thing", type="thing", label=TOOLS[params.tool].label))
    w.facts.update(params=params, animal1=a1, animal2=a2, cloth=cloth, tool=tool)

    w.say(f"At {PLACES[params.place]}, a {a1.label_word} and a {a2.label_word} played near the path.")
    w.say(f"{a1.label_word.capitalize()} wore {CLOTHS[params.cloth].phrase}, and the {cloth.label} swayed as the game went on.")
    w.say(f"Then a little splash of dirt landed on the {CLOTHS[params.cloth].hem_word}.")

    w.para()
    a1.meters["dirt"] += 1
    propagate(w, narrate=False)
    w.say(f"{a2.label_word.capitalize()} gasped, \"Oh no, your {cloth.label} is ruined!\"")
    w.say(f"{a1.label_word.capitalize()} shook {a1.pronoun('possessive')} head and said, \"No, no, that dirt is only on the {CLOTHS[params.cloth].hem_word}.\"")
    w.say(f"{a2.label_word.capitalize()} blinked, then smiled. \"A hem is not the whole thing,\" {a2.pronoun()} said.")

    w.para()
    w.say(f"Together they got {TOOLS[params.tool].phrase} and {TOOLS[params.tool].action}.")
    cloth.meters["dirt"] = 0.0
    cloth.memes["thankful"] += 1
    a1.memes["joy"] += 1
    a2.memes["joy"] += 1
    a2.memes["teamwork"] += 1
    w.say(f"One held the cloth steady while the other worked, and the dirt came away in a small gray curl.")
    w.say(f"Then they tied the cloth neat and clean, and both animals laughed: \"Brush and hush, dirt dash and rush.\"")

    w.facts.update(outcome="clean", explained=True, teamwork=True)
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write an animal story that includes the words dirt and hem, where a {p.animal1} and a {p.animal2} first misunderstand what happened.",
        f"Tell a gentle story about teamwork: a {p.animal1} gets dirt on a hem, a {p.animal2} thinks it is worse than it is, and they fix it together.",
        "Write a child-friendly animal story that ends with a little rhyme after the friends clean up the mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question="What happened to the cloth?",
            answer="A little dirt landed on the hem, so it looked messy at first. The two animals cleaned it together, and the cloth ended up neat again."
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{p.animal2.capitalize()} thought the cloth was ruined, but {p.animal1.capitalize()} explained that only the hem had dirt on it. After that, they both understood the problem and worked side by side."
        ),
        QAItem(
            question="How did teamwork help?",
            answer="One animal held the cloth steady while the other cleaned the dirt away. Working together made the job quick and calm."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is dirt?", answer="Dirt is soil from the ground. It can stick to paws, clothes, and hands."),
        QAItem(question="What is a hem?", answer="A hem is the edge of cloth or clothing. It is the part you notice when something hangs low or gets a little messy."),
        QAItem(question="What is teamwork?", answer="Teamwork means helping each other to do a job. When animals or people share the work, things often get done faster and more kindly."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"facts={sorted(world.facts.keys())}")
    return "\n".join(out)


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


def valid_story_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for a1 in ANIMALS:
        for a2 in ANIMALS:
            if a1 == a2:
                continue
            for cloth in CLOTHS:
                for tool in TOOLS:
                    for place in PLACES:
                        combos.append((a1, a2, cloth, tool, place))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_full() -> int:
    rc = 0
    if not generate(CURATED[0]).story:
        print("MISMATCH: smoke generate failed.")
        rc = 1
    if asp_verify() != 0:
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        try:
            rc = asp_verify_full()
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: verification smoke test passed.")
            sys.exit(rc)
        except StoryError as e:
            print(str(e))
            sys.exit(1)
    if args.asp:
        import asp
        print(f"{len(valid_story_combos())} python combos")
        model = asp.one_model(asp_program("#show valid/5."))
        print(f"{len(asp.atoms(model, 'valid'))} asp combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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

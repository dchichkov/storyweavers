#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/long_smirk_children_s_museum_flashback_repetition.py
====================================================================================

A tiny storyworld set in a children's museum, told in a fable-like style.

Seed idea:
- A child feels left out in a long line at a children's museum.
- A smug smirk, a remembered flashback, and a repeated lesson turn the mood.
- The story ends with a kinder choice and a small visible change in the world.

The world model is intentionally small:
- entities have physical meters and emotional memes
- a simple causal loop drives the prose
- flashback and repetition are represented as world state, not text tricks

Run it:
    python storyworlds/worlds/gpt-5.4-mini/long_smirk_children_s_museum_flashback_repetition.py
    python storyworlds/worlds/gpt-5.4-mini/long_smirk_children_s_museum_flashback_repetition.py --all
    python storyworlds/worlds/gpt-5.4-mini/long_smirk_children_s_museum_flashback_repetition.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/long_smirk_children_s_museum_flashback_repetition.py --verify
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
class Exhibit:
    id: str
    label: str
    shine: str
    echo: str
    long: bool = False
    breakable: bool = False
    visible: bool = True
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
class Memory:
    id: str
    scene: str
    lesson: str
    repeat_line: str

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.memes["tease"] >= THRESHOLD and ("repeat", ent.id) not in world.fired:
                world.fired.add(("repeat", ent.id))
                ent.memes["repeat"] += 1
                produced.append("__repeat__")
                changed = True
            if ent.meters["shaken"] >= THRESHOLD and ("comfort", ent.id) not in world.fired:
                world.fired.add(("comfort", ent.id))
                ent.memes["softened"] += 1
                produced.append("__comfort__")
                changed = True
    if narrate:
        for line in produced:
            if line != "__repeat__" and line != "__comfort__":
                world.say(line)
    return produced


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    guide: str
    guide_gender: str
    exhibit: str
    memory: str
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


CHILD_NAMES = ["Mia", "Lena", "Noah", "Eli", "Nora", "Maya", "Theo", "Zoe"]
GUIDE_NAMES = ["Aunt June", "Mr. Reed", "Mama", "Papa", "Ms. Bell"]
GENDERS = ["girl", "boy"]
MEMORIES = [
    Memory("pigeons", "a long line by the fountain exhibit", "Waiting can be hard, but waiting can also make the next wonder sweeter.", "They waited, and they waited, and the lesson stayed the same."),
    Memory("shells", "a long line beside the sea room", "A kind face can make a hard wait feel small.", "Be kind in the line, be kind in the line."),
    Memory("dinosaurs", "a long line under the dino sign", "A smirk may feel tall, but kindness stands taller.", "Again and again, the kind choice is the wise choice."),
]

EXHIBITS = {
    "mirror": Exhibit("mirror", "the giant mirror tunnel", "glittered like a river", "made every step look doubled", long=True, breakable=False, tags={"mirror", "long"}),
    "castle": Exhibit("castle", "the cardboard castle", "shone with painted towers", "waited like a sleepy fort", long=False, breakable=True, tags={"castle"}),
    "buttons": Exhibit("buttons", "the long button wall", "blinked red and blue", "asked to be pressed in order", long=True, breakable=False, tags={"buttons", "long"}),
    "fish": Exhibit("fish", "the round fish tank", "glowed green and gold", "swam in quiet circles", long=False, breakable=False, tags={"fish"}),
}

CURATED = [
    StoryParams("Mia", "girl", "Mama", "woman", "buttons", "pigeons"),
    StoryParams("Noah", "boy", "Aunt June", "woman", "mirror", "shells"),
    StoryParams("Zoe", "girl", "Papa", "man", "castle", "dinosaurs"),
]

ASP_RULES = r"""
tease_to_repeat(C) :- child(C), tease(C).
shaken_to_softened(C) :- child(C), shaken(C).
valid_story(C, E, M) :- child(C), exhibit(E), memory(M), long(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CHILD_NAMES:
        lines.append(asp.fact("child_name", c))
    for eid, ex in EXHIBITS.items():
        lines.append(asp.fact("exhibit", eid))
        if ex.long:
            lines.append(asp.fact("long", eid))
        if ex.breakable:
            lines.append(asp.fact("breakable", eid))
    for mem in MEMORIES:
        lines.append(asp.fact("memory", mem.id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    return [(c, e) for c in CHILD_NAMES for e, ex in EXHIBITS.items() if ex.long]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Children's museum fable storyworld.")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--guide", choices=GUIDE_NAMES)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--memory", choices=[m.id for m in MEMORIES])
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
    if args.exhibit and not EXHIBITS[args.exhibit].long:
        raise StoryError("The chosen exhibit is not part of the long-line flashback tale.")
    choices = [(c, e) for c, e in valid_combos()
               if (args.child is None or c == args.child)
               and (args.exhibit is None or e == args.exhibit)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    child, exhibit = rng.choice(choices)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    memory = args.memory or rng.choice([m.id for m in MEMORIES])
    gender = "girl" if child in {"Mia", "Lena", "Nora", "Maya", "Zoe"} else "boy"
    guide_gender = "woman" if guide in {"Aunt June", "Mama", "Ms. Bell"} else "man"
    return StoryParams(child, gender, guide, guide_gender, exhibit, memory)


def _flashback_text(mem: Memory, child: Entity, guide: Entity) -> str:
    return (
        f"Long ago, {child.id} had seen {mem.scene}. {guide.id} had whispered "
        f'"{mem.lesson}" and pointed to the same small kindness.'
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child, "character", params.child_gender, role="child"))
    guide = world.add(Entity("Guide", "character", params.guide_gender, label=params.guide, role="guide"))
    ex = EXHIBITS[params.exhibit]
    mem = next(m for m in MEMORIES if m.id == params.memory)

    child.memes["pride"] = 1
    child.memes["tease"] = 1
    world.say(
        f"In a children's museum, {child.id} and {guide.label or guide.id} came to "
        f"see {ex.label}. It was a long day, and the line itself seemed to stretch like a story."
    )
    world.say(
        f"{child.id} gave a small smirk, as if the wait could not touch {child.pronoun('possessive')} mood."
    )
    world.say(_flashback_text(mem, child, guide))

    world.para()
    child.meters["shaken"] += 1
    world.say(
        f"But when the line stayed long, {child.id}'s smirk faded. The museum was full of voices, "
        f"and {child.id} began to feel small."
    )
    guide.memes["patience"] += 1
    world.say(
        f"{guide.id} repeated the old lesson at once: \"{mem.repeat_line}\""
    )
    world.say(
        f"Then {guide.id} repeated it again, because some truths are easier to keep when they are spoken twice."
    )
    propagate(world, narrate=False)
    child.memes["tease"] = 0
    child.memes["humility"] += 1
    child.memes["kindness"] += 1

    world.para()
    world.say(
        f"{child.id} looked at the long line, then at {guide.id}, and chose a kinder face. "
        f"The smirk was gone; in its place was a patient smile."
    )
    world.say(
        f"When at last they reached {ex.label}, {child.id} shared the first turn and kept the second turn for someone smaller."
    )
    world.say(
        f"So the day ended the way fables like best: the one who had been proud learned to be gentle, "
        f"and the museum felt brighter for it."
    )

    world.facts.update(
        child=child, guide=guide, exhibit=ex, memory=mem,
        flashback=True, repetition=True, softened=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story set in a children\'s museum that uses the words "long" and "smirk".',
        f"Tell a children's museum story where {f['child'].id} starts with a smirk, remembers an old lesson, and changes by the end.",
        f"Write a gentle fable with flashback and repetition about waiting in a long line at the museum.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    mem = f["memory"]
    ex = f["exhibit"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer="It was set in a children's museum, where the rooms were full of things to look at and try."
        ),
        QAItem(
            question=f"What changed in {child.id} by the end?",
            answer=(
                f"{child.id} started with a smirk and a proud way of waiting, but the long line and "
                f"{guide.id}'s repeated lesson helped {child.pronoun('object')} become patient. "
                f"By the end, {child.id} was smiling kindly and sharing turns."
            ),
        ),
        QAItem(
            question="What was the flashback for?",
            answer=(
                f"The flashback reminded {child.id} of {mem.lesson.lower()} It showed why the same lesson mattered again in the museum line."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    ex = world.facts["exhibit"]
    return [
        QAItem(
            question="What is a children's museum?",
            answer="A children's museum is a place where children can learn by looking, touching, and playing with exhibits."
        ),
        QAItem(
            question="What does a smirk usually show?",
            answer="A smirk usually shows pride, teasing, or feeling a little too pleased with yourself."
        ),
        QAItem(
            question="Why do people repeat an important lesson?",
            answer="People repeat an important lesson so it is easier to remember and more likely to be followed."
        ),
        QAItem(
            question=f"Why might a long line matter at {ex.label}?",
            answer="A long line means children must wait their turn, which can test patience and manners."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        em = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if em:
            bits.append(f"memes={dict(em)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    ok = clingo_set == py_set
    if ok:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        print("MISMATCH in gate:")
        if clingo_set - py_set:
            print(" only in clingo:", sorted(clingo_set - py_set))
        if py_set - clingo_set:
            print(" only in python:", sorted(py_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.world is not None
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0 if ok else 1


def _choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos.")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            try:
                params = _choose_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at the children's museum with {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = CURATED if "CURATED" in globals() else [
    StoryParams("Mia", "girl", "Mama", "woman", "buttons", "pigeons"),
    StoryParams("Noah", "boy", "Aunt June", "woman", "mirror", "shells"),
    StoryParams("Zoe", "girl", "Papa", "man", "castle", "dinosaurs"),
]


if __name__ == "__main__":
    main()

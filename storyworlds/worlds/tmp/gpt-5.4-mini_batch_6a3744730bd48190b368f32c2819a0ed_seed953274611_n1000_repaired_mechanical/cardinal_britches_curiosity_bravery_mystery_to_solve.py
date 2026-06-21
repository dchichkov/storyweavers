#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cardinal_britches_curiosity_bravery_mystery_to_solve.py
=======================================================================================

A small comedy storyworld: a curious cardinal in britches notices a mystery,
bravely investigates, and discovers a silly explanation that changes the ending
image. The world is tiny on purpose: a few locations, a few clues, and one
gentle solved mystery.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cardinal_britches_curiosity_bravery_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4-mini/cardinal_britches_curiosity_bravery_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4-mini/cardinal_britches_curiosity_bravery_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/cardinal_britches_curiosity_bravery_mystery_to_solve.py --verify
"""

from __future__ import annotations

import argparse
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        birdish = {"cardinal"}
        if self.type in birdish:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Location:
    id: str
    label: str
    light: str
    smell: str
    sound: str
    clue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Mystery:
    id: str
    what: str
    culprit: str
    reveal: str
    cue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Comfort:
    id: str
    label: str
    use: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    comfort: str
    name: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


LOCATIONS = {
    "garden": Location(
        id="garden",
        label="the garden fence",
        light="sunny and bright",
        smell="like warm dirt and flowers",
        sound="a soft rustle in the leaves",
        clue="a tiny trail of berry crumbs",
        tags={"garden", "berries"},
    ),
    "porch": Location(
        id="porch",
        label="the porch steps",
        light="golden and cozy",
        smell="like biscuits and dust",
        sound="a thump under the step",
        clue="a puff of feather fluff",
        tags={"porch", "fluff"},
    ),
    "barn": Location(
        id="barn",
        label="the old barn corner",
        light="striped by afternoon sun",
        smell="like hay and apples",
        sound="a squeaky little scuffle",
        clue="a noodle of twine",
        tags={"barn", "twine"},
    ),
}

MYSTERIES = {
    "berries": Mystery(
        id="berries",
        what="who kept stealing the berries",
        culprit="the squirrel",
        reveal="the squirrel had been hauling berries into a hollow log for winter",
        cue="berry crumbs",
        tags={"berries", "squirrel"},
    ),
    "feather": Mystery(
        id="feather",
        what="why the porch was tickled with fluff",
        culprit="a windy sparrow",
        reveal="a sparrow kept flapping by with a feather stuck to one toe",
        cue="feather fluff",
        tags={"feather", "sparrow"},
    ),
    "twine": Mystery(
        id="twine",
        what="who made the strange barn thump",
        culprit="a very busy mouse",
        reveal="a mouse had been dragging twine into a nest and bouncing off a boot",
        cue="twine",
        tags={"twine", "mouse"},
    ),
}

COMFORTS = {
    "leaf_patch": Comfort(
        id="leaf_patch",
        label="a big leaf patch",
        use="to mend his britches with a leaf and a berry-stain grin",
        tags={"leaf", "fix"},
    ),
    "pocket": Comfort(
        id="pocket",
        label="a tiny extra pocket",
        use="to keep clues from spilling out again",
        tags={"pocket", "fix"},
    ),
    "pin": Comfort(
        id="pin",
        label="a bright little clothespin",
        use="to clip the torn britches closed",
        tags={"pin", "fix"},
    ),
}

GAMES = ["curiosity", "bravery", "mystery"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, m, c) for p in LOCATIONS for m in MYSTERIES for c in COMFORTS]


def reasonableness_gate(place: str, mystery: str, comfort: str) -> None:
    if place not in LOCATIONS:
        raise StoryError("Unknown place.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if comfort not in COMFORTS:
        raise StoryError("Unknown fix.")
    if place == "garden" and mystery != "berries":
        raise StoryError("The garden mystery should involve berries so the clues feel natural.")
    if place == "porch" and mystery != "feather":
        raise StoryError("The porch mystery should involve fluff or feathers.")
    if place == "barn" and mystery != "twine":
        raise StoryError("The barn mystery should involve twine.")
    if comfort == "pocket" and mystery == "berries":
        raise StoryError("A pocket does not fix a berry trail; choose a patch or pin.")
    if comfort == "pin" and mystery == "feather":
        raise StoryError("A pin is a funny fix, but the story wants a patch or pocket for this clue.")


def _solve(world: World) -> None:
    for e in list(world.entities.values()):
        if e.meters["mystery"] >= THRESHOLD and ("solve", e.id) not in world.fired:
            world.fired.add(("solve", e.id))
            e.memes["relief"] += 1


def tell(place: Location, mystery: Mystery, comfort: Comfort, name: str) -> World:
    w = World()
    bird = w.add(Entity(id=name, kind="character", type="cardinal", label=name))
    britches = w.add(Entity(id="britches", kind="thing", type="britches", label="britches", plural=True))
    clue = w.add(Entity(id="clue", kind="thing", type="clue", label=mystery.cue))
    fix = w.add(Entity(id="fix", kind="thing", type=comfort.label))
    bird.memes["curiosity"] = 2
    bird.memes["bravery"] = 1
    britches.meters["torn"] = 1
    w.facts.update(place=place, mystery=mystery, comfort=comfort, bird=bird, britches=britches, clue=clue, fix=fix)

    w.say(
        f"One bright day, {name} the cardinal wore his britches and wandered to {place.label}. "
        f"It was {place.light}, and the air smelled {place.smell}."
    )
    w.say(
        f"Then came {place.sound}. {name}'s head tilted. He was full of curiosity, and curiosity in a cardinal is a loud little engine."
    )
    w.para()
    bird.memes["curiosity"] += 1
    w.say(
        f"He peered around bravely and found {place.clue}. \"Aha,\" he said. "
        f"\"This is a mystery to solve.\""
    )
    bird.meters["looking"] += 1
    bird.memes["bravery"] += 1
    w.say(
        f"He marched one step, then another, even though the fence shadow looked properly dramatic. "
        f"That was bravery, with a silly little hop."
    )
    if mystery.id == "berries":
        bird.meters["mystery"] += 1
        _solve(w)
        w.para()
        w.say(
            f"At last, {name} spotted {mystery.reveal}. The whole great berry mystery was not a monster at all, just a squirrel with a plan."
        )
        w.say(
            f"{name} laughed so hard that his britches wiggled. He used {comfort.use}, and the torn spot looked so jaunty that even the squirrel seemed impressed."
        )
    elif mystery.id == "feather":
        bird.meters["mystery"] += 1
        _solve(w)
        w.para()
        w.say(
            f"After a few brave peeks, {name} discovered {mystery.reveal}. The porch mystery turned out to be a windy little feather dance."
        )
        w.say(
            f"{name} gave his britches a proud pat and used {comfort.use}. The feather blew past again, and this time the cardinal bowed to it like it was famous."
        )
    else:
        bird.meters["mystery"] += 1
        _solve(w)
        w.para()
        w.say(
            f"Behind a hay bale, {name} finally saw {mystery.reveal}. The barn thump belonged to the busiest mouse in the county."
        )
        w.say(
            f"{name} chuckled, then used {comfort.use}. His britches stayed neat, and the mouse got exactly one tiny audience and a very polite clapping."
        )
    bird.memes["joy"] += 1
    w.facts["resolved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child about a cardinal and his britches, with curiosity and bravery, set at {f["place"].label}.',
        f'Create a comedy mystery where a cardinal notices {f["mystery"].cue} and bravely solves the mystery without getting scared away.',
        f'Write a gentle, silly story that includes the words "cardinal" and "britches" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bird = f["bird"]
    mystery: Mystery = f["mystery"]
    comfort: Comfort = f["comfort"]
    place: Location = f["place"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {bird.id}, a cardinal who wore britches and went looking for a mystery at {place.label}. He was the one who kept noticing the clues first."
        ),
        QAItem(
            question="What made the cardinal start investigating?",
            answer=f"He heard {place.sound} and saw {place.clue}. That made his curiosity switch on, and he decided to solve the mystery instead of ignoring it."
        ),
        QAItem(
            question=f"What was the mystery?",
            answer=f"The mystery was {mystery.what}. It turned out to be {mystery.reveal}, which is a very silly answer for such a serious-looking clue."
        ),
        QAItem(
            question="How did bravery help?",
            answer=f"He kept going even when the shadowy corner looked dramatic. Bravery helped him take another step, and that let him reach the answer."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {bird.id} laughing, the mystery solved, and his britches fixed with {comfort.label}. The ending image proves that the problem changed from puzzling to playful."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = [
        QAItem(
            question="What is a cardinal?",
            answer="A cardinal is a bright red bird with a pointed crest. Cardinals can hop, fly, and look very serious even when they are being funny."
        ),
        QAItem(
            question="What are britches?",
            answer="Britches are old-fashioned pants. In a story, they can be funny clothing for a bird or a person."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to look, ask, and learn. It helps a character notice clues and try to understand them."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the next helpful thing even if you feel a little nervous. It does not mean being loud all the time; it means not giving up."
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="Solving a mystery means finding the answer to a puzzling question. Usually there are clues, then a discovery, then the answer makes sense."
        ),
    ]
    if f["place"].id == "garden":
        q.append(QAItem(question="Why do gardens make good mystery places?", answer="Gardens have leaves, crumbs, shadows, and tiny hiding spots, so clues can feel like they are everywhere."))
    if f["place"].id == "porch":
        q.append(QAItem(question="Why can a porch be a good place to search?", answer="A porch has steps, corners, and little breezes that can move clues around. That makes the search feel lively."))
    if f["place"].id == "barn":
        q.append(QAItem(question="Why can a barn be a good place for a clue?", answer="Barns often have hay, tools, and small animal paths, so a mystery can hide in plain sight."))
    return q


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
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
        if e.plural:
            bits.append("plural=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in LOCATIONS:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


ASP_RULES = r"""
solve(P) :- place(P), mystery(M), comfort(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solve/1."))
    return sorted(set(asp.atoms(model, "solve")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {(p,) for p in LOCATIONS}:
        print("OK: ASP and Python combo gates agree at the place level.")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python valid_combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy cardinal mystery storyworld.")
    ap.add_argument("--place", choices=sorted(LOCATIONS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("--name")
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
    place = args.place or rng.choice(sorted(LOCATIONS))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    reasonableness_gate(place, mystery, comfort)
    name = args.name or rng.choice(["Ruby", "Pip", "Iris", "Milo", "June", "Finn"])
    return StoryParams(place=place, mystery=mystery, comfort=comfort, name=name)


def generate(params: StoryParams) -> StorySample:
    if params.place not in LOCATIONS:
        raise StoryError("Unknown place.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown fix.")
    world = tell(LOCATIONS[params.place], MYSTERIES[params.mystery], COMFORTS[params.comfort], params.name)
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
    StoryParams(place="garden", mystery="berries", comfort="leaf_patch", name="Ruby"),
    StoryParams(place="porch", mystery="feather", comfort="pocket", name="Pip"),
    StoryParams(place="barn", mystery="twine", comfort="pin", name="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solve/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

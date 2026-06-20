#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sonogram_magazine_alternative_misunderstanding_suspense_mystery.py
===================================================================================================

A standalone story world for a small mystery-style tale: a child, a parent, a
waiting room, a missing magazine, a sonogram appointment, and a calm alternative
that resolves a misunderstanding.

The world keeps a simple physical/emotional model:
- physical meters: missing, found, waiting, worry, relief
- emotional memes: curiosity, suspicion, calm, joy, embarrassment

It produces complete, child-facing stories with:
- a clear setup
- a misunderstanding that creates suspense
- a careful investigation
- a resolution that proves what changed

Seed words woven into the domain:
- sonogram
- magazine
- alternative

The "alternative" is a safe replacement for the missing magazine, usually a
picture book or puzzle sheet that fits the waiting room scene.

Run:
    python storyworlds/worlds/gpt-5.4-mini/sonogram_magazine_alternative_misunderstanding_suspense_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/sonogram_magazine_alternative_misunderstanding_suspense_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/sonogram_magazine_alternative_misunderstanding_suspense_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

ROOMS = {"clinic", "waiting_room", "hallway"}
ITEM_TYPES = {"magazine", "book", "puzzle_sheet", "toy"}
PERSON_TYPES = {"child", "parent", "nurse", "receptionist"}


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Scene:
    id: str
    place: str
    waiting_sound: str
    detail: str
    mood: str

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
class MysteryObject:
    id: str
    label: str
    clue: str
    is_missing: bool = False
    is_alt: bool = False
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
class Mistake:
    id: str
    misunderstanding: str
    suspicion: str
    correction: str
    calm_move: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("waiting")
    if not room:
        return out
    if room.meters["mystery"] < THRESHOLD:
        return out
    sig = ("missing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"child", "parent"}:
            e.memes["curiosity"] += 1
            e.memes["suspicion"] += 1
    out.append("__missing__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.entities["magazine"].meters["found"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.role in {"child", "parent"}:
            e.memes["relief"] += 1
            e.memes["calm"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("missing", "social", _r_missing), Rule("relief", "social", _r_relief)]


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


def sensible_alternatives() -> list[str]:
    return [a.id for a in ALTERNATIVES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for obj in OBJECTS:
            for alt in ALTERNATIVES:
                if obj == "magazine" and alt != "picture_book":
                    continue
                combos.append((scene, obj, alt))
    return combos


def explain_rejection(obj: MysteryObject, alt: str) -> str:
    if obj.id != "magazine":
        return "(No story: this world centers on a missing magazine in a waiting room.)"
    if alt != "picture_book":
        return "(No story: the alternative must be a calm, reading-friendly choice.)"
    return "(No story: this combination is not reasonable.)"


@dataclass
@dataclass
class StoryParams:
    scene: str
    object: str
    alternative: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    helper: str
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


def tell(scene: Scene, obj: MysteryObject, alt: MysteryObject,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Dad", parent_gender: str = "father",
         helper_name: str = "Nurse", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))

    waiting = world.add(Entity(id="waiting", kind="room", type="room", label=scene.place))
    magazine = world.add(Entity(id="magazine", kind="thing", type="magazine", label=obj.label, role="object"))
    alt_ent = world.add(Entity(id="alternative", kind="thing", type="book", label=alt.label, role="alternative"))
    sonogram = world.add(Entity(id="sonogram", kind="thing", type="picture", label="sonogram", role="clue"))

    child.memes["curiosity"] = 1
    parent.memes["calm"] = 1
    waiting.meters["mystery"] = 1

    world.say(
        f"{child.id} and {parent.id} sat in the {scene.place}, where {scene.waiting_sound} "
        f"and the air felt still. {scene.detail}"
    )
    world.say(
        f"{child.id} noticed a sonogram picture on the wall and asked, "
        f'"Is that for the baby, or is it a clue?"'
    )
    world.say(
        f"{parent.id} smiled and said they were there for a sonogram, a picture that shows what is inside."
    )

    world.para()
    world.say(
        f"Then {child.id} reached for the magazine on the table -- or what looked like a magazine."
    )
    world.say(
        f"It was gone from the spot where it had been, and that made the waiting room feel like a mystery."
    )
    propagate(world, narrate=False)
    child.memes["worry"] += 1
    parent.memes["worry"] += 1
    waiting.meters["mystery"] += 1

    world.para()
    world.say(
        f'"Did someone take it?" {child.id} whispered. "Maybe the sonogram picture moved it."'
    )
    world.say(
        f"{parent.id} looked around carefully, because a misunderstanding had turned a tiny wait into suspense."
    )

    world.para()
    world.say(
        f"{helper.id} came over with a calm voice and pointed to the desk. "
        f'"The magazine was moved to the other chair," {helper.id} said. '
        f'"And if you want something to read, here is an alternative."'
    )
    world.say(f"{helper.id} handed over {alt.label}.")

    magazine.meters["found"] += 1
    waiting.meters["mystery"] = 0
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{child.id} blinked, then laughed in embarrassment. "
        f'"Oh! I thought the sonogram or the magazine had vanished."'
    )
    world.say(
        f"{parent.id} sat closer, and the waiting room felt easy again with the alternative open on {child.id}'s lap."
    )
    world.say(
        f"By the time the sonogram was done, the missing magazine was no longer a mystery, just a small mix-up."
    )

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        scene=scene,
        object_cfg=obj,
        alternative_cfg=alt,
        magazine=magazine,
        sonogram=sonogram,
        outcome="resolved",
    )
    return world


SCENES = {
    "clinic": Scene("clinic", "clinic waiting room", "a clock ticked softly", "A fish tank hummed near the chair.", "quiet"),
    "hospital": Scene("hospital", "hospital waiting room", "pages rustled softly", "A poster of stars hung by the door.", "hushed"),
    "office": Scene("office", "doctor office waiting room", "air vents whispered", "A stack of papers leaned under a lamp.", "still"),
}

OBJECTS = {
    "magazine": MysteryObject("magazine", "a magazine", "something to read", is_missing=True, tags={"magazine"}),
}

ALTERNATIVES = {
    "picture_book": MysteryObject("picture_book", "a picture book", "a calm reading choice", is_alt=True, tags={"alternative"}),
    "puzzle_sheet": MysteryObject("puzzle_sheet", "a puzzle sheet", "a quiet page of puzzles", is_alt=True, tags={"alternative"}),
    "coloring_book": MysteryObject("coloring_book", "a coloring book", "crayons and pictures", is_alt=True, tags={"alternative"}),
}

KNOWLEDGE = {
    "sonogram": [("What is a sonogram?",
                  "A sonogram is a picture doctors make with sound waves. It helps them see inside the body without cutting it open.")],
    "magazine": [("What is a magazine?",
                 "A magazine is a small book with stories, pictures, or facts to read.")],
    "alternative": [("What is an alternative?",
                     "An alternative is another choice you can use instead.")],
    "mystery": [("What is a mystery?",
                "A mystery is something that is not fully known yet, so people try to figure it out.")],
    "suspense": [("What is suspense?",
                 "Suspense is the feeling of wondering what will happen next.")],
    "waiting": [("Why do people wait in a clinic?",
                "People wait in a clinic because they are waiting for an appointment or a checkup.")],
}
KNOWLEDGE_ORDER = ["sonogram", "magazine", "alternative", "mystery", "suspense", "waiting"]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly mystery story that uses the words "sonogram", "magazine", and "alternative".',
        f"Tell a short suspense story set in a waiting room where {world.facts['child'].id} "
        f"misunderstands a missing magazine and then learns the calm alternative.",
        "Write a simple mystery with a misunderstanding, a careful look around, and a gentle ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    h = world.facts["helper"]
    alt = world.facts["alternative_cfg"]
    return [
        QAItem("Who is the story about?",
               f"It is about {c.id}, {p.id}, and {h.id} in a waiting room mystery. The missing magazine makes the scene feel suspenseful at first."),
        QAItem("What did the child misunderstand?",
               f"{c.id} thought the sonogram picture or the magazine had vanished for a bigger reason. It was really only a small mix-up about where the magazine had been moved."),
        QAItem("How was the problem solved?",
               f"{h.id} brought an alternative and showed where the magazine had gone. That calm help turned the suspense into relief."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"sonogram", "magazine", "alternative", "mystery", "suspense", "waiting"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key]
            out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clinic", "magazine", "picture_book", "Mina", "girl", "mother", "woman"),
    StoryParams("hospital", "magazine", "puzzle_sheet", "Eli", "boy", "father", "man"),
    StoryParams("office", "magazine", "coloring_book", "Nora", "girl", "mother", "woman"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for aid in ALTERNATIVES:
        lines.append(asp.fact("alternative", aid))
        if aid == "picture_book":
            lines.append(asp.fact("sensible", aid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, O, A) :- scene(S), object(O), alternative(A), O = magazine, A = picture_book.
sensible(A) :- alternative(A), A = picture_book.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) == set(sensible_alternatives()):
        print("OK: sensible alternatives match.")
    else:
        rc = 1
        print("MISMATCH in sensible alternatives")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery story world with sonogram, magazine, and alternative.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father", "woman", "man"])
    ap.add_argument("--helper")
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
    if args.object and args.object != "magazine":
        raise StoryError("(No story: this world centers on a missing magazine.)")
    if args.alternative and args.alternative != "picture_book":
        raise StoryError("(No story: the alternative here must be a picture book.)")
    combos = valid_combos()
    scene, obj, alt = rng.choice(combos)
    child = args.child or rng.choice(["Mina", "Eli", "Nora", "Owen", "Luna"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["Mom", "Dad"])
    parent_gender = args.parent_gender or ("mother" if parent == "Mom" else "father")
    helper = args.helper or rng.choice(["Nurse", "Receptionist"])
    return StoryParams(scene, obj, alt, child, child_gender, parent, parent_gender, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], OBJECTS[params.object], ALTERNATIVES[params.alternative],
                 params.child, params.child_gender, params.parent, params.parent_gender, params.helper)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

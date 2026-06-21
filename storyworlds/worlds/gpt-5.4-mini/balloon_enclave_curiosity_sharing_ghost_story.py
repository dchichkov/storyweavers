#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/balloon_enclave_curiosity_sharing_ghost_story.py
================================================================================

A small standalone story world about a child, a balloon, a hidden enclave, and a
ghost-story mood. The premise is gentle: a curious child finds a whispering
balloon in a tucked-away enclave, learns that sharing calms what seems spooky,
and ends with a warm lantern-like image proving the air, the place, and the
feelings have changed.

The world model tracks physical meters and emotional memes, uses forward rules
for cause/effect, provides grounded QA, and includes an inline ASP twin for the
reasonableness gate and outcome parity checks.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Place:
    id: str
    label: str
    shadowy: bool = False
    quiet: bool = False
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
class Balloon:
    id: str
    label: str
    color: str
    whisper: str
    glow: str
    fragile: bool = True
    tag: str = "balloon"

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
class Lantern:
    id: str
    label: str
    phrase: str
    glow: str
    tag: str = "lantern"

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_uneasy(world: World) -> list[str]:
    out: list[str] = []
    balloon = world.get("balloon")
    child = world.get("child")
    enclave = world.get("enclave")
    if balloon.meters["haunted"] < THRESHOLD:
        return out
    sig = ("uneasy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    enclave.memes["spooky"] += 1
    child.memes["uneasy"] += 1
    out.append("__uneasy__")
    return out


def _r_shared(world: World) -> list[str]:
    out: list[str] = []
    balloon = world.get("balloon")
    child = world.get("child")
    if balloon.meters["shared"] < THRESHOLD:
        return out
    sig = ("shared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["warmth"] += 1
    child.memes["fear"] = 0.0
    out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("uneasy", "emotional", _r_uneasy), Rule("shared", "emotional", _r_shared)]


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


@dataclass
@dataclass
class StoryParams:
    place: str
    balloon: str
    lantern: str
    name: str
    gender: str
    parent: str
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


PLACES = {
    "enclave": Place("enclave", "the little enclave", shadowy=True, quiet=True,
                     tags={"enclave", "shadow", "ghost"}),
    "garden": Place("garden", "the garden nook", shadowy=False, quiet=True,
                    tags={"garden"}),
    "attic": Place("attic", "the attic corner", shadowy=True, quiet=True,
                   tags={"attic", "ghost"}),
}

BALLOONS = {
    "silver": Balloon("silver", "a silver balloon", "silver",
                      "a faint whisper like a secret", "it caught the moonlight"),
    "blue": Balloon("blue", "a blue balloon", "blue",
                    "a tiny hush that sounded lonely", "it gleamed softly"),
    "red": Balloon("red", "a red balloon", "red",
                   "a wobbling murmur like a sleepy ghost", "it shone warm and round"),
}

LANTERNS = {
    "paper": Lantern("paper", "a paper lantern", "paper lantern", "it glowed like a tiny moon"),
    "jar": Lantern("jar", "a jar lantern", "jar lantern", "it glowed like a safe star"),
}

GIRL_NAMES = ["Mia", "Lina", "Tess", "Nora", "Ivy", "Rose"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Max", "Leo"]
TRAITS = ["curious", "kind", "careful", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, b, l) for p in PLACES for b in BALLOONS for l in LANTERNS]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def outcome_of(params: StoryParams) -> str:
    return "calmed" if RESPONSES[params.lantern].power >= 1 else "drifted"


RESPONSES = {
    "share": Response(
        "share", 3, 2,
        "held the balloon carefully and shared it with a friend until the whisper turned into a soft song",
        "tried to hush the balloon alone, but the whisper only grew stranger",
        "shared the balloon with a friend and the spooky whisper became gentle",
        tags={"share", "balloon"},
    ),
    "listen": Response(
        "listen", 2, 1,
        "set the balloon on a bench and listened until it stopped seeming spooky",
        "waited too long, and the whisper kept tugging at the dark",
        "listened calmly and let the balloon quiet down",
        tags={"listen", "balloon"},
    ),
}


def reasonableness_ok(place: Place, balloon: Balloon) -> bool:
    return place.shadowy and balloon.fragile


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story style balloon enclave tale.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--balloon", choices=BALLOONS)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    balloon = args.balloon or rng.choice(list(BALLOONS))
    lantern = args.lantern or rng.choice(list(LANTERNS))
    if not reasonableness_ok(PLACES[place], BALLOONS[balloon]):
        raise StoryError("No story: the balloon story needs a shadowy place where curiosity can echo.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, balloon, lantern, name, gender, parent)


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity("child", kind="character", type=params.gender, label=params.name))
    parent = w.add(Entity("parent", kind="character", type=params.parent, label="the parent"))
    place = w.add(Entity("enclave", type="place", label=PLACES[params.place].label))
    balloon = w.add(Entity("balloon", type="balloon", label=BALLOONS[params.balloon].label))
    lantern = w.add(Entity("lantern", type="lantern", label=LANTERNS[params.lantern].phrase))
    child.memes["curiosity"] += 1
    w.say(f"One quiet night, {child.id} wandered to {place.label}, a little enclave hidden behind the hedges.")
    w.say(f"There, a {balloon.label} floated in the dark, and its {BALLOONS[params.balloon].whisper} made {child.id} stare.")
    w.say(f'{child.id} leaned closer. "I wonder what it wants," {child.pronoun()} whispered.')
    w.para()
    child.memes["curiosity"] += 1
    balloon.meters["haunted"] += 1
    propagate(w, narrate=False)
    w.say(f"The balloon trembled, and for a moment the enclave felt like a ghost story waiting to be told.")
    w.say(f'"Please share it carefully," {parent.label_word} said, coming up behind {child.id}. "Spooky things feel smaller when they are shared."')
    balloon.meters["shared"] += 1
    propagate(w, narrate=False)
    w.para()
    w.say(f"{child.id} nodded, lifted {balloon.label} between both hands, and let a neighbor peek too.")
    w.say(f"Then {parent.label_word} clicked on {lantern.label}, and {lantern.glow}.")
    w.say(f"The whisper softened into a friendly hush, and the little enclave stopped feeling haunted at all.")
    w.say(f"{child.id} smiled, not scared now, and the balloon bobbed above the path like a tiny moon.")
    w.facts.update(child=child, parent=parent, place=place, balloon=balloon, lantern=lantern,
                   outcome="calmed", shared=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story for a young child that includes the words "balloon" and "enclave".',
        f"Tell a story where {f['child'].id} is curious about a balloon in a secret enclave and learns that sharing makes it feel safe.",
        f'Write a spooky-but-kind story with a balloon, a hidden enclave, and a warm ending where sharing changes the mood.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, balloon, lantern = f["child"], f["parent"], f["balloon"], f["lantern"]
    return [
        QAItem(
            question="What did the child find in the enclave?",
            answer=f"{child.id} found {balloon.label} in the little enclave. It looked spooky at first because it whispered in the dark."
        ),
        QAItem(
            question="Why did the mood change?",
            answer=f"The mood changed because {child.id} shared the balloon instead of keeping the mystery alone. Sharing made the whisper feel friendly, and {parent.label_word} brought a lantern to make the place bright."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a calm, glowing enclave and a balloon that felt friendly instead of eerie. The child was smiling, and the dark place no longer felt haunted."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a balloon?",
            answer="A balloon is a light, stretchy object filled with air or helium. It floats and bobs because the air inside gives it shape."
        ),
        QAItem(
            question="What is an enclave?",
            answer="An enclave is a small place that feels tucked away from everything else. It can seem secret, quiet, or protected."
        ),
        QAItem(
            question="Why can sharing help when something feels spooky?",
            answer="Sharing can make a scary thing feel less lonely and less mysterious. When someone else looks with you, the fear often gets smaller."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


CURATED = [
    StoryParams("enclave", "silver", "paper", "Mia", "girl", "mother"),
    StoryParams("attic", "blue", "jar", "Eli", "boy", "father"),
]


ASP_RULES = r"""
valid(P,B,L) :- place(P), balloon(B), lantern(L), shadowy(P), fragile(B).
calmed :- shared(balloon).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.shadowy:
            lines.append(asp.fact("shadowy", pid))
    for bid in BALLOONS:
        lines.append(asp.fact("balloon", bid))
        lines.append(asp.fact("fragile", bid))
    for lid in LANTERNS:
        lines.append(asp.fact("lantern", lid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    gate = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if gate == cl:
        print(f"OK: gate matches valid_combos() ({len(gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, balloon=None, lantern=None, parent=None, name=None, gender=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

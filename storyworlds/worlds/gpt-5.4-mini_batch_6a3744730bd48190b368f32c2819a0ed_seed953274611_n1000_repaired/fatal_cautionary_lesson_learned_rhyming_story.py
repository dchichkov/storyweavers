#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fatal_cautionary_lesson_learned_rhyming_story.py
=================================================================================

A standalone storyworld for a tiny cautionary rhyming tale: two children wander
near a risky frozen pond, one child wants to skate, the other warns, a grown-up
helps, and the children learn a lasting lesson.

The story keeps the verse-like, child-facing feel of a rhyming story while still
being a simulated world with meters/memes, a reasonableness gate, and an ASP twin.
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
RHYME_ENDINGS = ("ight", "ow", "ale", "oon", "are", "ay")


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    scene: str
    boundary: str
    rhyme: str
    risky: bool = False
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


@dataclass
class Hazard:
    id: str
    label: str
    warning: str
    risk_word: str
    makes_fatal: bool = True
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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        import copy
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def rhymes(a: str, b: str) -> bool:
    return a[-3:] == b[-3:] if len(a) >= 3 and len(b) >= 3 else False


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for h in HAZARDS:
            if p.risky and h.makes_fatal:
                combos.append((p.id, h.id))
    return combos


@dataclass
class StoryParams:
    place: str
    hazard: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    response: str
    seed: Optional[int] = None
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


PLACES = {
    "pond": Place(
        id="pond",
        scene="the frozen pond by the reeds",
        boundary="the ice had a pale blue gleam",
        rhyme="light",
        risky=True,
    ),
    "dock": Place(
        id="dock",
        scene="the dock by the water",
        boundary="the boards were slick and low",
        rhyme="ow",
        risky=True,
    ),
}

HAZARDS = {
    "ice": Hazard(
        id="ice",
        label="thin ice",
        warning="That ice can crack with a bite",
        risk_word="fatal",
        makes_fatal=True,
    ),
    "plank": Hazard(
        id="plank",
        label="a loose plank",
        warning="That plank can tip out of sight",
        risk_word="fatal",
        makes_fatal=True,
    ),
}

RESPONSES = {
    "rope": Response(
        id="rope",
        sense=3,
        power=3,
        text="threw a rope and pulled them back to the shore so bright",
        fail="threw a rope, but the gap was wide and the reach was tight",
        qa_text="threw a rope and pulled them back to shore",
    ),
    "call_help": Response(
        id="call_help",
        sense=3,
        power=3,
        text="called for help and guided them in time before any fright",
        fail="called for help, but the trouble moved too fast in the night",
        qa_text="called for help and guided them to safety",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max"]


def default_rhyme() -> str:
    return "ight"


def make_line(*parts: str) -> str:
    return " ".join(parts)


def hazard_at_risk(place: Place, hazard: Hazard) -> bool:
    return place.risky and hazard.makes_fatal


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def fire_severity(place: Place) -> int:
    return 3 if place.id == "pond" else 4


def is_contained(response: Response, place: Place) -> bool:
    return response.power >= fire_severity(place)


def tell(place: Place, hazard: Hazard, response: Response,
         child1: Entity, child2: Entity, parent: Entity) -> World:
    world = World()
    a = world.add(child1)
    b = world.add(child2)
    mom = world.add(parent)
    a.memes["joy"] += 1
    b.memes["joy"] += 1

    world.say(
        f"{a.id} and {b.id} went out to play by {place.scene}, a place that shimmered and glowed."
    )
    world.say(
        f"{place.boundary.capitalize()}, and {a.id} wanted fun that was daring and bold."
    )
    world.para()
    world.say(
        f"But {b.id} frowned and gave a small warning in rhyme, "
        f'"{hazard.warning}, or trouble may come in time."'
    )
    world.say(
        f'"{hazard.label.capitalize()} is no game," {b.id} said with care, '
        f'\"a fatal mistake can lurk in the air.\"'
    )
    world.say(
        f"{a.id} paused at the edge, then called for {mom.label_word} by name, "
        f"because the cold ice can trick kids into risky play."
    )
    if response.id == "rope":
        world.para()
        world.say(
            f"{mom.label_word.capitalize()} came quickly and {response.text}."
        )
        world.say(
            f"The risky ground stilled, and the children stood proud with their feet back on land."
        )
    else:
        world.para()
        world.say(
            f"{mom.label_word.capitalize()} came quickly and {response.text}."
        )
        world.say(
            f"The scare passed by, and the children were safe with help close at hand."
        )
    world.para()
    world.say(
        f"{mom.label_word.capitalize()} knelt down and said, \"Remember this lesson so clear: "
        f"{hazard.label} can be {hazard.risk_word}, so call a grown-up when danger is near.\""
    )
    world.say(
        f"{a.id} and {b.id} nodded and promised to listen and learn, "
        f"and they walked home together with warm cheeks that burned."
    )
    world.facts.update(
        child1=a, child2=b, parent=mom, place=place, hazard=hazard,
        response=response, outcome="safe", learned=True, fatal_word=hazard.risk_word
    )
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["child1"], f["child2"], f["parent"]
    hazard = f["hazard"]
    response = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two children who were playing near a risky place. {parent.label_word.capitalize()} helped them when the trouble started."),
        ("What was the dangerous thing?",
         f"The dangerous thing was {hazard.label}. It could be fatal if someone stepped where they should not, so {b.id} warned {a.id} right away."),
        ("What did the grown-up do?",
         f"{parent.label_word.capitalize()} came quickly and {response.qa_text}. That kept the children safe and turned the scare into a lesson."),
        ("What did the children learn?",
         f"They learned to listen when a place looks risky and to call a grown-up first. They also learned that {hazard.label} can be fatal if they ignore the warning."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("Why can thin ice be dangerous?",
         "Thin ice can crack, and then a person can fall into very cold water. That is why it can be fatal and must be treated with care."),
        ("What should children do when something looks unsafe?",
         "They should stop, back away, and call a grown-up right away. Asking for help is the safest choice."),
        ("What does a rope help with in a rescue?",
         "A rope can help a grown-up pull someone back from a risky place without walking onto the danger. It gives help from a safer spot."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming cautionary story that includes the word "{f["hazard"].risk_word}" and ends with a lesson learned.',
        f"Tell a child-friendly rhyme where {f['child1'].id} wants to explore the danger, but {f['child2'].id} warns them and a grown-up helps.",
        f"Write a brief rhyming story about a risky place, a careful warning, and a lesson learned about safety.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


def explain_rejection(place: Place, hazard: Hazard) -> str:
    return f"(No story: {place.id} is not risky enough for {hazard.label} to drive a cautionary lesson.)"


ASP_RULES = r"""
valid(P,H) :- place(P), hazard(H), risky(P), fatal(H).
outcome(safe) :- valid(P,H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.makes_fatal:
            lines.append(asp.fact("fatal", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP parity")
        return 1
    try:
        s = resolve_params(argparse.Namespace(place=None, hazard=None, response=None, seed=None, n=1, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(777))
        sample = generate(s)
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming cautionary storyworld with a fatal lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.place and args.hazard:
        if not hazard_at_risk(PLACES[args.place], HAZARDS[args.hazard]):
            raise StoryError(explain_rejection(PLACES[args.place], HAZARDS[args.hazard]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    c1 = rng.choice(GIRL_NAMES + BOY_NAMES)
    c2 = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != c1])
    gender1 = "girl" if c1 in GIRL_NAMES else "boy"
    gender2 = "girl" if c2 in GIRL_NAMES else "boy"
    parent = rng.choice(["mom", "dad"])
    return StoryParams(
        place=place, hazard=hazard, child1=c1, child1_gender=gender1,
        child2=c2, child2_gender=gender2, parent=parent, response=response
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.response not in RESPONSES:
        raise StoryError("invalid params")
    place = PLACES[params.place]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    world = tell(
        place=place,
        hazard=hazard,
        response=response,
        child1=Entity(id=params.child1, kind="character", type=params.child1_gender, role="instigator"),
        child2=Entity(id=params.child2, kind="character", type=params.child2_gender, role="cautioner"),
        parent=Entity(id=params.parent, kind="character", type="mother" if params.parent == "mom" else "father", role="parent"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(place="pond", hazard="ice", child1="Mia", child1_gender="girl", child2="Leo", child2_gender="boy", parent="mom", response="rope"),
    StoryParams(place="dock", hazard="plank", child1="Nora", child1_gender="girl", child2="Max", child2_gender="boy", parent="dad", response="call_help"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

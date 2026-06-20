#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ton_humongous_cautionary_suspense_mystery.py
=============================================================================

A standalone story world for a small cautionary mystery with suspense.

Premise
-------
A child notices a strange humongous shape, follows clues through a quiet place,
and learns not to touch something risky without a grown-up. The story is built
from a simulated world with entities, physical meters, emotional memes, and a
few causal rules so the prose comes from state changes rather than a frozen
template.

Seed words
----------
ton, humongous

Style notes
-----------
- Mystery-flavored: clues, quiet observations, a reveal, and a final explanation.
- Cautionary: an unsafe choice is resisted or corrected.
- Suspense: the child hesitates, hears a sound, and chooses carefully.

The file is intentionally self-contained and uses only stdlib plus
``storyworlds/results.py`` for shared result containers.
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

# Make shared result containers importable when run directly from repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
class Place:
    id: str
    label: str
    dark: bool = False
    echo: bool = False
    clues: list[str] = field(default_factory=list)

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
    phrase: str
    risky: bool = False
    heavy: bool = False
    dusty: bool = False
    secret: str = ""
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def kids(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.role in {"child", "cautioner"}]


@dataclass
class Rule:
    name: str
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


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["fear"] < THRESHOLD:
            continue
        sig = ("anxiety", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["unease"] += 1
        out.append("")
    return out


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for obj in list(world.entities.values()):
        if obj.meters["opened"] < THRESHOLD:
            continue
        sig = ("dust", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        obj.meters["dust"] += 1
        out.append("__dust__")
    return out


CAUSAL_RULES = [Rule("anxiety", _r_anxiety), Rule("dust", _r_dust)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if x and not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


SENSE_MIN = 2


def hazard_at_risk(obj: MysteryObject) -> bool:
    return obj.risky


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def story_moment(world: World, child: Entity, guide: Entity, place: Place, obj: MysteryObject) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {guide.id} wandered into {place.label}. "
        f"Something there looked humongous in the half-light, and it made the room feel very still."
    )
    world.say(
        f"{child.id} noticed a clue: {place.clues[0]}. {guide.id} pointed to the shape and said it might hide a secret."
    )
    world.say(
        f'{child.id} whispered, "What is that?" and stepped closer to the ton of old boxes.'
    )
    if obj.heavy:
        child.memes["worry"] += 1


def warn(world: World, guide: Entity, child: Entity, obj: MysteryObject) -> None:
    guide.memes["care"] += 1
    world.say(
        f'{guide.id} frowned a little. "{child.id}, do not tug on it yet," {guide.pronoun()} said. '
        f'"It looks dusty, and some secrets are better handled slowly."'
    )


def open_too_fast(world: World, child: Entity, obj: MysteryObject) -> None:
    child.memes["defiance"] += 1
    obj.meters["opened"] += 1
    world.say(
        f"Still, {child.id} reached for the latch. The humongous lid gave a soft creak, and a puff of dust floated out."
    )
    propagate(world, narrate=False)


def reveal(world: World, guide: Entity, child: Entity, obj: MysteryObject, response: Response) -> None:
    world.say(
        f"{guide.id} came right over and {response.text.replace('{object}', obj.label)}."
    )
    world.say(
        f"Inside was not a monster at all, only {obj.secret}. The mystery had a plain answer, but it was still a careful one."
    )
    child.memes["relief"] += 1


def fail_reveal(world: World, guide: Entity, child: Entity, obj: MysteryObject, response: Response) -> None:
    world.say(
        f"{guide.id} came running, but {response.fail.replace('{object}', obj.label)}."
    )
    world.say(
        f"The lid thumped down again. {child.id} backed away, and the humongous shape stayed closed until help arrived."
    )


def ending(world: World, child: Entity, guide: Entity, obj: MysteryObject) -> None:
    world.say(
        f"In the end, {child.id} and {guide.id} wrote the clue on a little note and left the box alone."
    )
    world.say(
        f"The room felt normal again, and the humongous thing turned out to be just a mysterious old box with a plain secret inside."
    )


def tell(place: Place, obj: MysteryObject, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         guide_name: str = "Mom", guide_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    world.add(Entity(id=place.id, type="place", label=place.label))
    box = world.add(Entity(id=obj.id, type="object", label=obj.label))
    story_moment(world, child, guide, place, obj)
    world.para()
    warn(world, guide, child, obj)
    open_too_fast(world, child, obj)
    world.para()
    if response.power >= 2:
        reveal(world, guide, child, box if False else obj, response)
        ending(world, child, guide, obj)
        outcome = "safe"
    else:
        fail_reveal(world, guide, child, obj, response)
        ending(world, child, guide, obj)
        outcome = "cautious"
    world.facts.update(child=child, guide=guide, place=place, obj=obj,
                       response=response, outcome=outcome)
    return world


PLACES = {
    "attic": Place("attic", "the attic", dark=True, echo=True,
                   clues=["the floor creaked like a slow drum"]),
    "shed": Place("shed", "the garden shed", dark=True, echo=True,
                  clues=["a tiny moonbeam slipped through a crack"]),
    "library": Place("library", "the back corner of the library", dark=True, echo=False,
                     clues=["the air smelled like paper and dust"]),
}

OBJECTS = {
    "box": MysteryObject("box", "old box", "a humongous old box", risky=True, heavy=True,
                         dusty=True, secret="a pile of costume hats", tags={"mystery", "dust", "box"}),
    "trunk": MysteryObject("trunk", "trunk", "a humongous wooden trunk", risky=True, heavy=True,
                           dusty=True, secret="grandpa's folded maps", tags={"mystery", "trunk"}),
    "crate": MysteryObject("crate", "crate", "a humongous crate", risky=True, heavy=True,
                           dusty=True, secret="three sleepy kittens and a blanket", tags={"mystery", "crate"}),
}

RESPONSES = {
    "peek": Response("peek", 3, 3,
                     "lifted the lid carefully and checked inside",
                     "tried to peek inside, but the lid was too heavy to move safely",
                     "lifted the lid carefully and looked inside"),
    "ask": Response("ask", 3, 2,
                    "asked the grown-up to open it slowly and show what was inside",
                    "asked, but the grown-up could not open it yet",
                    "asked the grown-up to open it slowly"),
    "wait": Response("wait", 2, 2,
                     "waited until the grown-up moved the box to the light",
                     "waited, but the mystery stayed closed for the moment",
                     "waited until the grown-up moved the box"),
    "tug": Response("tug", 1, 1,
                    "tugged it open",
                    "tugged, but it would not budge",
                    "tugged it open"),
}

CHILD_NAMES = ["Mia", "Lena", "Noah", "Eli", "Ava", "Lily", "Theo", "Nina"]
GUIDE_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa"]


@dataclass
@dataclass
class StoryParams:
    place: str
    obj: str
    response: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
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
    combos = []
    for pid, place in PLACES.items():
        for oid, obj in OBJECTS.items():
            if not hazard_at_risk(obj):
                continue
            for rid, resp in RESPONSES.items():
                if resp.sense >= SENSE_MIN:
                    combos.append((pid, oid, rid))
    return combos


KNOWLEDGE = {
    "mystery": [("What is a mystery?",
                 "A mystery is something that is not known at first, so people look for clues and ask questions.")],
    "dust": [("Why should you be careful with dusty old things?",
              "Dust can make you sneeze, and old things may be fragile, so it is smarter to open them slowly.")],
    "box": [("What can be inside an old box?",
             "An old box can hold many things, like toys, papers, clothes, or costumes.")],
    "trunk": [("What is a trunk?",
               "A trunk is a big, sturdy box for storing things like clothes or papers.")],
    "crate": [("What is a crate?",
               "A crate is a strong box made for carrying or storing things safely.")],
    "caution": [("What does it mean to be cautious?",
                 "Being cautious means slowing down, looking carefully, and choosing the safer move.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a cautionary mystery for a young child that includes the word "humongous" and the word "ton".',
        f"Tell a suspenseful story where {f['child'].id} spots a humongous object in {f['place'].label} and learns not to open it too fast.",
        f"Write a simple mystery ending with a grown-up helping a child solve a scary-looking clue safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide, place, obj = f["child"], f["guide"], f["place"], f["obj"]
    resp = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {guide.id}. They found a humongous-looking mystery in {place.label}."),
        ("What made the child nervous?",
         f"The humongous {obj.label} looked strange in the dark, and the dust made it feel even more suspicious. That is why the child wanted to know the answer right away."),
        ("What did the grown-up say to do?",
         f"{guide.id} told {child.id} not to tug on it yet and to move slowly. That warning kept the mystery from becoming a mistake."),
        ("How did they solve the mystery?",
         f"They used a careful {resp.qa_text.lower()} and found out what was inside. The answer was ordinary, but the careful way mattered."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["obj"].tags) | {"mystery", "caution"}
    out: list[tuple[str, str]] = []
    for key in ["mystery", "dust", "box", "trunk", "crate", "caution"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "box", "peek", "Mia", "girl", "Mom", "girl"),
    StoryParams("shed", "crate", "ask", "Noah", "boy", "Dad", "boy"),
    StoryParams("library", "trunk", "wait", "Ava", "girl", "Aunt June", "girl"),
]


def explain_rejection(obj: MysteryObject) -> str:
    return f"(No story: {obj.label} is not a risky mystery object in this world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.risky:
            lines.append(asp.fact("risky", oid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O,R) :- place(P), object(O), risky(O), response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} valid combos.")
    # smoke test ordinary generation
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, obj=None, response=None,
                                                           child_name=None, child_gender=None,
                                                           guide_name=None, guide_gender=None,
                                                           seed=None), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary suspense mystery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["girl", "boy"])
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
    if args.obj and not OBJECTS[args.obj].risky:
        raise StoryError(explain_rejection(OBJECTS[args.obj]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.obj is None or c[1] == args.obj)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    guide_name = args.guide_name or rng.choice(GUIDE_NAMES)
    return StoryParams(place, obj, response, child_name, child_gender, guide_name, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OBJECTS[params.obj], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.guide_name, params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

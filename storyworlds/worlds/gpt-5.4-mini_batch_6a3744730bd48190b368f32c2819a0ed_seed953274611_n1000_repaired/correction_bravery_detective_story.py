#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/correction_bravery_detective_story.py
=====================================================================

A small detective storyworld about a brave child detective who makes a mistake,
gets a correction, and uses that correction to solve the case.

Premise:
- A child detective follows a clue, but the clue is partly wrong.
- A braver friend or grown-up corrects the mistake.
- The detective uses the corrected clue to find the missing object.
- The ending proves bravery changed the outcome: the detective asks, listens,
  and finishes the case.

The world is simulated with typed entities that track physical meters and
emotional memes. The story text is driven from world state, not templated with
swapped nouns.

Supports:
- default run
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp

Stdlib-only, with lazy import of storyworlds.asp for ASP modes.
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
BRAVERY_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    kind: str
    details: str
    has_visitor: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    wrong_lead: str
    correction: str
    evidence: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Suspect:
    id: str
    label: str
    type: str
    truthful: bool
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
class StoryParams:
    location: str = "library"
    clue: str = "blue_note"
    suspect: str = "librarian"
    hero: str = "Nina"
    hero_gender: str = "girl"
    helper: str = "Milo"
    helper_gender: str = "boy"
    helper_role: str = "friend"
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["confusion"] >= THRESHOLD and ("alarm",) not in world.fired:
        world.fired.add(("alarm",))
        hero.memes["unease"] += 1
        out.append("__alarm__")
    return out


def _r_correction(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.memes["bravery"] < BRAVERY_MIN:
        return out
    if hero.meters["confusion"] < THRESHOLD or helper.meters["correction"] >= THRESHOLD:
        return out
    world.fired.add(("correction",))
    helper.meters["correction"] += 1
    hero.meters["confusion"] = 0.0
    hero.meters["understanding"] += 1
    hero.memes["hope"] += 1
    out.append("__correction__")
    return out


def _r_find(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["understanding"] < THRESHOLD or ("found",) in world.fired:
        return out
    world.fired.add(("found",))
    world.get("object").meters["found"] = 1.0
    hero.memes["pride"] += 1
    out.append("__found__")
    return out


RULES = [Rule("alarm", _r_alarm), Rule("correction", _r_correction), Rule("find", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_case(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["confusion"] += 1
    propagate(sim, narrate=False)
    return {
        "corrected": sim.get("hero").meters["understanding"] >= THRESHOLD,
        "found": sim.get("object").meters["found"] >= THRESHOLD,
    }


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role=params.helper_role))
    object_ent = world.add(Entity(id="object", kind="thing", type="thing", label="the missing red kite"))
    location = world.add(Entity(id="location", kind="thing", type="place", label=LOCATIONS[params.location].label))
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    world.add(Entity(id="suspect", kind="character", type=suspect.type, label=suspect.label))

    hero.memes["bravery"] = 3.0
    helper.memes["bravery"] = 3.0
    world.facts["location"] = location
    world.facts["clue"] = clue
    world.facts["suspect"] = suspect
    world.facts["object"] = object_ent

    world.say(f"{hero.id} was a small detective with a brave heart and a notebook full of marks.")
    world.say(f"At {location.label}, {hero.id} found a clue: {clue.phrase}.")
    world.say(f'"This must mean {clue.wrong_lead}!" {hero.id} said, and hurried off with a bright grin.')

    world.para()
    hero.meters["confusion"] += 1
    helper.memes["bravery"] += 1
    world.say(f"But {helper.id} frowned. " + f'"{clue.correction}," {helper.id} said. "That first clue was not the whole truth."')
    if helper.memes["bravery"] >= BRAVERY_MIN:
        world.say(f"{helper.id} was brave enough to speak up, even when the room got quiet.")
    pred = predict_case(world)
    world.facts["prediction"] = pred

    if pred["corrected"]:
        world.para()
        world.say(f"{hero.id} took a breath, wrote down the correction, and asked one more question.")
        world.say(f"That brave correction led them to {clue.evidence}, where the missing kite was hidden.")
        hero.meters["understanding"] += 1
        propagate(world, narrate=False)
        world.say(f"At the end, {hero.id} held up the kite and smiled beside {helper.id}.")
    else:
        world.para()
        world.say(f"{hero.id} kept the notebook closed and the case stayed unfinished.")

    world.facts.update(hero=hero, helper=helper, params=params)
    return world


LOCATIONS = {
    "library": Location(
        id="library",
        label="the library",
        kind="quiet room",
        details="rows of tall shelves and a desk lamp",
        tags={"book", "quiet"},
    ),
    "museum": Location(
        id="museum",
        label="the museum hall",
        kind="gallery",
        details="glass cases and a polished floor",
        tags={"glass", "echo"},
    ),
    "station": Location(
        id="station",
        label="the train station",
        kind="platform",
        details="a long bench and a clock that ticked loud",
        tags={"ticket", "clock"},
    ),
}

CLUES = {
    "blue_note": Clue(
        id="blue_note",
        label="blue note",
        phrase="a blue note that said 'look by the tall books'",
        wrong_lead="the tallest shelf",
        correction="the note meant the tall books near the reading desk",
        evidence="a hollow book with a pocket inside",
        tags={"book", "note"},
    ),
    "silver_key": Clue(
        id="silver_key",
        label="silver key",
        phrase="a silver key with a scratch across the handle",
        wrong_lead="the locked gate outside",
        correction="the key fit the small drawer in the front desk",
        evidence="a drawer with a secret map inside",
        tags={"key", "drawer"},
    ),
    "red_thread": Clue(
        id="red_thread",
        label="red thread",
        phrase="a red thread tied to a bench leg",
        wrong_lead="the far back door",
        correction="the thread pointed under the bench",
        evidence="the missing kite tucked safely under the seat",
        tags={"thread", "bench"},
    ),
}

SUSPECTS = {
    "librarian": Suspect(id="librarian", label="the librarian", type="woman", truthful=True, tags={"book"}),
    "porter": Suspect(id="porter", label="the porter", type="man", truthful=True, tags={"bag"}),
    "guard": Suspect(id="guard", label="the guard", type="man", truthful=True, tags={"key"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for clue in CLUES:
            for suspect in SUSPECTS:
                combos.append((loc, clue, suspect))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with bravery and correction.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.location is None or c[0] == args.location)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    loc, clue, suspect = rng.choice(sorted(combos))
    return StoryParams(
        location=loc,
        clue=clue,
        suspect=suspect,
        hero=args.name or rng.choice(["Nina", "Ada", "Pia", "Mara", "Ivy"]),
        helper=args.helper or rng.choice(["Milo", "Owen", "June", "Noah", "Theo"]),
        hero_gender=rng.choice(["girl", "boy"]),
        helper_gender=rng.choice(["girl", "boy"]),
        helper_role="friend",
    )


def generate(params: StoryParams) -> StorySample:
    if params.location not in LOCATIONS:
        raise StoryError("Unknown location.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"]
    return [
        f'Write a detective story for a young child that includes the word "correction" and a brave friend who speaks up.',
        f"Tell a detective story where {f['hero'].id} follows a clue, gets a correction, and finds the missing object.",
        f"Write a brave little mystery with a mistake, a correction, and a happy ending at {f['location'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, clue = f["hero"], f["helper"], f["clue"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a small detective who wanted to solve a mystery. {helper.id} helped by giving a correction when the first clue was wrong."),
        ("What mistake did the detective make?",
         f"{hero.id} thought {clue.wrong_lead} was the answer, but that was only the first idea. The correction showed that the clue meant something else."),
        ("How did bravery matter in the story?",
         f"{helper.id} was brave enough to speak up and correct the mistake. That bravery helped {hero.id} slow down, listen, and keep looking in the right place."),
    ]
    if f["prediction"]["corrected"]:
        qa.append((
            "How did the case end?",
            f"The case ended well because {hero.id} accepted the correction and followed it. Then they found the missing kite and finished the mystery together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"]
    loc = f["location"]
    out = []
    if "book" in clue.tags:
        out.append(("Why are books useful for clues?",
                    "Books can hide notes, pockets, and secret places, so a detective may find clues inside them. They are also full of words that can help explain a mystery."))
    if "drawer" in clue.tags:
        out.append(("What is a drawer?",
                    "A drawer is a box-like part of a desk or cabinet that slides in and out. People use it to store small things safely."))
    if "bench" in clue.tags:
        out.append(("What is a bench?",
                    "A bench is a long seat where people can sit down. It can also hide something underneath it if a clue points there."))
    out.append(("What is a correction?",
                "A correction is a new answer that fixes a mistake. It helps someone understand the truth more clearly."))
    out.append(("Why is bravery useful in a mystery?",
                "Bravery helps someone speak up, ask questions, and follow a clue even when they feel unsure. That can lead them to the real answer."))
    return out


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
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
confusion(hero) :- clue_wrong(hero).
brave_correction(helper) :- bravery(helper), helper_speaks(helper).
understanding(hero) :- brave_correction(_), confusion(hero).
found(object) :- understanding(hero).
outcome(solved) :- found(object).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for loc in LOCATIONS:
        lines.append(asp.fact("location", loc))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "book" in c.tags:
            lines.append(asp.fact("clue_wrong", "hero"))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("bravery", "helper"))
    lines.append(asp.fact("helper_speaks", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1.\n#show understanding/1."))
    asp_ok = bool(asp.atoms(model, "outcome"))
    sample = generate(StoryParams())
    py_ok = "missing kite" in sample.story and "correction" in sample.story
    if asp_ok and py_ok:
        print("OK: ASP and Python smoke tests passed.")
        return 0
    print("MISMATCH in verify.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show location/1.\n"))
    return sorted(set(asp.atoms(model, "location")))


def world_knowledge_tags(params: StoryParams) -> set[str]:
    return set(CLUES[params.clue].tags)


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return world_knowledge_qa_impl(world)


def world_knowledge_qa_impl(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue = f["clue"]
    qa = [
        ("What is a correction?",
         "A correction is a new answer that fixes a mistake. It helps someone understand the truth more clearly."),
        ("Why is bravery useful in a mystery?",
         "Bravery helps someone speak up, ask questions, and follow a clue even when they feel unsure. That can lead them to the real answer."),
    ]
    if "book" in clue.tags:
        qa.append(("Why are books useful for clues?",
                   "Books can hide notes, pockets, and secret places, so a detective may find clues inside them. They are also full of words that can help explain a mystery."))
    if "drawer" in clue.tags:
        qa.append(("What is a drawer?",
                   "A drawer is a box-like part of a desk or cabinet that slides in and out. People use it to store small things safely."))
    if "bench" in clue.tags:
        qa.append(("What is a bench?",
                   "A bench is a long seat where people can sit down. It can also hide something underneath it if a clue points there."))
    return qa


def generate_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a detective story for a young child that includes the word "correction" and a brave friend who speaks up.',
        f"Tell a detective story where {f['hero'].id} follows a clue, gets a correction, and finds the missing object.",
        f"Write a brave little mystery with a mistake, a correction, and a happy ending at {f['location'].label}.",
    ]


def valid_combos_checker() -> list[tuple[str, str, str]]:
    return valid_combos()


def generate_story_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
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
        print("\n".join(lines))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show outcome/1.\n#show understanding/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible locations:")
        for loc in LOCATIONS:
            print(f"  {loc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(location=l, clue=c, suspect=s, hero="Nina", helper="Milo")) for l, c, s in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

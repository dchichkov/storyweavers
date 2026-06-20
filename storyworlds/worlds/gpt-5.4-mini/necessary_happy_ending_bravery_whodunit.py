#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/necessary_happy_ending_bravery_whodunit.py
===========================================================================

A standalone storyworld for a tiny cozy whodunit about a necessary clue,
a brave child detective, and a happy ending.

Premise
-------
A child notices that something necessary has gone missing right before a small
family event. The child follows clues, asks careful questions, and solves the
mystery with bravery instead of panic. The missing thing is found in a surprising
place, and the ending proves that the household is safe, cheerful, and ready.

The domain is intentionally small and state-driven:
- typed entities with physical meters and emotional memes
- a few plausible mystery objects and hiding places
- forward-chained causal rules
- a reasonableness gate that refuses weak or impossible mysteries
- grounded QA from world state, not from rendered prose

This world is designed to read like a child-friendly whodunit with a complete arc:
setup, clue gathering, reveal, and a warm happy ending image.
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
BRAVE_MIN = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    place: str = ""
    hidden: bool = False
    searchable: bool = False
    necessary: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Mystery:
    id: str
    clue: str
    missing_phrase: str
    title: str
    necessary_word: str = "necessary"
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class HidingPlace:
    id: str
    phrase: str
    kind: str
    requires_courage: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["worry"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            e.memes["anxiety"] += 1
            out.append("__worry__")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["bravery"] < BRAVE_MIN:
            continue
        sig = ("brave", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["courage"] += 1
        out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("brave", "social", _r_brave)]


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


def mystery_at_risk(mystery: Mystery, place: HidingPlace) -> bool:
    return place.searchable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def reasonability_gate() -> list[tuple[str, str]]:
    out = []
    for mid in MYSTERIES:
        for pid in PLACES:
            if mystery_at_risk(MYSTERIES[mid], PLACES[pid]):
                out.append((mid, pid))
    return out


def find_clue(world: World, detective: Entity, mystery: Mystery, place: HidingPlace) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f'{detective.id} noticed a clue: {mystery.clue} near {place.phrase}. '
        f'That felt odd, because the thing that went missing was necessary.'
    )


def ask_helper(world: World, helper: Entity, detective: Entity) -> None:
    helper.memes["helpfulness"] += 1
    world.say(
        f'{helper.id} listened carefully and told {detective.id} to keep looking, '
        f'one clue at a time.'
    )


def search(world: World, detective: Entity, place: HidingPlace) -> None:
    detective.memes["bravery"] += 1
    world.say(
        f'{detective.id} took a brave breath and looked in {place.phrase}. '
        f'{detective.pronoun().capitalize()} was nervous, but kept going.'
    )


def reveal(world: World, detective: Entity, mystery: Mystery, place: HidingPlace) -> None:
    world.say(
        f'At last, {detective.id} found the missing {mystery.missing_phrase} in {place.phrase}. '
        f'It had been hidden there all along.'
    )
    if place.requires_courage:
        detective.memes["bravery"] += 1
    detective.memes["joy"] += 1


def solve(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{detective.id} showed {helper.id} the clue and solved the mystery. '
        f'{helper.id} smiled, proud of that brave thinking.'
    )


def ending(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"By bedtime, everything was calm again. The necessary {mystery.title} was back, "
        f"and {detective.id} sat happily beside {helper.id}, brave and smiling."
    )


def tell(mystery: Mystery, place: HidingPlace, detective_name: str = "Maya",
         detective_gender: str = "girl", helper_name: str = "Mom",
         helper_gender: str = "mother") -> World:
    world = World()
    det = world.add(Entity(
        id=detective_name, kind="character", type=detective_gender, role="detective",
        traits=["careful", "brave"], necessary=True
    ))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    item = world.add(Entity(id="item", type="thing", label=mystery.title, hidden=True, searchable=True, necessary=True))
    room = world.add(Entity(id="room", type="room", label="the room"))
    world.facts["mystery"] = mystery
    world.facts["place"] = place
    world.facts["detective"] = det
    world.facts["helper"] = helper
    world.facts["item"] = item
    world.facts["room"] = room

    det.memes["worry"] = 1
    det.memes["bravery"] = 4
    helper.memes["trust"] = 1

    world.say(
        f"One morning, {det.id} noticed something necessary was missing: {mystery.missing_phrase}. "
        f"{helper.id} looked around, puzzled, because it should have been easy to find."
    )
    world.say(
        f'{det.id} said, "I can solve this." {det.pronoun().capitalize()} tried to stay calm, '
        f'like a true detective.'
    )
    world.para()
    find_clue(world, det, mystery, place)
    ask_helper(world, helper, det)
    search(world, det, place)
    reveal(world, det, mystery, place)
    world.para()
    solve(world, det, helper, mystery)
    ending(world, det, helper, mystery)

    propagate(world, narrate=False)
    world.facts["resolved"] = True
    return world


MYSTERIES = {
    "bell": Mystery("bell", "a tiny note under the rug", "doorbell chime", "doorbell chime", tags={"home", "sound", "necessary"}),
    "keys": Mystery("keys", "a shiny tag by the coat rack", "front-door keys", "front-door keys", tags={"home", "keys", "necessary"}),
    "recipe": Mystery("recipe", "a flour smudge on the cookbook", "cake recipe card", "cake recipe card", tags={"kitchen", "recipe", "necessary"}),
}

PLACES = {
    "toy_box": HidingPlace("toy_box", "the toy box", "box"),
    "basket": HidingPlace("basket", "the laundry basket", "basket"),
    "piano_bench": HidingPlace("piano_bench", "under the piano bench", "bench", requires_courage=True),
}

RESPONSES = {
    "look_low": Response("look_low", 3, "looked low and slow, checking the floor first"),
    "ask": Response("ask", 3, "asked a helper to remember where it had gone"),
    "peek": Response("peek", 2, "peeked behind the bench with a brave grin"),
}

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Max", "Finn", "Leo"]


@dataclass
@dataclass
class StoryParams:
    mystery: str
    place: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    response: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


KNOWLEDGE = {
    "necessary": [("What does necessary mean?",
                   "Necessary means something is needed or important, so it should not be forgotten.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing something even when you feel nervous. It does not mean you are never scared.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues, asks careful questions, and tries to solve a mystery.")],
    "keys": [("What are keys for?",
              "Keys are used to open locks, like the front door or a box.")],
    "bell": [("What is a doorbell chime?",
             "A doorbell chime is the sound a doorbell makes when someone rings it.")],
    "recipe": [("What is a recipe card?",
                "A recipe card has the steps for making food, like a cake or cookies.")],
}
KNOWLEDGE_ORDER = ["necessary", "bravery", "detective", "keys", "bell", "recipe"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for mid, mystery in MYSTERIES.items():
        for pid, place in PLACES.items():
            if mystery_at_risk(mystery, place):
                combos.append((mid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a necessary thing goes missing, a brave child solves the mystery, and everything ends happily."
    )
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("necessary", mid))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.searchable:
            lines.append(asp.fact("searchable", pid))
        if place.requires_courage:
            lines.append(asp.fact("courage_place", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, P) :- mystery(M), place(P), searchable(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
brave_reveal(P) :- courage_place(P).
outcome(happy) :- valid(_, _), sensible(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    if set(asp_sensible()) == set(RESPONSES):
        print("OK: response sense parity.")
    else:
        rc = 1
        print("MISMATCH in response sense.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("Response is too weak for a happy ending whodunit.")
    combos = [c for c in valid_combos()
              if (args.mystery is None or c[0] == args.mystery)
              and (args.place is None or c[1] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery, place = rng.choice(sorted(combos))
    det_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    detective = args.detective or rng.choice(GIRL_NAMES if det_gender == "girl" else BOY_NAMES)
    helper = args.helper or ("Mom" if helper_gender == "mother" else "Dad")
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(mystery, place, detective, det_gender, helper, helper_gender, response)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m, p = f["mystery"], f["place"]
    return [
        f'Write a cozy whodunit for a 3-to-5-year-old where something necessary goes missing and the child follows clues to {p.phrase}.',
        f'Tell a brave little mystery story where {f["detective"].id} solves the disappearance of {m.missing_phrase} and ends happily.',
        f'Write a story that includes the word "necessary" and shows a child detective being brave, careful, and right in the end.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, helper, mystery, place = f["detective"], f["helper"], f["mystery"], f["place"]
    return [
        ("Who is the story about?",
         f"It is about {det.id}, a brave little detective, and {helper.id}, who helped keep the search calm."),
        ("What was missing?",
         f"The missing thing was {mystery.missing_phrase}. It was necessary, so everyone wanted it found quickly."),
        ("Where was it found?",
         f"It was found in {place.phrase}. The clue led {det.id} there one careful step at a time."),
        ("How did the story end?",
         f"It ended happily, with the necessary {mystery.title} back where it belonged and everyone smiling."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.hidden:
            bits.append("hidden")
        if e.necessary:
            bits.append("necessary")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("keys", "toy_box", "Maya", "girl", "Mom", "mother", "ask"),
    StoryParams("bell", "basket", "Noah", "boy", "Dad", "father", "look_low"),
    StoryParams("recipe", "piano_bench", "Lily", "girl", "Mom", "mother", "peek"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(MYSTERIES[params.mystery], PLACES[params.place],
                 params.detective, params.detective_gender,
                 params.helper, params.helper_gender)
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
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (mystery, place) combos:")
        for m, p in asp_valid_combos():
            print(f"  {m:10} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/welfare_bounty_ambidextrous_kindness_detective_story.py
=========================================================================================

A standalone storyworld for a tiny detective tale: a child detective solves a
missing welfare bounty case with kindness, careful noticing, and ambidextrous
help. The world is built around a small simulated case file, physical meters,
and emotional memes, so the story grows from state changes instead of a frozen
template.

The seed words are woven into the domain:
- welfare
- bounty
- ambidextrous

Style: Detective Story
Feature: Kindness
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class District:
    id: str
    place: str
    detail: str
    mood: str
    has_welfare: bool = False
    has_bounty: bool = False
    has_clue: bool = False
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
class CaseItem:
    id: str
    label: str
    phrase: str
    kind: str
    found_where: str
    keywords: set[str] = field(default_factory=set)
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Response:
    id: str
    sense: int
    method: str
    text: str
    qa_text: str
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
    district: str
    case_item: str
    response: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    kind_trait: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    if world.get("case").meters["missing"] < THRESHOLD:
        return out
    if ("worry", "civic") in world.fired:
        return out
    world.fired.add(("worry", "civic"))
    world.get("helper").memes["concern"] += 1
    world.get("detective").memes["drive"] += 1
    out.append("")
    return out


def _r_kindness(world: World) -> list[str]:
    if world.get("helper").memes["kindness"] < THRESHOLD:
        return []
    if ("kindness",) in world.fired:
        return []
    world.fired.add(("kindness",))
    world.get("detective").memes["hope"] += 1
    return []


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("kindness", _r_kindness)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combo(district: District, case_item: CaseItem, response: Response) -> bool:
    return district.has_welfare and district.has_bounty and district.has_clue and response.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for d in DISTRICTS:
        for c in CASE_ITEMS:
            for r in RESPONSES:
                if valid_combo(DISTRICTS[d], CASE_ITEMS[c], RESPONSES[r]):
                    out.append((d, c, r))
    return out


def reasonableness_gate(case_item: CaseItem) -> bool:
    return "welfare" in case_item.keywords or "bounty" in case_item.keywords


def tell(params: StoryParams) -> World:
    if params.district not in DISTRICTS:
        raise StoryError("Unknown district.")
    if params.case_item not in CASE_ITEMS:
        raise StoryError("Unknown case item.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    response = RESPONSES[params.response]
    if response.sense < 2:
        raise StoryError("The response is too flimsy for a detective story.")

    district = DISTRICTS[params.district]
    case_item = CASE_ITEMS[params.case_item]
    if not reasonableness_gate(case_item):
        raise StoryError("This case item does not fit the welfare bounty mystery.")

    world = World()
    d = world.add(Entity(id="detective", kind="character", type=params.detective_gender,
                         role="detective", traits=["observant", "ambidextrous"],
                         attrs={"name": params.detective_name, "kind_trait": params.kind_trait}))
    h = world.add(Entity(id="helper", kind="character", type=params.helper_gender,
                         role="helper", traits=["kind", params.kind_trait],
                         attrs={"name": params.helper_name}))
    c = world.add(Entity(id="case", kind="thing", type="case", label=case_item.label))
    c.meters["missing"] = 1.0
    d.memes["curiosity"] += 1
    h.memes["kindness"] += 1

    world.say(
        f"On a misty afternoon in {district.place}, {params.detective_name} was called to a small mystery. "
        f"The welfare desk had gone quiet, and the community's bounty was missing."
    )
    world.say(
        f"{params.detective_name} was an ambidextrous detective, able to jot notes with either hand while the other held a magnifier. "
        f"{params.helper_name} stayed close, because kindness helped the whole block feel brave."
    )

    world.para()
    world.say(
        f"The first clue was in {district.detail}. Someone had left a tiny mark near {case_item.found_where}, "
        f"as if the missing {case_item.label} had been carried away in a hurry."
    )
    world.say(
        f"{params.detective_name} leaned down, looked with both eyes, and asked gentle questions instead of sharp ones."
    )

    world.para()
    world.say(
        f"At last, the trail led to the old office by the corner shop. There, {params.helper_name} spotted the {case_item.phrase} tucked safely where nobody would trip on it."
    )
    if response.method == "kindly_return":
        world.say(
            f"{params.detective_name} chose a kind fix: {response.text}. Nobody was scolded, and the truth came out softly."
        )
        case_item_obj = case_item
        world.get("case").meters["missing"] = 0.0
        world.get("detective").memes["joy"] += 1
        world.get("helper").memes["relief"] += 1
        world.para()
        world.say(
            f"By sunset, the welfare desk was open again, the bounty was back in place, and the whole street breathed easier."
        )
        world.say(
            f"The detective tucked the notes into {d.pronoun('possessive')} pocket, one hand and then the other, and smiled at a job done with kindness."
        )
    elif response.method == "share_notice":
        world.say(
            f"{params.detective_name} did not rush. {response.text}. The warning reached the right people, and the case was settled without a scene."
        )
        world.get("case").meters["missing"] = 0.0
        world.get("helper").memes["relief"] += 1
        world.para()
        world.say(
            f"The bounty returned to the welfare desk before supper, and the detective's careful kindness became the best clue of all."
        )
    else:
        world.say(
            f"{params.detective_name} used {response.method}, and {response.text}."
        )
        world.get("case").meters["missing"] = 0.0
        world.para()
        world.say(
            f"The mystery ended with the missing bounty back where it belonged, and the street kept its warm, neighborly feel."
        )

    propagate(world)
    world.facts.update(
        detective=d,
        helper=h,
        district=district,
        case_item=case_item,
        response=response,
        outcome="found",
    )
    return world


DISTRICTS = {
    "harbor": District(
        id="harbor",
        place="the harbor market",
        detail="the fish stall behind the blue awning",
        mood="foggy",
        has_welfare=True,
        has_bounty=True,
        has_clue=True,
    ),
    "library": District(
        id="library",
        place="the little library",
        detail="the return shelf by the lamp",
        mood="quiet",
        has_welfare=True,
        has_bounty=True,
        has_clue=True,
    ),
    "station": District(
        id="station",
        place="the tram station",
        detail="the bench under the timetable board",
        mood="windy",
        has_welfare=True,
        has_bounty=True,
        has_clue=True,
    ),
}

CASE_ITEMS = {
    "envelope": CaseItem(
        id="envelope",
        label="envelope",
        phrase="the welfare envelope",
        kind="paper",
        found_where="the chalk desk",
        keywords={"welfare", "bounty"},
    ),
    "badge": CaseItem(
        id="badge",
        label="badge",
        phrase="the bounty badge",
        kind="metal",
        found_where="the coat hook",
        keywords={"bounty"},
    ),
}

RESPONSES = {
    "kindly_return": Response(
        id="kindly_return",
        sense=3,
        method="kindly_return",
        text="she returned the welfare envelope with a polite thank-you and a small smile",
        qa_text="returned the welfare envelope kindly",
        tags={"kindness"},
    ),
    "share_notice": Response(
        id="share_notice",
        sense=3,
        method="share_notice",
        text="he shared the news with the welfare office and let the helper carry the message",
        qa_text="shared the news with the welfare office",
        tags={"kindness"},
    ),
    "gentle_note": Response(
        id="gentle_note",
        sense=2,
        method="gentle_note",
        text="they left a gentle note so the right person could follow the trail without blame",
        qa_text="left a gentle note",
        tags={"kindness"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Iris", "Lena", "Ada"]
BOY_NAMES = ["Noel", "Theo", "Ezra", "Leo", "Milo"]
KIND_TRAITS = ["kind", "gentle", "patient", "helpful", "warm"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about welfare, bounty, ambidextrous kindness.")
    ap.add_argument("--district", choices=DISTRICTS)
    ap.add_argument("--case-item", choices=CASE_ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--kind-trait", choices=KIND_TRAITS)
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
    districts = list(DISTRICTS)
    case_items = list(CASE_ITEMS)
    responses = list(RESPONSES)
    d = args.district or rng.choice(districts)
    c = args.case_item or rng.choice(case_items)
    r = args.response or rng.choice(responses)
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    kind_trait = args.kind_trait or rng.choice(KIND_TRAITS)
    if not valid_combo(DISTRICTS[d], CASE_ITEMS[c], RESPONSES[r]):
        raise StoryError("This combination does not make a sensible detective mystery.")
    return StoryParams(
        district=d,
        case_item=c,
        response=r,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        kind_trait=kind_trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story for a young child that includes the words welfare, bounty, and ambidextrous.",
        f"Tell a gentle mystery where {f['detective'].attrs['name']} finds a missing welfare bounty with kindness.",
        f"Write a story set in {f['district'].place} where a child detective uses both hands and a kind helper to solve a problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    district = f["district"]
    case_item = f["case_item"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{d.attrs['name']} solved it, helped by {h.attrs['name']}. {d.attrs['name']} was the ambidextrous detective, so notes and clues could be handled with either hand."
        ),
        QAItem(
            question="Why was the helper important?",
            answer=f"{h.attrs['name']} kept the mood kind and calm, which helped people answer questions without feeling blamed. That kindness made the welfare mystery easier to untangle."
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The welfare {case_item.label} and the bounty tied to it were missing from {district.place}. The detective followed a quiet trail and found it safely."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ambidextrous mean?",
            answer="Ambidextrous means a person can use both the left hand and the right hand well. It is helpful when writing, drawing, or handling clues."
        ),
        QAItem(
            question="What is welfare?",
            answer="Welfare means help and support that keeps people safe, fed, and cared for. A welfare office or desk helps a community with that kind of support."
        ),
        QAItem(
            question="What is a bounty?",
            answer="A bounty is a reward or prize. In a detective story, it can be the important item that everyone is trying to find."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating people gently and helping them feel safe. A kind detective listens carefully and tries to help instead of scare people."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    if params.district not in DISTRICTS or params.case_item not in CASE_ITEMS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
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


ASP_RULES = r"""
missing_case(C) :- case(C).
kindness_present :- helper_kind.
found(C) :- missing_case(C), kindness_present.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for d in DISTRICTS:
        lines.append(asp.fact("district", d))
    for c in CASE_ITEMS:
        lines.append(asp.fact("case", c))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show found/1."))
    return sorted(set(asp.atoms(model, "found")))


def asp_verify() -> int:
    rc = 0
    if not valid_combos():
        print("MISMATCH: python valid_combos() returned no combos.")
        rc = 1
    # smoke test ordinary generation
    try:
        sample = generate(StoryParams(
            district="harbor",
            case_item="envelope",
            response="kindly_return",
            detective_name="Mina",
            detective_gender="girl",
            helper_name="Noel",
            helper_gender="boy",
            kind_trait="kind",
        ))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    try:
        _ = sample.to_json()
    except Exception as e:
        print(f"JSON SMOKE TEST FAILED: {e}")
        rc = 1
    print("OK: smoke test passed.")
    return rc


CURATED = [
    StoryParams(
        district="harbor",
        case_item="envelope",
        response="kindly_return",
        detective_name="Mina",
        detective_gender="girl",
        helper_name="Noel",
        helper_gender="boy",
        kind_trait="gentle",
    ),
    StoryParams(
        district="library",
        case_item="badge",
        response="share_notice",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="Iris",
        helper_gender="girl",
        kind_trait="patient",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show found/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

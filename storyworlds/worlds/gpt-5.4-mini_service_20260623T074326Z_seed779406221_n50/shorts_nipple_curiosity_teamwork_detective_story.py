#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/shorts_nipple_curiosity_teamwork_detective_story.py
===============================================================================================================

A standalone storyworld in a small detective-story domain for child-facing
mysteries. The seed words are "shorts" and "nipple"; the world centers on a
curious team solving a tiny clue trail in a bedroom, laundry area, and nursery.

Premise:
- A child notices a puzzling missing item.
- Curiosity pushes the pair to inspect clues.
- Teamwork helps them connect the clue to the right place.
- The ending proves what changed: the found item is returned and the mystery is solved.

This file follows the Storyweavers contract:
- stdlib script, one file, self-contained
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared result containers importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    type: str = "thing"
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    location: str
    hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    rooms: tuple[str, str, str]
    mood: str
    search_line: str
    ending_line: str


@dataclass
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    story_bits: list[str] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.story_bits.append(text)

    def render(self) -> str:
        return " ".join(self.story_bits)

    def copy(self) -> "World":
        return World(
            entities=copy.deepcopy(self.entities),
            story_bits=[],
            fired=set(self.fired),
            facts=copy.deepcopy(self.facts),
        )


@dataclass
class StoryParams:
    setting: str
    missing: str
    clue: str
    response: str
    detective: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "apartment": Setting(
        id="apartment",
        place="a small apartment",
        rooms=("hallway", "laundry room", "nursery"),
        mood="quiet and tidy",
        search_line="The hallway, the laundry room, and the nursery made a tiny trail of clues.",
        ending_line="The apartment felt calm again, like a puzzle with the last piece back in place.",
    ),
    "house": Setting(
        id="house",
        place="a cozy house",
        rooms=("mudroom", "bathroom", "playroom"),
        mood="sunny and busy",
        search_line="The mudroom, the bathroom, and the playroom each held a clue to follow.",
        ending_line="The house seemed brighter once the mystery was solved.",
    ),
    "daycare": Setting(
        id="daycare",
        place="a bright daycare",
        rooms=("cloakroom", "wash area", "nap room"),
        mood="lively and neat",
        search_line="The cloakroom, the wash area, and the nap room all had to be checked with care.",
        ending_line="The daycare buzzed happily once the lost thing was found.",
    ),
}

MISSING = {
    "shorts": Clue(
        id="shorts",
        label="shorts",
        phrase="a pair of shorts",
        location="by the laundry basket",
        hint="The clue was a wrinkled tag stuck to a chair leg.",
        tags={"shorts"},
    ),
    "nipple": Clue(
        id="nipple",
        label="bottle nipple",
        phrase="a baby bottle nipple",
        location="in the nursery drawer",
        hint="The clue was a tiny cap-shaped piece near a bottle brush.",
        tags={"nipple"},
    ),
}

RESPONSES = {
    "check": Response(
        id="check",
        sense=3,
        text="checked the rooms one by one and compared the clues carefully",
        qa_text="checked the rooms one by one",
        tags={"curiosity"},
    ),
    "label": Response(
        id="label",
        sense=3,
        text="read the labels on the baskets and matched each clue to the right drawer",
        qa_text="read the labels and matched each clue to the right drawer",
        tags={"teamwork"},
    ),
    "ask": Response(
        id="ask",
        sense=2,
        text="asked the grown-up what the clue belonged to, then looked again together",
        qa_text="asked the grown-up for help and looked again together",
        tags={"teamwork"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        text="shouted guesses from the doorway without really looking",
        qa_text="shouted guesses",
        tags={"noise"},
    ),
}

DETECTIVES = ["Maya", "Leo", "Nina", "Owen", "Iris", "Ben", "Ada", "Theo"]
HELPERS = ["Sami", "Ruth", "Milo", "June", "Zara", "Hana"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world about clues, curiosity, and teamwork.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--missing", choices=sorted(MISSING))
    ap.add_argument("--clue", choices=sorted(MISSING))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--helper", choices=HELPERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        for t in sorted(r.tags):
            lines.append(asp.fact("rtag", rid, t))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, M, C) :- setting(S), missing(M), missing(C).
solve(Curiosity, Teamwork) :- sensible(Curiosity), sensible(Teamwork).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = sorted(rid for rid, r in RESPONSES.items() if r.sense >= SENSE_MIN)
    cl = asp_sensible()
    if py != cl:
        rc = 1
        print(f"MISMATCH: python={py} clingo={cl}")
    else:
        print(f"OK: sensible responses match {py}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    missing = args.missing or rng.choice(sorted(MISSING))
    if args.clue and args.clue != missing:
        raise StoryError("The chosen clue must match the missing item.")
    clue = args.clue or missing
    if missing not in MISSING:
        raise StoryError("Unknown missing item.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for a detective story.")
    response = args.response or rng.choice([r for r, o in RESPONSES.items() if o.sense >= SENSE_MIN])
    setting = args.setting or rng.choice(sorted(SETTINGS))
    detective = args.detective or rng.choice(DETECTIVES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != detective])
    return StoryParams(setting=setting, missing=missing, clue=clue, response=response, detective=detective, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly detective story where {f['detective']} and {f['helper']} solve the mystery of the missing {f['missing']}.",
        f"Tell a story in which curiosity and teamwork help the kids follow clues through the {f['setting'].place}.",
        f"Make the ending clear: the lost {f['missing']} is found, and the pair learns to look carefully instead of guessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {f['detective']} and {f['helper']} try to solve?",
            answer=f"They tried to solve the mystery of the missing {f['missing']} in the {f['setting'].place}.",
        ),
        QAItem(
            question="What two features helped them most?",
            answer="Curiosity helped them keep looking, and teamwork helped them compare clues and work together.",
        ),
        QAItem(
            question="What clue did they notice first?",
            answer=f"They noticed {f['clue'].hint.lower()} That clue pointed them toward {f['clue'].location}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The missing {f['missing']} was found and returned, so the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does curiosity do in a detective story?",
            answer="Curiosity makes a detective keep asking questions, noticing small clues, and looking until the puzzle makes sense.",
        ),
        QAItem(
            question="What does teamwork do?",
            answer="Teamwork means people help each other, share clues, and solve the problem together.",
        ),
        QAItem(
            question=f"Why might a child look in the nursery when a {f['missing']} is missing?",
            answer=f"A child might look there because the clue could belong near baby things, like a {f['missing']}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("\n== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} role={e.role} attrs={e.attrs} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    missing = MISSING[params.missing]
    clue = MISSING[params.clue]
    response = RESPONSES[params.response]
    w = World()
    d = w.add(Entity(id=params.detective, kind="character", role="detective", meters={}, memes={"curiosity": 1.0, "confidence": 0.5}))
    h = w.add(Entity(id=params.helper, kind="character", role="helper", meters={}, memes={"teamwork": 1.0, "care": 0.5}))
    w.add(Entity(id="room", kind="place", label=setting.place))
    w.facts.update(setting=setting, missing=missing, clue=clue, response=response, detective=d.id, helper=h.id)

    d.memes["curiosity"] += 1
    h.memes["teamwork"] += 1
    w.say(f"In {setting.place}, {d.id} noticed that something was missing: {missing.phrase}.")
    w.say(setting.search_line)
    w.say(f'{d.id} said, "This feels like a case," and {h.id} said, "Then let us check every clue together."')
    if clue.id == "shorts":
        w.say("On a chair leg, they found a wrinkled tag that said shorts.")
    else:
        w.say("Near the bottle basket, they found a tiny cap-shaped clue: nipple.")
    w.say(f"{d.id} used {response.text}.")
    if response.id == "shout":
        w.say("That only made the puzzle noisier, so the kids stopped and looked more carefully.")
    if missing.id == clue.id:
        w.say(f"They followed the clue to {clue.location} and found the missing {missing.label}.")
    else:
        w.say(f"They traced the clue to {missing.location} and found the missing {missing.label}.")
    w.say(f"{h.id} smiled, because teamwork had helped the case make sense.")
    w.say(setting.ending_line)

    w.facts["outcome"] = "solved"
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


CURATED = [
    StoryParams("apartment", "shorts", "shorts", "check", "Maya", "Sami"),
    StoryParams("house", "nipple", "nipple", "label", "Leo", "Ruth"),
    StoryParams("daycare", "shorts", "shorts", "ask", "Nina", "Milo"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_many(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    return [resolve_params(args, random.Random(rng.randint(0, 2**31 - 1))) for _ in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(args.n):
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py
========================================================================

A standalone story world for a tiny cautionary detective tale.

Premise
-------
Two child detectives are playing at solving a mystery. They hear a duet from
another room and notice a slight clue. The tempting part is to follow the clue
without asking a grown-up. The cautionary turn is that they stop, check the
evidence carefully, and call in help before anything goes wrong.

This world keeps the prose concrete and state-driven:
- physical meters track things like noise, worry, and mess
- emotional memes track curiosity, caution, relief, and pride
- the story changes depending on whether the clue is just an innocent lead or
  something that could become trouble if handled badly

The seed words "duet" and "slight" are woven into the story, and the style stays
close to a child-friendly detective story with a gentle warning embedded in it.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/duet_slight_cautionary_detective_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Clue:
    id: str
    label: str
    slight: bool = False
    risky: bool = False
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
class Setting:
    id: str
    place: str
    detective_nest: str
    normal_sound: str

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
    power: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    response: str
    detective1: str
    detective1_gender: str
    detective2: str
    detective2_gender: str
    adult: str
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


SETTINGS = {
    "library": Setting("library", "the little library", "a cozy detective nest", "soft page rustles"),
    "music_room": Setting("music_room", "the music room", "a window-side detective nest", "a bright piano tune"),
    "hallway": Setting("hallway", "the hallway", "a shoe-rack detective nest", "small footsteps"),
}

CLUES = {
    "slight_note": Clue("slight_note", "a slight note", slight=True, risky=False, tags={"note"}),
    "slight_scrape": Clue("slight_scrape", "a slight scrape on the floor", slight=True, risky=False, tags={"scratch"}),
    "open_door": Clue("open_door", "an open door", slight=False, risky=True, tags={"door"}),
    "missing_stamp": Clue("missing_stamp", "a missing stamp pad", slight=False, risky=True, tags={"stamp"}),
}

RESPONSES = {
    "ask": Response("ask", 3, 3, "asked a grown-up and checked the clue together", "asked too late and the clue got mixed up", "asked a grown-up and checked the clue together", {"help"}),
    "wait": Response("wait", 2, 2, "waited by the desk until a grown-up came", "waited, but the clue was already gone", "waited by the desk until a grown-up came", {"help"}),
    "touch": Response("touch", 1, 1, "picked it up right away", "picked it up, but that only made the mystery messier", "picked it up right away", {"risk"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Max", "Noah", "Theo", "Ben", "Eli", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            if clue.slight or clue.risky:
                combos.append((sid, cid))
    return combos


def clue_is_reasonable(clue: Clue) -> bool:
    return clue.slight or clue.risky


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_safe_story(clue: Clue, response: Response) -> bool:
    return clue.slight and response.sense >= SENSE_MIN


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.slight:
            lines.append(asp.fact("slight", cid))
        if clue.risky:
            lines.append(asp.fact("risky", cid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C) :- setting(S), clue(C), slight(C).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
safe_story(S, C, R) :- valid(S, C), sensible(R), response(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) != set(asp_valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if {r.id for r in sensible_responses()} != set(asp_sensible()):
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for a sensible detective story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    g1 = rng.choice(["girl", "boy"])
    g2 = "boy" if g1 == "girl" else "girl"
    d1 = _pick_name(rng, g1)
    d2 = _pick_name(rng, g2)
    while d2 == d1:
        d2 = _pick_name(rng, g2)
    adult = rng.choice(["mother", "father"])
    return StoryParams(setting, clue, response, d1, g1, d2, g2, adult)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    response = RESPONSES[params.response]
    a = world.add(Entity(params.detective1, kind="character", type=params.detective1_gender, role="detective"))
    b = world.add(Entity(params.detective2, kind="character", type=params.detective2_gender, role="detective"))
    adult = world.add(Entity("Adult", kind="character", type=params.adult, role="adult", label="the grown-up"))

    a.memes["curiosity"] = 2
    b.memes["caution"] = 1 if clue.slight else 0.5

    world.say(f"{a.id} and {b.id} were two little detectives in {setting.detective_nest}.")
    world.say(f"They listened for clues, and that day they heard a duet from {setting.place}.")
    world.say(f"Near the floor, they noticed {clue.label}.")
    world.para()
    world.say(f'"That might be important," said {a.id}. "{a.id} wanted to follow it at once."')
    world.say(f'{b.id} tilted {b.id if False else "their"} head. "It is only a slight clue," {b.id} said. "Let us be careful."')
    if clue.risky:
        a.meters["worry"] += 1
        world.say("The clue led toward a place where children should not poke around alone.")
    else:
        world.say("The clue looked small, but small clues can still matter in a mystery.")

    world.para()
    if is_safe_story(clue, response):
        a.memes["trust"] += 1
        b.memes["relief"] += 1
        world.say(f"They chose the careful way: {response.text}.")
        world.say(f"{adult.label_word.capitalize()} found the answer quickly and smiled at their good thinking.")
        world.say("The duet kept playing softly, and the two detectives closed the case without making a mess.")
        outcome = "safe"
    else:
        a.meters["worry"] += 1
        world.say(f"{a.id} did not wait, and {response.text}.")
        world.say(f"{adult.label_word.capitalize()} had to step in because the clue had become a small problem.")
        world.say("In the end they learned that a detective should look first, touch later, and ask for help early.")
        outcome = "messy"

    world.facts.update(
        detective1=a, detective2=b, adult=adult, setting=setting, clue=clue,
        response=response, outcome=outcome
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "duet" and a slight clue in {f["setting"].place}.',
        f"Tell a cautionary mystery where {f['detective1'].id} and {f['detective2'].id} hear a duet and learn to be careful before touching clues.",
        f'Write a short detective story for a 3-to-5-year-old that uses the word "slight" and ends with a gentle warning about asking a grown-up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d1, d2, clue, resp = f["detective1"], f["detective2"], f["clue"], f["response"]
    qa = [
        QAItem(question="Who were the story about?",
               answer=f"The story was about {d1.id} and {d2.id}, two little detectives who liked solving mysteries together."),
        QAItem(question="What did they hear?",
               answer="They heard a duet. That sound gave them a reason to look around and notice a clue."),
        QAItem(question=f"What did {d1.id} notice?",
               answer=f"{d1.id} noticed {clue.label}, which was a slight clue. It seemed small, but it was still worth checking carefully."),
    ]
    if f["outcome"] == "safe":
        qa.append(QAItem(
            question="How did they handle the mystery?",
            answer=f"They chose the careful response and asked a grown-up before touching anything. That kept the mystery neat and helped them solve it safely."
        ))
    else:
        qa.append(QAItem(
            question="What lesson did they learn?",
            answer="They learned to look first, touch later, and ask for help early. A detective can be brave and still be careful."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a duet?",
               answer="A duet is a performance with two voices or two instruments playing together."),
        QAItem(question="What does slight mean?",
               answer="Slight means small or not very big."),
        QAItem(question="What should you do before touching something important you found?",
               answer="You should ask a grown-up first, because clues and tiny problems can become bigger if you grab them too quickly."),
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "slight_note", "ask", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("music_room", "slight_scrape", "wait", "Eli", "boy", "Ava", "girl", "father"),
    StoryParams("hallway", "open_door", "touch", "Lily", "girl", "Theo", "boy", "mother"),
    StoryParams("library", "missing_stamp", "ask", "Max", "boy", "Nora", "girl", "father"),
]


def explain_rejection(clue: Clue, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return f"(No story: response '{response.id}' is too weak for a cautious mystery.)"
    return "(No story: that combination does not make a workable detective tale.)"


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    resp = RESPONSES[params.response]
    return "safe" if is_safe_story(clue, resp) else "messy"


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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, c in asp_valid_combos():
            print(f"  {s:12} {c}")
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
        header = f"### {sample.params.detective1} & {sample.params.detective2}: {sample.params.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

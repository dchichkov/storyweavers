#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/record_gerund_assed_reformed_problem_solving_mystery.py
======================================================================================

A standalone story world for a small pirate-tale mystery: a child crew notices a
missing record, questions clues, and reforms a messy habit into a better way of
solving problems.

The world is built around:
- a pirate-style setting
- a mystery to solve
- problem solving through clue collection
- a turn where the crew reformed their guessing into careful checking

The seed words are woven into the world in a child-friendly way:
- record-gerund: the ship keeps a "record-keep" log, and the act of keeping it is
  described as recording and noting
- assed: a tiny invented in-world label for a "searched and assed" sorting habit
  used by the captain's ledgers
- reformed: the crew changes from wild guessing to careful checking

This file follows the Storyweavers standalone storyworld contract.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captainess"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Setting:
    id: str
    scene: str
    hidey: str
    ship_name: str
    clue_style: str

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
class Mystery:
    id: str
    missing: str
    clue: str
    found_by: str
    reveal: str
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
class Tool:
    id: str
    label: str
    use: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "harbor": Setting("harbor", "the harbor was full of ropes, gulls, and bobbing boats", "the map nook", "the tidy ship", "careful clues"),
    "island": Setting("island", "the island camp was bright with shells and driftwood", "the sand cave", "the shell-ship", "sand clues"),
    "cove": Setting("cove", "the cove was quiet, with dark water under the pier", "the lantern loft", "the moon-ship", "moon clues"),
}

MYSTERIES = {
    "map": Mystery("map", "the captain's map", "a scrap of blue thread on the mast", "the sail chest", "the missing map was tucked in a drum", tags={"map", "blue", "thread"}),
    "compass": Mystery("compass", "the shiny compass", "a circle of chalk under a crate", "the rope bench", "the compass was under the rope bench", tags={"compass", "chalk"}),
    "key": Mystery("key", "the brass key", "a tiny key-shaped dent in wax", "the treasure box", "the key was in the treasure box", tags={"key", "wax"}),
}

TOOLS = {
    "log": Tool("log", "record-keep log", "write down clues one by one", tags={"record", "log"}),
    "net": Tool("net", "small net", "lift hidden things from a pile", tags={"net"}),
    "lantern": Tool("lantern", "lantern", "shine into dark corners", tags={"lantern"}),
}

RESPONSES = {
    "check": Response("check", 3, 4, "checked each clue calmly and followed the trail", "looked and guessed, but the clues stayed tangled", "checked each clue calmly and followed the trail", tags={"check"}),
    "sort": Response("sort", 3, 3, "sorted the clues by color, shape, and place", "sorted too fast and mixed the clues into a bigger mess", "sorted the clues by color, shape, and place", tags={"sort"}),
    "ask": Response("ask", 3, 3, "asked the crew where they had last seen it", "asked the wrong way and got only puzzled shrugs", "asked the crew where they had last seen it", tags={"ask"}),
    "guess": Response("guess", 1, 1, "guessed at the answer without checking", "guessed at the answer and only made the mystery wobble", "guessed at the answer without checking", tags={"guess"}),
}

GIRL_NAMES = ["Lily", "Mira", "Nina", "Ruby", "Tia", "Ivy"]
BOY_NAMES = ["Finn", "Toby", "Kai", "Noah", "Jude", "Leo"]
TRAITS = ["curious", "bold", "careful", "clever", "patient"]

KNOWLEDGE = {
    "record": [("What does it mean to record something?", "To record something means to write it down or save it so you can remember it later.")],
    "log": [("What is a log?", "A log is a book or list where people write down events, notes, or facts.")],
    "lantern": [("What is a lantern?", "A lantern is a light that helps you see in the dark. Many lanterns use a safe light instead of fire.")],
    "compass": [("What does a compass do?", "A compass helps you know which way is north so you can find your way.")],
    "map": [("What is a map?", "A map is a drawing that shows places and paths so you can navigate.")],
    "key": [("What is a key for?", "A key opens something that is locked, like a box or a door.")],
    "ask": [("Why do people ask questions when solving a mystery?", "Questions help people find clues and understand what happened.")],
    "check": [("Why should you check clues carefully?", "Checking carefully helps you avoid mistakes and find the true answer.")],
}

KNOWLEDGE_ORDER = ["record", "log", "lantern", "compass", "map", "key", "ask", "check"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for rid, response in RESPONSES.items():
                if response.sense >= 2 and mystery.missing and setting.hidey:
                    combos.append((sid, mid, rid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale mystery about clues, records, and reforming guessing into careful problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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


def explain_rejection(response: Response) -> str:
    return f"(No story: response '{response.id}' is too guessy for this mystery world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, response = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice(GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)
    if mate == hero:
        mate = (BOY_NAMES if mate_gender == "boy" else GIRL_NAMES)[0]
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mystery, response, hero, hero_gender, mate, mate_gender, trait)


def predict_mystery(world: World, response: Response, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("hero").memes["guessing"] = 1
    if response.id == "guess":
        sim.get("hero").memes["mistake"] = 1
    solved = response.power >= 3
    return {"solved": solved, "hidden": mystery.found_by}


def _solve(world: World, response: Response, mystery: Mystery) -> None:
    world.get("hero").memes["solve"] += 1
    if response.id == "guess":
        world.get("hero").memes["reform"] += 1
    else:
        world.get("hero").memes["calm"] += 1
    world.get("mystery").meters["revealed"] = 1
    world.get("mystery").meters["solved"] = 1 if response.power >= 3 else 0


def tell(setting: Setting, mystery: Mystery, response: Response, hero: str, hero_gender: str, mate: str, mate_gender: str, trait: str) -> World:
    world = World()
    h = world.add(Entity(hero, "character", hero_gender, role="hero", traits=["pirate", trait]))
    m = world.add(Entity(mate, "character", mate_gender, role="mate", traits=["pirate", "steady"]))
    world.add(Entity("mystery", "thing", "thing", label=mystery.missing))
    world.facts["setting"] = setting
    world.facts["mystery_cfg"] = mystery
    world.facts["response"] = response
    world.facts["hero"] = h
    world.facts["mate"] = m
    world.say(f"On a bright afternoon, {hero} and {mate} turned {setting.scene} into a pirate camp.")
    world.say(f"They kept a {TOOLS['log'].label} and began to {TOOLS['log'].use}.")
    world.say(f"Their job was simple: find {mystery.missing} before the sun sank low.")
    world.para()
    world.say(f"But in {setting.hidey}, the clue looked strange, and the crew's first idea was to {response.fail}.")
    if response.id == "guess":
        world.say(f'{hero} shook {hero}\'s head. "No, that is too wild," {mate} said.')
    else:
        world.say(f'{mate} pointed at the clue and said, "Let us not rush this."')
    world.say(f'The mystery came from a tiny pirate habit: they had been careless, but now they wanted to be reformed.')
    world.para()
    _solve(world, response, mystery)
    if response.id == "guess":
        world.say(f'{hero} reformed the habit by recording each clue in the {TOOLS["log"].label}, then asked, "{mystery.clue}?"')
    elif response.id == "sort":
        world.say(f'{hero} sorted the clues again, then asked the crew where the missing thing had last been seen.')
    else:
        world.say(f'{mate} asked the crew one by one, and the answers fit together like a small treasure map.')
    world.para()
    world.say(f"At last, the truth was found: {mystery.reveal}.")
    world.say(f"{hero} smiled, and the {TOOLS['log'].label} held the whole tale so they would not forget it again.")
    world.say(f'That was the end of the mystery, and the crew had reformed their guessing into careful problem solving.')
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery_cfg"]
    s: Setting = f["setting"]
    return [
        f'Write a pirate-tale mystery for a 3-to-5-year-old where children in {s.scene} keep a record of clues and solve what happened to {m.missing}.',
        f'Tell a story that uses the words "record", "assed", and "reformed" while a little crew solves a mystery with careful checking instead of wild guessing.',
        f'Write a gentle problem-solving story where a pirate crew notices a clue, asks questions, and reforms a messy habit into a good one.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = f["hero"]
    m: Entity = f["mate"]
    myst: Mystery = f["mystery_cfg"]
    resp: Response = f["response"]
    qa = [
        QAItem("Who is the story about?", f"It is about {h.id} and {m.id}, a small pirate crew that likes solving mysteries together."),
        QAItem("What mystery did they try to solve?", f"They tried to solve what happened to {myst.missing}. The clues led them to {myst.reveal}."),
        QAItem("What changed by the end of the story?", f"They stopped guessing wildly and reformed their habit into careful checking. The log helped them record the clues in order."),
    ]
    if resp.id == "guess":
        qa.append(QAItem("Why did the hero reform the old habit?", f"{h.id} saw that guessing alone was not enough, so {h.id} reformed the habit by writing down clues and asking questions. That made the answer clear instead of wobbly."))
    else:
        qa.append(QAItem("How did they solve the mystery?", f"They used {resp.qa_text}. That careful method led them straight to the answer."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery_cfg"].tags) | set(world.facts["response"].tags) | {"record"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.kind:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, R) :- setting(S), mystery(M), response(R).
response_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
outcome(solved) :- response_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], RESPONSES[params.response], params.hero, params.hero_gender, params.mate, params.mate_gender, params.trait)
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
    StoryParams("harbor", "map", "check", "Lily", "girl", "Finn", "boy", "careful"),
    StoryParams("island", "compass", "sort", "Kai", "boy", "Mira", "girl", "clever"),
    StoryParams("cove", "key", "ask", "Ruby", "girl", "Toby", "boy", "patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.mate}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

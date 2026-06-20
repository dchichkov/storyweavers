#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pray_masquerade_mystery_to_solve_bedtime_story.py
=================================================================================

A standalone storyworld for a tiny bedtime mystery: a child, a masquerade,
a missing bedtime item, a calm prayer, a clue chase, and a gentle reveal.

Seed words and cues:
- pray
- masquerade
- Mystery to Solve
- Bedtime Story

This world keeps the simulation small and classical:
- one child wants to enjoy a masquerade before bed
- something important goes missing
- a parent and child search by clue rather than by plot summary
- a prayer is part of the calm, hopeful turn
- the ending proves what changed in the world state

It supports the shared Storyweavers CLI contract, JSON, trace, QA, ASP twin,
and verification.
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
class Masquerade:
    id: str
    setting: str
    costume: str
    lights: str
    music: str
    bedtime_word: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    where_hidden: str
    clue: str
    found_in: str
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
    method: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    masquerade: str
    missing: str
    response: str
    child_name: str
    child_gender: str
    parent_type: str
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


MASQUERADES = {
    "moon": Masquerade(
        "moon", "a moonlit bedroom masquerade", "a silver paper crown",
        "a tiny lamp", "soft music", "bedtime", {"masquerade", "bedtime", "moon"}
    ),
    "garden": Masquerade(
        "garden", "a garden masquerade by lantern light", "a leaf-green cape",
        "a lantern", "humming crickets", "bedtime", {"masquerade", "bedtime", "garden"}
    ),
    "castle": Masquerade(
        "castle", "a pretend castle masquerade", "a velvet mask",
        "a night-light", "gentle music", "bedtime", {"masquerade", "bedtime", "castle"}
    ),
}

MISSING = {
    "star": MissingThing(
        "star", "the little star mask", "the little star mask",
        "under the pillow", "look under the pillow", "the pillow",
        {"mystery", "mask", "bedtime"}
    ),
    "ribbon": MissingThing(
        "ribbon", "the ribbon", "the ribbon",
        "inside the story basket", "check the story basket", "the story basket",
        {"mystery", "ribbon", "bedtime"}
    ),
    "bell": MissingThing(
        "bell", "the tiny bell", "the tiny bell",
        "behind the curtain", "listen near the curtain", "the curtain",
        {"mystery", "bell", "bedtime"}
    ),
}

RESPONSES = {
    "pray": Response(
        "pray", 3,
        "paused to pray for a calm mind, then looked again with gentle eyes",
        "tried to pray, but the worry stayed loud and the clue got missed",
        "paused to pray, then looked again with calm eyes",
        {"pray", "calm"}
    ),
    "search_lamp": Response(
        "search_lamp", 3,
        "turned on the lamp and searched one quiet place at a time",
        "shone the lamp everywhere at once and still could not find it",
        "turned on the lamp and searched one quiet place at a time",
        {"search", "lamp"}
    ),
    "shake_blanket": Response(
        "shake_blanket", 2,
        "shook the blanket hard and hoped the missing thing would fall out",
        "shook the blanket, but that only made more mess and no clue",
        "shook the blanket and hoped the missing thing would fall out",
        {"messy", "weak"}
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for m in MASQUERADES:
        for miss in MISSING:
            if m == "moon" and miss == "star":
                combos.append((m, miss))
            if m == "garden" and miss == "ribbon":
                combos.append((m, miss))
            if m == "castle" and miss == "bell":
                combos.append((m, miss))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 3]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def reasonableness_gate(masquerade: Masquerade, missing: MissingThing, response: Response) -> None:
    if response.sense < 3:
        raise StoryError(f"(Refusing response '{response.id}': it is too weak for a bedtime mystery.)")
    if (masquerade.id, missing.id) not in valid_combos():
        raise StoryError("(No story: this masquerade and missing thing do not form a real, gentle mystery.)")


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        e.memes["worry"] = max(0.0, e.memes["worry"] - 1)
        out.append("__calm__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("searched") and not world.facts.get("found"):
        sig = ("clue", "once")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["hope"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [
    _r_calm,
    _r_clue,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_found(world: World, missing: MissingThing) -> bool:
    sim = world.copy()
    sim.facts["searched"] = True
    return sim.facts.get("chosen_search") == missing.where_hidden


def intro(world: World, child: Entity, masq: Masquerade) -> None:
    world.say(
        f"At bedtime, {child.id} wanted one last masquerade in "
        f"{masq.setting}. {masq.costume} waited nearby, and {masq.lights} "
        f"made the room glow like a soft secret."
    )


def mystery(world: World, child: Entity, missing: MissingThing, masq: Masquerade) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} looked for {missing.phrase} and could not find it. "
        f"{child.pronoun().capitalize()} checked twice, because the bedtime "
        f"game would not feel right without it."
    )
    world.say(
        f'"Where did it go?" {child.id} whispered. The answer was hidden in '
        f"{missing.where_hidden}."
    )


def pray(world: World, child: Entity) -> None:
    child.memes["calm"] += 1
    world.say(
        f"{child.id} closed {child.pronoun('possessive')} eyes and chose to pray. "
        f"The little prayer was quiet, and it made the room feel less lonely."
    )


def search(world: World, child: Entity, parent: Entity, missing: MissingThing, response: Response) -> None:
    world.facts["searched"] = True
    world.facts["chosen_search"] = missing.where_hidden
    child.memes["curiosity"] += 1
    world.say(
        f"{parent.label_word.capitalize()} smiled and helped {child.id} {response.method}. "
        f"Together they followed the clue: {missing.clue}."
    )
    world.say(
        f"They moved slowly, one gentle place at a time, until {child.id} peeked "
        f"where the clue pointed."
    )


def reveal(world: World, child: Entity, missing: MissingThing, masq: Masquerade) -> None:
    child.memes["joy"] += 1
    world.facts["found"] = True
    world.say(
        f"At last, there it was -- {missing.found_in}, tucked away as if it had "
        f"been waiting for the mystery to be solved."
    )
    world.say(
        f"{child.id} laughed with relief and put on {missing.label} again. "
        f"The masquerade could continue, and the bedtime room felt peaceful."
    )
    world.say(
        f"In the end, {child.id} wore {missing.label} under the soft lights, "
        f"ready for sleep and proud of the small mystery solved."
    )


def tell(masquerade: Masquerade, missing: MissingThing, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    reasonableness_gate(masquerade, missing, response)
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    child.memes["worry"] = 0.0

    intro(world, child, masquerade)
    world.para()
    mystery(world, child, missing, masquerade)
    world.say(
        f"{child.id} wanted to know the answer before bed, but {child.pronoun('possessive')} "
        f"{parent.label_word} said the calm thing first: breathe, then look."
    )
    world.para()
    pray(world, child)
    search(world, child, parent, missing, response)
    reveal(world, child, missing, masquerade)

    world.facts.update(
        child=child,
        parent=parent,
        masquerade=masquerade,
        missing=missing,
        response=response,
        outcome="found",
    )
    return world


THEMES = {
    "moon": MASQUERADES["moon"],
    "garden": MASQUERADES["garden"],
    "castle": MASQUERADES["castle"],
}

MISSING_REGISTRY = MISSING
RESPONSES_REGISTRY = RESPONSES

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Zoe", "Ella", "Ruby"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Theo", "Milo", "Finn", "Jude"]


@dataclass
class StoryParams:
    masquerade: str
    missing: str
    response: str
    child_name: str
    child_gender: str
    parent_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime mystery story world about a masquerade, a prayer, and a clue.")
    ap.add_argument("--masquerade", choices=THEMES)
    ap.add_argument("--missing", choices=MISSING_REGISTRY)
    ap.add_argument("--response", choices=RESPONSES_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.masquerade is None or c[0] == args.masquerade)
              and (args.missing is None or c[1] == args.missing)]
    if not combos:
        raise StoryError("(No valid masquerade mystery matches the given options.)")
    masquerade, missing = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(masquerade, missing, response, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.masquerade], MISSING_REGISTRY[params.missing],
                 RESPONSES_REGISTRY[params.response], params.child_name,
                 params.child_gender, params.parent_type)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = f["masquerade"]
    miss = f["missing"]
    return [
        f'Write a bedtime story about a masquerade where the word "pray" appears and a mystery is solved.',
        f"Tell a gentle story for a child named {f['child'].id} who wants to keep the masquerade going, but the {miss.label} is missing and a calm prayer helps."
        ,
        f'Write a cozy mystery-to-solve bedtime story that includes "masquerade" and ends with the missing {miss.label} found.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    missing = f["missing"]
    masq = f["masquerade"]
    response = f["response"]
    return [
        ("What kind of story is this?",
         "It is a bedtime mystery about a masquerade, a missing thing, and a calm search that solves the problem."),
        (f"What was missing?",
         f"{missing.label} was missing. The clue pointed to {missing.where_hidden}, where it had been tucked away."),
        (f"What did {child.id} do before searching?",
         f"{child.id} paused to pray, which helped {child.pronoun('possessive')} mind feel calm and ready to look again."),
        ("How did the search end?",
         f"{parent.label_word.capitalize()} helped {child.id} {response.method}, and they found {missing.label} in {missing.found_in}. "
         f"The masquerade could continue, and bedtime became peaceful again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["masquerade"].tags) | set(f["missing"].tags) | set(f["response"].tags)
    qa: list[tuple[str, str]] = []
    if "pray" in tags:
        qa.append(("What does it mean to pray?",
                    "To pray means to quietly talk to God, ask for help, or say thanks. Many people do it when they want comfort or calm." ))
    if "masquerade" in tags:
        qa.append(("What is a masquerade?",
                    "A masquerade is a pretend party or play where people wear costumes or masks. It can feel magical and a little mysterious." ))
    if "mask" in tags:
        qa.append(("What is a mask?",
                    "A mask is something you wear over part of your face for pretend play or a costume." ))
    if "calm" in tags:
        qa.append(("Why is being calm helpful?",
                    "Being calm helps you think clearly and notice clues. It can make a problem easier to solve." ))
    if "search" in tags:
        qa.append(("How do you solve a mystery?",
                    "You solve a mystery by noticing clues, asking careful questions, and looking in the right place." ))
    return qa


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, S) :- masquerade(M), missing(S), can_pair(M, S).
sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.
calm_after_pray :- pray("pray").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in THEMES:
        lines.append(asp.fact("masquerade", mid))
    for sid in MISSING_REGISTRY:
        lines.append(asp.fact("missing", sid))
    for rid, r in RESPONSES_REGISTRY.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 3))
    for m, s in valid_combos():
        lines.append(asp.fact("can_pair", m, s))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH: ASP sensible responses differ from Python.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            masquerade=None, missing=None, response=None, gender=None, name=None,
            parent=None, n=1, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("moon", "star", "pray", "Mia", "girl", "mother"),
    StoryParams("garden", "ribbon", "search_lamp", "Noah", "boy", "father"),
    StoryParams("castle", "bell", "pray", "Luna", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for m, s in asp_valid_combos():
            print(f"  {m:8} {s}")
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.masquerade} / {p.missing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

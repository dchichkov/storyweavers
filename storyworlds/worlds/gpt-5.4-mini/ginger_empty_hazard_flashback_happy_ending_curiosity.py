#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ginger_empty_hazard_flashback_happy_ending_curiosity.py
=======================================================================================

A small storyworld in a whodunit style: a curious child notices an odd, empty
hazard in the kitchen, remembers a flashback clue, and helps solve the mystery
before anything goes wrong. The story keeps the seed words "ginger", "empty",
and "hazard" while staying child-facing and concrete.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/ginger_empty_hazard_flashback_happy_ending_curiosity.py
    python storyworlds/worlds/gpt-5.4-mini/ginger_empty_hazard_flashback_happy_ending_curiosity.py --all
    python storyworlds/worlds/gpt-5.4-mini/ginger_empty_hazard_flashback_happy_ending_curiosity.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/ginger_empty_hazard_flashback_happy_ending_curiosity.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_MIN = 1.0
HELPER_TRUST_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    room: str
    smell: str
    shadow: str

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
class Object:
    id: str
    label: str
    phrase: str
    hazard: bool = False
    empty: bool = False
    clue: bool = False
    label_detail: str = ""

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
class Flashback:
    id: str
    cue: str
    detail: str
    revelation: str

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
class Twist:
    id: str
    title: str
    explanation: str
    safe_fix: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    rules = [RISK_RULE, FLASHBACK_RULE, RESOLUTION_RULE]
    while changed:
        changed = False
        for rule in rules:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _risk_rule(world: World) -> list[str]:
    out: list[str] = []
    if "hazard" not in world.entities or "curious" not in world.entities:
        return out
    hazard = world.get("hazard")
    child = world.get("curious")
    if hazard.meters.get("risk", 0.0) < THRESHOLD:
        return out
    sig = ("risk", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["alert"] = child.memes.get("alert", 0.0) + 1
    out.append("The kitchen felt more serious at once.")
    return out


def _flashback_rule(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("curious")
    if child.memes.get("remember", 0.0) < THRESHOLD:
        return out
    sig = ("flashback", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("A flashback returned to the child's mind, clear as a bell.")
    return out


def _resolution_rule(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("curious")
    helper = world.get("helper")
    hazard = world.get("hazard")
    if child.memes.get("solved", 0.0) < THRESHOLD:
        return out
    sig = ("resolved", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    out.append("The mystery was solved before any harm could begin.")
    return out


RISK_RULE = Rule("risk", _risk_rule)
FLASHBACK_RULE = Rule("flashback", _flashback_rule)
RESOLUTION_RULE = Rule("resolution", _resolution_rule)


def suggest_risk(obj: Object) -> bool:
    return obj.hazard


def safe_response(twist: Twist) -> bool:
    return bool(twist.safe_fix)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hazard in HAZARDS:
            for twist in TWISTS:
                combos.append((setting, hazard, twist))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    twist: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "kitchen", "warm ginger and toast", "a dim corner"),
    "pantry": Setting("pantry", "the pantry", "pantry", "ginger and flour", "a tall shelf"),
    "market": Setting("market", "the little market", "market", "ginger and oranges", "a crowded aisle"),
}

HAZARDS = {
    "empty_jar": Object("empty_jar", "an empty jar", "an empty jar on the counter", hazard=True, empty=True),
    "loose_step": Object("loose_step", "a loose step", "a loose step by the shelf", hazard=True),
    "spilled_salt": Object("spilled_salt", "spilled salt", "a spilled pile of salt", hazard=True),
}

TWISTS = {
    "missing_note": Twist("missing_note", "missing note", "a note had been moved", "put the note back where it belonged"),
    "flashback_key": Twist("flashback_key", "flashback key", "a key from yesterday fit the drawer", "use the key to open the drawer"),
    "ginger_crumbs": Twist("ginger_crumbs", "ginger crumbs", "ginger crumbs pointed to the pantry", "follow the crumbs to the pantry"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Max", "Finn", "Theo", "Owen"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a curious child, a hazard, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and not suggest_risk(HAZARDS[args.hazard]):
        raise StoryError("That hazard would not matter in this story.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hazard = args.hazard or rng.choice(sorted(HAZARDS))
    twist = args.twist or rng.choice(sorted(TWISTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("girl" if child_gender == "boy" else "boy")
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    if child_name == helper_name:
        helper_name = _pick_name(rng, helper_gender, avoid=child_name)
    return StoryParams(setting, hazard, twist, child_name, child_gender, helper_name, helper_gender)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("curious", kind="character", type=params.child_gender, role="curious", traits=["curious"]))
    helper = world.add(Entity("helper", kind="character", type=params.helper_gender, role="helper", traits=["steady"]))
    hazard = world.add(Entity("hazard", kind="thing", type="thing", label=HAZARDS[params.hazard].label))
    clue = world.add(Entity("clue", kind="thing", type="thing", label=TWISTS[params.twist].title))

    child.id = params.child_name
    helper.id = params.helper_name
    child.memes["curiosity"] = 1.0
    helper.memes["trust"] = 3.0
    hazard.meters["risk"] = 1.0

    world.say(
        f"On a quiet day in {world.setting.label}, {child.id} noticed {HAZARDS[params.hazard].phrase}. "
        f"The air smelled of {world.setting.smell}, and the whole room felt like it was hiding a secret."
    )
    world.say(
        f'"That is odd," {child.id} said. {child.pronoun().capitalize()} was full of curiosity and wanted to solve the hazard.'
    )
    world.para()
    world.say(
        f"Then a flashback came back to {child.id}: {TWISTS[params.twist].explanation}. "
        f"{TWISTS[params.twist].detail.capitalize()}."
    )
    child.memes["remember"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{helper.id} came over and listened carefully. Together they looked at {HAZARDS[params.hazard].label} again."
    )
    child.memes["solved"] = 1.0
    world.say(
        f'{child.id} pointed to the clue and whispered, "The answer is simple: {TWISTS[params.twist].safe_fix}."'
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{helper.id} smiled, and the little mystery ended with a happy ending. "
        f"{child.id} had solved the puzzle, the hazard was harmless, and the ginger smell of the kitchen felt cozy again."
    )

    world.facts.update(
        child=child,
        helper=helper,
        hazard=hazard,
        clue=clue,
        params=params,
        twist=TWISTS[params.twist],
        setting=SETTINGS[params.setting],
        outcome="happy",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-sized whodunit set in {f["setting"].label} that includes the words "ginger", "empty", and "hazard".',
        f"Tell a curious mystery about {f['child'].id} who notices an empty hazard and solves it with a flashback clue.",
        f"Write a happy-ending detective story where a child remembers a flashback and uses it to understand a hazard in the kitchen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    hazard = f["hazard"]
    twist = f["twist"]
    return [
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"{child.id} noticed something strange and started asking questions instead of ignoring it. The flashback clue gave the story a whodunit feeling because it helped explain what the hazard really meant."
        ),
        QAItem(
            question="How was the hazard solved?",
            answer=f"{child.id} remembered the clue and pointed to the right answer, then {helper.id} helped make it safe. That turned the danger into a harmless thing and kept the ending happy."
        ),
        QAItem(
            question="What did the flashback help the child remember?",
            answer=f"It helped {child.id} remember {twist.explanation}. That memory matched what was happening in the room, so the child could solve the mystery."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is ginger?", "Ginger is a strong-smelling root that people use to flavor food and drinks. It can make a kitchen smell warm and spicy."),
        QAItem("What does empty mean?", "Empty means there is nothing inside something. An empty jar or empty box does not have its usual contents anymore."),
        QAItem("What is a hazard?", "A hazard is something that could cause trouble or hurt someone. People notice hazards so they can stay safe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "empty_jar", "flashback_key", "Mia", "girl", "Noah", "boy"),
    StoryParams("pantry", "loose_step", "ginger_crumbs", "Leo", "boy", "Nora", "girl"),
    StoryParams("market", "spilled_salt", "missing_note", "Ava", "girl", "Finn", "boy"),
]


ASP_RULES = r"""
hazard(H) :- object(H), risky(H).
curious_event(C) :- child(C), remembers(C).
happy_ending :- solved, harmless_hazard.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("object", hid))
        if h.hazard:
            lines.append(asp.fact("risky", hid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    lines.append(asp.fact("child", "curious"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/1."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid()) != set((h,) for h in HAZARDS):
        print("MISMATCH: ASP hazard set differs from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, twist=None, child_name=None, child_gender=None, helper_name=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        return 1
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
        print(asp_program("", "#show hazard/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{h[0]}" for h in asp_valid()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as exc:
                print(exc)
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

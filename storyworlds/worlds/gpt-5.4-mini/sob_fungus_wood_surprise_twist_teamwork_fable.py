#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sob_fungus_wood_surprise_twist_teamwork_fable.py
=================================================================================

A small fable-style storyworld about a tiny forest problem:
a child or little animal is upset about a patch of fungus on a wooden object,
then a surprise twist reveals the fungus is not the enemy, and teamwork turns
the mess into something useful.

Seed words: sob, fungus, wood
Instruments: Surprise, Twist, Teamwork
Style: Fable
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "deer"}
        male = {"boy", "father", "dad", "man", "fox", "badger"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class CharacterSpec:
    id: str
    type: str
    role: str
    label: str
    trait: str

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
class ObjectSpec:
    id: str
    label: str
    material: str
    spoilable: bool = False
    useful_by: str = ""
    cleaned_by_team: bool = False

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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class Rule:
    name: str
    tag: str
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


@dataclass
class Setting:
    id: str
    place: str
    tone: str
    woods: str

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
class FungusPatch:
    id: str
    label: str
    color: str
    safe: bool
    role: str

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
@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    object: str
    fungus: str
    response: str
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
    "grove": Setting("grove", "the mossy grove", "gentle", "tall pines"),
    "meadow": Setting("meadow", "the sunny meadow", "bright", "soft grass"),
    "orchard": Setting("orchard", "the old orchard", "quiet", "rows of apple trees"),
}

CHILDREN = [
    CharacterSpec("pip", "mouse", "child", "little mouse", "brave"),
    CharacterSpec("mina", "girl", "child", "little girl", "curious"),
    CharacterSpec("otto", "boy", "child", "little boy", "thoughtful"),
]

HELPERS = [
    CharacterSpec("bram", "badger", "helper", "wise badger", "steady"),
    CharacterSpec("luna", "owl", "helper", "old owl", "kind"),
    CharacterSpec("fern", "deer", "helper", "kind deer", "patient"),
]

OBJECTS = {
    "woodstool": ObjectSpec("woodstool", "wooden stool", "wood", spoilable=True, useful_by="fireplace"),
    "woodbridge": ObjectSpec("woodbridge", "wooden bridge", "wood", spoilable=True, useful_by="stream"),
    "woodcrate": ObjectSpec("woodcrate", "wooden crate", "wood", spoilable=True, useful_by="garden"),
}

FUNGI = {
    "green": FungusPatch("green", "green fungus", "green", safe=True, role="patch"),
    "white": FungusPatch("white", "white fungus", "white", safe=True, role="patch"),
    "dark": FungusPatch("dark", "dark fungus", "brown", safe=False, role="patch"),
}

RESPONSES = {
    "wipe": Response("wipe", 2, 2,
                     "wiped the fungus away with a dry cloth",
                     "tried to wipe it away, but it had already spread too far",
                     "wiped the fungus away with a dry cloth"),
    "scrape": Response("scrape", 3, 3,
                       "scraped the fungus off with a small blade and brushed the wood clean",
                       "scraped too slowly, and the fungus stayed thick on the wood",
                       "scraped the fungus off and brushed the wood clean"),
    "save": Response("save", 4, 4,
                     "left the useful fungus in place and cleaned only the spoiled edges",
                     "tried to save the board, but the whole piece was too far gone",
                     "left the useful fungus in place and cleaned the spoiled edges"),
}

SENSIBLE_MIN = 2

GROW_NAMES = ["moss", "crumbs", "shade", "rain", "sleep", "spores"]


def _r_spread(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["fungal"] < THRESHOLD:
            continue
        sig = ("spread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "board" in world.entities:
            world.get("board").meters["stained"] += 1
        out.append("__spread__")
    return out


def _r_sob(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if child and child.memes["sob"] >= THRESHOLD:
        sig = ("sob", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["sadness"] += 1
            out.append("__sob__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread), Rule("sob", "social", _r_sob)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def can_reasonably_tell(object_cfg: ObjectSpec, fungus: FungusPatch, response: Response) -> bool:
    return object_cfg.spoilable and response.sense >= SENSIBLE_MIN


def story_problem(setting: Setting, child: Entity, helper: Entity, object_ent: Entity, fungus: FungusPatch) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    child_spec = next(c for c in CHILDREN if c.id == params.child)
    helper_spec = next(h for h in HELPERS if h.id == params.helper)
    obj_spec = OBJECTS[params.object]
    fungus = FUNGI[params.fungus]

    child = world.add(Entity(id=child_spec.id, kind="character", type=child_spec.type, role="child", label=child_spec.label, traits=[child_spec.trait]))
    helper = world.add(Entity(id=helper_spec.id, kind="character", type=helper_spec.type, role="helper", label=helper_spec.label, traits=[helper_spec.trait]))
    board = world.add(Entity(id="board", kind="thing", type="board", label=obj_spec.label, attrs={"material": obj_spec.material}))
    patch = world.add(Entity(id="patch", kind="thing", type="fungus", label=fungus.label, attrs={"safe": fungus.safe}))

    child.memes["sob"] = 0.0
    helper.memes["twist"] = 0.0
    helper.memes["teamwork"] = 0.0

    world.say(
        f"In {setting.place}, a little tale began beside {setting.woods}. "
        f"{child.id.capitalize()} found {fungus.label} on the {obj_spec.label}, and a soft sob shook {child.pronoun('possessive')} chest."
    )
    world.say(
        f'"Oh no," {child.id} sniffled, "the {obj_spec.material} looks ruined." '
        f"{helper.id.capitalize()} listened closely, and the air felt calm and old as a fable."
    )

    world.para()
    child.memes["sob"] += 1
    board.meters["fungal"] += 1
    patch.meters["fungal"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id.capitalize()} took a closer look and smiled with a surprise. "
        f'"This fungus is a twist," {helper.id} said. "It is not always a foe."'
    )
    world.say(
        f'{helper.id.capitalize()} explained that {fungus.label} could help keep the wood from drying and cracking.'
    )

    world.para()
    helper.memes["twist"] += 1
    helper.memes["teamwork"] += 1
    child.memes["teamwork"] += 1
    if params.response == "save":
        world.say(
            f"Together, they cleaned only the spoiled edges, then left the helpful part in place."
        )
        world.say(
            f"{child.id.capitalize()} fetched a soft brush, and {helper.id} steadied the {obj_spec.label} while they worked."
        )
    elif params.response == "wipe":
        world.say(
            f"Together, they carefully wiped the loose fuzz away, but left the soundest wood alone."
        )
        world.say(
            f"{child.id.capitalize()} wiped, {helper.id} watched, and neither rushed the job."
        )
    else:
        world.say(
            f"Together, they scraped the bad bits from the {obj_spec.label} and brushed away the dust."
        )
        world.say(
            f"{child.id.capitalize()} held the board still while {helper.id} did the careful scraping."
        )

    world.para()
    world.say(
        f"In the end, the {obj_spec.label} stayed useful, and the little team learned that not every strange thing is bad."
    )
    world.say(
        f"The child stopped sobbing, the wood was safe again, and the grove felt wiser for the surprise."
    )

    world.facts.update(
        setting=setting,
        child=child,
        helper=helper,
        board=board,
        patch=patch,
        object_cfg=obj_spec,
        fungus_cfg=fungus,
        response=RESPONSES[params.response],
        outcome="taught",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children that uses the words "sob", "{f["fungus_cfg"].label}", and "{f["object_cfg"].material}".',
        f"Tell a woodland fable where {f['child'].id} starts to sob over {f['fungus_cfg'].label} on a {f['object_cfg'].label}, then a helpful twist changes the problem.",
        f"Write a story with a surprise twist and teamwork, set in {f['setting'].place}, that teaches children how to stay calm when something looks spoiled.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Why was the child sobbing at the start?",
            answer=(
                f"{f['child'].id} thought the fungus had ruined the {f['object_cfg'].label}. "
                f"After the surprise twist, the helper showed that the wood was not useless at all."
            ),
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=(
                f"The helper explained that the fungus was not only a problem. "
                f"It could also be useful on wood, so they did not throw everything away."
            ),
        ),
        QAItem(
            question="How did teamwork help?",
            answer=(
                f"The child and helper worked together to clean the spoiled edges and steady the board. "
                f"Because they shared the job, the wood stayed useful and the child stopped crying."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fungus?",
            answer="Fungus is a living thing that can grow in damp places. Some kinds are helpful, and some kinds spoil food or wood.",
        ),
        QAItem(
            question="Why can wood change when it gets damp?",
            answer="Wood can swell, crack, or grow patchy when it gets too wet. Taking care of it helps it stay strong for longer.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other with the same job. It often makes a hard task easier and kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obj: ObjectSpec, fungus: FungusPatch) -> str:
    return (
        f"(No story: this combination is too thin for a fable. "
        f"The wood must be a real risk, and the fungus must allow a useful twist. "
        f"Try the wooden stool, wooden bridge, or wooden crate.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHILDREN:
            for h in HELPERS:
                for o in OBJECTS.values():
                    for f in FUNGI.values():
                        for r in RESPONSES.values():
                            if can_reasonably_tell(o, f, r):
                                combos.append((s, c.id, o.id))
    return combos


def outcome_of(params: StoryParams) -> str:
    return "taught"


ASP_RULES = r"""
valid(S, C, O) :- setting(S), child(C), object(O), spoilable(O).
surprise :- fungus(F), helpful(F).
twist :- surprise.
teamwork :- helper(H), child(C).
outcome(taught) :- valid(_, _, _), twist, teamwork.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for c in CHILDREN:
        lines.append(asp.fact("child", c.id))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.spoilable:
            lines.append(asp.fact("spoilable", oid))
    for fid, f in FUNGI.items():
        lines.append(asp.fact("fungus", fid))
        if f.safe:
            lines.append(asp.fact("helpful", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, child=None, child_type=None, helper=None, helper_type=None, object=None, fungus=None, response=None, seed=None), random.Random(1)))
        assert sample.story
        print("OK: generate smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: generate smoke test crashed: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world of sobbing, fungus, wood, surprise, twist, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=[c.id for c in CHILDREN])
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fungus", choices=FUNGI)
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
    if args.response and RESPONSES[args.response].sense < SENSIBLE_MIN:
        raise StoryError("Response is too weak for a reasonable fable.")
    setting = args.setting or rng.choice(list(SETTINGS))
    child = args.child or rng.choice([c.id for c in CHILDREN])
    helper = args.helper or rng.choice([h.id for h in HELPERS])
    object_id = args.object or rng.choice(list(OBJECTS))
    fungus = args.fungus or rng.choice(list(FUNGI))
    response = args.response or rng.choice([r.id for r in RESPONSES.values() if r.sense >= SENSIBLE_MIN])
    if not can_reasonably_tell(OBJECTS[object_id], FUNGI[fungus], RESPONSES[response]):
        raise StoryError(explain_rejection(OBJECTS[object_id], FUNGI[fungus]))
    return StoryParams(setting, child, "child", helper, "helper", object_id, fungus, response)


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


CURATED = [
    StoryParams("grove", "pip", "child", "bram", "helper", "woodstool", "green", "save"),
    StoryParams("orchard", "mina", "child", "luna", "helper", "woodcrate", "white", "wipe"),
    StoryParams("meadow", "otto", "child", "fern", "helper", "woodbridge", "dark", "scrape"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

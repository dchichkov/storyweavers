#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py
======================================================================

A standalone story world for a small adventure tale built from the seed words
"viaduct" and "slip".  The domain is a child-sized bridge adventure: a pair of
children explore an old viaduct, one child slips on a damp stone, the other
calls a grown-up, and the ending is happy because the adult uses the right gear
and turns the scare into a safer adventure.

The world is deliberately small:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate
- a Python/ASP twin for parity checks
- three Q&A sets grounded in the simulated story

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py --trace
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py --json
    python storyworlds/worlds/gpt-5.4-mini/viaduct_slip_happy_ending_adventure.py --verify
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
SENSE_MIN = 2


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
class Setting:
    id: str
    place: str
    detail: str
    adventure_word: str
    risk_word: str
    affords: set[str] = field(default_factory=set)

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
class SlipPath:
    id: str
    label: str
    cause: str
    danger: str
    zone: set[str]
    slippery: bool = True

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
class Gear:
    id: str
    label: str
    phrase: str
    use: str
    guards: set[str]
    covers: set[str]
    plural: bool = False

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


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["slip"] < THRESHOLD:
            continue
        sig = ("slip", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] += 1
        if "trail" in world.entities:
            world.get("trail").meters["danger"] += 1
        out.append("__slip__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["fear"] < THRESHOLD or ent.role != "rescuer":
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["resolve"] += 1
        out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("slip", "physical", _r_slip), Rule("worry", "social", _r_worry)]


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


def hazard_at_risk(path: SlipPath, prize: str) -> bool:
    return path.slippery and prize in {"bridge", "crossing", "path"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict_slip(world: World, child_id: str) -> dict:
    sim = world.copy()
    sim.get(child_id).meters["slip"] += 1
    propagate(sim, narrate=False)
    return {"fear": sim.get(child_id).memes["fear"], "danger": sim.get("trail").meters["danger"]}


def play_setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} set off on an adventure at {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"They treated the old viaduct like part of the quest, as if every stone could lead to treasure."
    )


def slip_beat(world: World, a: Entity, path: SlipPath) -> None:
    a.meters["slip"] += 1
    world.say(
        f"At the narrow arch, {a.id} stepped on {path.cause} and nearly {path.danger}."
    )
    propagate(world, narrate=False)


def alarm(world: World, b: Entity, a: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} shouted. "Hold still -- I\'m right here!"')


def call_adult(world: World, parent: Entity, response: Response, delay: int) -> None:
    body = response.text
    if not is_contained(response, delay):
        body = response.fail
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    if is_contained(response, delay):
        world.say("The scare ended fast, and the bridge was safe again.")
    else:
        world.say("The rescue took too long, but everyone got out safely.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for ent in (a, b):
        ent.memes["relief"] += 1
        ent.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I am glad you called for help," {parent.pronoun()} said. '
        f'"Adventure is wonderful, but a slippery stone can turn a game into a fall."'
    )


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, gear: Gear) -> None:
    world.say(
        f"Then {parent.pronoun()} showed them {gear.phrase}, and the three of them crossed together."
    )
    world.say(
        f"This time, {a.id} watched {b.id} point out the safest stones, and the viaduct looked like a brave, bright path."
    )
    world.say(
        f"They reached the other side smiling, with the whole adventure turned into a happy story instead of a tumble."
    )


def tell(setting: Setting, path: SlipPath, gear: Gear, response: Response,
         a_name: str = "Lily", a_gender: str = "girl",
         b_name: str = "Tom", b_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="explorer"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="rescuer"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="rescuer", label="the parent"))
    trail = world.add(Entity(id="trail", type="trail", label="the trail"))
    world.facts["setting"] = setting
    world.facts["path"] = path
    world.facts["gear"] = gear
    world.facts["response"] = response
    world.facts["delay"] = delay

    play_setup(world, a, b, setting)
    world.para()
    slip_beat(world, a, path)
    alarm(world, b, a)
    world.para()
    call_adult(world, parent, response, delay)
    lesson(world, parent, a, b)
    world.para()
    safe_finish(world, parent, a, b, gear)

    world.facts.update(outcome="happy", a=a, b=b, parent=parent, trail=trail,
                       slipped=a.meters["slip"] >= THRESHOLD)
    return world


SETTINGS = {
    "viaduct": Setting(
        "viaduct", "the old viaduct",
        "Its long arches echoed footsteps, and the view below made the whole place feel like a grand adventure.",
        "adventure", "slip", affords={"crossing"},
    ),
    "station": Setting(
        "station", "the hill station bridge",
        "The rails hummed beside the walkway, and the bright signs made the place feel busy and exciting.",
        "adventure", "slip", affords={"crossing"},
    ),
}

PATHS = {
    "slick_stone": SlipPath("slick_stone", "a slick stone", "a slick stone", "slip over the edge", {"feet", "legs"}),
    "wet_leaf": SlipPath("wet_leaf", "a wet leaf", "a wet leaf", "slip sideways", {"feet"}),
    "mossy_patch": SlipPath("mossy_patch", "a mossy patch", "a mossy patch", "slip hard", {"feet", "legs"}),
}

GEAR = {
    "handrail_gloves": Gear("handrail_gloves", "grippy gloves", "grippy gloves", "hold the rail better", {"slippery"}, {"hands"}),
    "walking_stick": Gear("walking_stick", "a short walking stick", "a short walking stick", "steady the walk", {"slippery"}, {"feet", "legs"}),
    "boots": Gear("boots", "sturdy boots", "sturdy boots", "keep feet steady", {"slippery"}, {"feet"}),
}

RESPONSES = {
    "grab": Response("grab", 3, 2, "grabbed the rail, steadied the child, and helped them breathe again",
                     "grabbed the rail too late, but still got there to help", "grabbed the rail and steadied the child"),
    "guide": Response("guide", 3, 3, "guided them to the safe side of the walkway and checked their knees",
                      "guided them, but the stumble was already too quick", "guided them to the safe side"),
    "stair_wait": Response("stair_wait", 2, 1, "waited by the stairs and called out for them to come slowly",
                           "waited, but the slip had already turned into a tumble", "waited by the stairs and called out"),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Finn", "Leo", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PATHS:
            for g in GEAR:
                if hazard_at_risk(PATHS[p], "bridge"):
                    combos.append((s, p, g))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    path: str
    gear: str
    response: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    parent: str
    delay: int = 0
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
    "viaduct": [("What is a viaduct?", "A viaduct is a long bridge or series of bridges that carries a road or path across a gap or over lower ground.")],
    "slip": [("What does it mean to slip?", "To slip means your foot slides out of place, so you can nearly fall unless you catch yourself.")],
    "bridge": [("Why should you be careful on a bridge?", "A bridge can be high up or narrow, so it is important to walk slowly and keep a good grip.")],
    "boots": [("What do sturdy boots do?", "Sturdy boots help your feet stay steady and protected on rough ground.")],
    "grippy": [("What does something grippy do?", "A grippy thing helps you hold on without sliding.")],
    "rescue": [("Why do people call a grown-up in an accident?", "A grown-up can help in a calm way and use the right tools to keep everyone safe.")],
}
KNOWLEDGE_ORDER = ["viaduct", "slip", "bridge", "boots", "grippy", "rescue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a happy adventure story for a 3-to-5-year-old that includes the word "viaduct" and the word "slip".',
        f"Tell a child-sized adventure story where {f['a'].id} and {f['b'].id} cross a viaduct, one of them nearly slips, and a grown-up helps them finish safely.",
        f'Write a simple bridge adventure with a happy ending, a cautious rescue, and a final safe crossing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["a"], f["b"], f["parent"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, who were exploring the viaduct together with {parent.label_word}."),
        ("What happened on the bridge?",
         f"{a.id} stepped on a slippery stone and nearly slipped. {b.id} shouted right away so help could come quickly."),
        ("How did the story end?",
         f"It ended happily. The parent helped them cross safely, and the adventure turned into a brave, happy walk across the viaduct."),
    ]
    if f.get("slipped"):
        qa.append((
            f"What did {a.id} do after slipping?",
            f"{a.id} stayed still and listened while {b.id} called for help. That kept the moment small instead of making it worse."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"viaduct", "slip", "bridge", "rescue", "boots", "grippy"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
    StoryParams("viaduct", "slick_stone", "boots", "grab", "Lily", "girl", "Tom", "boy", "mother", 0),
    StoryParams("station", "wet_leaf", "walking_stick", "guide", "Mia", "girl", "Sam", "boy", "father", 0),
    StoryParams("viaduct", "mossy_patch", "boots", "stair_wait", "Finn", "boy", "Ava", "girl", "mother", 1),
]


def explain_rejection(path: SlipPath) -> str:
    return f"(No story: that path is not slippery enough to support a slip.)"


def sensible_response_ids() -> list[str]:
    return [r.id for r in sensible_responses()]


def outcome_of(params: StoryParams) -> str:
    return "happy"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("adventure", sid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        if p.slippery:
            lines.append(asp.fact("slippery", pid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for gu in sorted(g.guards):
            lines.append(asp.fact("guards", gid, gu))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P) :- path(P), slippery(P).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,P,G) :- setting(S), path(P), gear(G), hazard(P).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    if set(asp_sensible()) != set(sensible_response_ids()):
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A happy viaduct adventure with a slip and a safe ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    path = args.path or rng.choice(list(PATHS))
    gear = args.gear or rng.choice(list(GEAR))
    response = args.response or rng.choice(sensible_response_ids())
    if args.path and not PATHS[args.path].slippery:
        raise StoryError(explain_rejection(PATHS[args.path]))
    name = args.name or rng.choice(["Lily", "Mia", "Ava", "Tom", "Finn", "Sam"])
    companion = args.companion or rng.choice([n for n in ["Lily", "Mia", "Ava", "Tom", "Finn", "Sam"] if n != name])
    parent = args.parent or rng.choice(["mother", "father"])
    g1 = "girl" if name in {"Lily", "Mia", "Ava"} else "boy"
    g2 = "girl" if companion in {"Lily", "Mia", "Ava"} else "boy"
    return StoryParams(setting, path, gear, response, name, g1, companion, g2, parent, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PATHS[params.path], GEAR[params.gear], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.companion, params.companion_gender,
                 params.parent, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.hero} at the {p.setting} ({p.path}, happy ending)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

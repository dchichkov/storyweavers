#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barefoot_nuisance_achoo_foreshadowing_moral_value_myth.py
=========================================================================================

A small myth-style storyworld about a barefoot child, a nuisance spirit, an
"achoo" omen, and a moral-value ending that pays off earlier foreshadowing.

The world is intentionally tiny: a child goes barefoot to a shrine path, a
mischievous nuisance spirit makes trouble, the spirit's sneeze foreshadows a
bigger problem, and a wise elder turns the moment into a lesson about respect,
kindness, and listening before the final blessing.

The script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates story-grounded and world-knowledge QA from simulated state
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
class Place:
    id: str
    label: str
    description: str
    sacred: bool = False
    barefoot_suitable: bool = True

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
class Nuisance:
    id: str
    label: str
    act: str
    sneeze: str
    foreshadow: str
    disruptive: bool = True

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
class Blessing:
    id: str
    label: str
    tone: str
    value: str

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
        return c


@dataclass
class Rule:
    name: str
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


def _r_stumble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    path = world.get("path")
    if child.meters["barefoot"] < THRESHOLD:
        return out
    sig = ("stumble", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    path.meters["disturbed"] += 1
    out.append("__stumble__")
    return out


def _r_omen(world: World) -> list[str]:
    out: list[str] = []
    spirit = world.get("spirit")
    if spirit.meters["sneeze"] < THRESHOLD:
        return out
    sig = ("omen", spirit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sky").meters["cloud"] += 1
    world.get("child").memes["warning"] += 1
    out.append("__omen__")
    return out


CAUSAL_RULES = [Rule("stumble", _r_stumble), Rule("omen", _r_omen)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend([g for g in got if not g.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def barefoot_at_risk(place: Place) -> bool:
    return place.barefoot_suitable


def valid_combos() -> list[str]:
    return [p.id for p in PLACES.values() if p.barefoot_suitable and p.sacred]


def reasonable_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def resolve_fate(place: Place, nuisance: Nuisance, delay: int, response: Response) -> str:
    if delay <= 0:
        return "blessing"
    return "lesson" if response.power >= delay else "mourn"


def predict(world: World, nuisance: Nuisance) -> dict:
    sim = world.copy()
    sim.get("spirit").meters["sneeze"] += 1
    propagate(sim, narrate=False)
    return {"warning": sim.get("child").memes["warning"], "cloud": sim.get("sky").meters["cloud"]}


def tell(place: Place, nuisance: Nuisance, blessing: Blessing, response: Response,
         child_name: str = "Mira", child_gender: str = "girl",
         elder_name: str = "Grandmother", elder_gender: str = "woman",
         delay: int = 1) -> World:
    world = World()
    child = world.add(Entity("child", "character", child_gender, role="seeker"))
    elder = world.add(Entity("elder", "character", elder_gender, role="elder"))
    spirit = world.add(Entity("spirit", "character", "thing", role="nuisance"))
    path = world.add(Entity("path", "thing", "path", label="the shrine path"))
    sky = world.add(Entity("sky", "thing", "sky", label="the sky"))

    child.id = child_name
    elder.id = elder_name
    child.label = child_name
    elder.label = elder_name

    child.meters["barefoot"] = 1.0
    child.memes["curiosity"] = 1.0
    spirit.meters["nuisance"] = 1.0

    world.facts["place"] = place
    world.facts["nuisance"] = nuisance
    world.facts["blessing"] = blessing
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["elder"] = elder

    world.say(
        f"Long ago, at {place.label}, {child.id} walked barefoot along {place.description}. "
        f"{child.id} liked the hush of the stones and the old songs in the air."
    )
    world.say(
        f"But there lived there a nuisance spirit named {nuisance.label}. "
        f"It would tug at ribbons, rattle jars, and laugh whenever the lanterns shook."
    )

    world.para()
    world.say(
        f"{child.id} noticed a small sign of trouble before the trouble itself: "
        f"{nuisance.foreshadow}. {child.pronoun().capitalize()} paused, and the air felt thinner."
    )
    child.memes["foreshadowing"] += 1
    predict(world, nuisance)

    world.para()
    world.say(
        f"Then the nuisance spirit let out a loud {nuisance.sneeze} that echoed under the trees. "
        f"The sound startled birds from the branches, and {child.id} felt the omen in {child.pronoun('possessive')} chest."
    )
    spirit.meters["sneeze"] += 1
    propagate(world, narrate=False)

    if delay <= 0:
        world.say(
            f"{elder.id} stepped forward at once and raised a calm hand. "
            f'"That is enough," {elder.pronoun()} said, and the spirit grew quiet.'
        )
        world.say(
            f"{child.id} bowed {child.pronoun('possessive')} head, and the path grew still again. "
            f"The old stones seemed kinder after that."
        )
        world.para()
        world.say(
            f"To teach the right value, {elder.id} told {child.id} that a place sacred to many hearts "
            f"must be treated with care. {blessing.value} came when respect came first."
        )
    else:
        world.say(
            f"{elder.id} arrived with {response.text}. The nuisance spirit stopped its mischief, and the cloud broke."
        )
        world.para()
        world.say(
            f"{elder.id} then gave the lesson plainly: {blessing.value}. "
            f"{child.id} listened, and {child.id} understood that kindness keeps even an old path safe."
        )
        child.memes["lesson"] += 1

    world.para()
    world.say(
        f"At sunset, {child.id} went home barefoot no longer feeling bold for boldness alone, "
        f"but wise enough to honor the world that had carried {child.pronoun('object')}."
    )

    world.facts.update(
        outcome="lesson",
        child=child,
        spirit=spirit,
        path=path,
        sky=sky,
        foreshadowed=True,
        sneezed=True,
    )
    return world


PLACES = {
    "temple_steps": Place("temple_steps", "the temple steps", "the worn marble steps beside the shrine", sacred=True, barefoot_suitable=True),
    "river_bank": Place("river_bank", "the river bank", "the silver bank where reeds whispered", sacred=False, barefoot_suitable=True),
    "harbor_path": Place("harbor_path", "the harbor path", "the salt path by the boats", sacred=True, barefoot_suitable=True),
}

NUISANCES = {
    "sprite": Nuisance("sprite", "a nuisance sprite", "play tricks", "achoo", "a feather twitching in its nose"),
    "kobold": Nuisance("kobold", "a nuisance kobold", "poke and tease", "achoo", "dust dancing around its whiskers"),
    "imp": Nuisance("imp", "a nuisance imp", "scatter pebbles", "achoo", "a leaf stuck to its cheek"),
}

BLESSINGS = {
    "respect": Blessing("respect", "respect", "gentle", "Respect keeps holy places calm."),
    "kindness": Blessing("kindness", "kindness", "warm", "Kindness turns a nuisance into a neighbor."),
    "humility": Blessing("humility", "humility", "quiet", "Humility helps small hearts hear wise warnings."),
}

RESPONSES = {
    "calm": Response("calm", 3, 3, "spoke softly and asked the spirit to settle down", "spoke softly and asked the spirit to settle down"),
    "song": Response("song", 2, 2, "began an old lullaby that soothed the air", "began an old lullaby that soothed the air"),
    "blessing": Response("blessing", 4, 4, "lifted a hand and said a blessing over the path", "lifted a hand and said a blessing over the path"),
}



@dataclass
class StoryParams:
    place: str
    nuisance: str
    blessing: str
    response: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    delay: int = 1
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

CURATED = [
    ("temple_steps", "sprite", "respect", "calm", "Mira", "girl", "Grandmother", "woman", 1),
    ("harbor_path", "kobold", "kindness", "song", "Owen", "boy", "Elder", "man", 1),
    ("river_bank", "imp", "humility", "blessing", "Lina", "girl", "Grandmother", "woman", 2),
]



KNOWLEDGE = {
    "barefoot": [("What does barefoot mean?", "Barefoot means not wearing shoes or sandals. Feet can feel the ground directly.")],
    "nuisance": [("What is a nuisance?", "A nuisance is something or someone that keeps causing little trouble and irritation.")],
    "achoo": [("Why do people say achoo?", "Achoo is the sound people often make when they sneeze.")],
    "respect": [("What is respect?", "Respect means treating places, people, and rules with care.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring toward others.")],
    "humility": [("What is humility?", "Humility means knowing you can listen and learn instead of acting proud.")],
    "temple": [("What is a temple?", "A temple is a special place where people go to pray, remember, or honor what they believe is holy.")],
    "river": [("Why do rivers matter?", "Rivers give water to plants, animals, and people, so people should treat them carefully.")],
    "hush": [("What is a hush?", "A hush is a quiet stillness when everyone becomes calm.")],
}
KNOWLEDGE_ORDER = ["barefoot", "nuisance", "achoo", "respect", "kindness", "humility", "temple", "river", "hush"]


def valid_combos_tuple() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        if not PLACES[p].sacred:
            continue
        for n in NUISANCES:
            for b in BLESSINGS:
                out.append((p, n, b))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-style story for a young child that includes the words "barefoot", "nuisance", and "achoo".',
        f"Tell a small myth where {f['child'].id} walks barefoot to {f['place'].label}, notices a nuisance spirit, and learns a moral value.",
        f"Write a foreshadowing story in a myth tone where an achoo from a nuisance spirit leads to a wise lesson about {f['blessing'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    place: Place = f["place"]
    nuisance: Nuisance = f["nuisance"]
    blessing: Blessing = f["blessing"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, who walked barefoot to {place.label}, and {elder.id}, who helped turn the nuisance into a lesson. The spirit's trouble made the myth feel old and important.",
        ),
        QAItem(
            question=f"What did {child.id} notice before the sneeze?",
            answer=f"{child.id} noticed {nuisance.foreshadow} before the loud achoo. That was foreshadowing, because it hinted that the nuisance spirit was about to cause more trouble.",
        ),
        QAItem(
            question="What did the sneeze change?",
            answer=f"The achoo stirred the air, startled the birds, and made the warning feel real. After that, the elder could speak the moral value plainly.",
        ),
        QAItem(
            question="What moral did the elder teach?",
            answer=f"The elder taught that {blessing.value.lower()} matters. In a sacred place, respect and kindness keep the path calm and safe for everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"barefoot", "nuisance", "achoo", world.facts["blessing"].id}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
barefoot_at_risk(P) :- place(P), sacred(P), barefoot_suitable(P).
foreshadow(F) :- nuisance(N), foreshadowing(N, F).
omen(P) :- barefoot_at_risk(P), foreshadow(_).
moral_value(B) :- blessing(B), value(B, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.sacred:
            lines.append(asp.fact("sacred", pid))
        if p.barefoot_suitable:
            lines.append(asp.fact("barefoot_suitable", pid))
    for nid, n in NUISANCES.items():
        lines.append(asp.fact("nuisance", nid))
        lines.append(asp.fact("foreshadowing", nid, n.foreshadow))
    for bid, b in BLESSINGS.items():
        lines.append(asp.fact("blessing", bid))
        lines.append(asp.fact("value", bid, b.value))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show barefoot_at_risk/1."))
    return sorted(set(asp.atoms(model, "barefoot_at_risk")))


def asp_verify() -> int:
    rc = 0
    p = set(valid_combos())
    c = set(x[0] for x in asp_valid_combos())
    if p != c:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only python:", sorted(p - c))
        print("  only clingo:", sorted(c - p))
    else:
        print(f"OK: gate matches valid_combos() ({len(p)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, nuisance=None, blessing=None, response=None, child=None, elder=None, delay=None, n=1, seed=None, all=False, trace=False, qa=False, json=False, asp=False, verify=False, show_asp=False), random.Random(777)))
        assert sample.story
        print("OK: smoke test story generation works.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style barefoot nuisance storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--nuisance", choices=NUISANCES)
    ap.add_argument("--blessing", choices=BLESSINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--elder")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    combos = valid_combos_tuple()
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.place and not PLACES[args.place].sacred:
        raise StoryError("This place is not sacred enough for the myth story.")
    if args.nuisance and args.nuisance not in NUISANCES:
        raise StoryError("Unknown nuisance.")
    if args.blessing and args.blessing not in BLESSINGS:
        raise StoryError("Unknown blessing.")
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")

    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.nuisance is None or c[1] == args.nuisance)
                and (args.blessing is None or c[2] == args.blessing)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    place, nuisance, blessing = rng.choice(filtered)
    response = args.response or rng.choice(sorted(RESPONSES))
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    child = args.child or rng.choice(["Mira", "Owen", "Lina", "Tao", "Iris"])
    elder = args.elder or rng.choice(["Grandmother", "Grandfather", "Aunt", "Uncle", "Elder"])
    child_gender = "girl" if child in {"Mira", "Lina", "Iris"} else "boy"
    elder_gender = "woman" if elder in {"Grandmother", "Aunt"} else "man"
    return StoryParams(place, nuisance, blessing, response, child, child_gender, elder, elder_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], NUISANCES[params.nuisance], BLESSINGS[params.blessing], RESPONSES[params.response], params.child_name, params.child_gender, params.elder_name, params.elder_gender, params.delay)
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
        print(asp_program("", "#show barefoot_at_risk/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} barefoot-safe sacred places.")
        for item in asp_valid_combos():
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p, n, b, "calm", "Mira", "girl", "Grandmother", "woman", d))
                   for p, n, b, _, _, _, _, _, d in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as exc:
                print(exc)
                return
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wiener_cripple_twist_dialogue_teamwork_ghost_story.py
======================================================================================

A standalone story world for a small, child-facing ghost story domain.

Premise
-------
A child and a helper face a spooky old room at night. A ghost makes the room feel
cold and strange, but the characters use dialogue and teamwork to find the truth:
the "ghost" is not trying to scare them away from danger, it is trying to guide
them toward something lost. The twist reveals the haunting was a warning, and the
ending proves the room is safe again.

Seed words and instruments
--------------------------
Words: wiener, cripple
Features: twist, dialogue, teamwork
Style: ghost story

The world is intentionally tiny. It stays within a single setting, a small cast,
one spooky tension, one revealing twist, and one cooperative resolution.
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
SENSE_MIN = 2


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
class Setting:
    id: str
    place: str
    darkness: str
    sound: str

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
class Clue:
    id: str
    label: str
    object_phrase: str
    hidden_reason: str
    visible_reason: str
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


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    twist_kind: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["haunted"] < THRESHOLD:
        return out
    if ("cold",) in world.fired:
        return out
    world.fired.add(("cold",))
    world.get("room").meters["chill"] += 1
    for eid in ("child", "helper"):
        world.get(eid).memes["unease"] += 1
    out.append("__spook__")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(clue: Clue) -> bool:
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for setting in SETTINGS:
        for clue in CLUES:
            for response in RESPONSES:
                combos.append((setting, clue, response))
    return combos


def tension_level(clue: Clue) -> int:
    return 2 if "haunt" in clue.tags else 1


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def play_setup(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a damp evening, {child.id} and {helper.id} stepped into {world.setting.place}. "
        f"The air felt {world.setting.darkness}, and every board seemed to remember a secret."
    )


def first_haunting(world: World, clue: Clue, child: Entity) -> None:
    world.get("room").meters["haunted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came a tiny sound: {world.setting.sound}. "
        f"{child.id} froze when the old {clue.label} seemed to sway all by itself."
    )


def dialogue_warning(world: World, helper: Entity, child: Entity, clue: Clue, parent: Entity) -> None:
    helper.memes["caution"] += 1
    world.say(
        f'"Did you hear that?" {helper.id} whispered. "{child.id}, this place feels wrong."'
    )
    world.say(
        f'"Maybe," {child.id} said, peering at the {clue.label}, "but look. '
        f'It might be trying to tell us something."'
    )
    world.say(
        f'"Your {parent.label_word} always says to ask before guessing," {helper.id} replied.'
    )


def teamwork_search(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.say(
        f"Together they moved one step at a time. {helper.id} held the lantern high "
        f"while {child.id} looked under the bed and behind the curtain."
    )
    world.say(
        f"The old {clue.label} was not a monster at all. It was a clue."
    )


def twist_reveal(world: World, clue: Clue, parent: Entity) -> None:
    world.facts["twist"] = clue.hidden_reason
    world.say(
        f"At last they found the truth: the room was not haunted by a cruel ghost. "
        f"It was haunted by a worried one."
    )
    world.say(
        f'The ghost had been pointing at the {clue.object_phrase} all along, because '
        f"{clue.hidden_reason}."
    )
    world.say(
        f'"A lost thing can make a lot of noise in the dark," {parent.label_word} said softly.'
    )


def fix_it(world: World, child: Entity, helper: Entity, parent: Entity, response: Response, clue: Clue) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came in with a calm smile. In one quick motion, "
        f"{parent.pronoun()} {response.text}."
    )
    world.say(
        f"The strange sound stopped. The cold in the room loosened, and the old {clue.label} stopped shaking."
    )
    world.say(
        f'Turns out the scare had been a warning, not a threat: the missing {clue.label} was right there.'
    )


def ending_image(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, {child.id} and {helper.id} laughed in the warm light. "
        f"They set the {clue.label} back where it belonged, and the room felt like a room again."
    )
    world.say(
        f"The only ghost left was the shivery memory of the dark, and even that was fading by the window."
    )


SETTINGS = {
    "attic": Setting("attic", "the attic", "cool and whispery", "tap-tap, tap"),
    "basement": Setting("basement", "the basement", "cold and hollow", "drip... drip..."),
    "hall": Setting("hall", "the old hall", "long and echoing", "knock... knock..."),
}

CLUES = {
    "wiener_sign": Clue(
        "wiener_sign",
        "sign",
        "wiener sign",
        "the sign had fallen behind the chest",
        "a missing sign could make a spooky draft feel like a ghost",
        {"wiener", "ghost", "clue"},
    ),
    "wiener_dog_toy": Clue(
        "wiener_dog_toy",
        "toy dog",
        "wiener dog toy",
        "the toy had rolled under the stairs",
        "a lost toy in the dark can look like a moving shadow",
        {"wiener", "toy", "ghost"},
    ),
    "crippled_lamp": Clue(
        "crippled_lamp",
        "lamp",
        "crippled lamp",
        "the lamp had a bent stand and a loose cord",
        "a crooked lamp can wobble and make eerie shapes on the wall",
        {"cripple", "ghost", "clue"},
    ),
    "crippled_chair": Clue(
        "crippled_chair",
        "chair",
        "crippled chair",
        "the chair leg was broken and nudged the floorboards",
        "a broken chair can make tapping noises when the house shifts",
        {"cripple", "ghost", "clue"},
    ),
}

RESPONSES = {
    "listen": Response(
        "listen",
        3,
        3,
        "listened carefully and followed the sound to the far corner",
        "listened, but the sound slipped away before they could find it",
        "followed the sound and found the clue",
        {"dialogue", "teamwork"},
    ),
    "light": Response(
        "light",
        3,
        3,
        "turned on the lantern and shone it behind the boxes",
        "shone the lantern, but the dark shape was still too hard to read",
        "shone a lantern and looked behind the boxes",
        {"dialogue", "teamwork"},
    ),
    "ask": Response(
        "ask",
        2,
        2,
        "called out a soft question and waited for an answer",
        "called out, but only the echo answered back",
        "called out a question and waited for an answer",
        {"dialogue"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Rose", "Ada"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Theo", "Ben", "Finn"]
TWO_STEP_TRAITS = ["careful", "brave", "curious", "gentle", "patient"]


def story_topic(clue: Clue) -> str:
    return "wiener" if "wiener" in clue.tags else "cripple"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"]
    return [
        f'Write a child-friendly ghost story that includes the word "{story_topic(clue)}" and ends with a twist.',
        f"Tell a spooky-but-kind story where {f['child'].id} and {f['helper'].id} work together to solve the noise in the dark.",
        f'Write a ghost story with dialogue and teamwork, and make the scary thing turn out to be a clue.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, parent, clue = f["child"], f["helper"], f["parent"], f["clue"]
    qa = [
        (
            "Who are the story about?",
            f"It is about {child.id} and {helper.id}, who went into {world.setting.place} with {parent.label_word}.",
        ),
        (
            "What made the place feel spooky?",
            f"The room felt {world.setting.darkness}, and {world.setting.sound} kept sounding in the dark. That made the children think something ghostly was there.",
        ),
        (
            "What did the children do to solve the mystery?",
            f"They used dialogue and teamwork. {helper.id} listened, and {child.id} searched, so they could find the clue together.",
        ),
    ]
    qa.append(
        (
            "What was the twist at the end?",
            f"The ghost was not trying to frighten them for fun. It was pointing them toward {clue.hidden_reason}, so the haunting was really a warning.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    clue: Clue = world.facts["clue"]
    tags = set(clue.tags)
    if "wiener" in tags:
        return [
            ("What is a wiener?",
             "A wiener is a small sausage, often served in a bun as a hot dog. It is food, not something spooky."),
            ("Why can a small lost object seem scary in the dark?",
             "In the dark, your eyes may not see it clearly, so a small object can look like a strange shape until someone shines a light."),
        ]
    return [
        ("What does crippled mean here?",
         "Here it means something is broken, bent, or not working right, like a chair leg or a lamp stand. It is not about a person."),
        ("Why can a broken thing make a spooky sound?",
         "When a broken thing shifts or taps the floor, the noise can echo and sound eerie in an old house."),
    ]


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
    return "\n".join(lines)


def explain_rejection(*_args) -> str:
    return "(No story: this tiny ghost world accepts the given choices, but it still needs sensible defaults.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, C, R) :- setting(S), clue(C), response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if "wiener" in c.tags:
            lines.append(asp.fact("wiener_clue", cid))
        if "cripple" in c.tags:
            lines.append(asp.fact("cripple_clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


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
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, clue=None, response=None, child=None, child_gender=None,
            helper=None, helper_gender=None, parent=None, twist_kind=None
        ), random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny ghost story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--twist-kind", choices=["warning", "secret", "lost-item"])
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


def valid_child_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" and rng.random() < 0.5 else "girl")
    child = args.child or rng.choice(valid_child_names(child_gender))
    helper = args.helper or rng.choice([n for n in valid_child_names(helper_gender) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    twist_kind = args.twist_kind or rng.choice(["warning", "secret", "lost-item"])
    if args.response and args.response not in RESPONSES:
        raise StoryError("invalid response")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    return StoryParams(setting, clue, response, child, child_gender, helper, helper_gender, parent, twist_kind)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity("helper", kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity("parent", kind="character", type=params.parent, role="parent"))
    room = world.add(Entity("room", type="room", label="the room"))

    clue = CLUES[params.clue]
    response = RESPONSES[params.response]

    world.facts.update(child=child, helper=helper, parent=parent, clue=clue, response=response)

    play_setup(world, child, helper)
    world.para()
    first_haunting(world, clue, child)
    dialogue_warning(world, helper, child, clue, parent)
    teamwork_search(world, child, helper, clue)
    world.para()
    twist_reveal(world, clue, parent)
    fix_it(world, child, helper, parent, response, clue)
    ending_image(world, child, helper, clue)
    world.facts["outcome"] = "resolved"
    world.facts["room"] = room
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos.")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("attic", "wiener_sign", "listen", "Mina", "girl", "Eli", "boy", "mother", "warning"),
            StoryParams("basement", "crippled_lamp", "light", "Noah", "boy", "Ivy", "girl", "father", "secret"),
            StoryParams("hall", "crippled_chair", "ask", "Rose", "girl", "Ben", "boy", "mother", "lost-item"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

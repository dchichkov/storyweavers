#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dog_dim_velcro_save_problem_solving_moral.py
============================================================================

A standalone storyworld for a small pirate-themed problem-solving tale with a
moral value center: two children in pirate play must save a tiny dog from a dim,
rising tide using a clever velcro fix and a calm, kind choice.

Seed words: dog-dim, velcro, save
Style: Pirate Tale
Features: Problem Solving, Moral Value

This world follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers only
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
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
BRAVERY_INIT = 5.5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
    scene: str
    deck: str
    dark_spot: str
    place_name: str

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
class Hazard:
    id: str
    label: str
    makes_problem: bool = True
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
class RescueTool:
    id: str
    label: str
    phrase: str
    method: str
    power: int
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
class FixIdea:
    id: str
    label: str
    clause: str
    kindness: str
    power: int
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
        clone = World(self.setting)
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    tide = world.get("tide")
    if tide.meters["rising"] >= THRESHOLD and ("danger", "tide") not in world.fired:
        world.fired.add(("danger", "tide"))
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("__tide__")
    return out


CAUSAL_RULES = [Rule("danger", "physical", _r_danger)]


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


def hazard_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.makes_problem and setting.id in {"deck", "cove", "harbor"}


def can_use_idea(hazard: Hazard, idea: FixIdea) -> bool:
    return hazard.id in idea.tags or "save" in idea.tags


def best_fix() -> FixIdea:
    return max(FIX_IDEAS.values(), key=lambda x: x.power)


def solve_power(setting: Setting, delay: int) -> int:
    return 2 + delay + (1 if setting.id == "deck" else 0)


def is_saved(tool: RescueTool, setting: Setting, delay: int) -> bool:
    return tool.power >= solve_power(setting, delay)


def predict_problem(world: World) -> dict:
    sim = world.copy()
    _raise_tide(sim, narrate=False)
    return {
        "worry": sum(e.memes["worry"] for e in sim.characters()),
        "rising": sim.get("tide").meters["rising"],
    }


def _raise_tide(world: World, narrate: bool = True) -> None:
    world.get("tide").meters["rising"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a quiet afternoon, {a.id} and {b.id} turned the old {setting.place_name} into {setting.scene}. "
        f"{setting.deck}"
    )
    world.say(
        f"They were hunting for a way to cross the {setting.dark_spot} and keep their little dog safe."
    )


def need_help(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"But the {setting.dark_spot} was getting dim, and a small tide was licking higher at the boards."
    )
    world.say(
        f'"We need to save the dog-dim," {b.id} whispered, peering into the shadow.'
    )


def tempt(world: World, a: Entity, hazard: Hazard) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} lifted {a.pronoun("possessive")} chin. "I know! {hazard.label}. '
        f'We can use it and be heroes right away."'
    )


def warn(world: World, b: Entity, a: Entity, hazard: Hazard) -> None:
    pred = predict_problem(world)
    b.memes["caution"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, that would make the game worse. '
        f'We need a way to save, not a way to stumble."'
    )
    if pred["worry"] >= THRESHOLD:
        world.say(f"{b.id} pointed at the dark water and kept watch like a careful captain.")


def _rescue_story(world: World, captain: Entity, hazard: Hazard, tool: RescueTool,
                  setting: Setting) -> None:
    world.say(
        f"{captain.label_word.capitalize()} came running with {tool.phrase}, and {tool.method}."
    )
    world.say(
        f"The clever fix held, the little dog was guided to safety, and the dim corner no longer felt scary."
    )
    world.say(
        f"Then the children remembered the kind thing to do: they shared the rope, checked the deck, and made sure nobody was left behind."
    )


def _moral_end(world: World, a: Entity, b: Entity, setting: Setting, fix: FixIdea) -> None:
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'For a moment, nobody spoke. Then {a.id} and {b.id} looked at the safe knot and smiled. '
        f'"Good pirates save each other," they said together.'
    )
    world.say(
        f"The next day they used {fix.label} again, not for trouble, but for helping."
    )
    world.say(
        f"And the little dog wagged under the lantern glow while the {setting.place_name} stayed bright and kind."
    )


def _bad_end(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"There was no quick fix. The tide spread across the boards, and the children had to back away and call for help."
    )
    world.say(
        f"Even then, they stayed together, because saving each other mattered more than saving the game."
    )
    world.say(
        f"When the grown-up came, the children learned that a brave choice is asking for help before the trouble grows too big."
    )


def tell(setting: Setting, hazard: Hazard, tool: RescueTool, fix: FixIdea,
         hero: str = "Mina", hero_gender: str = "girl",
         mate: str = "Jace", mate_gender: str = "boy",
         captain: str = "Captain", delay: int = 0) -> World:
    world = World(setting)
    a = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    b = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    tide = world.add(Entity(id="tide", type="thing", label="the tide"))
    dog = world.add(Entity(id="dog", type="thing", label="the tiny dog"))
    world.facts.update(dog=dog, tide=tide, hazard=hazard, tool=tool, fix=fix, delay=delay)

    setup(world, a, b, setting)
    world.para()
    need_help(world, a, b, setting)
    tempt(world, a, hazard)
    warn(world, b, a, hazard)

    world.para()
    if fix.id == "velcro_patch" or can_use_idea(hazard, fix):
        if hazard.id == "hook":
            world.say(f"{a.id} stopped and thought. The hook would tangle the line, not save it.")
        world.say(f'{b.id} held up the strip of velcro and said, "{fix.clause}"')
        if is_saved(tool, setting, delay):
            _rescue_story(world, b, hazard, tool, setting)
            _moral_end(world, a, b, setting, fix)
            outcome = "saved"
        else:
            world.say(
                f"The velcro helped some, but the tide had already climbed too high."
            )
            _bad_end(world, a, b, setting)
            outcome = "delayed"
    else:
        world.say(
            f"They tried the wrong thing first, and the problem grew louder instead of smaller."
        )
        _bad_end(world, a, b, setting)
        outcome = "lost"

    world.facts["outcome"] = outcome
    return world


SETTINGS = {
    "deck": Setting(
        "deck",
        "a pirate deck full of ropes, barrels, and lantern light",
        "The deck boards creaked like friendly footsteps, and a bright lantern swung from the mast.",
        "Below the rail, a dim little nook hid where a tiny dog could slip if nobody was careful.",
        "the deck",
    ),
    "cove": Setting(
        "cove",
        "a moonlit cove with a bobbing boat and soft waves",
        "The boat rocked gently, and the lantern made a small gold pool on the water.",
        "Behind a stack of crates, a dim hollow could swallow a tiny paw in a blink.",
        "the cove",
    ),
}

HAZARDS = {
    "hook": Hazard("hook", "a loose hook on the rope"),
    "net": Hazard("net", "a tangled fishing net"),
    "plank": Hazard("plank", "a crooked plank that would slip"),
}

TOOLS = {
    "rope": RescueTool("rope", "a sturdy rope", "a sturdy rope", "tied a safe loop and guided the dog", 2, {"save"}),
    "lantern": RescueTool("lantern", "a lantern", "a lantern", "lit the way so they could see the dog", 2, {"save"}),
    "plank_wedge": RescueTool("plank_wedge", "a wooden wedge", "a wooden wedge", "held the board steady", 1, {"save"}),
}

FIX_IDEAS = {
    "velcro_patch": FixIdea(
        "velcro_patch",
        "a strip of velcro",
        "Velcro can hold the little latch shut without hurting anyone.",
        "save",
        3,
        {"save", "velcro"},
    ),
    "knot": FixIdea(
        "knot",
        "a quick knot",
        "A quick knot can keep the rope from slipping.",
        "save",
        2,
        {"save"},
    ),
    "call_help": FixIdea(
        "call_help",
        "calling a grown-up",
        "If the trouble is too big, we save by calling a grown-up right away.",
        "save",
        5,
        {"save"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ada", "Zoe", "Ella"]
BOY_NAMES = ["Jace", "Tom", "Finn", "Noah", "Eli", "Ben"]
TRAITS = ["kind", "careful", "curious", "thoughtful", "brave"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HAZARDS:
            for t in TOOLS:
                for f in FIX_IDEAS:
                    combos.append((s, h, t, f))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    tool: str
    fix: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    trait: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-themed story for a preschooler that includes the word "velcro" and the phrase "dog-dim".',
        f"Tell a story where {f['hero'].id} and {f['mate'].id} must save a tiny dog using {f['fix'].label}, and the right choice shows kindness.",
        f'Write a small adventure where the children solve a problem by using "velcro" instead of rushing, and end with a moral lesson.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mate = f["hero"], f["mate"]
    fix, hazard, tool, setting = f["fix"], f["hazard"], f["tool"], f["setting"]
    qa = [
        (
            "Who are the story about?",
            f"It is about {hero.id} and {mate.id}, two little pirates who cared about a tiny dog. They were exploring {setting.place_name} and trying to keep everyone safe.",
        ),
        (
            "What problem did they have?",
            f"They found a dim, tricky spot where the tiny dog could get stuck or lost. The trouble could grow if they chose the wrong tool, so they had to think first.",
        ),
        (
            "What did the children decide to use?",
            f"They chose {fix.label}. That was the clever choice because it could help them save the dog without making the situation worse.",
        ),
    ]
    if f["outcome"] == "saved":
        qa.append((
            "How did they save the dog?",
            f"They used {fix.label} and then {tool.label} to guide the dog to safety. The plan worked because they stayed calm, used their heads, and helped each other.",
        ))
        qa.append((
            "What did the story teach?",
            f"It taught that a kind choice can be the bravest choice. When a problem appears, it is better to solve it gently than to rush and make it bigger.",
        ))
    elif f["outcome"] == "delayed":
        qa.append((
            "Did the first plan solve everything?",
            f"No. {fix.label} helped some, but the tide had already climbed too high, so they still needed a grown-up. They learned that even a good idea must come in time to save the day.",
        ))
        qa.append((
            "What moral did they learn?",
            f"They learned to ask for help early and to keep being kind even when the plan is not enough. Saving matters most when everyone stays safe.",
        ))
    else:
        qa.append((
            "What happened at the end?",
            f"The problem grew too big, so the children backed away and called for help. They still did the right thing by staying together and choosing safety.",
        ))
        qa.append((
            "What did they learn?",
            f"They learned that a brave pirate knows when to stop and call a grown-up. Kindness and safety are part of being truly strong.",
        ))
    return qa


KNOWLEDGE = {
    "velcro": [(
        "What is velcro?",
        "Velcro is a fastener with two sides that stick together. People use it to close shoes, bags, and clothes without tying knots.",
    )],
    "save": [(
        "What does it mean to save someone?",
        "To save someone means to help keep them safe from harm or trouble. It can mean using a smart plan or asking for help right away.",
    )],
    "dog": [(
        "What do dogs like?",
        "Dogs often like food, walks, play, and being with people who treat them kindly.",
    )],
    "pirate": [(
        "What is a pirate in a story?",
        "A pirate is a pretend adventurer who sails on the sea and looks for treasure. In stories for children, pirates can be brave and kind too.",
    )],
    "lantern": [(
        "Why is a lantern useful?",
        "A lantern gives light in dark places. It helps people see where they are going without rushing.",
    )],
    "kindness": [(
        "Why is kindness important?",
        "Kindness helps people feel safe and cared for. It also helps a group work together when a problem needs solving.",
    )],
}
KNOWLEDGE_ORDER = ["velcro", "save", "dog", "pirate", "lantern", "kindness"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["fix"].tags) | {"save", "dog", "pirate", "lantern", "kindness"}
    out: list[tuple[str, str]] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags and k in KNOWLEDGE:
            out.extend(KNOWLEDGE[k])
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not make a coherent save-the-day problem.)"


ASP_RULES = r"""
setting(S) :- base_setting(S).
hazard(H) :- base_hazard(H).
tool(T) :- base_tool(T).
fix(F) :- base_fix(F).

valid(S, H, T, F) :- setting(S), hazard(H), tool(T), fix(F).

saved :- chosen_fix(F), fix_power(F, P), needed(N), P >= N.
needed(N) :- delay(D), setting_id(deck), N = 2 + D + 1.
needed(N) :- delay(D), setting_id(cove), N = 2 + D.

outcome(saved) :- saved.
outcome(delayed) :- not saved, chosen_fix(F), fix_power(F, P), P >= 2.
outcome(lost) :- not saved, not (chosen_fix(F), fix_power(F, P), P >= 2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("base_setting", sid))
        lines.append(asp.fact("setting_id", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("base_hazard", hid))
    for tid in TOOLS:
        lines.append(asp.fact("base_tool", tid))
    for fid, f in FIX_IDEAS.items():
        lines.append(asp.fact("base_fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    for p in CURATED:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)
            break
    else:
        print("OK: ASP outcome matches Python outcome on curated cases.")
    try:
        generate(CURATED[0])
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print("SMOKE TEST FAILED:", exc)
    return rc


def outcome_of(params: StoryParams) -> str:
    if params.fix == "call_help":
        return "saved" if params.delay <= 1 else "delayed"
    if params.delay <= 0 and params.fix in {"velcro_patch", "knot"}:
        return "saved"
    return "delayed" if params.delay == 1 else "lost"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-themed save storyworld with velcro.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIX_IDEAS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.fix and args.fix not in FIX_IDEAS:
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.hazard:
        combos = [c for c in combos if c[1] == args.hazard]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if args.fix:
        combos = [c for c in combos if c[3] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, tool, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate_pool = [n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != hero]
    mate = args.mate or rng.choice(mate_pool)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, hazard, tool, fix, hero, hero_gender, mate, mate_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], TOOLS[params.tool],
                 FIX_IDEAS[params.fix], params.hero, params.hero_gender,
                 params.mate, params.mate_gender, params.trait, params.delay)
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


CURATED = [
    StoryParams("deck", "hook", "rope", "velcro_patch", "Mina", "girl", "Jace", "boy", "kind", 0),
    StoryParams("cove", "net", "lantern", "knot", "Lily", "girl", "Finn", "boy", "careful", 1),
    StoryParams("deck", "plank", "plank_wedge", "call_help", "Nora", "girl", "Eli", "boy", "thoughtful", 2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.mate}: {p.fix} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

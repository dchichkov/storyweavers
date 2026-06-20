#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/guardian_dine_quest_rhyme_bad_ending_superhero.py
=================================================================================

A small superhero-themed story world built from the seed words *guardian* and
*dine*, with the instruments *Quest*, *Rhyme*, and *Bad Ending*.

Premise:
- A child superhero and a guardian hero set out on a quest to reach a dinner
  place before the evening gets too late.
- They try to solve problems with brave, rhyming lines and helpful gadgets.
- The turn comes when the path is blocked and the hero makes a risky choice.
- The ending is bad: the meal is missed, the quest fails, and the guardian must
  rescue the child and bring them home tired and disappointed.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chaining causal model
- grounded QA generated from world state, not rendered English
- a Python reasonableness gate plus an inline ASP twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
BRAVERY_BASE = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    quest_goal: str
    place_detail: str
    dinner_spot: str
    time_pressure: str
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
class Villain:
    id: str
    label: str
    block: str
    trouble: str
    danger: int
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
class HelpTool:
    id: str
    label: str
    glow: str
    strength: int
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["trouble"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        for other in world.characters():
            if other.id != e.id:
                other.memes["worry"] += 0.5
        out.append("__fear__")
    return out


def _r_lost_meal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("meal_lost"):
        sig = ("lostmeal",)
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.characters():
                e.memes["sad"] += 1
            out.append("__sad__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("lost_meal", "social", _r_lost_meal)]


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


def hazard_at_risk(villain: Villain, setting: Setting) -> bool:
    return villain.danger >= 1 and setting.id in {"city", "bridge", "alley", "harbor"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, villain: Villain) -> bool:
    return response.power >= villain.danger


def predict_badness(world: World, villain_id: str) -> dict:
    sim = world.copy()
    _do_block(sim, sim.get(villain_id), narrate=False)
    return {
        "trouble": sim.get("hero").meters["trouble"],
        "meal_lost": sim.facts.get("meal_lost", False),
    }


def _do_block(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["trouble"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, guardian: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    guardian.memes["calm"] += 1
    world.say(
        f"On a bright evening, {hero.id} and {guardian.id} watched the city shine. "
        f"{hero.id} was a small hero with a big cape, and {guardian.id} was the guardian who knew every safe street."
    )
    world.say(
        f"They had one important quest: reach {setting.dinner_spot} before the night got too late, so they could dine together in peace."
    )


def quest_call(world: World, hero: Entity, setting: Setting, tool: HelpTool) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"Quest time!" {hero.id} said. {hero.pronoun().capitalize()} held up {tool.label}, '
        f'which {tool.glow}, and pointed toward {setting.place}.'
    )
    world.say(
        f'The path to {setting.quest_goal} looked tricky, but the glowing tool made the route feel like a true superhero mission.'
    )


def rhyme_warning(world: World, guardian: Entity, hero: Entity, villain: Villain, setting: Setting) -> None:
    hero.memes["hope"] += 1
    guardian.memes["alert"] += 1
    pred = predict_badness(world, "villain")
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{guardian.id} frowned and spoke in a rhyme: "No fast dash, no splashy crash; {villain.block} can slow the rush."'
    )
    world.say(
        f'{guardian.id} added, "If we stay careful, we can still dine on time at {setting.dinner_spot}."'
    )


def defy(world: World, hero: Entity, villain: Villain) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I can beat it!" {hero.id} said, and {hero.pronoun()} raced ahead anyway.'
    )


def battle(world: World, hero: Entity, guardian: Entity, villain: Villain) -> None:
    _do_block(world, world.get("villain"))
    world.say(
        f'But the {villain.label} burst from the shadows, and {villain.block}. '
        f"The obstacle was bigger than {hero.id}'s first plan."
    )
    world.say(f'"{hero.id}!" {guardian.id} shouted, rushing after {hero.id}."')


def bad_ending(world: World, hero: Entity, guardian: Entity, villain: Villain, setting: Setting) -> None:
    world.facts["meal_lost"] = True
    propagate(world, narrate=False)
    hero.memes["sad"] += 1
    guardian.memes["sad"] += 1
    world.say(
        f"{guardian.id} caught up, but the way to {setting.dinner_spot} was already closed. "
        f"Their dinner was missed, and the city lights turned lonely and cold."
    )
    world.say(
        f"They went home tired and quiet, while the {villain.label} kept the night stuck in place."
    )


def lesson(world: World, guardian: Entity, hero: Entity) -> None:
    guardian.memes["love"] += 1
    hero.memes["love"] += 1
    world.say(
        f"At home, {guardian.id} wrapped {hero.id} in a hug and said, "
        f'"A real hero listens, slows down, and asks for help before the trouble grows."'
    )
    world.say(
        f"{hero.id} nodded, still brave but now much wiser."
    )


def tell(setting: Setting, villain: Villain, tool: HelpTool, response: Response,
         hero_name: str = "Nova", hero_gender: str = "girl",
         guardian_name: str = "Milo", guardian_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_gender, role="guardian"))
    world.add(Entity(id="villain", kind="thing", type="villain", label=villain.label))
    intro(world, hero, guardian, setting)
    world.para()
    quest_call(world, hero, setting, tool)
    rhyme_warning(world, guardian, hero, villain, setting)
    if not hazard_at_risk(villain, setting):
        raise StoryError("(No story: the chosen setting does not make the quest feel risky enough.)")
    defy(world, hero, villain)
    world.para()
    battle(world, hero, guardian, villain)
    if is_contained(response, villain):
        # This world is defined to end badly; even if a response could work, the
        # chosen story arc still loses because the delay is too long.
        world.facts["meal_lost"] = True
    bad_ending(world, hero, guardian, villain, setting)
    lesson(world, guardian, hero)
    world.facts.update(
        hero=hero, guardian=guardian, setting=setting, villain=villain,
        tool=tool, response=response, outcome="bad"
    )
    return world


SETTINGS = {
    "city": Setting("city", "Star City", "Moonrise Diner", "The streets were bright with windows and neon", "Moonrise Diner", "the clock was ticking", {"city"}),
    "harbor": Setting("harbor", "Harbor Row", "Harbor Diner", "The docks smelled like salt and old rope", "Harbor Diner", "the tide was turning", {"harbor"}),
    "bridge": Setting("bridge", "Gleam Bridge", "Skyline Diner", "The bridge lamps were glowing one by one", "Skyline Diner", "the last bus was nearly gone", {"bridge"}),
}

VILLAINS = {
    "fog": Villain("fog", "fog monster", "covered the street in thick gray mist", "hid the diner signs", 2, {"city", "harbor", "bridge"}),
    "blocks": Villain("blocks", "block wall", "locked the alley with a falling stack of crates", "blocked the short path", 2, {"harbor", "city"}),
    "storm": Villain("storm", "storm cloud", "brought a crackling thundercloud overhead", "slowed every step", 3, {"bridge", "city"}),
}

TOOLS = {
    "beam": HelpTool("beam", "a beam lantern", "shone like a tiny sun", 2, {"light"}),
    "map": HelpTool("map", "a silver map", "glimmered with a street glow", 1, {"map"}),
    "radio": HelpTool("radio", "a pocket radio", "clicked with brave music", 1, {"music"}),
}

RESPONSES = {
    "dash": Response("dash", 1, 1, "raced down the street too fast to notice the turn", "raced ahead, but the night swallowed the path", "raced down the street", {"fast"}),
    "shield": Response("shield", 3, 3, "raised a shining shield and pushed through the trouble", "raised a shield, but it was too late", "raised a shining shield", {"shield"}),
    "hover": Response("hover", 2, 2, "floated above the trouble and kept going", "floated, but the path stayed blocked", "floated above the trouble", {"hover"}),
}

GIRL_NAMES = ["Nova", "Mira", "Zia", "Luna", "Ari"]
BOY_NAMES = ["Milo", "Jett", "Arlo", "Finn", "Toby"]
TRAITS = ["brave", "quick", "curious", "kind", "bold"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    villain: str
    tool: str
    response: str
    hero_name: str
    hero_gender: str
    guardian_name: str
    guardian_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for vid, villain in VILLAINS.items():
            if not hazard_at_risk(villain, setting):
                continue
            for tid in TOOLS:
                combos.append((sid, vid, tid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guardian, setting, villain, tool = f["hero"], f["guardian"], f["setting"], f["villain"], f["tool"]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "guardian" and "dine".',
        f"Tell a Quest story where {hero.id} and {guardian.id} try to reach {setting.dinner_spot}, but {villain.label} blocks the way and the guardian speaks in a rhyme.",
        f"Write a Bad Ending superhero story where a brave child ignores a guardian's warning, the dinner is missed, and the hero goes home sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guardian, setting, villain = f["hero"], f["guardian"], f["setting"], f["villain"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {guardian.id}, a child hero and a guardian hero. They set out together on a quest to dine at {setting.dinner_spot}."
        ),
        QAItem(
            question="What was the quest?",
            answer=f"The quest was to get to {setting.dinner_spot} in time for dinner. They wanted to dine there before the night got too late."
        ),
        QAItem(
            question=f"What did {guardian.id} say in a rhyme?",
            answer=f"{guardian.id} warned that they should not rush into {villain.block}. The rhyme was a calm way to slow the quest down and keep everyone safe."
        ),
        QAItem(
            question="Why did the story end badly?",
            answer=f"It ended badly because {hero.id} rushed ahead and the path stayed blocked. They missed dinner, and the quest did not reach a happy ending."
        ),
    ]
    if f.get("meal_lost"):
        qa.append(QAItem(
            question="What changed by the end?",
            answer="The heroes did not get to dine together, and the night felt heavy instead of cheerful. The guardian brought the child home, but the missed meal made the ending sad."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["villain"].tags) | set(f["tool"].tags)
    return [
        QAItem("What is a guardian?", "A guardian is someone who protects and watches over another person. In a superhero story, a guardian helps keep a child safe."),
        QAItem("What does dine mean?", "To dine means to eat a meal. It is a grown-up sounding word for sitting down to eat together."),
        QAItem("What is a quest?", "A quest is a mission or journey to reach an important goal. Superheroes often go on quests to help someone or find something."),
        QAItem("Why can a blocked street cause trouble?", "If the road is blocked, it takes longer to reach the destination. That can make a careful plan fail or make people late."),
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


CURATED = [
    StoryParams("city", "storm", "beam", "shield", "Nova", "girl", "Milo", "boy", "brave"),
    StoryParams("harbor", "blocks", "map", "hover", "Ari", "girl", "Jett", "boy", "curious"),
    StoryParams("bridge", "fog", "radio", "dash", "Milo", "boy", "Nova", "girl", "kind"),
]


def explain_rejection(villain: Villain, setting: Setting) -> str:
    return f"(No story: {villain.label} does not make the quest feel plausible in {setting.place}.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazard(V, S) :- villain(V), setting(S), risky(V, S).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
bad_ending :- hazard(_, _), chosen_response(R), response(R), not rescue_ok(R).
rescue_ok(R) :- response(R), power(R, P), danger(V, D), P >= D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("dinner_spot", sid, s.dinner_spot.replace(" ", "_")))
    for vid, v in VILLAINS.items():
        lines.append(asp.fact("villain", vid))
        lines.append(asp.fact("danger", vid, v.danger))
        for t in sorted(v.tags):
            lines.append(asp.fact("risky", vid, t))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    if not any(v for v in VILLAINS.values()):
        rc = 1
    cases = [CURATED[0]]
    for p in cases:
        try:
            _ = generate(p)
        except Exception as e:
            print(f"SMOKE FAIL: {e}")
            return 1
    print("OK: smoke generate passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero quest storyworld with a guardian, a dine goal, rhyme, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian-name")
    ap.add_argument("--guardian-gender", choices=["girl", "boy"])
    ap.add_argument("--trait")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.villain is None or c[1] == args.villain)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, villain, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guardian_gender = args.guardian_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    guardian_name = args.guardian_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, villain, tool, response, hero_name, hero_gender, guardian_name, guardian_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], VILLAINS[params.villain], TOOLS[params.tool], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.guardian_name, params.guardian_gender)
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
        print(asp_program(show="#show sensible/1.\n#show hazard/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

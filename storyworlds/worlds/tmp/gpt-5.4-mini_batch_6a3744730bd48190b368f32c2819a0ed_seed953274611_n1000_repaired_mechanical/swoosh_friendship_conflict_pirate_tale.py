#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swoosh_friendship_conflict_pirate_tale.py
========================================================================

A standalone storyworld about pirate friends, a sudden conflict, and a soft
resolution that keeps the adventure going. The seed word "swoosh" is woven
into the motion of a sail, rope, or wave, and the world stays small enough for
TinyStories-style narration.

The domain:
- Two pirate friends are sailing a little boat.
- One wants a risky shortcut to find treasure.
- The other warns about a reef, a cranky gull, or a slippery deck.
- A conflict happens when the first child ignores the warning.
- A calm grown-up or friendly captain helps repair the problem.
- The friends finish with a safer plan and a strong image of friendship.

This script follows the storyworld contract:
- typed entities with physical meters and emotional memes
- a reasonableness gate plus inline ASP twin
- story-grounded and world-knowledge QA from world state, not rendered text
- standard CLI flags including --verify, --asp, and --show-asp
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
FRIENDSHIP_MIN = 1
CONFLICT_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    ship_title: str
    helper_title: str
    goal: str
    dark_place: str
    send_off: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    makes_mess: bool = True
    risky: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    severity: int
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Repair:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_conflict(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.memes["tension"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= REPAIR_SENSE_MIN]


def valid_combo(theme: Theme, risk: Risk, trouble: Trouble, repair: Repair) -> bool:
    return risk.risky and trouble.severity >= 1 and repair.sense >= REPAIR_SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for t in THEMES:
        for r in RISKS:
            for tr in TROUBLES:
                for rp in REPAIRS:
                    if valid_combo(THEMES[t], RISKS[r], TROUBLES[tr], REPAIRS[rp]):
                        combos.append((t, r, tr, rp))
    return combos


def choice_name(rng: random.Random, names: list[str], avoid: str = "") -> str:
    pool = [n for n in names if n != avoid]
    return rng.choice(pool)


def predict_conflict(world: World, risk_id: str, trouble_id: str) -> dict:
    sim = world.copy()
    _risk_event(sim, sim.get("risk"), RISKS[risk_id], narrate=False)
    return {
        "mess": sim.get("deck").meters["mess"],
        "tension": sim.get("friend_a").memes["tension"] + sim.get("friend_b").memes["tension"],
    }


def _risk_event(world: World, actor: Entity, risk: Risk, narrate: bool = True) -> None:
    actor.meters["motion"] += 1
    actor.meters["mess"] += 1 if risk.makes_mess else 0
    propagate(world, narrate=narrate)


def sail_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"On a bright day, {a.id} and {b.id} turned their little boat into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.ship_title} {a.id}!" {a.id} shouted. '
        f'"{theme.helper_title} {b.id}!" {b.id} laughed back. '
        f'Together they wanted to find {theme.goal}.'
    )


def breeze(world: World, theme: Theme, trouble: Trouble) -> None:
    world.say(
        f"A salt breeze went {trouble.phrase} past {theme.dark_place}, and the boat creaked softly."
    )


def warning(world: World, helper: Entity, actor: Entity, risk: Risk) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} pointed ahead. "Wait," {helper.pronoun()} said. '
        f'"That {risk.label} is not a toy for a pirate game."'
    )


def defy(world: World, actor: Entity, helper: Entity, risk: Risk) -> None:
    actor.memes["boldness"] += 1
    actor.memes["tension"] += 1
    world.say(
        f'"I can do it myself," {actor.id} said, and the rope went {risk.phrase} with a quick swoosh.'
    )


def clash(world: World, actor: Entity, helper: Entity, trouble: Trouble) -> None:
    actor.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f'But the move only made things worse. The deck slid, the {trouble.label} caused a stir, '
        f'and {actor.id} and {helper.id} ended up in a small argument.'
    )


def calm_fix(world: World, adult: Entity, repair: Repair, trouble: Trouble) -> None:
    world.say(
        f"{adult.label_word.capitalize()} came over, smiled, and {repair.text.replace('{trouble}', trouble.label)}."
    )


def lesson(world: World, adult: Entity, a: Entity, b: Entity) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    a.memes["conflict"] = 0
    b.memes["conflict"] = 0
    world.say(
        f'"Friends do not have to agree on every wave," {adult.label_word} said. '
        f'"They just have to listen and keep each other safe."'
    )
    world.say(f"{a.id} and {b.id} nodded, and their shoulders relaxed at once.")


def safe_finish(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"After that, {a.id} and {b.id} used a slower plan and found {theme.goal} together. "
        f"The boat rocked gently, and the sea made a happy swoosh against the side."
    )
    world.say(
        f"By sunset, the two friends were side by side again, with a better map and a brighter grin."
    )


def tell(theme: Theme, risk: Risk, trouble: Trouble, repair: Repair,
         a_name: str = "Milo", a_gender: str = "boy",
         b_name: str = "Nia", b_gender: str = "girl",
         adult_type: str = "captain") -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend_a"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend_b"))
    adult = world.add(Entity(id="Captain", kind="character", type=adult_type, label="the captain"))
    deck = world.add(Entity(id="deck", type="place", label="the deck"))
    world.facts["risk"] = risk.id
    world.facts["trouble"] = trouble.id
    world.facts["repair"] = repair.id

    sail_setup(world, a, b, theme)
    world.para()
    breeze(world, theme, trouble)
    warning(world, b, a, risk)
    world.say(f"{a.id} did not want to stop, because the adventure felt too exciting.")

    world.para()
    defy(world, a, b, risk)
    _risk_event(world, a, risk, narrate=True)
    clash(world, a, b, trouble)

    world.para()
    calm_fix(world, adult, repair, trouble)
    lesson(world, adult, a, b)
    world.para()
    safe_finish(world, a, b, theme)

    world.facts.update(
        friend_a=a, friend_b=b, adult=adult, theme=theme, risk_cfg=risk, trouble_cfg=trouble,
        repair_cfg=repair, conflict=a.memes["conflict"] >= THRESHOLD or b.memes["conflict"] >= THRESHOLD,
        friendship=a.memes["friendship"] + b.memes["friendship"],
    )
    return world


THEMES = {
    "pirate_tale": Theme(
        id="pirate_tale",
        scene="a pirate ship",
        rig="The sail was high, the mast was tall, and a blue flag snapped in the wind.",
        ship_title="Captain",
        helper_title="Mate",
        goal="the hidden cove",
        dark_place="the foggy rocks",
        send_off="sailed on",
    )
}

RISKS = {
    "rope": Risk(id="rope", label="rope", phrase="around the mast", makes_mess=True, risky=True),
    "sail": Risk(id="sail", label="sail", phrase="with a wild tug", makes_mess=True, risky=True),
    "bell": Risk(id="bell", label="deck bell", phrase="with a loud clang", makes_mess=True, risky=True),
}

TROUBLES = {
    "reef": Trouble(id="reef", label="reef", phrase="around the reef", severity=2),
    "gull": Trouble(id="gull", label="gull", phrase="over the gulls", severity=1),
    "fog": Trouble(id="fog", label="fog bank", phrase="through the fog bank", severity=2),
}

REPAIRS = {
    "chart": Repair(id="chart", sense=3, power=3,
                    text="held up a better chart and pointed the boat away from the reef",
                    fail="tried to use a torn chart, but the boat still bumped the reef",
                    qa_text="held up a better chart and pointed the boat away from the reef"),
    "anchor": Repair(id="anchor", sense=3, power=2,
                     text="dropped the anchor and waited for the water to settle",
                     fail="dropped the anchor too late, and the boat still drifted sideways",
                     qa_text="dropped the anchor and waited for the water to settle"),
    "apology": Repair(id="apology", sense=2, power=1,
                      text="brought them both together and let the two friends talk it out",
                      fail="asked for a quick apology, but nobody was ready yet",
                      qa_text="brought them both together and let the two friends talk it out"),
}

REPAIR_SENSE_MIN = 2
GIRL_NAMES = ["Nia", "Luna", "Mara", "Tess", "Pip"]
BOY_NAMES = ["Milo", "Jace", "Rory", "Ben", "Toby"]


@dataclass
class StoryParams:
    theme: str
    risk: str
    trouble: str
    repair: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    adult_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(theme="pirate_tale", risk="rope", trouble="reef", repair="chart",
                friend_a="Milo", friend_a_gender="boy", friend_b="Nia", friend_b_gender="girl",
                adult_type="captain"),
    StoryParams(theme="pirate_tale", risk="sail", trouble="fog", repair="anchor",
                friend_a="Toby", friend_a_gender="boy", friend_b="Mara", friend_b_gender="girl",
                adult_type="captain"),
    StoryParams(theme="pirate_tale", risk="bell", trouble="gull", repair="apology",
                friend_a="Luna", friend_a_gender="girl", friend_b="Rory", friend_b_gender="boy",
                adult_type="captain"),
]


def explain_rejection(risk: Risk, trouble: Trouble) -> str:
    return f"(No story: that pirate problem is too weak to make a real conflict.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate friendship story that includes the word "swoosh" and a small conflict between {f["friend_a"].id} and {f["friend_b"].id}.',
        f"Tell a child-friendly pirate tale where {f['friend_b'].id} warns about {f['risk_cfg'].label}, but the first friend ignores the warning and conflict follows.",
        f'Write a story about pirate friends who argue, listen, and end up safer together, with a sea-side swoosh in the ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["friend_a"], f["friend_b"]
    repair = f["repair_cfg"]
    qa = [
        ("Who are the story about?",
         f"It is about two pirate friends, {a.id} and {b.id}. They start as teammates, then have a small conflict, and end by helping each other again."),
        ("What caused the conflict?",
         f"The conflict began when {a.id} ignored {b.id}'s warning about {f['risk_cfg'].label}. The risky move stirred up trouble near {f['trouble_cfg'].label}."),
        ("How did they fix the problem?",
         f"They calmed down with help from {f['adult'].label_word} and used a safer plan. {repair.qa_text.capitalize()}."),
        ("How did the story end?",
         f"It ended with the two friends side by side on the boat, feeling closer and safer. The last image is a gentle swoosh of water and a better map."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pirate ship?", "A pirate ship is a boat that sails on the sea. In stories, pirates use it for adventures and treasure hunts."),
        ("What does swoosh mean?", "Swoosh is a word for a smooth rushing sound, like a sail in the wind or water sliding past a boat."),
        ("Why is it good to listen to a friend?", "Listening can stop mistakes before they turn into bigger trouble. Friends keep each other safer when they pay attention."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict(Friend) :- tension(Friend).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if r.risky:
            lines.append(asp.fact("risky", rid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for rid, r in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("repair_min", REPAIR_SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate friendship conflict storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    theme = args.theme or rng.choice(list(THEMES))
    risk = args.risk or rng.choice(list(RISKS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    repair = args.repair or rng.choice(list(REPAIRS))
    if REPAIRS[repair].sense < REPAIR_SENSE_MIN:
        raise StoryError("repair too weak")
    a_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = choice_name(rng, GIRL_NAMES + BOY_NAMES, avoid=a_name)
    a_gender = "girl" if a_name in GIRL_NAMES else "boy"
    b_gender = "girl" if b_name in GIRL_NAMES else "boy"
    return StoryParams(
        theme=theme,
        risk=risk,
        trouble=trouble,
        repair=repair,
        friend_a=a_name,
        friend_a_gender=a_gender,
        friend_b=b_name,
        friend_b_gender=b_gender,
        adult_type="captain",
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.risk not in RISKS or params.trouble not in TROUBLES or params.repair not in REPAIRS:
        raise StoryError("invalid parameters")
    world = tell(THEMES[params.theme], RISKS[params.risk], TROUBLES[params.trouble], REPAIRS[params.repair],
                 params.friend_a, params.friend_a_gender, params.friend_b, params.friend_b_gender, params.adult_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode not elaborated for this tiny world.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

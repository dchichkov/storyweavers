#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/appearance_discriminate_reconciliation_curiosity_twist_ghost_story.py
======================================================================================================

A small ghost-story storyworld about a child, a shy ghost, a mistaken judgment
about appearances, a curious investigation, a twist, and a reconciliation.

The domain is intentionally tiny:
- A child explores an old house.
- They discriminate incorrectly at first, judging the ghost by appearance.
- Curiosity reveals the twist: the "ghost" is protecting a hidden friendhood,
  memory, or misread signal rather than causing harm.
- A calm reconciliation follows, and the final image shows the changed state.

This script follows the Storyweavers storyworld contract:
- stdlib-only prose engine
- typed entities with meters and memes
- Python reasonableness gate plus inline ASP twin
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA grounded in the simulated world state, not by parsing rendered prose
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
BRAVERY_INIT = 4.0
CURIOSITY_INIT = 3.0


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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    detail: str
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
class Haunting:
    id: str
    appearance: str
    misread: str
    clue: str
    twist: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Truth:
    id: str
    reveal: str
    peace: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    setting: str
    haunting: str
    truth: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.meters["seen"] < THRESHOLD or ("fear",) in world.fired:
        return out
    world.fired.add(("fear",))
    child.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("reconciled") and ("soften",) not in world.fired:
        world.fired.add(("soften",))
        child = world.entities.get("child")
        ghost = world.entities.get("ghost")
        if child:
            child.memes["fear"] = 0.0
            child.memes["trust"] += 1
        if ghost:
            ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1.0)
            ghost.memes["peace"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def should_misjudge(haunting: Haunting) -> bool:
    return "gloom" in haunting.tags or "appearance" in haunting.tags


def curiosity_can_probe(child: Entity) -> bool:
    return child.memes["curiosity"] >= CURIOSITY_INIT


def is_reasonable(setting: Setting, haunting: Haunting, truth: Truth) -> bool:
    return bool(setting.place and haunting.appearance and truth.reveal)


def _do_ghost(world: World, narrate: bool = True) -> None:
    ghost = world.get("ghost")
    ghost.meters["seen"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a fog-soft evening, {child.id} and {helper.id} walked into {setting.place}. "
        f"{setting.detail} The house felt {setting.mood}."
    )


def first_look(world: World, child: Entity, haunting: Haunting) -> None:
    world.say(
        f"In the hall, a pale shape drifted by the stairs. {haunting.appearance} "
        f"At first, {child.id} wanted to discriminate by appearances and call it mean."
    )
    child.memes["suspicion"] += 1


def warning(world: World, helper: Entity, child: Entity, haunting: Haunting) -> None:
    world.say(
        f'{helper.id} squeezed {child.pronoun("possessive")} hand. "{haunting.misread}," '
        f"{helper.id} whispered, \"but let's look closer before we decide.\""
    )


def investigate(world: World, child: Entity, haunting: Haunting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} took a careful step forward anyway. {child.pronoun().capitalize()} "
        f"followed the little sound and noticed {haunting.clue}."
    )


def reveal_twist(world: World, haunting: Haunting, truth: Truth) -> None:
    ghost = world.get("ghost")
    ghost.meters["seen"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f"Then the twist came clear: {haunting.twist} {truth.reveal} "
        f"The pale shape was not trying to scare anyone away."
    )


def reconcile(world: World, child: Entity, helper: Entity, haunting: Haunting, truth: Truth) -> None:
    world.facts["reconciled"] = True
    child.memes["guilt"] += 1
    child.memes["understanding"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"{child.id} lowered {child.pronoun('possessive')} eyes and said sorry for jumping to "
        f"the wrong conclusion. {helper.id} nodded, and together they listened to the ghost."
    )
    world.say(
        f"{truth.peace} The room felt less cold, and the long hallway stopped seeming so lonely."
    )


def ending(world: World, child: Entity, helper: Entity, truth: Truth) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    ghost = world.get("ghost")
    ghost.memes["peace"] += 1
    world.say(
        f"{truth.ending_image} In the final light, {child.id} and {helper.id} left the hall "
        f"with gentler hearts, and the ghost no longer looked frightening."
    )


def tell(setting: Setting, haunting: Haunting, truth: Truth,
         child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ghost = world.add(Entity(id="ghost", kind="character", type="thing", label="the ghost", role="ghost"))
    child.memes["curiosity"] = CURIOSITY_INIT
    child.memes["bravery"] = BRAVERY_INIT
    helper.memes["calm"] = 1.0
    ghost.memes["lonely"] = 1.0

    set_scene(world, child, helper, setting)
    world.para()
    first_look(world, child, haunting)
    warning(world, helper, child, haunting)
    if should_misjudge(haunting):
        _do_ghost(world, narrate=False)
        investigate(world, child, haunting)
    else:
        child.memes["curiosity"] += 2
        world.say(f"{child.id} did not want to be fooled by a guess, so {child.pronoun()} looked closer.")
    world.para()
    reveal_twist(world, haunting, truth)
    reconcile(world, child, helper, haunting, truth)
    world.para()
    ending(world, child, helper, truth)

    world.facts.update(
        child=child, helper=helper, ghost=ghost, setting=setting,
        haunting=haunting, truth=truth, outcome="reconciled", seen=True,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        mood="dusty and moon-bright",
        detail="Old boxes leaned against the beams, and one window made a silver square on the floor.",
    ),
    "garden": Setting(
        id="garden",
        place="the garden gate",
        mood="still and misty",
        detail="Vines made soft shapes in the dark, and the wet stones shone like little mirrors.",
    ),
    "school": Setting(
        id="school",
        place="the empty music room",
        mood="quiet and echoing",
        detail="Rows of tiny chairs waited under a clock that clicked like a careful spider.",
    ),
}

HAUNTINGS = {
    "sheet": Haunting(
        id="sheet",
        appearance="Its white shape fluttered like a torn sheet.",
        misread="That looks like a scary ghost",
        clue="a tiny blue ribbon snagged on the stair rail",
        twist="It turned out to be",
        tags={"appearance", "gloom"},
    ),
    "lantern": Haunting(
        id="lantern",
        appearance="A dim glow bobbed in the dark like a floating eye.",
        misread="Maybe it is something dangerous",
        clue="a warm drip of wax on the floor",
        twist="The light was only",
        tags={"appearance", "curiosity"},
    ),
    "shadow": Haunting(
        id="shadow",
        appearance="A long dark shape leaned out of the corner.",
        misread="I should not judge by the first look",
        clue="a family photo hanging crooked on the wall",
        twist="The shape was only",
        tags={"appearance", "discriminate"},
    ),
}

TRUTHS = {
    "lost_cat": Truth(
        id="lost_cat",
        reveal="a little cat was hiding inside the old costume, blinking through two eyeholes.",
        peace="It had been looking for warmth, not trouble.",
        ending_image="At the end, the cat curled up in a blanket basket by the fire.",
        tags={"curiosity", "reconciliation"},
    ),
    "grandpa_note": Truth(
        id="grandpa_note",
        reveal="the 'ghost' was Grandpa's old voice player, skipping one song over and over.",
        peace="The strange sound had only been a memory kept in a dusty room.",
        ending_image="By the last paragraph, the music room felt like a place for songs again.",
        tags={"twist", "reconciliation"},
    ),
    "sister_game": Truth(
        id="sister_game",
        reveal="it was the helper's older sister, wrapped in a sheet, trying to guide them to a surprise gift.",
        peace="She had wanted to startle them, but not to hurt anyone.",
        ending_image="At the end, everybody laughed together by the stairs, and the sheet became a picnic cloth.",
        tags={"twist", "curiosity", "reconciliation"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Iris", "Pia"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Noah", "Finn", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, haunting in HAUNTINGS.items():
            for tid, truth in TRUTHS.items():
                if is_reasonable(setting, haunting, truth):
                    combos.append((sid, hid, tid))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen setting, ghost image, and twist do not form a reasonable ghost-story premise.)"


def explain_haunting(hid: str) -> str:
    return f"(No story: unknown haunting '{hid}'.)"


def explain_truth(tid: str) -> str:
    return f"(No story: unknown twist/reconciliation truth '{tid}'.)"


@dataclass
class StoryParams:
    setting: str
    haunting: str
    truth: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: appearance, curiosity, twist, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--haunting", choices=HAUNTINGS)
    ap.add_argument("--truth", choices=TRUTHS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.haunting is None or c[1] == args.haunting)
              and (args.truth is None or c[2] == args.truth)]
    if not combos:
        raise StoryError(explain_rejection())

    setting, haunting, truth = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != child]
    helper = args.helper or rng.choice(helper_pool)
    return StoryParams(
        setting=setting,
        haunting=haunting,
        truth=truth,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the words "appearance" and "discriminate".',
        f"Tell a spooky-but-kind story where {f['child'].id} learns not to discriminate by appearance alone and discovers the truth.",
        f"Write a ghost story with curiosity, a twist, and reconciliation in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, haunting, truth = f["child"], f["helper"], f["haunting"], f["truth"]
    return [
        QAItem(
            question=f"What did {child.id} do at first when the ghost appeared?",
            answer=(
                f"{child.id} first judged the ghost by its appearance and was ready to call it scary. "
                f"Then {child.id}'s curiosity pushed {child.pronoun()} to look more carefully."
            ),
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                f"The twist was that {truth.reveal} The spooky-looking part was misleading, so the first guess was wrong."
            ),
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} reconcile?",
            answer=(
                f"{child.id} apologized for the quick judgment, and {helper.id} stayed calm. "
                f"They listened to the truth together, and that turned fear into understanding."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why shouldn't you judge someone by appearance alone?",
            answer=(
                "Because what someone looks like on the outside can be misleading. "
                "It is kinder and wiser to look closer and learn the truth before deciding."
            ),
        ),
        QAItem(
            question="What does curiosity help you do?",
            answer=(
                "Curiosity helps you ask questions and notice details. "
                "That can reveal something important you would miss if you only guessed."
            ),
        ),
        QAItem(
            question="What is a reconciliation?",
            answer=(
                "A reconciliation is when people make peace after a misunderstanding. "
                "They listen, apologize if needed, and feel better together again."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.haunting not in HAUNTINGS:
        raise StoryError(explain_haunting(params.haunting))
    if params.truth not in TRUTHS:
        raise StoryError(explain_truth(params.truth))
    world = tell(
        SETTINGS[params.setting],
        HAUNTINGS[params.haunting],
        TRUTHS[params.truth],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    StoryParams(setting="attic", haunting="sheet", truth="lost_cat", child="Mina", child_gender="girl", helper="Owen", helper_gender="boy"),
    StoryParams(setting="school", haunting="lantern", truth="grandpa_note", child="Eli", child_gender="boy", helper="Nora", helper_gender="girl"),
    StoryParams(setting="garden", haunting="shadow", truth="sister_game", child="Iris", child_gender="girl", helper="Finn", helper_gender="boy"),
]


ASP_RULES = r"""
reasonably_possible(S,H,T) :- setting(S), haunting(H), truth(T).
valid(S,H,T) :- reasonably_possible(S,H,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAUNTINGS:
        lines.append(asp.fact("haunting", hid))
    for tid in TRUTHS:
        lines.append(asp.fact("truth", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.child} / {p.setting} / {p.haunting} / {p.truth}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

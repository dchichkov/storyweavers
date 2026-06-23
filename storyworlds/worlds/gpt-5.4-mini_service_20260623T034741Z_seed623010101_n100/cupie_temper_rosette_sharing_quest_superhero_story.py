#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/cupie_temper_rosette_sharing_quest_superhero_story.py
=============================================================================================================

A small standalone storyworld for a superhero-style sharing quest.

Premise:
- A child hero named Cupie wants to finish a quest.
- A shiny rosette is needed as a prize/key/keepsake.
- A temper flare can make sharing hard, so a helper or mentor can guide a better choice.

The world models:
- physical meters: carrying, blocked, tangled, polished, swapped, delivered
- emotional memes: joy, temper, trust, worry, pride, calm, friendship

This script follows the shared Storyweavers contract:
- generate() builds a world and a complete story
- three QA sets are produced from world state, not by parsing prose
- Python reasonableness gate plus inline ASP twin
- --verify exercises both parity and story generation smoke tests
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
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    helper_of: Optional[str] = None
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
        return self.label or self.id
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    indoor: bool = False
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
class Quest:
    id: str
    scene: str
    action: str
    motion: str
    need: str
    turn: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Prize:
    id: str
    label: str
    phrase: str
    place: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class SharingTool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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


def _r_tidy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    prize = world.entities.get("prize")
    if not hero or not prize:
        return out
    if hero.meters["carrying"] < THRESHOLD:
        return out
    sig = ("tidy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["polished"] += 1
    hero.memes["pride"] += 1
    out.append("__tidy__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    prize = world.entities.get("prize")
    if not hero or not helper or not prize:
        return out
    if hero.memes["temper"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["temper"] = 0.0
    hero.memes["trust"] += 1
    helper.memes["friendship"] += 1
    prize.meters["swapped"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("tidy", "physical", _r_tidy), Rule("share", "social", _r_share)]


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


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return quest.need == prize.place


def select_tool(quest: Quest, prize: Prize) -> Optional[SharingTool]:
    for tool in TOOLS:
        if quest.id in tool.helps and prize.place in tool.tags:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for quest in QUESTS:
            for prize in PRIZES:
                if quest_at_risk(QUESTS[quest], PRIZES[prize]) and select_tool(QUESTS[quest], PRIZES[prize]):
                    combos.append((setting, quest, prize))
    return combos


def predict_turn(world: World, hero: Entity, helper: Entity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get("hero").meters["carrying"] += 1
    sim.get("hero").memes["temper"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get(prize_id).meters["swapped"] >= THRESHOLD,
        "polished": sim.get(prize_id).meters["polished"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"Cupie was a little hero who liked bright capes, kind plans, and missions that felt important. "
        f"{quest.scene}"
    )
    world.say(
        f"On this day, {hero.id} wanted to {quest.action}, because the {prize.label} was part of the rescue route."
    )
    helper.memes["calm"] += 1


def want_and_warn(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    hero.meters["carrying"] += 1
    hero.memes["temper"] += 1
    world.say(
        f"{hero.id} reached for the {prize.label}, but {helper.id} lifted a gentle hand. "
        f'“If we keep only one thing for ourselves, the quest can’t help everyone,” {helper.id} said.'
    )
    pred = predict_turn(world, hero, helper, prize.id)
    world.facts["predicted_shared"] = pred["shared"]
    world.facts["predicted_polished"] = pred["polished"]


def flare(world: World, hero: Entity, helper: Entity, quest: Quest, prize: Entity) -> None:
    world.say(
        f"{hero.id}'s temper flickered like a tiny spark. The shiny {prize.label} felt too special to hand over."
    )
    if hero.memes["temper"] >= THRESHOLD:
        world.say(
            f"{hero.id} stamped one boot and said, “I found it first!”"
        )


def resolve_share(world: World, hero: Entity, helper: Entity, tool: SharingTool, prize: Entity, quest: Quest) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.meters["carrying"] = 0.0
    prize.meters["swapped"] += 1
    prize.meters["delivered"] += 1
    world.say(
        f"Then {helper.id} showed the {tool.label}. “We can share the {prize.label} and still finish the quest,” {helper.id} said."
    )
    world.say(
        f"{hero.id} took a breath, let the temper go, and passed the {prize.label} over. "
        f"Together they used it to {quest.turn}."
    )
    world.say(
        f"At the end, the {prize.label} was not hidden away at all. It was shining on the team, "
        f"and {hero.id} was smiling beside {helper.id} like a true superhero."
    )


def resolve_keep(world: World, hero: Entity, helper: Entity, tool: SharingTool, prize: Entity, quest: Quest) -> None:
    world.say(
        f"Instead of arguing, {hero.id} listened. {helper.id} set out the {tool.label}, and the two of them shared the plan."
    )
    world.say(
        f"They used the {prize.label} together, and the quest moved forward without any more temper at all."
    )
    prize.meters["delivered"] += 1


SETTINGS = {
    "skybridge": Setting(place="the skybridge above Star Harbor", affords={"quest"}),
    "sunroom": Setting(place="the sunroom of the hero clubhouse", affords={"sharing", "quest"}, indoor=True),
    "laneway": Setting(place="the lantern-lit lane by the museum", affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        scene="The city needed a bright clue from the Sky Clock, and the team had to cross the skybridge to find it.",
        action="reach the far tower",
        motion="hurry across the bridge",
        need="the far tower",
        turn="unlock the sky gate",
        ending="the skyline glittered like a medal",
        tags={"quest", "superhero"},
    ),
    "sharing": Quest(
        id="sharing",
        scene="The clubhouse had a shelf of rescue tools, and every hero had to choose one thing to share with the others.",
        action="share the best tool",
        motion="walk to the center table",
        need="the center table",
        turn="open the teamwork chest",
        ending="every cape looked brighter together",
        tags={"sharing", "superhero"},
    ),
}

PRIZES = {
    "rosette": Prize(
        id="rosette",
        label="rosette",
        phrase="a gold rosette with a blue ribbon",
        place="the far tower",
        tags={"rosette", "shiny"},
    ),
    "cupie": Prize(
        id="cupie",
        label="cupie",
        phrase="a small cupie charm with a smile",
        place="the center table",
        tags={"cupie", "keepsake"},
    ),
    "temper": Prize(
        id="temper",
        label="temper",
        phrase="a temper token sealed in a clear case",
        place="the far tower",
        tags={"temper", "emotion"},
    ),
}

TOOLS = [
    SharingTool(id="teamwalk", label="teamwalk rope", phrase="a teamwalk rope", helps={"quest"}, tags={"the far tower"}),
    SharingTool(id="swapbox", label="swap box", phrase="a swap box", helps={"sharing"}, tags={"the center table"}),
    SharingTool(id="kindnote", label="kind note", phrase="a kind note card", helps={"quest", "sharing"}, tags={"the far tower", "the center table"}),
]

HERO_NAMES = ["Cupie", "Milo", "Nia", "Rae", "Zed", "Tavi"]
HELPER_NAMES = ["Nova", "Iris", "Bea", "Jax", "Lumi", "Pip"]


@dataclass
class StoryParams:
    setting: str = "skybridge"
    quest: str = "quest"
    prize: str = "rosette"
    hero_name: str = "Cupie"
    hero_type: str = "girl"
    helper_name: str = "Nova"
    helper_type: str = "girl"
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "cupie", "temper", and "rosette".',
        f"Tell a short quest story where {f['hero'].id} must share a {f['prize'].label} to finish a heroic task.",
        f"Write a gentle superhero tale about sharing, a tricky temper, and a shiny {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, quest = f["hero"], f["helper"], f["prize_obj"], f["quest_obj"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} starts the quest?",
            answer=f"It is about {hero.id}, a little superhero who wants to finish a quest with {helper.id}. The {prize.label} is the special thing they need to handle wisely.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel a temper flare when the {prize.label} came into the story?",
            answer=f"{hero.id} wanted to keep the {prize.label} close instead of sharing it. That made the temper rise, because the quest needed teamwork, not just one hero holding on tight.",
        ),
    ]
    if f.get("shared"):
        qa.append(
            QAItem(
                question=f"How did {helper.id} help {hero.id} with the {prize.label}?",
                answer=f"{helper.id} offered a calm plan and a sharing tool, so {hero.id} could let go of the temper and pass the {prize.label} along. After that, they used it together and the quest moved forward.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed by the ending of the story?",
                answer=f"At the start, the {prize.label} was hard to share, but by the end it was helping both heroes at once. The temper was gone, and the team looked proud and bright.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too. It helps people work together and feel like a team.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special mission or adventure where someone tries hard to reach a goal. In superhero stories, a quest usually means helping others.",
        ),
        QAItem(
            question="What is a rosette?",
            answer="A rosette is a small decoration or prize that can look like a flower or badge. It often shows that something was done well.",
        ),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_risk(Q, P) :- quest(Q), prize(P), need(Q, N), place(P, N).
fix(T, Q, P) :- tool(T), helps(T, Q), prize(P), need(P, N), tags(T, N), quest_risk(Q, P).
valid(Setting, Q, P) :- setting(Setting), quest(Q), prize(P), quest_risk(Q, P), fix(_, Q, P).

shared :- hero_carries, helper_calm.
polite_end :- shared.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("need", qid, q.need))
        lines.append(asp.fact("action", qid, q.action))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("need", pid, p.place))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for tid, t in TOOLS:
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
        for tg in sorted(t.tags):
            lines.append(asp.fact("tags", tid, tg))
    lines.append(asp.fact("hero_carries"))
    lines.append(asp.fact("helper_calm"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and Python valid_combos():")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: Cupie, temper, and a rosette on a superhero quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, prize = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        quest=quest,
        prize=prize,
        hero_name=hero_name,
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        helper_name=helper_name,
        helper_type=args.helper_type or rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.prize not in PRIZES:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    prize_cfg = PRIZES[params.prize]
    tool = select_tool(quest, prize_cfg)
    if tool is None:
        raise StoryError("No reasonable sharing tool exists for this quest and prize.")
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label="hero"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label="helper", role="guide"))
    prize = world.add(Entity(id="prize", kind="thing", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.add(Entity(id="tool", kind="thing", type="thing", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_obj=prize, quest_obj=quest, tool=tool, shared=False)

    intro(world, hero, helper, quest, prize)
    world.para()
    want_and_warn(world, hero, helper, quest, prize)
    flare(world, hero, helper, quest, prize)
    world.para()
    if hero.memes["temper"] >= THRESHOLD:
        if tool.id == "kindnote":
            resolve_share(world, hero, helper, tool, prize, quest)
            world.facts["shared"] = True
        else:
            resolve_keep(world, hero, helper, tool, prize, quest)
            world.facts["shared"] = True
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
    StoryParams(setting="skybridge", quest="quest", prize="rosette", hero_name="Cupie", hero_type="girl", helper_name="Nova", helper_type="girl"),
    StoryParams(setting="sunroom", quest="sharing", prize="cupie", hero_name="Cupie", hero_type="boy", helper_name="Iris", helper_type="girl"),
]


def valid_story_outcome(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.quest in QUESTS and params.prize in PRIZES


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, quest, prize) combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

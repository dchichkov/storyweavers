#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pivot_laundry_room_moral_value_sharing_superhero.py
===================================================================================

A standalone storyworld about a tiny superhero mission in a laundry room.

Seed premise
------------
A child superhero wants to keep a promise and share a useful thing, but the
laundry room is crowded with spinning, clattering chores. The story pivots from
a selfish temptation to a generous choice: the hero shares a helper item, saves
the day, and earns trust by doing the right thing.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate
- an inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
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
MIN_KINDNESS = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Setting:
    id: str
    place: str
    afford: set[str] = field(default_factory=set)
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
class HeroConfig:
    id: str
    title: str
    costume: str
    virtue: str
    helper_item: str
    rescue_line: str
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
class Need:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    vulnerable: bool = True
    tags: set[str] = field(default_factory=set)
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


@dataclass
class SharingAction:
    id: str
    label: str
    share_text: str
    effect_text: str
    kindness: int
    power: int
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["calm"] < THRESHOLD or (("calm",) in world.fired):
            continue
        world.fired.add(("calm",))
        world.get("room").meters["chaos"] = max(0.0, world.get("room").meters["chaos"] - 1.0)
        out.append("The room settled a little.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    other = world.entities.get("friend")
    if not hero or not other:
        return out
    if hero.meters["shared"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["pride"] += 1
    other.memes["trust"] += 1
    out.append("__share__")
    return out


def _r_pivot(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["pivot"] < THRESHOLD:
        return out
    sig = ("pivot",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["resolve"] += 1
    out.append("__pivot__")
    return out


CAUSAL_RULES = [Rule("pivot", _r_pivot), Rule("share", _r_share), Rule("calm", _r_calm)]


def reasonableness_ok(setting: Setting, need: Need, action: SharingAction) -> bool:
    return setting.id == "laundry_room" and need.vulnerable and action.kindness >= MIN_KINDNESS


def outcome_from(action: SharingAction, delay: int) -> str:
    return "saved" if action.power >= (2 + delay) else "scrambled"


def predict(world: World, action: SharingAction, need: Need) -> dict:
    sim = world.copy()
    do_action(sim, sim.get("hero"), sim.get("friend"), action, need, narrate=False)
    return {
        "calm": sim.get("room").meters["chaos"] < 1.0,
        "shared": sim.get("hero").meters["shared"] >= THRESHOLD,
    }


def do_action(world: World, hero: Entity, friend: Entity, action: SharingAction, need: Need, narrate: bool = True) -> None:
    hero.meters["shared"] += 1
    hero.memes["kindness"] += action.kindness
    friend.memes["hope"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(action.share_text.replace("{need}", need.label))


def setup(world: World, hero: Entity, friend: Entity, setting: Setting, hero_cfg: HeroConfig) -> None:
    hero.memes["duty"] += 1
    friend.memes["need"] += 1
    world.say(
        f"In the {setting.place}, {hero.id} wore {hero_cfg.costume} and listened for trouble. "
        f"{friend.id} stood by the dryer, where the towels were still warm."
    )
    world.say(
        f'{hero.id} called {friend.id} "{hero_cfg.title} {friend.id}!" and promised, '
        f'"If anybody needs help, I will {hero_cfg.rescue_line}."'
    )


def tension(world: World, hero: Entity, friend: Entity, need: Need) -> None:
    hero.memes["want"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"Then the machine doors thumped shut and {need.phrase} slipped toward a spinning pile. "
        f'{friend.id} whispered, "We need that {need.label} right now."'
    )
    world.say(
        f"{hero.id} looked at the crowded room and almost chose the easy thing: keep the best tool."
    )


def pivot_beat(world: World, hero: Entity, friend: Entity, action: SharingAction, need: Need) -> None:
    hero.meters["pivot"] += 1
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a breath and pivoted from keeping the tool to sharing it. "
        f'"You can have it first," {hero.id} said, and the room felt braver at once.'
    )
    world.say(action.effect_text.replace("{need}", need.label))


def rescue(world: World, hero: Entity, friend: Entity, need: Need) -> None:
    room = world.get("room")
    room.meters["chaos"] = 0.0
    hero.meters["saved"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"With the shared helper in both hands, they stopped the mess before it spread. "
        f"The {need.label} stayed safe, and the laundry room grew quiet again."
    )


def lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["glow"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"After that, {friend.id} grinned and {hero.id} smiled back. "
        f'The best part of being a hero was not keeping the power -- it was sharing it.'
    )
    world.say(
        f"By the end, {hero.id}'s cape hung still, the floor was dry, and both friends knew the brave choice had been the kind one."
    )


def tell(setting: Setting, hero_cfg: HeroConfig, need: Need, action: SharingAction,
         hero_name: str = "Nova", friend_name: str = "Milo") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label="the hero", role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label="the friend", role="friend"))
    room = world.add(Entity(id="room", type="room", label="the laundry room"))
    world.add(Entity(id="tool", type="thing", label=hero_cfg.helper_item, tags=set(hero_cfg.tags)))
    world.add(Entity(id="need", type="thing", label=need.label, tags=set(need.tags)))

    setup(world, hero, friend, setting, hero_cfg)
    world.para()
    tension(world, hero, friend, need)
    world.say(f"The word that kept echoing in {hero.id}'s head was: pivot.")

    if not reasonableness_ok(setting, need, action):
        raise StoryError("This setup does not support a fair sharing pivot in the laundry room.")

    pred = predict(world, action, need)
    world.facts["predicted_shared"] = pred["shared"]

    world.para()
    pivot_beat(world, hero, friend, action, need)
    do_action(world, hero, friend, action, need, narrate=False)

    world.para()
    rescue(world, hero, friend, need)
    lesson(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        room=room,
        setting=setting,
        hero_cfg=hero_cfg,
        need=need,
        action=action,
        outcome="saved" if action.power >= 2 else "scrambled",
    )
    return world


SETTINGS = {
    "laundry_room": Setting(id="laundry_room", place="laundry room", afford={"sharing"}),
}

HEROES = {
    "nova": HeroConfig(
        id="nova",
        title="Captain",
        costume="a bright blue cape and shiny gloves",
        virtue="sharing",
        helper_item="a rescue basket",
        rescue_line="grab the rescue basket and help",
        tags={"cape", "gloves", "basket"},
    ),
    "bolt": HeroConfig(
        id="bolt",
        title="Commander",
        costume="a red cape and a mask with a star",
        virtue="sharing",
        helper_item="a sorting tray",
        rescue_line="lift the sorting tray and help",
        tags={"cape", "mask", "tray"},
    ),
}

NEEDS = {
    "lost_sock": Need(id="lost_sock", label="sock", phrase="a tiny sock rolled under the washer", risk="missing", region="floor", vulnerable=True, tags={"sock"}),
    "soap_bar": Need(id="soap_bar", label="soap", phrase="a slippery bar of soap slid toward a drain", risk="slip", region="floor", vulnerable=True, tags={"soap"}),
}

ACTIONS = {
    "share_basket": SharingAction(
        id="share_basket",
        label="share the basket",
        share_text="Together, they used the basket to catch {need} before it disappeared.",
        effect_text="The shared basket made the rescue easier, and both children could reach {need}.",
        kindness=3,
        power=3,
        tags={"basket", "sharing"},
    ),
    "share_tray": SharingAction(
        id="share_tray",
        label="share the tray",
        share_text="Together, they slid the tray under {need} and lifted it safely.",
        effect_text="The shared tray turned the rush into teamwork, and {need} stopped slipping.",
        kindness=2,
        power=2,
        tags={"tray", "sharing"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    hero: str
    need: str
    action: str
    friend: str = "Milo"
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
    StoryParams(setting="laundry_room", hero="nova", need="lost_sock", action="share_basket", seed=7),
    StoryParams(setting="laundry_room", hero="bolt", need="soap_bar", action="share_tray", seed=9),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for hid, h in HEROES.items():
            for nid, n in NEEDS.items():
                for aid, a in ACTIONS.items():
                    if reasonableness_ok(s, n, a):
                        out.append((sid, hid, aid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, need, action = f["hero"], f["need"], f["action"]
    return [
        f'Write a superhero story set in a laundry room that includes the word "pivot" and a moment of sharing.',
        f"Tell a child-friendly superhero tale where {hero.id} must pivot from keeping a helper item to sharing it so {need.label} can be saved.",
        f"Write a story about a laundry room emergency where the hero chooses sharing over selfishness and the ending proves the choice helped.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, need, action = f["hero"], f["friend"], f["need"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id} in the laundry room, with {hero.id} acting like a superhero."),
        ("What did the hero have to do?",
         f"{hero.id} had to pivot from holding onto the helper item to sharing it. That choice let both children save {need.label}."),
        ("Why was sharing important?",
         f"Sharing mattered because the need was real and the room was crowded. When {hero.id} shared, the rescue became possible instead of stuck."),
        ("How did the story end?",
         f"It ended with the laundry room calm again, the helper item shared, and everyone proud of the kind choice."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does pivot mean?",
         "To pivot means to turn in a new direction or change your plan. In stories, it can show a smart switch from one choice to another."),
        ("What is sharing?",
         "Sharing means letting someone else use or have something too. It is a kind way to help when more than one person needs the same thing."),
        ("What is a laundry room for?",
         "A laundry room is a place where clothes are washed and dried. It often has a washer, a dryer, baskets, and towels."),
        ("What is a superhero story?",
         "A superhero story is about someone who tries to help, protect others, and make a brave choice. The hero often uses special courage or tools to do it."),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not make a fair sharing pivot in the laundry room.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld about pivoting to sharing in a laundry room.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--friend")
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
    if args.setting and args.setting != "laundry_room":
        raise StoryError(explain_rejection())
    if args.action and args.action not in ACTIONS:
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.setting or args.hero or args.action:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.hero is None or c[1] == args.hero)
                  and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, hero, action = rng.choice(sorted(combos))
    need = args.need or rng.choice(sorted(NEEDS))
    if need not in NEEDS:
        raise StoryError(explain_rejection())
    return StoryParams(
        setting=setting,
        hero=hero,
        need=need,
        action=action,
        friend=args.friend or "Milo",
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero not in HEROES or params.need not in NEEDS or params.action not in ACTIONS:
        raise StoryError(explain_rejection())
    setting = SETTINGS[params.setting]
    hero_cfg = HEROES[params.hero]
    need = NEEDS[params.need]
    action = ACTIONS[params.action]
    if not reasonableness_ok(setting, need, action):
        raise StoryError(explain_rejection())
    world = tell(setting, hero_cfg, need, action, hero_name="Nova" if params.hero == "nova" else "Bolt", friend_name=params.friend)
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


ASP_RULES = r"""
valid(S,H,A) :- setting(S), hero(H), action(A), S = laundry_room.
shared :- pivoted, sharing.
pivoted :- hero_choice(keep), need_present.
hero_choice(share) :- shared.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    lines.append(asp.fact("need_present"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"MISMATCH: normal generation failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: ASP and Python agree; generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

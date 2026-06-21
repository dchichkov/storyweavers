#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/debt_hijklmnop_novocaine_magic_friendship_adventure.py
======================================================================================

A standalone story world for a tiny Adventure tale with Magic, Friendship, and
the required seed words: debt, hijklmnop, novocaine.

Premise:
- A child or small adventuring pair owes a small magical debt.
- They need to travel on a tiny quest to repay it.
- A strange magic word, hijklmnop, unlocks a helpful enchantment.
- Novocaine appears as a soothing spell or potion that helps with pain so the
  quest can continue safely.
- Friendship changes the result: the friends cooperate, share the burden, and
  finish with a warmer ending image.

This is a small, classical simulation with typed entities, physical meters, and
emotional memes. The story is state-driven, with a causal turn and an ending
that proves what changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/debt_hijklmnop_novocaine_magic_friendship_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/debt_hijklmnop_novocaine_magic_friendship_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/debt_hijklmnop_novocaine_magic_friendship_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/debt_hijklmnop_novocaine_magic_friendship_adventure.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""  # adventurer | friend | mentor | debt_holder | obstacle | tool | place
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

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
    mood: str
    hazard: str
    path: str

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
class Quest:
    id: str
    debt_name: str
    debt_amount: int
    promise: str
    pay_phrase: str
    outcome_phrase: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
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
class SoothingSpell:
    id: str
    label: str
    phrase: str
    calm_phrase: str
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


class AdventureWorld(World):
    pass


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["hurt"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["hurt"] = 0.0
        ent.memes["relief"] += 1
        ent.memes["hope"] += 1
        out.append(f"{ent.id} felt the pain fade.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    advs = [e for e in list(world.entities.values()) if e.role == "adventurer"]
    if len(advs) < 2:
        return out
    if sum(a.memes["trust"] for a in advs) < 2:
        return out
    sig = ("friendship", tuple(sorted(a.id for a in advs)))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for a in advs:
        a.memes["brave"] += 1
        a.memes["joy"] += 1
    out.append("The friends stood together.")
    return out


def _r_repay(world: World) -> list[str]:
    out: list[str] = []
    debt = world.get("debt")
    if debt.meters["owed"] < THRESHOLD:
        return out
    if debt.meters["paid"] < debt.meters["owed"]:
        return out
    sig = ("repay", debt.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    debt.meters["owed"] = 0.0
    debt.memes["satisfied"] += 1
    out.append("The debt was paid.")
    return out


CAUSAL_RULES = [
    Rule("relief", "physical", _r_relief),
    Rule("friendship", "social", _r_friendship),
    Rule("repay", "economic", _r_repay),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def want_adventure(world: World, hero: Entity, setting: Setting, quest: Quest) -> None:
    hero.memes["curious"] += 1
    world.say(
        f"On a bright morning, {hero.id} set out for {setting.place}, where the air felt "
        f"{setting.mood} and the path curved like a promise."
    )
    world.say(
        f"{hero.id} had a small {quest.debt_name} to repay, and the only clue was a scrap of "
        f"paper with the word hijklmnop written on it."
    )


def meet_friend(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"At the trailhead, {friend.id} waved and said they would help. "
        f"Friendship made the quest feel less heavy."
    )
    world.say(
        f'"We will share the work," {friend.id} said. "That is how we pay a debt and keep '
        f"our promise."
    )


def discover_magic(world: World, hero: Entity, spell: MagicItem) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Deep in the path, {hero.id} found {spell.phrase}. "
        f"When {hero.id} whispered hijklmnop, {spell.effect}."
    )


def pain_turn(world: World, hero: Entity, spell: SoothingSpell) -> None:
    hero.meters["hurt"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sharp ache tapped at {hero.id}'s tooth, and the adventure nearly stopped."
    )
    world.say(
        f"{spell.phrase.capitalize()} helped at once: {spell.calm_phrase}."
    )
    world.say(
        f"With novocaine and a steady breath, {hero.id} could smile again and keep going."
    )


def solve_quest(world: World, hero: Entity, friend: Entity, quest: Quest, setting: Setting) -> None:
    debt = world.get("debt")
    debt.meters["paid"] += quest.debt_amount
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together, {hero.id} and {friend.id} followed the path to the little stone gate, "
        f"then delivered {quest.pay_phrase} to the keeper."
    )
    world.say(
        f"The keeper nodded, and the last bit of {quest.debt_name} lifted from their shoulders."
    )


def ending_image(world: World, hero: Entity, friend: Entity, setting: Setting, quest: Quest) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"By sunset, the two friends walked home under a gold sky, lighter than before."
    )
    world.say(
        f"{hero.id} tucked the hijklmnop scrap into a pocket, and {friend.id} laughed beside "
        f"{hero.id}; the adventure had become a story about trust, courage, and a paid debt."
    )
    world.say(
        f"{quest.outcome_phrase.capitalize()}, and the path back to {setting.place} glowed like a "
        f"safe little magic road."
    )


def tell(setting: Setting, quest: Quest, magic: MagicItem, spell: SoothingSpell,
         hero_name: str = "Mila", hero_type: str = "girl",
         friend_name: str = "Jon", friend_type: str = "boy") -> World:
    world = AdventureWorld()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="adventurer"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="adventurer"))
    debt = world.add(Entity(id="debt", type="thing", label="debt", role="debt_holder"))
    debt.meters["owed"] = float(quest.debt_amount)
    debt.meters["paid"] = 0.0
    debt.memes["expectation"] = 1.0
    world.add(Entity(id=setting.id, type="place", label=setting.place, role="place"))
    world.add(Entity(id=magic.id, type="thing", label=magic.label, role="tool"))
    world.add(Entity(id=spell.id, type="thing", label=spell.label, role="tool"))

    want_adventure(world, hero, setting, quest)
    world.para()
    meet_friend(world, hero, friend, quest)
    discover_magic(world, hero, magic)
    world.para()
    pain_turn(world, hero, spell)
    solve_quest(world, hero, friend, quest, setting)
    world.para()
    ending_image(world, hero, friend, setting, quest)

    world.facts.update(
        hero=hero, friend=friend, debt=debt, setting=setting, quest=quest, magic=magic, spell=spell
    )
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest", "bright and green", "old roots", "stone path"),
    "harbor": Setting("harbor", "the harbor", "windy and salt-bright", "wet planks", "dock road"),
    "ruins": Setting("ruins", "the old ruins", "quiet and echoing", "fallen blocks", "moon path"),
}

QUESTS = {
    "small_debt": Quest("small_debt", "debt", 1, "a shiny coin and a promise", "the shiny coin and the promise", "their promise was kept", {"debt"}),
    "library_debt": Quest("library_debt", "debt", 2, "two coins and an apology", "two coins and an apology", "their debt was cleared", {"debt"}),
}

MAGIC_ITEMS = {
    "wand": MagicItem("wand", "a pocket wand", "a pocket wand", "a tiny spark danced in the air", {"Magic"}),
    "stone": MagicItem("stone", "a glowing stone", "a glowing stone", "soft blue light bloomed around it", {"Magic"}),
}

SOOTHING = {
    "novocaine_spell": SoothingSpell("novocaine", "novocaine", "a gentle novocaine spell", "the ache went quiet at once", {"novocaine"}),
    "cool_drops": SoothingSpell("cool_drops", "cool drops", "a little vial of cool drops", "the pain faded like mist", {"novocaine"}),
}



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for m in MAGIC_ITEMS:
                for sp in SOOTHING:
                    combos.append((s, q, m, sp))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    magic: str
    soothing: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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

CURATED = [
    ("forest", "small_debt", "wand", "novocaine_spell", "Mila", "girl", "Jon", "boy"),
    ("harbor", "library_debt", "stone", "cool_drops", "Ari", "boy", "Pia", "girl"),
    ("ruins", "small_debt", "wand", "novocaine_spell", "Nia", "girl", "Sol", "boy"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magic friendship adventure about debt and healing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--soothing", choices=SOOTHING)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
              and (args.magic is None or c[2] == args.magic)
              and (args.soothing is None or c[3] == args.soothing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, magic, soothing = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(["Mila", "Ari", "Nia", "Lina", "Tari"])
    friend = args.friend or rng.choice(["Jon", "Pia", "Sol", "Ezra", "Kia"])
    if hero == friend:
        friend = friend + "n"
    return StoryParams(setting, quest, magic, soothing, hero, hero_type, friend, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "debt", "hijklmnop", and "novocaine".',
        f"Tell a friendship adventure where {f['hero'].id} and {f['friend'].id} travel to {f['setting'].place} to repay a debt, and a magic word helps them along the way.",
        f"Write a magical quest story where a small debt is paid, friendship matters, and novocaine helps soothe pain so the heroes can finish the journey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    setting = f["setting"]
    spell = f["spell"]
    return [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {friend.id} went together as friends. They shared the quest and helped each other through it."
        ),
        QAItem(
            question="Why did they travel to the path?",
            answer=f"They traveled there to repay a debt. The journey gave them a clear goal, and paying it back was the promise they wanted to keep."
        ),
        QAItem(
            question="What happened when the toothache started?",
            answer=f"The ache nearly stopped the trip, but {spell.phrase} helped calm it. That let {hero.id} breathe easy and keep going with {friend.id}."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the debt paid and the two friends walking home together. Their adventure turned into a happy memory because they stayed kind and brave."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is debt?",
            answer="Debt is something you owe to someone and need to pay back later. It can be money, help, or another promise."
        ),
        QAItem(
            question="What does friendship do in a hard adventure?",
            answer="Friendship helps people share fear, work, and hope. Friends can make a hard task feel lighter and more possible."
        ),
        QAItem(
            question="What is novocaine for?",
            answer="Novocaine is something that can help make pain feel smaller. It is used to soothe an ache so a person can rest or get help."
        ),
        QAItem(
            question="What does a magic word do in stories?",
            answer="A magic word can unlock a spell, a door, or a helpful surprise. In stories, it often changes the world in a gentle, marvelous way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MAGIC_ITEMS:
        lines.append(asp.fact("magic", m))
    for sp in SOOTHING:
        lines.append(asp.fact("soothing", sp))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,M,SP) :- setting(S), quest(Q), magic(M), soothing(SP).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    if not ok:
        print("MISMATCH between clingo and Python valid_combos().")
        return 1
    try:
        sample = generate(CURATED[0] if False else resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        MAGIC_ITEMS[params.magic],
        SOOTHING[params.soothing],
        params.hero,
        params.hero_type,
        params.friend,
        params.friend_type,
    )
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/4."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, "Mila", "girl", "Jon", "boy")) for c in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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

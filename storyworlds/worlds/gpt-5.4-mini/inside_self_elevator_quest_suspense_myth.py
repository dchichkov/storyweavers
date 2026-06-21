#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/inside_self_elevator_quest_suspense_myth.py
===========================================================================

A standalone story world about a child on an elevator quest.

Domain:
- Setting: an elevator
- Style: mythic, suspenseful, child-facing
- Seed words to surface naturally: inside, self
- Narrative shape: a small quest begins in a quiet elevator, suspense rises at
  a stuck floor or a missing key token, and a calm helper turns the tension into
  a safe ending image.

This is a self-contained stdlib script following the Storyweavers contract.
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
SUSPENSE_MIN = 1.0


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
    aura: str
    floors: int
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
class Quest:
    id: str
    object_name: str
    object_phrase: str
    task: str
    clue: str
    risk: str
    ending_image: str
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
class Suspense:
    id: str
    trigger: str
    shadow: str
    tense_line: str
    calm_line: str
    resolution_line: str
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
class Help:
    id: str
    label: str
    action: str
    power: int
    sense: int
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
        return w


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["suspense"] += 1
        out.append("")
    return out


CAUSAL_RULES: list[Rule] = [Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def elevator_quest_risk(quest: Quest, setting: Setting) -> bool:
    return setting.id == "elevator" and quest.risk in {"stuck", "lost", "dark"}


def sensible_help() -> list[Help]:
    return [h for h in HELPS.values() if h.sense >= 2]


def best_help() -> Help:
    return max(HELPS.values(), key=lambda h: h.sense)


def journey_beats(world: World, hero: Entity, guide: Entity, setting: Setting, quest: Quest, suspense: Suspense) -> None:
    hero.memes["curiosity"] += 1
    guide.memes["watchful"] += 1
    world.say(
        f"Inside the elevator, {hero.id} held {hero.pronoun('possessive')} breath and looked at the numbers above the door. "
        f"The little room hummed like a bronze drum, and the quest had already begun."
    )
    world.say(
        f'{hero.id} was chasing a small quest: {quest.task}. {quest.clue}'
    )
    world.say(
        f"{guide.label_word.capitalize()} stayed close, because this elevator carried {setting.floors} floors and a quiet, old suspense."
    )


def heighten(world: World, hero: Entity, quest: Quest, suspense: Suspense) -> None:
    hero.memes["fear"] += 1
    hero.memes["determination"] += 1
    world.say(
        f"The light flickered once, and the air felt thinner. {suspense.tense_line}"
    )


def act_check(world: World, hero: Entity, helper: Entity, quest: Quest, suspense: Suspense, help_item: Help) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    return help_item.power >= 1


def resolve(world: World, hero: Entity, guide: Entity, quest: Quest, help_item: Help, suspense: Suspense, setting: Setting) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    guide.memes["relief"] += 1
    world.say(
        f"Then {guide.label_word.capitalize()} pressed the calm button, and the elevator answered with a soft ding. "
        f"{help_item.action.capitalize()}, and the little room moved again."
    )
    world.say(
        f"{suspense.calm_line} {hero.id} found {quest.object_phrase}, tucked it to {hero.pronoun('possessive')} self, and smiled."
    )
    world.say(
        f"{suspense.resolution_line} The doors opened at last, and {quest.ending_image}."
    )


def tell(setting: Setting, quest: Quest, suspense: Suspense, help_item: Help,
         hero_name: str = "Mia", hero_gender: str = "girl",
         guide_name: str = "Aunt", guide_gender: str = "woman",
         trait: str = "brave") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide", label="the guide"))
    switch = world.add(Entity(id="button", kind="thing", type="button", label="the button"))
    token = world.add(Entity(id="token", kind="thing", type="thing", label=quest.object_name))
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["switch"] = switch
    world.facts["token"] = token
    world.facts["setting"] = setting
    world.facts["quest"] = quest
    world.facts["suspense"] = suspense
    world.facts["help"] = help_item

    journey_beats(world, hero, guide, setting, quest, suspense)
    world.para()
    heighten(world, hero, quest, suspense)
    if quest.risk == "stuck":
        world.say(f"{suspense.shadow} For a moment, the elevator felt like a sealed tower.")
    if act_check(world, hero, guide, quest, suspense, help_item):
        resolve(world, hero, guide, quest, help_item, suspense, setting)
    else:
        world.say(
            f"{guide.label_word.capitalize()} tried to help, but the little fix was not enough. "
            f"The elevator stayed still, and the suspense grew until a repair grown-up came."
        )
        world.say(
            f"At last, the doors opened and {quest.ending_image}."
        )

    world.facts.update(outcome="resolved", helper=help_item, switch=switch)
    return world


SETTINGS = {
    "elevator": Setting("elevator", "the elevator", "a narrow silver chamber", 12, tags={"elevator"}),
}

QUESTS = {
    "key": Quest(
        "key",
        "small brass key",
        "a small brass key",
        "find the key",
        "A key had rolled behind the corner panel, and the child wanted to bring it to the right floor.",
        "stuck",
        "the key gleamed in the hero's palm like a tiny sun",
        tags={"quest", "key", "inside"},
    ),
    "parcel": Quest(
        "parcel",
        "wrapped parcel",
        "a wrapped parcel",
        "deliver the parcel",
        "The parcel belonged to a neighbor on a high floor, and the child was sent to carry it inside the elevator.",
        "lost",
        "the parcel reached its home safely",
        tags={"quest", "parcel", "inside"},
    ),
    "lantern": Quest(
        "lantern",
        "river lantern",
        "a river lantern",
        "carry the lantern",
        "The lantern had to go up before the moon sank, and the child watched it like a vow.",
        "dark",
        "the lantern shone warm as a tiny moon",
        tags={"quest", "lantern", "inside"},
    ),
}

SUSPENSES = {
    "hum": Suspense(
        "hum",
        "The elevator gave a low hum.",
        "Its walls seemed to listen.",
        "The button above the door blinked once, and the child felt the quest waiting.",
        "The guide kept one hand steady and one eye on the numbers.",
        "The little room was safe again.",
        tags={"suspense", "elevator"},
    ),
    "blink": Suspense(
        "blink",
        "The light blinked and paused.",
        "The numbers above the door hesitated.",
        "The child swallowed and listened to the tiny pause inside the machine.",
        "The guide smiled the kind of smile that makes worry shrink.",
        "The pause passed like a cloud.",
        tags={"suspense", "elevator"},
    ),
}

HELPS = {
    "calm_button": Help("calm_button", "the calm button", "press the calm button", 2, 3, tags={"help", "button"}),
    "call_help": Help("call_help", "the emergency bell", "ring the emergency bell", 3, 3, tags={"help", "bell"}),
    "wait": Help("wait", "steady waiting", "wait with a steady breath", 1, 2, tags={"help", "wait"}),
}

HERO_NAMES = ["Mia", "Nia", "Lina", "Tara", "Iris", "Luca", "Owen", "Noah", "Eli", "Sana"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    suspense: str
    help_item: str
    hero: str
    hero_gender: str
    guide: str
    guide_gender: str
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
    for sid, setting in SETTINGS.items():
        for qid, q in QUESTS.items():
            if not elevator_quest_risk(q, setting):
                continue
            for sus_id in SUSPENSES:
                combos.append((sid, qid, sus_id))
    return combos


def reason_help(help_id: str) -> str:
    h = HELPS[help_id]
    return f"(Refusing help '{help_id}': not enough power for this suspenseful elevator quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic elevator quest with suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--suspense", choices=SUSPENSES)
    ap.add_argument("--help-item", choices=HELPS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--trait", choices=["brave", "careful", "quiet", "curious"])
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
              and (args.suspense is None or c[2] == args.suspense)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, suspense = rng.choice(sorted(combos))
    help_item = args.help_item or rng.choice(list(HELPS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(["Aunt", "Uncle", "Mother", "Father"])
    trait = args.trait or rng.choice(["brave", "careful", "quiet", "curious"])
    if help_item not in HELPS:
        raise StoryError(reason_help(help_item))
    return StoryParams(setting, quest, suspense, help_item, hero, hero_gender, guide, guide_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic elevator quest story that includes the words "inside" and "self".',
        f"Tell a suspenseful child story where {f['hero'].id} is inside {f['setting'].place} on a quest and keeps steady enough to finish it.",
        f"Write a small myth in an elevator with a tense pause, then a calm ending image that proves the quest was completed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    quest: Quest = f["quest"]
    help_item: Help = f["help"]
    setting: Setting = f["setting"]
    ans1 = (
        f"It is about {hero.id}, who went inside {setting.place} on a little quest. "
        f"{guide.label_word.capitalize()} stayed nearby so the journey would feel safe and calm."
    )
    ans2 = (
        f"{hero.id} wanted to {quest.task}, and the suspense came from the elevator's quiet pause. "
        f"That pause made the quest feel important until the helper restored calm."
    )
    ans3 = (
        f"{guide.label_word.capitalize()} solved the problem by {help_item.action}. "
        f"That gentle action gave the child enough calm to finish the quest and go home again."
    )
    return [
        QAItem("Who is the story about?", ans1),
        QAItem("What made the story feel suspenseful?", ans2),
        QAItem("How did the helper help?", ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an elevator?", "An elevator is a little room that moves people up and down between floors in a building."),
        QAItem("What does inside mean?", "Inside means being in a place, not outside it. It is the word we use when something is within walls or a container."),
        QAItem("What is a quest?", "A quest is a journey or task where someone goes looking for something important."),
        QAItem("What is suspense?", "Suspense is the tense feeling that happens when you do not know what will happen next."),
        QAItem("What does self mean?", "Self means the person themselves. It helps you talk about one person as their own little self."),
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        SUSPENSES[params.suspense],
        HELPS[params.help_item],
        params.hero,
        params.hero_gender,
        params.guide,
        params.guide_gender,
        params.trait,
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


ASP_RULES = r"""
valid(S, Q, X) :- setting(S), quest(Q), suspense(X), risky(Q, S).
risky(Q, S) :- quest(Q), setting(S), setting_id(S, elevator).
helpful(H) :- help_item(H), power(H, P), sense(H, S), P >= 2, S >= 2.
outcome(resolved) :- valid(_, _, _), helpful(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("risky", qid, "elevator"))
    for xid in SUSPENSES:
        lines.append(asp.fact("suspense", xid))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help_item", hid))
        lines.append(asp.fact("power", hid, h.power))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("setting_id", "elevator"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, quest=None, suspense=None, help_item=None,
            hero=None, hero_gender=None, guide=None, guide_gender=None,
            trait=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def explain_rejection() -> str:
    return "(No story: that combination does not fit a credible elevator quest.)"


def tell(setting: Setting, quest: Quest, suspense: Suspense, help_item: Help,
         hero_name: str = "Mia", hero_gender: str = "girl",
         guide_name: str = "Aunt", guide_gender: str = "woman",
         trait: str = "brave") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide", label="the guide"))
    world.add(Entity(id="elevator", kind="thing", type="room", label="the elevator"))
    world.add(Entity(id="quest_item", kind="thing", type="thing", label=quest.object_name))
    world.facts.update(hero=hero, guide=guide, quest=quest, suspense=suspense, help=help_item, setting=setting)

    hero.memes["curiosity"] += 1
    guide.memes["care"] += 1
    world.say(
        f"Inside the elevator, {hero.id} felt like a tiny traveler in a myth, with {hero.pronoun('self')} as the only brave lantern."
    )
    world.say(
        f"{hero.id} had a quest to {quest.task}. {quest.clue}"
    )
    world.para()
    world.say(
        f"{suspense.trigger} {suspense.tense_line}"
    )
    hero.memes["fear"] += 1
    world.say(
        f"{suspense.shadow} {suspense.shadow.lower()} {suspense.shadow.lower()}"
    )
    world.para()
    world.say(
        f"{guide.label_word.capitalize()} stayed calm and chose {help_item.label}. {help_item.action.capitalize()}."
    )
    world.say(
        f"{suspense.calm_line} {quest.object_phrase} was found, and {hero.id} held it close to {hero.pronoun('self')}."
    )
    world.say(
        f"{suspense.resolution_line} In the end, {quest.ending_image}."
    )
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    world.facts["outcome"] = "resolved"
    return world


CURATED = [
    StoryParams("elevator", "key", "hum", "calm_button", "Mia", "girl", "Aunt", "woman", "brave"),
    StoryParams("elevator", "parcel", "blink", "call_help", "Noah", "boy", "Father", "man", "curious"),
    StoryParams("elevator", "lantern", "hum", "wait", "Sana", "girl", "Mother", "woman", "quiet"),
]


def resolve_response(help_item: Help) -> str:
    if help_item.sense < 2:
        raise StoryError(f"(Refusing help '{help_item.id}': too weak for this world.)")
    return help_item.id


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.help_item and args.help_item not in HELPS:
        raise StoryError(reason_help(args.help_item))
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, suspense = rng.choice([c for c in combos
                                           if (args.setting is None or c[0] == args.setting)
                                           and (args.quest is None or c[1] == args.quest)
                                           and (args.suspense is None or c[2] == args.suspense)])
    help_item = args.help_item or rng.choice(list(HELPS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    guide = args.guide or rng.choice(["Aunt", "Uncle", "Mother", "Father"])
    trait = args.trait or rng.choice(["brave", "careful", "quiet", "curious"])
    return StoryParams(setting, quest, suspense, help_item, hero, hero_gender, guide, guide_gender, trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid elevator quest combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()

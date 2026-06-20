#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py
====================================================================

A standalone story world for a tiny folk-tale quest in a loft: a child climbs
into a quiet loft, loses something of value, seeks it with help, makes a moral
choice, and returns changed. The simulation keeps the world small and concrete:
one loft, one quest item, one temptation, one helper, one choice, and one ending
image that proves what changed.

The story is designed to read like a folk tale: simple repeated motions, a
careful helper, a tempting shortcut, and a moral value that matters more than
greed. The quest may be to recover a lost charm, feather, key, or ribbon from
the loft. The tension comes from whether the seeker takes a found thing that is
not theirs. The resolution depends on the choice to return what was found and
accept a kinder reward.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/loft_moral_value_quest_folk_tale.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    held: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)



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
    loft_name: str
    dark_spot: str
    mood: str
    weather: str

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
class QuestThing:
    id: str
    label: str
    phrase: str
    near: str
    precious: bool = True
    small: bool = True

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
class Temptation:
    id: str
    label: str
    phrase: str
    claim: str
    not_theirs: str
    whisper: str

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
class Reward:
    id: str
    label: str
    phrase: str
    glow: str

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable

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


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    quest = world.facts.get("quest")
    if hero is None or quest is None:
        return out
    if hero.meters["lost"] < THRESHOLD:
        return out
    sig = ("loss", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    out.append("__lost__")
    return out


def _r_honor(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    treasure = world.facts.get("quest")
    if hero is None or helper is None or treasure is None:
        return out
    if hero.memes["honest"] < MORAL_THRESHOLD:
        return out
    sig = ("honor", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["pride"] += 1
    out.append("__honor__")
    return out


CAUSAL_RULES = [Rule("loss", _r_loss), Rule("honor", _r_honor)]


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


def reasonableness_gate(setting: Setting, quest: QuestThing, temptation: Temptation) -> bool:
    return setting.id == "loft" and quest.small and quest.precious and temptation.id in {"coin", "cake", "key", "ring", "feather"}


def predict_moral_turn(world: World, hero: Entity, temptation: Temptation) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["tempted"] += 1
    sim.get(hero.id).memes["honest"] += 1
    return {
        "turns_away": sim.get(hero.id).memes["honest"] >= MORAL_THRESHOLD,
        "gives_in": sim.get(hero.id).meters["tempted"] > 0 and sim.get(hero.id).memes["honest"] < MORAL_THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"Long ago, in {setting.place}, there was a {hero.type} named {hero.id} and a wise {helper.label_word} who knew the old rafters well."
    )
    world.say(
        f"Above them waited the {setting.loft_name}, a quiet place with {setting.dark_spot} and {setting.mood} beams."
    )


def quest_begins(world: World, hero: Entity, quest: QuestThing) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} climbed up to the loft on a little quest: to find {quest.phrase}, which had slipped away near {quest.near}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} looked under boxes and beside old cloth, searching like the children in a folk tale who know a lost thing can be found if the heart stays steady."
    )


def temptation_scene(world: World, hero: Entity, helper: Entity, temptation: Temptation, quest: QuestThing) -> None:
    hero.meters["tempted"] += 1
    hero.memes["want"] += 1
    world.say(
        f"Then {hero.id} saw {temptation.phrase}. It shone by the beams, and for a moment it seemed easier to keep it than to keep looking."
    )
    world.say(
        f'"{temptation.whisper}" {temptation.claim} the small voice of greed seemed to say.'
    )
    world.say(
        f"But {helper.id} touched {hero.pronoun('possessive')} sleeve and reminded {hero.pronoun('object')} that {temptation.not_theirs} and that the quest was to find {quest.label}, not to steal."
    )


def moral_choice(world: World, hero: Entity, temptation: Temptation, helper: Entity, quest: QuestThing) -> None:
    pred = predict_moral_turn(world, hero, temptation)
    hero.memes["honest"] += 1
    if pred["turns_away"]:
        world.say(
            f"{hero.id} took a long breath, set {temptation.label} back where it belonged, and chose the kinder path."
        )
    else:
        world.say(
            f"{hero.id} almost reached for it, but then {helper.id}'s gentle words won the day, and {hero.id} let it be."
        )
    hero.memes["kind"] += 1
    quest.held = True
    world.say(
        f"At last, behind a loose board, {hero.id} found {quest.phrase} and held it as if it were a star brought down from the roof."
    )
    propagate(world, narrate=False)


def return_and_reward(world: World, hero: Entity, helper: Entity, quest: QuestThing, reward: Reward, setting: Setting) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} carried {quest.label} back to the right hands, and the whole loft seemed to breathe easier."
    )
    world.say(
        f"Then {helper.id} smiled and gave {hero.id} {reward.phrase}. It {reward.glow}, a fair prize for an honest heart."
    )
    world.say(
        f"After that, {hero.id} climbed down from {setting.loft_name} with empty pockets, a bright face, and a lighter step."
    )


def tell(setting: Setting, quest: QuestThing, temptation: Temptation, reward: Reward,
         hero_name: str = "Mara", hero_gender: str = "girl",
         helper_name: str = "Grandmother", helper_gender: str = "grandmother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label="grandmother"))
    world.add(Entity(id="loft", type="place", label=setting.loft_name))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["quest"] = quest
    world.facts["setting"] = setting
    world.facts["temptation"] = temptation
    world.facts["reward"] = reward

    introduce(world, hero, helper, setting)
    world.para()
    quest_begins(world, hero, quest)
    temptation_scene(world, hero, helper, temptation, quest)
    world.para()
    moral_choice(world, hero, temptation, helper, quest)
    world.para()
    return_and_reward(world, hero, helper, quest, reward, setting)
    world.facts["outcome"] = "honest"
    return world


SETTINGS = {
    "loft": Setting("loft", "an old cottage", "loft", "dusty corners", "full of mouse-soft shadows", "windy"),
    "barn_loft": Setting("barn_loft", "a red barn", "hay loft", "loose straw", "warm with hay and echoes", "bright"),
    "mill_loft": Setting("mill_loft", "a water mill", "loft", "high rafters", "filled with grain dust and creaks", "cool"),
}

QUESTS = {
    "key": QuestThing("key", "the little brass key", "the little brass key", "an old nail"),
    "feather": QuestThing("feather", "the silver feather", "the silver feather", "a cracked beam"),
    "ring": QuestThing("ring", "the wedding ring", "the wedding ring", "a basket of cloth"),
    "coin": QuestThing("coin", "the bright coin", "the bright coin", "a tangle of rope"),
}

TEMPTATIONS = {
    "coin": Temptation("coin", "a gold coin", "a gold coin", "it might buy sweet buns", "it was not theirs", "Keep it, keep it"),
    "cake": Temptation("cake", "a honey cake", "a honey cake", "it looked delicious", "it was meant for the table below", "Take a bite, take a bite"),
    "key": Temptation("key", "a shiny key", "a shiny key", "it might open a locked chest", "it belonged to another family", "Pocket it, pocket it"),
    "ring": Temptation("ring", "a silver ring", "a silver ring", "it glittered like moonlight", "it was someone else's treasure", "Claim it, claim it"),
    "feather": Temptation("feather", "a white feather", "a white feather", "it looked rare and lovely", "it was tied to a keepsake box below", "Hide it, hide it"),
}

REWARDS = {
    "apple": Reward("apple", "a red apple", "a red apple", "glowed like a sunset"),
    "song": Reward("song", "a kindly song", "a kindly song", "rang sweetly through the loft"),
    "ribbon": Reward("ribbon", "a blue ribbon", "a blue ribbon", "shone bright as sky water"),
}

HERO_NAMES = ["Mara", "Nell", "Tess", "Poppy", "Ivy", "Anya", "June", "Wren"]
HELPERS = ["Grandmother", "Grandfather"]
GENDERS = ["girl", "boy"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    temptation: str
    reward: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        if setting.id != "loft":
            continue
        for qid, quest in QUESTS.items():
            for tid, temp in TEMPTATIONS.items():
                if reasonableness_gate(setting, quest, temp):
                    combos.append((sid, qid, tid))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation", tid))
    for rid in REWARDS:
        lines.append(asp.fact("reward", rid))
    lines.append(asp.fact("loft_setting", "loft"))
    for qid in QUESTS:
        lines.append(asp.fact("small_precious", qid))
    for tid in TEMPTATIONS:
        lines.append(asp.fact("temptation_candidate", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,T) :- setting(S), quest(Q), temptation(T), loft_setting(S), small_precious(Q), temptation_candidate(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale quest in a loft with a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=GENDERS)
    ap.add_argument("--helper-name", choices=HELPERS)
    ap.add_argument("--helper-gender", choices=HELPERS)
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
    if args.setting and args.setting != "loft":
        raise StoryError("This world only tells loft stories.")
    combos = valid_combos()
    if args.quest and args.temptation:
        if (args.setting or "loft", args.quest, args.temptation) not in combos:
            raise StoryError("That quest and temptation do not make a fitting loft tale.")
    qid = args.quest or rng.choice(sorted(QUESTS))
    tid = args.temptation or rng.choice(sorted(TEMPTATIONS))
    rid = args.reward or rng.choice(sorted(REWARDS))
    hero_gender = args.hero_gender or rng.choice(GENDERS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_gender = args.helper_gender or rng.choice(HELPERS)
    helper_name = args.helper_name or rng.choice(HELPERS)
    return StoryParams("loft", qid, tid, rid, hero_name, hero_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], TEMPTATIONS[params.temptation], REWARDS[params.reward], params.hero_name, params.hero_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    tempt = f["temptation"]
    return [
        f'Write a folk-tale style story for a child about a quest in a loft, and include the word "loft".',
        f"Tell a moral tale where {hero.id} searches for {quest.label} in a loft, is tempted by {tempt.label}, and chooses honesty.",
        f"Write a short quest story in a loft where a child returns what is not theirs and is rewarded kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    tempt = f["temptation"]
    reward = f["reward"]
    return [
        ("What kind of story is this?", "It is a folk-tale style quest story about a child in a loft. The child learns that honesty matters more than greed."),
        (f"What was {hero.id} looking for?", f"{hero.id} was looking for {quest.label} in the loft. It had slipped away near {quest.near}, so the search had to be careful."),
        (f"What tempted {hero.id}?", f"{tempt.label} tempted {hero.id}. It looked easy to keep, but {tempt.not_theirs} and that made it wrong to take."),
        (f"How did {hero.id} act at the end?", f"{hero.id} chose to return what was not theirs and keep the quest honest. That choice helped the search end well."),
        (f"What did {helper.id} give {hero.id}?", f"{helper.id} gave {hero.id} {reward.phrase}. It was a fair reward for a kind and honest choice."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a loft?", "A loft is a space high up under a roof. People store things there, and it can feel dusty and quiet."),
        ("What does honesty mean?", "Honesty means telling the truth and not taking things that belong to someone else. It is a kind value that helps people trust you."),
        ("What is a quest?", "A quest is a search for something important. In folk tales, a quest often asks the hero to be brave and wise."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in combo gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, temptation=None, reward=None, hero_name=None, hero_gender=None, helper_name=None, helper_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("loft", "key", "coin", "apple", "Mara", "girl", "Grandmother", "grandmother"),
    StoryParams("loft", "feather", "ring", "song", "Nell", "girl", "Grandfather", "grandfather"),
    StoryParams("loft", "coin", "cake", "ribbon", "Tess", "girl", "Grandmother", "grandmother"),
]


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible loft quest triples:\n")
        for sid, qid, tid in combos:
            print(f"  {sid:10} {qid:8} {tid:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.quest} in the loft"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

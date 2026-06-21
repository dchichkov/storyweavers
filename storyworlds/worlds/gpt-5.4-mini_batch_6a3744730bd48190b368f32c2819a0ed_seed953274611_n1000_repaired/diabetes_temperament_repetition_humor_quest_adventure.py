#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/diabetes_temperament_repetition_humor_quest_adventure.py
=======================================================================================

A small adventure storyworld about a child on a quest, a backpack full of gear,
repeated reminders, a comic temperament clash, and a careful diabetes routine.

Premise
-------
A child goes on a little quest with a helper. The child has diabetes, so the
journey must include snacks, water, and a meter check. The child and helper
disagree in temperament: one is bold and impatient, the other is calm and
repetitive. Humor comes from repeated quest chatter and a comic mix-up, but the
world state still drives the ending.

The world intentionally supports a few closely related variants rather than a
large vague space:
- a quest for a lost item
- a small diabetes routine during the quest
- temperament-driven tension
- repetition as a narrative instrument
- a safe, concrete resolution

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/diabetes_temperament_repetition_humor_quest_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/diabetes_temperament_repetition_humor_quest_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/diabetes_temperament_repetition_humor_quest_adventure.py --verify
    python storyworlds/worlds/gpt-5.4-mini/diabetes_temperament_repetition_humor_quest_adventure.py --qa --json
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
LOW_BG_MIN = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    temperament: str = ""
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
        return self.label or self.type
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
    detail: str
    quest_word: str
    route_word: str
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
class QuestItem:
    id: str
    label: str
    phrase: str
    tag: str
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
class Mood:
    id: str
    label: str
    scene: str
    joke: str
    fix: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_low(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    if kid.meters["tired"] >= THRESHOLD and ("low",) not in world.fired:
        world.fired.add(("low",))
        kid.memes["grit"] += 1
        out.append("__low__")
    return out


def _r_repeat(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    if helper.memes["repeat"] >= THRESHOLD and ("repeat",) not in world.fired:
        world.fired.add(("repeat",))
        out.append("__repeat__")
    return out


RULES = [Rule("low", _r_low), Rule("repeat", _r_repeat)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.quest in QUESTS and params.setting in SETTINGS and params.mood in MOODS


def quest_turn(world: World) -> None:
    kid = world.get("kid")
    helper = world.get("helper")
    setting = world.facts["setting"]
    mood = world.facts["mood"]
    item = world.facts["quest"]
    kid.meters["tired"] += 1
    helper.memes["repeat"] += 1
    world.say(
        f"On a bright morning, {kid.id} and {helper.id} set out on a quest to find {item.phrase}."
    )
    world.say(
        f"The path led past {setting.detail}, and the whole trip felt like a little adventure."
    )
    world.say(
        f"{kid.id} wanted to hurry, because {kid.pronoun('possessive')} temperament was all sparks and speed."
    )
    world.say(
        f"{helper.id} kept saying, \"Easy, easy, easy -- a quest is won one careful step at a time.\""
    )
    world.say(mood.scene)


def diabetes_beats(world: World) -> None:
    kid = world.get("kid")
    helper = world.get("helper")
    kid.memes["worry"] += 1
    world.say(
        f"Halfway there, {kid.id} stopped and checked {kid.pronoun('possessive')} diabetes bag."
    )
    world.say(
        f"There was the meter, the snack, and the water, right where they should be."
    )
    world.say(
        f"{helper.id} said it again: \"Check, snack, sip. Check, snack, sip.\""
    )
    world.say(
        f"{kid.id} grinned, because the chant sounded serious and silly at the same time."
    )


def comic_mixup(world: World) -> None:
    kid = world.get("kid")
    helper = world.get("helper")
    mood = world.facts["mood"]
    kid.memes["humor"] += 1
    helper.memes["humor"] += 1
    world.say(
        f"Then the map fluttered, and for a moment they both thought the lunch box was the treasure."
    )
    world.say(
        f"{kid.id} stared, then laughed. \"If lunch is treasure, then we are very rich,\" {kid.pronoun()} said."
    )
    world.say(
        f"{helper.id} laughed too, and repeated, \"Very rich, very ready, very hungry.\""
    )
    world.say(mood.joke)


def quest_finish(world: World) -> None:
    kid = world.get("kid")
    helper = world.get("helper")
    item = world.facts["quest"]
    kid.memes["joy"] += 1
    helper.memes["joy"] += 1
    kid.memes["calm"] += 1
    world.say(
        f"At last they found {item.phrase} tucked under a stone beside the trail."
    )
    world.say(
        f"{kid.id} picked it up, checked the meter one more time, and felt proud that {kid.pronoun('possessive')} diabetes kit had traveled with {kid.pronoun('object')}."
    )
    world.say(
        f"Together they walked home with the prize, the snack, and the silly little chant that had carried them there."
    )
    world.say(
        f"It was still an adventure, but now it ended with a safe bag, a found treasure, and a child who knew how to keep going."
    )


def tale(setting: Setting, quest: QuestItem, mood: Mood, kid_name: str = "Milo",
         kid_gender: str = "boy", helper_name: str = "Pip", helper_gender: str = "girl",
         temperament: str = "impulsive") -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="kid",
                           temperament=temperament))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", temperament="calm"))
    world.add(Entity(id="bag", kind="thing", type="bag", label="diabetes bag"))
    kid.meters["tired"] = 1.0
    helper.memes["repeat"] = 1.0

    world.facts.update(setting=setting, quest=quest, mood=mood)
    world.say(
        f"{kid.id} had a bold temperament, and {helper.id} had a calm one."
    )
    world.say(
        f"They packed the diabetes bag before dawn, because adventures went better when the bag came first."
    )
    world.say(
        f"{setting.place.capitalize()} waited like a doorway into a quest."
    )
    world.para()
    quest_turn(world)
    diabetes_beats(world)
    comic_mixup(world)
    world.para()
    quest_finish(world)
    world.facts.update(kid=kid, helper=helper, outcome="found")
    propagate(world, narrate=False)
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="the garden", detail="tall bean poles and buzzing bees",
                      quest_word="quest", route_word="trail"),
    "woods": Setting(id="woods", place="the woods", detail="pale stones and bending trees",
                     quest_word="quest", route_word="path"),
    "shore": Setting(id="shore", place="the shore", detail="round shells and sparkling waves",
                     quest_word="quest", route_word="beach path"),
}

QUESTS = {
    "compass": QuestItem(id="compass", label="compass", phrase="the lost compass", tag="search"),
    "key": QuestItem(id="key", label="key", phrase="the shiny key", tag="search"),
    "kite": QuestItem(id="kite", label="kite", phrase="the red kite", tag="search"),
}

MOODS = {
    "dry": Mood(id="dry", label="dry humor", scene="They repeated the plan so many times it sounded like a song.",
                joke="The joke was so roundabout that even the stones seemed to grin.", fix=""),
    "snack": Mood(id="snack", label="snack humor", scene="They checked the snack twice, and then checked it again for luck.",
                  joke="The snack box looked proud to be treated like treasure.", fix=""),
    "map": Mood(id="map", label="map humor", scene="The map kept folding itself into the wrong shape, as if it wanted to join the game.",
                joke="The map was so dramatic that it nearly asked for a curtain call.", fix=""),
}


@dataclass
class StoryParams:
    setting: str
    quest: str
    mood: str
    kid_name: str
    kid_gender: str
    helper_name: str
    helper_gender: str
    temperament: str
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
    StoryParams(setting="garden", quest="compass", mood="dry", kid_name="Milo", kid_gender="boy",
                helper_name="Pip", helper_gender="girl", temperament="impulsive"),
    StoryParams(setting="woods", quest="key", mood="snack", kid_name="Nia", kid_gender="girl",
                helper_name="Bram", helper_gender="boy", temperament="stubborn"),
    StoryParams(setting="shore", quest="kite", mood="map", kid_name="Owen", kid_gender="boy",
                helper_name="Luna", helper_gender="girl", temperament="curious"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, m) for s in SETTINGS for q in QUESTS for m in MOODS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with diabetes, temperament, repetition, humor, and a quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--temperament", choices=["impulsive", "stubborn", "curious", "bold"])
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
              and (args.mood is None or c[2] == args.mood)]
    if not combos:
        raise StoryError("No valid adventure matches the requested options.")
    setting, quest, mood = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        mood=mood,
        kid_name=args.name or rng.choice(["Milo", "Nia", "Owen", "Zuri", "Tess"]),
        kid_gender=args.gender or rng.choice(["boy", "girl"]),
        helper_name=args.helper or rng.choice(["Pip", "Bram", "Luna", "Dot"]),
        helper_gender=args.helper_gender or rng.choice(["boy", "girl"]),
        temperament=args.temperament or rng.choice(["impulsive", "stubborn", "curious", "bold"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.mood not in MOODS:
        raise StoryError("Invalid parameters for this adventure.")
    world = tale(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        MOODS[params.mood],
        kid_name=params.kid_name,
        kid_gender=params.kid_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        temperament=params.temperament,
    )
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
    return [
        f'Write an adventure story for a child with diabetes that includes the words "diabetes" and "temperament".',
        f"Tell a humorous quest story where {f['kid'].id} and {f['helper'].id} keep repeating a safety chant while searching for {f['quest'].phrase}.",
        f"Write a short adventure with a bold child, a calm helper, and a diabetes check that becomes part of the quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    kid = world.facts["kid"]
    helper = world.facts["helper"]
    quest = world.facts["quest"]
    setting = world.facts["setting"]
    return [
        ("Who went on the quest?",
         f"{kid.id} and {helper.id} went together, with {kid.id}'s temperament making the trip lively and {helper.id}'s calmness keeping it steady."),
        ("What did they carry because of diabetes?",
         "They carried a diabetes bag with a meter, a snack, and water. That mattered because the child needed to check, snack, and sip during the adventure."),
        ("What was funny about the story?",
         "They kept repeating the same little chant, and the lunch box nearly got mistaken for treasure. The repetition made the quest feel playful instead of serious."),
        ("How did the story end?",
         f"They found {quest.phrase} and went home safely. The ending image is a child with diabetes, a found treasure, and a bag packed for the next adventure."),
        ("Where did they search?",
         f"They searched in {setting.place}, which gave the quest its adventure feel and concrete path."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is diabetes?",
         "Diabetes is a condition where a person's body needs help managing sugar, so meals, snacks, and checks matter a lot."),
        ("Why might someone use a meter on a quest?",
         "A meter can help check blood sugar. That check helps a child stay safe and keep going."),
        ("What is temperament?",
         "Temperament is the way someone usually reacts and behaves, like being calm, bold, or impatient."),
        ("Why can repetition be helpful?",
         "Repetition can help people remember important steps. A repeated chant can make a routine easier to follow."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.temperament:
            bits.append(f"temperament={e.temperament}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(S,Q,M) :- setting(S), quest(Q), mood(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MOODS:
        lines.append(asp.fact("mood", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, q, m in asp_valid_combos():
            print(s, q, m)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py
=====================================================================================

A tiny heartwarming storyworld about a child, a church music moment, a shiny brass
object, kindness, and a lesson learned.

Premise
-------
A child wants to handle a polished brass object during a gospel gathering, but
must first choose between showing off and being kind. A small act of kindness
changes the room, earns trust, and leads to a warm lesson learned ending.

The domain is intentionally small: one child, one helper, one brass thing, one
gathering place, and one change in emotional state that drives the prose.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/gospel_brass_kindness_lesson_learned_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"polish": 0.0, "tension": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "joy": 0.0, "lesson": 0.0, "pride": 0.0}

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
    light: str
    mood: str
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
class BrassThing:
    id: str
    label: str
    phrase: str
    sound: str
    gleam: str
    role: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tarnish": 0.0, "shine": 1.0}
        if not self.memes:
            self.memes = {}
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    brass_item: str
    lesson: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.brass: BrassThing | None = None
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.brass = copy.deepcopy(self.brass)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    brass = world.brass
    if brass is None:
        return out
    if child.memes["kindness"] >= THRESHOLD and ("kindness",) not in world.fired:
        world.fired.add(("kindness",))
        helper.meters["trust"] = helper.meters.get("trust", 0.0) + 1
        brass.meters["shine"] = brass.meters.get("shine", 1.0) + 1
        out.append(f"The brass {brass.label} seemed brighter after the kind choice.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["lesson"] >= THRESHOLD and ("lesson",) not in world.fired:
        world.fired.add(("lesson",))
        out.append("The room felt calm enough for everyone to smile.")
    return out


CAUSAL_RULES = [Rule("kindness", _r_kindness), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def kind_choice(world: World, child: Entity, helper: Entity, brass: BrassThing) -> None:
    child.memes["kindness"] += 1
    child.memes["joy"] += 1
    world.say(
        f"In the soft hush of {world.setting.place}, {child.id} noticed the "
        f"{brass.label} shining beside the seats. "
        f'The gospel singing had begun, and {child.id} wanted to lift {brass.phrase} '
        f"right away."
    )
    world.say(
        f'But then {child.id} saw {helper.id} trying to straighten the hymn pages, '
        f"so {child.id} held back and helped first."
    )
    helper.memes["grateful"] = helper.memes.get("grateful", 0.0) + 1
    brass.meters["tarnish"] = max(0.0, brass.meters.get("tarnish", 0.0) - 0.5)
    brass.meters["shine"] = brass.meters.get("shine", 1.0) + 0.5
    world.say(
        f"{child.id} picked up the dropped papers with care, and {helper.id} "
        f"smiled with surprise."
    )
    propagate(world, narrate=True)


def warm_turn(world: World, child: Entity, helper: Entity, brass: BrassThing, lesson: str) -> None:
    child.memes["lesson"] += 1
    child.memes["pride"] += 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f'After the song, {helper.id} let {child.id} hold the {brass.label} for a moment. '
        f'It made a gentle {brass.sound}, and {brass.gleam} like a little sun.'
    )
    world.say(
        f'{helper.id} said, "That was kindness. {lesson.capitalize()}."'
    )
    world.say(
        f'{child.id} nodded, feeling warm inside, because helping had made the day better.'
    )


SETTING_REGISTRY = {
    "chapel": Setting(
        id="chapel",
        place="the little chapel",
        light="soft window light",
        mood="quiet and warm",
        tags={"gospel", "heartwarming"},
    ),
    "hall": Setting(
        id="hall",
        place="the church hall",
        light="bright morning light",
        mood="calm and friendly",
        tags={"gospel", "heartwarming"},
    ),
}

BRASS_REGISTRY = {
    "bell": BrassThing(
        id="bell",
        label="brass bell",
        phrase="the brass bell",
        sound="ding",
        gleam="brighter than honey",
        role="service",
        tags={"brass", "gospel"},
    ),
    "tray": BrassThing(
        id="tray",
        label="brass offering tray",
        phrase="the brass offering tray",
        sound="cling",
        gleam="like gold in the sun",
        role="offering",
        tags={"brass", "gospel"},
    ),
    "candlestick": BrassThing(
        id="candlestick",
        label="brass candlestick",
        phrase="the brass candlestick",
        sound="tink",
        gleam="soft and glowing",
        role="light",
        tags={"brass", "gospel"},
    ),
}

LESSONS = {
    "kindness": "kindness can be stronger than hurry",
    "help_first": "helping first makes the whole room lighter",
    "gentle_hands": "gentle hands keep good things safe",
}

NAMES_GIRL = ["Maya", "Ruby", "Ella", "Nina", "Lila"]
NAMES_BOY = ["Noah", "Eli", "Owen", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTING_REGISTRY:
        for b in BRASS_REGISTRY:
            combos.append((s, b))
    return combos


def explain_rejection(_: BrassThing) -> str:
    return "(No story: the requested setting and brass object do not make a gentle gospel moment.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming gospel-and-brass storyworld.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--brass-item", choices=BRASS_REGISTRY)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.brass_item is None or c[1] == args.brass_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, brass_item = rng.choice(combos)
    lesson = args.lesson or rng.choice(sorted(LESSONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper = args.helper or rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL)
    return StoryParams(
        setting=setting,
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        helper_gender=helper_gender,
        brass_item=brass_item,
        lesson=lesson,
    )


def tell(setting: Setting, child: Entity, helper: Entity, brass: BrassThing, lesson: str) -> World:
    world = World(setting)
    world.add(child)
    world.add(helper)
    world.brass = brass

    world.say(
        f"{child.id} came to {setting.place} on a morning that felt quiet and kind. "
        f"The air was {setting.mood}, with {setting.light} resting on the pews."
    )
    world.say(
        f"Near the front sat {brass.phrase}, polished and proud, ready for the gospel song."
    )
    world.para()
    kind_choice(world, child, helper, brass)
    world.para()
    warm_turn(world, child, helper, brass, lesson)
    world.facts.update(
        child=child,
        helper=helper,
        brass=brass,
        lesson=lesson,
        setting=setting,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY or params.brass_item not in BRASS_REGISTRY:
        raise StoryError("Invalid story parameters.")
    if params.lesson not in LESSONS:
        raise StoryError("Invalid lesson.")
    setting = SETTING_REGISTRY[params.setting]
    brass = BRASS_REGISTRY[params.brass_item]
    child = Entity(id=params.child_name, kind="character", type=params.child_gender, role="child")
    helper = Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper")
    world = tell(setting, child, helper, copy.deepcopy(brass), LESSONS[params.lesson])
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming gospel story for a small child that includes the words "gospel" and "brass".',
        f"Tell a gentle story where {f['child'].id} notices a {f['brass'].label} during a gospel gathering and learns to help first.",
        f"Write a story about kindness and a lesson learned in {f['setting'].place} with a shiny brass object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, brass, lesson = f["child"], f["helper"], f["brass"], f["lesson"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who comes to a gospel gathering and learns a kind lesson."),
        ("What shiny object is mentioned?", f"The story mentions {brass.phrase}, a brass object that shines in the room."),
        ("What did {0} do that was kind?".format(child.id), f"{child.id} helped {helper.id} first by picking up the dropped hymn pages. That choice showed kindness before asking for the brass item."),
        ("What lesson did the child learn?", f"The child learned that {lesson}. That lesson stayed with them because helping made the gathering warmer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is brass?", "Brass is a shiny metal that can be polished until it glows. People often make bells, trays, and other special things from it."),
        ("What is gospel music?", "Gospel music is joyful singing about faith and hope. It is often warm, lively, and sung together."),
        ("What does kindness mean?", "Kindness means helping, sharing, and caring about someone else's needs. Kind people make a room feel softer and safer."),
        ("Why do shiny things need gentle hands?", "Shiny things can be kept nice when people hold them carefully. Gentle hands help them stay bright and safe."),
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
        lines.append(f"  {e.id:8} ({e.type}) meters={e.meters} memes={e.memes} role={e.role}")
    if world.brass:
        lines.append(f"  brass    ({world.brass.id}) meters={world.brass.meters} tags={sorted(world.brass.tags)}")
    return "\n".join(lines)


ASP_RULES = r"""
good_story(S,B) :- setting(S), brass(B).
heartwarming(S) :- setting(S).
kindness_event :- child_kindness.
lesson_event :- lesson_learned.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for bid in BRASS_REGISTRY:
        lines.append(asp.fact("brass", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        setting="chapel",
        child_name="Maya",
        child_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        brass_item="bell",
        lesson="kindness",
    ),
    StoryParams(
        setting="hall",
        child_name="Eli",
        child_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        brass_item="tray",
        lesson="help_first",
    ),
    StoryParams(
        setting="chapel",
        child_name="Nina",
        child_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        brass_item="candlestick",
        lesson="gentle_hands",
    ),
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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming gospel story for a small child that includes the words "gospel" and "brass".',
        f"Tell a gentle story where {f['child'].id} notices a {f['brass'].label} during a gospel gathering and learns to help first.",
        f"Write a story about kindness and a lesson learned in {f['setting'].place} with a shiny brass object.",
    ]


if __name__ == "__main__":
    main()

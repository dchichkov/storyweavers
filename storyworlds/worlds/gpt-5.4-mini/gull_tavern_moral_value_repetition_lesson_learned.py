#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gull_tavern_moral_value_repetition_lesson_learned.py
====================================================================================

A standalone story world for a tiny space-adventure moral tale about a gull,
a tavern, repetition, and a lesson learned.

Premise:
- A child or crew member keeps repeating a mistake inside a spaceport tavern.
- A gull-like helper or lookout notices the trouble.
- A moral choice changes the outcome: honesty, patience, or sharing beats pride.
- The repeated action becomes a refrain in the story, and the ending proves the
  lesson was learned in the world state.

The story is kept small and classical: setup, repeated temptation, turn,
resolution, and an ending image.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/gull_tavern_moral_value_repetition_lesson_learned.py
    python storyworlds/worlds/gpt-5.4-mini/gull_tavern_moral_value_repetition_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4-mini/gull_tavern_moral_value_repetition_lesson_learned.py --qa --json
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot", "mechanic"}
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

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
    details: str
    window: str
    stars: str

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
class Moral:
    id: str
    value: str
    refrain: str
    action: str
    lesson: str
    change: str
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
class Repetition:
    id: str
    cue: str
    line: str
    times: int
    consequences: list[str]
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
class Lesson:
    id: str
    problem: str
    fix: str
    ending: str
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["repeat"] < THRESHOLD:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["tension"] += 1
        out.append("__repeat__")
    return out


def _r_moral_shift(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("hero")
    if actor.memes["honesty"] >= THRESHOLD and actor.memes["tension"] >= THRESHOLD:
        sig = ("moral", actor.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        actor.memes["resolve"] += 1
        world.get("room").meters["calm"] += 1
        out.append("__moral__")
    return out


CAUSAL_RULES = [Rule("repetition", "social", _r_repetition), Rule("moral_shift", "social", _r_moral_shift)]


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


def predict_spill(world: World, repeat_id: str) -> dict:
    sim = world.copy()
    sim.get(repeat_id).meters["repeat"] += 1
    propagate(sim, narrate=False)
    return {
        "tension": sim.get("hero").memes["tension"],
        "calm": sim.get("room").meters["calm"],
    }


def intro(world: World, hero: Entity, gull: Entity, setting: Setting) -> None:
    world.say(
        f"On a glittering evening, {hero.id} and the gull watched the {setting.place} blink under the stars. "
        f"{setting.details}"
    )
    world.say(
        f"{hero.id} liked the bright noise of the {setting.place}, and the gull kept hopping to the same rail again and again."
    )


def need(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"Inside the {setting.place}, the air smelled of soup, metal, and old stories. "
        f"But one small problem kept coming back: the captain's map had drifted toward the open hatch."
    )


def repeat_warning(world: World, hero: Entity, gull: Entity, moral: Moral, rep: Repetition, lesson: Lesson) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["honesty"] += 1
    world.say(
        f'"{rep.line}" the gull cried, once, then again, and then one more time, as if repetition could make the warning louder.'
    )
    world.say(
        f'{hero.id} kept hearing the same thought: {rep.cue}. {hero.id} wanted to ignore it, but {moral.value} mattered more.'
    )
    world.say(
        f'The gull pointed at the drifting map and the open hatch. "{lesson.problem}"'
    )


def choose_good(world: World, hero: Entity, moral: Moral) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f'{hero.id} took a breath and chose to do the right thing. {moral.action.capitalize()}, '
        f'and the room felt steadier at once.'
    )


def fix_it(world: World, hero: Entity, gull: Entity, setting: Setting, lesson: Lesson) -> None:
    room = world.get("room")
    room.meters["calm"] += 1
    world.say(
        f"{hero.id} shut the hatch, set the map on the table, and thanked the gull for the warning. "
        f"{lesson.fix.capitalize()}."
    )
    world.say(
        f'The {setting.place} settled down again, and the stars beyond the window looked kind instead of lonely.'
    )
    world.say(
        f"{lesson.ending} {hero.id} and the gull sat together in the warm light, smaller mistakes left behind."
    )


def tell(setting: Setting, moral: Moral, rep: Repetition, lesson: Lesson,
         hero_name: str = "Mira", hero_type: str = "girl",
         gull_name: str = "Glim", gull_type: str = "bird") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    gull = world.add(Entity(id=gull_name, kind="character", type=gull_type, role="helper", label="the gull"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    world.facts.update(setting=setting, moral=moral, repetition=rep, lesson=lesson, hero=hero, gull=gull, room=room)

    intro(world, hero, gull, setting)
    world.para()
    need(world, hero, setting)
    repeat_warning(world, hero, gull, moral, rep, lesson)
    hero.meters["repeat"] += 1
    propagate(world, narrate=False)
    pred = predict_spill(world, "hero")
    world.facts["prediction"] = pred
    world.para()
    choose_good(world, hero, moral)
    fix_it(world, hero, gull, setting, lesson)
    hero.memes["lesson_learned"] += 1
    world.facts["outcome"] = "learned"
    return world


SETTINGS = {
    "tavern": Setting(
        "tavern",
        "tavern",
        "The tables were bolted to the floor, a brass lamp glowed over the counter, and the window showed a silver river of stars.",
        "the round window",
        "bright stars",
    ),
    "spaceport": Setting(
        "spaceport",
        "spaceport tavern",
        "A sleepy freight shuttle rested outside, and the mugs on the shelf trembled when the docking bell rang.",
        "the porthole",
        "distant stars",
    ),
    "moon_hall": Setting(
        "moon_hall",
        "moon tavern",
        "The walls were pale as sugar, and an old jukebox hummed beside a crate of orbit apples.",
        "the moon glass",
        "far stars",
    ),
}

MORALS = {
    "honesty": Moral(
        "honesty",
        "honesty",
        "being honest",
        "tell the truth about the missing map",
        "Honesty is the bravest choice",
        "the room turned peaceful",
        tags={"honesty", "moral"},
    ),
    "kindness": Moral(
        "kindness",
        "kindness",
        "sharing kindly",
        "give the gull half the cracker first",
        "Kindness helps everyone breathe easier",
        "the air felt softer",
        tags={"kindness", "moral"},
    ),
    "patience": Moral(
        "patience",
        "patience",
        "waiting carefully",
        "wait for the storm bell before opening the hatch",
        "Patience keeps trouble from growing",
        "the stars stayed calm",
        tags={"patience", "moral"},
    ),
}

REPETITIONS = {
    "warning_three_times": Repetition(
        "warning_three_times",
        "open hatch",
        "Don't leave the hatch open!",
        3,
        ["again", "again", "one more time"],
        tags={"repeat", "warning"},
    ),
    "noisy_rhythm": Repetition(
        "noisy_rhythm",
        "drifted map",
        "The map keeps drifting!",
        2,
        ["again", "again"],
        tags={"repeat", "map"},
    ),
}

LESSONS = {
    "moral_value": Lesson(
        "moral_value",
        "The ship can slip if nobody tells the truth.",
        "So the hero spoke up and fixed the mistake right away.",
        "That is why the gull nodded, as if the lesson had finally landed.",
        tags={"lesson", "moral"},
    ),
    "lesson_learned": Lesson(
        "lesson_learned",
        "A small problem gets bigger when it is ignored.",
        "So the hero stopped, listened, and made the safe choice.",
        "The mistake did not grow any farther after that.",
        tags={"lesson"},
    ),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    moral: str
    repetition: str
    lesson: str
    hero_name: str
    hero_type: str
    gull_name: str = "Glim"
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, m, r, l) for s in SETTINGS for m in MORALS for r in REPETITIONS for l in LESSONS]


def explain_rejection() -> str:
    return "(No story: choose one setting, one moral, one repetition, and one lesson to make a complete tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-tavern moral story world with a gull.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--repetition", choices=REPETITIONS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gull-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
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
    if any(v is None for v in (args.setting, args.moral, args.repetition, args.lesson)):
        pass
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.moral:
        combos = [c for c in combos if c[1] == args.moral]
    if args.repetition:
        combos = [c for c in combos if c[2] == args.repetition]
    if args.lesson:
        combos = [c for c in combos if c[3] == args.lesson]
    if not combos:
        raise StoryError(explain_rejection())
    setting, moral, repetition, lesson = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(["Mira", "Nova", "Pip", "Lio", "Ada", "Juno"])
    gull_name = args.gull_name or rng.choice(["Glim", "Sail", "Rook", "Skim"])
    return StoryParams(setting, moral, repetition, lesson, hero_name, hero_type, gull_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly space adventure story that includes the words "gull" and "tavern".',
        f"Tell a story where {f['hero'].id} keeps hearing the same warning in a {f['setting'].place} and finally learns a moral lesson.",
        f"Write a short moral tale with repetition, a helpful gull, and a lesson learned at the {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    gull = f["gull"]
    setting = f["setting"]
    moral = f["moral"]
    rep = f["repetition"]
    lesson = f["lesson"]
    pred = f["prediction"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and the gull inside the {setting.place}. The gull keeps the space adventure moving by pointing out the danger again and again.",
        ),
        QAItem(
            question="Why did the warning repeat several times?",
            answer=f"The warning repeated because the trouble was easy to forget and the story wanted the feeling of repetition. That made the moment feel louder until {hero.id} finally listened.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{lesson.ending} {moral.lesson}. {hero.id} learned that {moral.value} matters more than ignoring a problem, and the calmer room proved it.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The open trouble was fixed, the room became calm, and {hero.id} chose the safe answer instead of repeating the mistake. The gull's warning helped turn the ending around.",
        ),
        QAItem(
            question="What did the prediction show?",
            answer=f"If the problem had been ignored, the tension would have risen to {pred['tension']} and the calm would have stayed at {pred['calm']}. That is why the hero acted before things got worse.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gull": [
        QAItem(
            question="What is a gull?",
            answer="A gull is a sea bird that often flies near harbors, boats, and shorelines. It has sharp eyes and a loud voice, so it can seem like a lookout in a story.",
        )
    ],
    "tavern": [
        QAItem(
            question="What is a tavern?",
            answer="A tavern is a place where grown-ups gather to eat, drink, and talk. In a space story, it can become a cozy room near the stars.",
        )
    ],
    "lesson": [
        QAItem(
            question="Why do stories repeat a warning?",
            answer="Repeating a warning helps the reader remember it and feel how serious it is. It also makes the lesson learned stand out at the end.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea like honesty, kindness, or patience that helps people choose well. Stories use moral values to show why one choice is better than another.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    out.extend(WORLD_KNOWLEDGE["gull"])
    out.extend(WORLD_KNOWLEDGE["tavern"])
    out.extend(WORLD_KNOWLEDGE["lesson"])
    out.extend(WORLD_KNOWLEDGE["moral"])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
repeat(E) :- entity(E), meter(E, repeat, V), V >= 1.
moral_shift(E) :- entity(E), meme(E, honesty, H), H >= 1, meme(E, tension, T), T >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    for rid in REPETITIONS:
        lines.append(asp.fact("repetition", rid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1."))
    clingo = sorted(set(asp.atoms(model, "setting")))
    python = sorted((s,) for s in SETTINGS)
    ok = clingo == python
    print(f"OK: ASP settings match Python ({len(clingo)}).") if ok else print("MISMATCH: settings differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MORALS[params.moral],
        REPETITIONS[params.repetition],
        LESSONS[params.lesson],
        params.hero_name,
        params.hero_type,
        params.gull_name,
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


CURATED = [
    StoryParams("tavern", "honesty", "warning_three_times", "moral_value", "Nova", "girl", "Glim"),
    StoryParams("spaceport", "kindness", "noisy_rhythm", "lesson_learned", "Mira", "boy", "Skim"),
    StoryParams("moon_hall", "patience", "warning_three_times", "lesson_learned", "Ada", "girl", "Rook"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show moral/1.\n#show repetition/1.\n#show lesson/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{k}" for k in SETTINGS))
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
        header = f"### {sample.params.hero_name}: {sample.params.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blonde_surprise_fable.py
========================================================

A small, self-contained story world in a fable style: a blonde child-animal
meets an unexpected surprise, learns a patient lesson, and ends with a changed
scene that proves the turn.

The domain is intentionally tiny:
- one blonde protagonist
- one cautious friend or elder helper
- one hidden surprise
- one simple problem that becomes a warm lesson

The prose aims for a classic fable feeling: concrete setting, a small moral
turn, and a closing image that shows what changed.
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
SURPRISE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    id: str
    place: str
    detail: str
    weather: str

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
class Surprise:
    id: str
    reveal: str
    hidden: str
    kind: str
    gift: str
    glow: str
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
class Problem:
    id: str
    worry: str
    risk: str
    action: str
    danger: str
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
    name: str
    method: str
    result: str
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


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["wonder"] < SURPRISE_MIN:
        return out
    sig = ("surprise", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["delight"] += 1
    world.get("gift").meters["revealed"] += 1
    out.append("__surprise__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gift").meters["revealed"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.get("helper")
    helper.memes["pride"] += 1
    out.append("The little surprise made the morning feel brighter.")
    return out


CAUSAL_RULES = [
    Rule("surprise", "social", _r_surprise),
    Rule("settle", "emotional", _r_settle),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def surprise_triggered(world: World) -> bool:
    return world.get("gift").meters["revealed"] >= THRESHOLD


def can_choose_lesson(problem: Problem, lesson: Lesson) -> bool:
    return problem.id in {"lost_song", "muddy_path"} and lesson.id in {"listen", "share"}


def choose_lesson(problem: Problem) -> Lesson:
    for lesson in LESSONS.values():
        if can_choose_lesson(problem, lesson):
            return lesson
    raise StoryError("No reasonable lesson fits this fable.")


def predict_surprise(world: World) -> dict:
    sim = world.copy()
    _reveal(sim, narrate=False)
    return {
        "revealed": surprise_triggered(sim),
        "delight": sim.get("hero").memes["delight"],
    }


def _reveal(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    gift = world.get("gift")
    hero.meters["wonder"] += 1
    gift.meters["opened"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In {setting.place}, {hero.id} the blonde little {hero.type} woke to a day "
        f"that smelled of grass and dew. {setting.detail}"
    )
    world.say(
        f"{helper.id} watched from nearby, calm as a stone, while {hero.id} "
        f"looked for something to make the day special."
    )


def want_play(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["want"] += 1
    world.say(
        f"{hero.id} wanted to {problem.action}, but {problem.worry} made "
        f"{hero.pronoun('possessive')} brow pinch."
    )


def warn(world: World, helper: Entity, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{helper.id} said, "{problem.risk}. If you hurry, {problem.danger}."'
    )


def hesitate(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} paused. The wish to {problem.action} was still there, but "
        f"{hero.pronoun('possessive')} eyes kept drifting to the shade by the gate."
    )


def reveal(world: World, hero: Entity, surprise: Surprise) -> None:
    _reveal(world)
    hero.memes["surprise"] += 1
    world.say(
        f"Then {surprise.reveal} -- the {surprise.kind} was hiding under the "
        f"blue cloth, and {surprise.gift} glowed {surprise.glow}."
    )


def act_on_surprise(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} laughed in surprise and held the gift close, while the "
        f"morning seemed to brighten around {hero.pronoun('object')}."
    )


def lesson_turn(world: World, helper: Entity, hero: Entity, lesson: Lesson) -> None:
    hero.memes["lesson"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} smiled and showed {hero.id} that {lesson.method}. "
        f"{lesson.result}"
    )


def ending(world: World, hero: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"By the end, {hero.id} and {helper.id} sat in {setting.place} beside "
        f"the opened gift, and the blonde fur on {hero.id}'s head shone in the sun."
    )
    world.say(
        "The day began with worry, but it ended in quiet joy, and that was the "
        "surprise hidden in the field."
    )


def tell(setting: Setting, surprise: Surprise, problem: Problem, lesson: Lesson,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    gift = world.add(Entity(id="gift", kind="thing", type="thing", label=surprise.kind))
    hero.meters["blonde"] = 1.0
    hero.meters["wonder"] = 0.0
    hero.memes["curious"] = 1.0
    world.facts["surprise"] = surprise
    world.facts["problem"] = problem
    world.facts["lesson"] = lesson

    introduce(world, hero, helper, setting)
    world.para()
    want_play(world, hero, problem)
    warn(world, helper, hero, problem)
    hesitate(world, hero, problem)
    world.para()
    reveal(world, hero, surprise)
    act_on_surprise(world, hero, surprise)
    lesson_turn(world, helper, hero, lesson)
    world.para()
    ending(world, hero, helper, setting)

    world.facts.update(
        hero=hero,
        helper=helper,
        gift=gift,
        revealed=surprise_triggered(world),
        mood="bright" if hero.memes["joy"] > 0 else "quiet",
    )
    return world


SETTINGS = {
    "meadow": Setting("meadow", "the meadow", "The grass bent softly in the wind.", "sunny"),
    "orchard": Setting("orchard", "the orchard", "Apple trees made a green roof overhead.", "sunny"),
    "brook": Setting("brook", "the brook", "A narrow stream sang over the stones.", "bright"),
}

SURPRISES = {
    "basket": Surprise("basket", "At last, the cloth lifted", "a basket", "basket", "a little basket of apples", "like a tiny moon", {"gift", "apple"}),
    "ribbon": Surprise("ribbon", "To the hero's astonishment, the box opened", "a ribbon", "box", "a ribbon of wildflowers", "soft and shining", {"gift", "flowers"}),
    "shell": Surprise("shell", "With a gentle creak, the stone cracked", "a shell", "stone", "a smooth shell charm", "pale as milk", {"gift", "shell"}),
}

PROBLEMS = {
    "lost_song": Problem("lost_song", "the old song was missing from the morning", "Listen first", "follow the quiet path", "the song might stay lost", {"quiet", "search"}),
    "muddy_path": Problem("muddy_path", "the path was slippery after the rain", "Walk carefully", "dash across the mud", "the feet might slide", {"mud", "path"}),
}

LESSONS = {
    "listen": Lesson("listen", "listen carefully", "listening first helps find the right thing", "Once {hero} listened, the answer was easy to see.", {"listen"}),
    "share": Lesson("share", "share the find", "sharing makes a surprise even sweeter", "When {hero} shared, the whole field felt warmer.", {"share"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Elsie", "Mabel"]
BOY_NAMES = ["Otto", "Robin", "Toby", "Ezra", "Simon"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    surprise: str
    problem: str
    lesson: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for l in LESSONS:
                for sp in SURPRISES:
                    combos.append((s, sp, p, l))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sur = f["surprise"]
    problem = f["problem"]
    return [
        f'Write a fable-style story for a child that includes the word "blonde" and a surprise in {f["hero"].id}\'s day.',
        f"Tell a gentle fable about {hero.id}, who is blonde, learns not to rush past {problem.worry}, and finds {sur.kind} instead.",
        f"Write a short moral story where a blonde character expects one thing, but a hidden surprise changes the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    sur = f["surprise"]
    lesson = f["lesson"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a blonde little {hero.type}, and {helper.id}, who helps keep the day calm."),
        ("Why did {hero} pause before acting?".replace("{hero}", hero.id),
         f"{hero.id} paused because {problem.worry} made the idea feel risky. {helper.id} warned that {problem.danger}, so {hero.id} stopped to listen."),
        ("What was the surprise?",
         f"The surprise was {sur.gift}, and it was hidden as {sur.hidden}. When it was revealed, it changed the whole mood of the day."),
        ("What did the story teach?",
         f"It taught that {lesson.method}. That choice led to a kinder ending, with worry turning into joy."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does blonde mean?",
         "Blonde means pale yellow or light-colored hair or fur. In stories, it can help picture a character clearly."),
        ("What is a surprise?",
         "A surprise is something you do not expect. It can make a moment feel exciting, warm, or wonderful."),
        ("What is a fable?",
         "A fable is a short story that often uses animals or simple characters to teach a lesson."),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise_revealed(H) :- hero(H), wonder(H, W), W >= 1.
gift_opened(G) :- gift(G), opened(G, O), O >= 1.
happy_end(H) :- surprise_revealed(H), gift_opened(gift).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show surprise_revealed/1.\n#show happy_end/1."))
    atoms = set(asp.atoms(model, "surprise_revealed"))
    rc = 0
    if atoms:
        print("OK: ASP program is parsable.")
    else:
        print("OK: ASP program loaded.")
    return rc


CURATED = [
    StoryParams("meadow", "basket", "lost_song", "listen", "Mina", "girl", "Rex", "boy"),
    StoryParams("orchard", "ribbon", "muddy_path", "share", "Otto", "boy", "Mabel", "girl"),
    StoryParams("brook", "shell", "lost_song", "share", "Elsie", "girl", "Finn", "boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: blonde surprise fable.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid hero gender.")
    setting = args.setting or rng.choice(list(SETTINGS))
    surprise = args.surprise or rng.choice(list(SURPRISES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    lesson = args.lesson or choose_lesson(PROBLEMS[problem]).id
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(setting, surprise, problem, lesson, hero_name, hero_gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SURPRISES[params.surprise],
        PROBLEMS[params.problem],
        LESSONS[params.lesson],
        params.hero_name,
        params.hero_gender,
        params.helper_name,
        params.helper_gender,
    )
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


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise SystemExit(1)
        rc = asp_verify()
        print(sample.story)
        sys.exit(rc)
    if args.asp:
        for c in asp_valid_combos():
            print(c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} in {p.setting} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

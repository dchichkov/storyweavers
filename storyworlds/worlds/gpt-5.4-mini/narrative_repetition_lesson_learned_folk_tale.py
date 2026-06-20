#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/narrative_repetition_lesson_learned_folk_tale.py
================================================================================

A standalone story world for a small folk-tale domain: a child or young helper
makes a repeated mistake, learns the lesson, and finishes with a changed action.

Seed prompt / intent
--------------------
Words: narrative
Features: Repetition, Lesson Learned
Style: Folk Tale

This world builds a short, classical folktale shape from simulated state:
a journey, a repeated refrain, a small trouble, a lesson learned, and a closing
image that proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/narrative_repetition_lesson_learned_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/narrative_repetition_lesson_learned_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/narrative_repetition_lesson_learned_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/narrative_repetition_lesson_learned_folk_tale.py --verify
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
LESSON_THRESHOLD = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



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
    mood: str
    road: str
    ending: str

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
class Item:
    id: str
    label: str
    phrase: str
    task: str
    risk: str
    safe: str
    kind: str
    tags: set[str] = field(default_factory=set)

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
class Lesson:
    id: str
    count: int
    text: str
    repeat_text: str
    turns: str
    tags: set[str] = field(default_factory=set)

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
        w = World(self.setting)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.meters["lost"] >= THRESHOLD and ("worry", hero.id) not in world.fired:
        world.fired.add(("worry", hero.id))
        hero.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes["lesson"] >= LESSON_THRESHOLD and ("lesson", hero.id) not in world.fired:
        world.fired.add(("lesson", hero.id))
        hero.memes["calm"] += 1
        out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("lesson", "social", _r_lesson)]


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


def reasonableness_gate(setting: Setting, item: Item, lesson: Lesson) -> bool:
    return setting.id in {"forest", "village", "hill"} and item.kind == "food" and lesson.count == 3


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for l in LESSONS:
                if reasonableness_gate(SETTINGS[s], ITEMS[i], LESSONS[l]):
                    combos.append((s, i, l))
    return combos


def _do_step(world: World, item: Item, lesson: Lesson, narrate: bool = True) -> None:
    hero = world.get("hero")
    hero.memes["hope"] += 1
    hero.meters["carried"] += 1
    hero.meters["bumped"] += 1
    if hero.meters["bumped"] >= lesson.count:
        hero.meters["lost"] += 1
    propagate(world, narrate=narrate)


def predict_turn(world: World, item: Item, lesson: Lesson) -> dict:
    sim = world.copy()
    _do_step(sim, item, lesson, narrate=False)
    return {"lost": sim.get("hero").meters["lost"], "lesson": sim.get("hero").memes["lesson"]}


def setup(world: World, hero: Entity, elder: Entity, item: Item, lesson: Lesson) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, {hero.id} and {elder.id} set out under {world.setting.mood} skies. "
        f"{hero.id} carried {item.phrase}, for {hero.pronoun('possessive')} errand was to {item.task}."
    )
    world.say(
        f"{world.setting.road.capitalize()} was the only way, and {hero.id} whispered the old road-song: "
        f"\"Step softly, step surely,\" as the tale began."
    )


def repeat_beats(world: World, hero: Entity, elder: Entity, item: Item, lesson: Lesson) -> None:
    for n in range(1, lesson.count + 1):
        if n > 1:
            world.para()
        world.say(
            f"The first time, {hero.id} hurried and nearly dropped {item.label}. "
            f"The second time, {hero.id} hurried again and nearly lost the way. "
            f"The third time, {hero.id} stopped to listen."
        )
        hero.meters["bumped"] += 1
        if n < lesson.count:
            hero.memes["restless"] += 1
        else:
            hero.memes["lesson"] += 1
        propagate(world, narrate=False)


def warn(world: World, elder: Entity, hero: Entity, item: Item, lesson: Lesson) -> None:
    pred = predict_turn(world, item, lesson)
    hero.memes["lesson"] += 1
    world.facts["predicted_lost"] = pred["lost"]
    world.say(
        f'{elder.id} raised a hand and said, "{lesson.repeat_text} If you rush, {item.risk}." '
        f"{hero.id} looked down at {item.label} and felt the warning settle in."
    )


def turn(world: World, hero: Entity, elder: Entity, item: Item, lesson: Lesson) -> None:
    hero.meters["lost"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"At last, {hero.id} remembered the lesson and did not hurry. "
        f"{hero.id} took a slower path, and {item.label} stayed safe in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"Then {elder.id} smiled and answered the road-song with a gentler line: "
        f"\"Those who listen arrive with what they love.\""
    )


def ending(world: World, hero: Entity, elder: Entity, item: Item, lesson: Lesson) -> None:
    hero.memes["joy"] += 1
    hero.memes["calm"] += 1
    world.say(
        f"By sunset, {hero.id} reached home with {item.phrase} still whole. "
        f"{hero.id} set it on the table, and the old house seemed warmer for it."
    )
    world.say(
        f"From that day on, whenever {hero.id} faced a long road, {hero.id} remembered: {lesson.turns}."
    )


def tell(setting: Setting, item: Item, lesson: Lesson, hero_name: str = "Pip", hero_type: str = "boy",
         elder_name: str = "Nan", elder_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder", label="the elder"))
    world.add(Entity(id="road", type="road", label=setting.road))
    setup(world, hero, elder, item, lesson)
    world.para()
    warn(world, elder, hero, item, lesson)
    repeat_beats(world, hero, elder, item, lesson)
    world.para()
    turn(world, hero, elder, item, lesson)
    world.para()
    ending(world, hero, elder, item, lesson)
    world.facts.update(hero=hero, elder=elder, item=item, lesson=lesson, setting=setting)
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest path", "golden and soft", "the winding path", "home"),
    "village": Setting("village", "the village lane", "busy and bright", "the lane by the wells", "the cottage"),
    "hill": Setting("hill", "the hill road", "windy and wide", "the little lane", "the hearth"),
}

ITEMS = {
    "bread": Item("bread", "a round loaf of bread", "a round loaf of bread", "deliver it to the old aunt", "the bread might go stale", "the bread will still be warm", "food", {"food", "narrative"}),
    "honey": Item("honey", "a little pot of honey", "a little pot of honey", "carry it to the beekeeper", "the lid might slip", "the honey will stay sweet", "food", {"food"}),
    "porridge": Item("porridge", "a covered bowl of porridge", "a covered bowl of porridge", "bring it to the sick child", "the bowl might tip", "the porridge will stay fit for supper", "food", {"food"}),
}

LESSONS = {
    "slowly": Lesson("slowly", 3, "slowly", "step softly, step surely", "the wise feet that do not rush", {"lesson", "repetition"}),
    "listen": Lesson("listen", 3, "listen", "listen twice before you move", "the careful heart that hears first", {"lesson", "repetition"}),
    "share": Lesson("share", 3, "share", "share what you can and keep your hands steady", "the kind hands that share and do not spill", {"lesson", "repetition"}),
}

GIRL_NAMES = ["Pip", "Mara", "Lina", "Tess", "Nina", "Ada"]
BOY_NAMES = ["Pip", "Rory", "Finn", "Milo", "Jem", "Otis"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    lesson: str
    hero: str
    hero_type: str
    elder: str
    elder_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world with repetition and a learned lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
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
              and (args.item is None or c[1] == args.item)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, lesson = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(GIRL_NAMES if elder_type == "grandmother" else BOY_NAMES)
    return StoryParams(setting, item, lesson, hero, hero_type, elder, elder_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale story that includes the word "narrative" and a repeated lesson about {f["lesson"].text}.',
        f"Tell a short narrative folk tale where {f['hero'].id} carries {f['item'].phrase} and learns not to rush on the road.",
        f"Write a gentle repetition story in a village style where the same warning is heard three times before the child understands.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, elder, item, lesson = f["hero"], f["elder"], f["item"], f["lesson"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, who goes on a little journey with {elder.id}. {hero.id} is the one who learns the lesson by the end."),
        ("What was the repeated lesson?",
         f"The repeated lesson was to {lesson.text}. {elder.id} said it more than once so {hero.id} would remember it on the road."),
        ("What did {0} carry?".format(hero.id),
         f"{hero.id} carried {item.phrase}, because the errand was to {item.task}. Keeping it steady mattered on the winding path."),
        ("How did the story end?",
         f"It ended with {hero.id} arriving home safely with {item.phrase} still whole. That ending shows the lesson was learned and used."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item"].tags) | set(f["lesson"].tags)
    qa = []
    if "food" in tags:
        qa.append(("Why should you carry food carefully?",
                   "Food can spill, break, or go stale, so carrying it carefully helps it arrive ready to eat."))
    if "lesson" in tags:
        qa.append(("Why do stories repeat a lesson?",
                   "Repeating a lesson helps listeners remember it. In folktales, the same words often come back three times."))
    if "repetition" in tags:
        qa.append(("What is repetition in a story?",
                   "Repetition is when a word, phrase, or event happens again and again. It makes a tale feel like a song."))
    return qa


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("forest", "bread", "slowly", "Pip", "boy", "Nan", "grandmother"),
    StoryParams("village", "honey", "listen", "Mara", "girl", "Oma", "grandmother"),
    StoryParams("hill", "porridge", "share", "Finn", "boy", "Grandpa", "grandfather"),
]


ASP_RULES = r"""
valid(S, I, L) :- setting(S), item(I), lesson(L).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    # smoke test generation
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story.")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], LESSONS[params.lesson],
                 params.hero, params.hero_type, params.elder, params.elder_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for x in asp_valid_combos():
            print(x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

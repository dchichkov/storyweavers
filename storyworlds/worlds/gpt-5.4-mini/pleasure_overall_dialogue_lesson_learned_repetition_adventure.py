#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pleasure_overall_dialogue_lesson_learned_repetition_adventure.py
===============================================================================================

A compact storyworld for a small adventure tale about a child exploring a tiny
island trail, learning to pace themselves, and discovering that the overall
pleasure of the journey is better when they share the work, listen, and repeat
the helpful steps.

Seed words: pleasure, overall
Features: Dialogue, Lesson Learned, Repetition
Style: Adventure
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"tired": 0.0, "load": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"hope": 0.0, "frustration": 0.0, "joy": 0.0})

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
    path: str
    challenge: str
    reward: str

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
class Task:
    id: str
    action: str
    repeat_line: str
    effect: str
    risk: str
    lesson: str
    strain: float
    joy_gain: float

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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.steps: list[str] = []

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.steps = list(self.steps)
        return clone


SETTINGS = {
    "reef": Setting("reef", "the sunlit reef", "the reef path", "a steep climb", "a hidden cove"),
    "cave": Setting("cave", "the echoing cave", "the cave path", "a dark bend", "a bright crystal pool"),
    "jungle": Setting("jungle", "the green jungle", "the jungle trail", "a tangled bridge", "a lookout tree"),
}

TASKS = {
    "carry_shells": Task(
        "carry_shells",
        "carry the shell basket",
        "one shell at a time, one shell at a time",
        "the basket stays steady",
        "the load gets too heavy",
        "carry the basket together and keep the shells safe",
        1.0,
        1.0,
    ),
    "cross_logs": Task(
        "cross_logs",
        "cross the log bridge",
        "step, step, step, and look ahead",
        "the bridge sways but holds",
        "the bridge wobbles more and more",
        "pause and cross slowly, one careful step at a time",
        1.0,
        1.0,
    ),
    "find_map": Task(
        "find_map",
        "follow the map clues",
        "look, point, and look again",
        "the map makes sense",
        "the clues start to blur",
        "read the map aloud and repeat the clues together",
        0.5,
        1.0,
    ),
}

NAMES_GIRL = ["Mia", "Lina", "Nora", "Tia", "Rina", "Ava"]
NAMES_BOY = ["Owen", "Nico", "Ben", "Theo", "Milo", "Jace"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in TASKS:
            combos.append((sid, tid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    hero: str
    hero_gender: str
    helper: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with dialogue, repetition, and a learned lesson.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    return StoryParams(setting, task, hero, hero_gender, helper, helper_gender)


def tell(world: World, params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    trail = world.add(Entity("trail", type="place", label=setting.path))
    goal = world.add(Entity("goal", type="place", label=setting.reward))

    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"On a bright morning, {hero.id} and {helper.id} set out along {setting.path}. "
        f"They were chasing {setting.reward}, and the whole trip promised adventure and pleasure."
    )
    world.say(
        f'"Look," said {helper.id}, "if we go slowly, we will get there." '
        f'"Slowly?" said {hero.id}. "I can go fast!"'
    )
    world.say(
        f'"Then repeat after me," said {helper.id}. "{task.repeat_line}." '
        f'"{task.repeat_line}," said {hero.id}, laughing as the path began to rise.'
    )

    hero.meters["tired"] += task.strain
    hero.memes["frustration"] += 1
    world.para()
    world.say(
        f"Halfway there, the trail turned hard. {setting.challenge.capitalize()} blocked the way, "
        f"and the load or the steps could have gone wrong."
    )
    world.say(
        f'"Maybe this is where we stop," said {hero.id}. '
        f'"No," said {helper.id}, "we can do it by working together."'
    )

    if task.id == "carry_shells":
        helper.meters["load"] += 1
        hero.meters["load"] += 1
        world.say(
            f"They shared the shell basket. {task.repeat_line.capitalize()}. "
            f"The basket stayed level, and the shells did not spill."
        )
    elif task.id == "cross_logs":
        world.say(
            f"They crossed the log bridge together. {task.repeat_line.capitalize()}. "
            f"The bridge swayed once, then settled under their careful feet."
        )
    else:
        world.say(
            f"They stopped and read the map aloud. {task.repeat_line.capitalize()}. "
            f"The clues cleared, and the path to the lookout tree opened up."
        )

    hero.memes["joy"] += 2
    helper.memes["joy"] += 1
    hero.memes["frustration"] = 0.0
    world.para()
    world.say(
        f"At last they reached {setting.reward}. {goal.label.capitalize()} gleamed ahead, "
        f"and {hero.id} grinned. \"Overall, the best part was not racing,\" said {hero.id}, "
        f"\"it was getting there together.\""
    )
    world.say(
        f'"That is the lesson," said {helper.id}. "A good adventure feels better when you listen, '
        f'repeat the safe steps, and keep going as a team."'
    )
    world.say(
        f"So they left with dusty shoes, happy hearts, and the warm pleasure of a day well learned."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        setting=setting,
        task=task,
        trail=trail,
        goal=goal,
        lesson="work together and repeat the safe steps",
        overall="overall, the best part was getting there together",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    task = f["task"]
    return [
        f'Write an adventure story for a young child that includes the words "pleasure" and "overall".',
        f"Tell a story where {hero.id} and {helper.id} travel through {setting.place}, speak to each other, and learn a lesson by repeating a helpful line.",
        f"Write a short adventure with dialogue, repetition, and a lesson learned, ending with a line about pleasure overall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    task = f["task"]
    return [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {helper.id} went together along {setting.path}. They shared the journey and helped each other when the trail got hard.",
        ),
        QAItem(
            question="What repeated line helped them?",
            answer=f'They repeated "{task.repeat_line}." The repeated line helped them slow down and keep doing the safe thing together.',
        ),
        QAItem(
            question="What lesson did they learn?",
            answer=f"They learned to work together and listen before rushing ahead. That lesson made the adventure safer and gave the trip its best ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or experience where someone goes somewhere new, faces a challenge, and keeps going bravely.",
        ),
        QAItem(
            question="What does repetition do in a story?",
            answer="Repetition means saying something again. It can help children remember an important idea and can make a story feel fun and steady.",
        ),
        QAItem(
            question="Why can a lesson learned matter in a story?",
            answer="A lesson learned shows how a character changes after a problem. It helps the story end with a clearer and wiser idea than it began with.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("reef", "carry_shells", "Mia", "girl", "Owen", "boy"),
    StoryParams("cave", "cross_logs", "Nico", "boy", "Tia", "girl"),
    StoryParams("jungle", "find_map", "Ava", "girl", "Theo", "boy"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
task(T) :- task_fact(T).
valid(S, T) :- setting(S), task(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for tid in TASKS:
        lines.append(asp.fact("task_fact", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(World(), params)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible setting/task combos:")
        for s, t in asp_valid_combos():
            print(f"  {s:8} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.setting} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

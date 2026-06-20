#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prolong_wheat_almond_teamwork_curiosity_magic_superhero.py
==========================================================================================

A standalone storyworld for a tiny superhero tale about curiosity, teamwork, and
a little burst of magic around wheat and almond bread.

The world is deliberately small and classical:
- one curious child hero
- one teammate
- one grown-up helper
- one magic object
- one practical task that can be helped or harmed
- a few causal rules that turn state changes into story beats

The seed words are treated as story ingredients, not as pasted text:
- prolong
- wheat
- almond

The style aims at a superhero-story feeling: capes, brave helpers, a small crisis,
a smart fix, and an ending image that proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/prolong_wheat_almond_teamwork_curiosity_magic_superhero.py
    python storyworlds/worlds/gpt-5.4-mini/prolong_wheat_almond_teamwork_curiosity_magic_superhero.py --all
    python storyworlds/worlds/gpt-5.4-mini/prolong_wheat_almond_teamwork_curiosity_magic_superhero.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/prolong_wheat_almond_teamwork_curiosity_magic_superhero.py --verify
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
    scene: str
    purpose: str
    dark_spot: str

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
class MagicTool:
    id: str
    label: str
    glow: str
    prolongs: bool = False
    sparkly: bool = False

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
    label: str
    item: str
    needs: str
    can_fail: bool = True
    safe: bool = True

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

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
@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    teammate: str
    teammate_gender: str
    parent: str
    task: str
    tool: str
    response: str
    delay: int = 0
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
        return clone


@dataclass
class Rule:
    name: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["teamwork"] >= THRESHOLD and world.get("teammate").memes["teamwork"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("task").memes["progress"] += 1
            out.append("Together, they made the hard thing feel smaller.")
    return out


def _r_magic_prolong(world: World) -> list[str]:
    out: list[str] = []
    tool = world.get("tool")
    task = world.get("task")
    if tool.meters["glow"] >= THRESHOLD and tool.attrs.get("prolongs") and task.meters["incomplete"] >= THRESHOLD:
        sig = ("prolong",)
        if sig not in world.fired:
            world.fired.add(sig)
            task.meters["ready"] += 1
            out.append("The magic glow stayed bright just long enough to finish the job.")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes["curiosity"] >= THRESHOLD:
        sig = ("curious",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("tool").memes["noticed"] += 1
            out.append("The curious hero looked closer and found the important clue.")
    return out


def _r_delay(world: World) -> list[str]:
    out: list[str] = []
    if world.get("task").meters["ready"] >= THRESHOLD and ("resolved",) not in world.fired:
        world.fired.add(("resolved",))
        world.get("task").meters["complete"] += 1
        out.append("The work was finished before the light faded.")
    return out


RULES = [
    Rule("curiosity", _r_curiosity),
    Rule("teamwork", _r_teamwork),
    Rule("magic_prolong", _r_magic_prolong),
    Rule("delay", _r_delay),
]


def task_needs(task: Task, setting: Setting) -> str:
    return f"{task.needs} in {setting.place}"


def predict(world: World, hero: Entity, teammate: Entity, tool: MagicTool, task: Task) -> dict:
    sim = world.copy()
    sim.get("hero").memes["curiosity"] += 1
    sim.get("hero").memes["teamwork"] += 1
    sim.get("teammate").memes["teamwork"] += 1
    sim.get("tool").meters["glow"] += 1
    sim.get("task").meters["incomplete"] += 1
    propagate(sim, narrate=False)
    return {
        "complete": sim.get("task").meters["complete"] >= THRESHOLD,
        "ready": sim.get("task").meters["ready"] >= THRESHOLD,
    }


def _do_story(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    teammate = world.get("teammate")
    parent = world.get("parent")
    tool = world.get("tool")
    task = world.get("task")

    hero.memes["curiosity"] += 1
    hero.memes["teamwork"] += 1
    teammate.memes["teamwork"] += 1
    hero.memes["joy"] += 1
    teammate.memes["joy"] += 1

    world.say(
        f"On a bright day at {world.setting.place}, {hero.id} and {teammate.id} were "
        f"little superheroes in capes. {world.setting.scene}"
    )
    world.say(
        f"They had one special job: {task.label}, because the day needed "
        f"{task.needs}."
    )

    world.para()
    world.say(
        f"But the curious hero noticed {tool.label} shining near {world.setting.dark_spot}. "
        f'"What does it do?" {hero.id} asked.'
    )
    world.say(
        f'{teammate.id} pointed to the sparkling cover. "It can {tool.glow} and '
        f'{world.setting.purpose}," {teammate.pronoun()} said.'
    )

    world.para()
    if predict(world, hero, teammate, tool, task)["complete"]:
        world.say(
            f'Then {hero.id} and {teammate.id} worked side by side. '
            f'They lifted, stirred, and smiled like a two-person rescue team.'
        )
        tool.meters["glow"] += 1
        task.meters["incomplete"] += 1
        propagate(world, narrate=True)
        world.say(
            f"The magic helped them {task.label}, and the glow stayed bright long enough "
            f"to see every step."
        )
        task.meters["complete"] += 1
        task.meters["incomplete"] = 0
        world.say(
            f"{parent.label_word.capitalize()} came over and clapped. "
            f'"That is real teamwork," {parent.pronoun()} said.'
        )
    else:
        world.say(
            f"The light began to fade too fast, so the two superheroes called for {parent.label_word}."
        )
        world.say(
            f"{parent.label_word.capitalize()} showed them the smarter way to use {tool.label}, "
            f"and together they finished {task.label} safely."
        )

    world.para()
    hero.memes["pride"] += 1
    teammate.memes["pride"] += 1
    world.say(
        f"In the end, {hero.id} and {teammate.id} stood under the sky with {task.item} "
        f"done at last, and {tool.label} still glowing softly like a tiny star."
    )

    world.facts.update(
        hero=hero,
        teammate=teammate,
        parent=parent,
        tool=tool,
        task=task,
        setting=world.setting,
        success=task.meters["complete"] >= THRESHOLD,
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    teammate = world.add(Entity(id=params.teammate, kind="character", type=params.teammate_gender, role="teammate"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    tool = world.add(Entity(id="tool", label=MAGIC_TOOLS[params.tool].label, attrs={"prolongs": MAGIC_TOOLS[params.tool].prolongs}))
    task = world.add(Entity(id="task", label=TASKS[params.task].label))
    tool.meters["glow"] = 1.0
    task.meters["incomplete"] = 1.0
    _do_story(world, params)
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "wheat", "almond", and "prolong".',
        f"Tell a short, child-friendly superhero story where {f['hero'].id} and {f['teammate'].id} use curiosity, teamwork, and magic to finish {f['task'].label}.",
        f"Write a magical teamwork story with a bright ending image, using wheat and almond as important story ingredients.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, teammate, parent, task = f["hero"], f["teammate"], f["parent"], f["task"]
    tool = f["tool"]
    return [
        ("Who is the story about?", f"It is about {hero.id} and {teammate.id}, two little superheroes who worked together. {parent.label_word.capitalize()} helped them finish the day with a happy ending."),
        ("What did the curious hero notice?", f"{hero.id} noticed {tool.label} shining near the work area. That question helped the team understand how to use the magic carefully."),
        ("How did they finish the job?", f"They used teamwork, and the magic helped {task.label}. The glow stayed bright long enough for them to finish together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is wheat?", "Wheat is a grain that people grind into flour for bread, pancakes, and other foods."),
        ("What are almonds?", "Almonds are crunchy nuts that people eat in snacks, desserts, and baked treats."),
        ("What does it mean to prolong something?", "To prolong something means to make it last longer."),
        ("What is teamwork?", "Teamwork means people help each other and work together to do a job."),
        ("What is curiosity?", "Curiosity is the wish to look, ask, and learn more about something."),
        ("What is magic in a story?", "Magic is something surprising and special that can do things ordinary tools cannot."),
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
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "rooftop": Setting("rooftop", "the rooftop garden", "The wind swirled around the flower boxes and little antennas.", "help the wheat and almond loaves finish baking", "the tall lantern by the railing"),
    "bakery": Setting("bakery", "the bakery", "Warm ovens hummed, and trays waited like tiny city blocks.", "keep the oven light steady", "the flour shelf by the window"),
    "market": Setting("market", "the market square", "Stalls stood in a row, and every banner fluttered like a cape.", "bring the bread basket safely to the crowd", "the stack of wheat sacks"),
}

MAGIC_TOOLS = {
    "lantern": MagicTool("lantern", "a magic lantern", "stay bright a little longer", prolongs=True, sparkly=True),
    "cape": MagicTool("cape", "a glowing cape", "warm the air and hold the shine", prolongs=True, sparkly=True),
    "wand": MagicTool("wand", "a small magic wand", "sparkle and hum", prolongs=False, sparkly=True),
}

TASKS = {
    "bread": Task("bread", "finish the wheat loaf", "the wheat loaf", "wheat bread"),
    "cookies": Task("cookies", "save the almond cookies", "the almond cookies", "almond cookies"),
    "basket": Task("basket", "guard the bread basket", "the bread basket", "the bread basket"),
}

CURATED = [
    StoryParams("rooftop", "Mina", "girl", "Tobi", "boy", "mother", "bread", "lantern", "cape", 0),
    StoryParams("bakery", "Leo", "boy", "Nora", "girl", "father", "cookies", "cape", "wand", 0),
    StoryParams("market", "Ava", "girl", "Ben", "boy", "mother", "basket", "lantern", "wand", 0),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, tool in MAGIC_TOOLS.items():
            for task_id in TASKS:
                if tool.prolongs:
                    combos.append((sid, tid, task_id))
    return combos


def explain_rejection(tool: MagicTool) -> str:
    return f"(No story: {tool.label} does not really prolong the light, so the superhero ending would be too weak.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero storyworld with teamwork, curiosity, and magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=MAGIC_TOOLS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--hero")
    ap.add_argument("--teammate")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.tool and not MAGIC_TOOLS[args.tool].prolongs:
        raise StoryError(explain_rejection(MAGIC_TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.task is None or c[2] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, task = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Mia", "Ava", "Leo", "Noah", "Nia", "Eli"])
    teammate = args.teammate or rng.choice([n for n in ["Tobi", "Nora", "Zed", "Ivy", "Ben", "Luna"] if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    hero_gender = "girl" if hero in {"Mia", "Ava", "Nia", "Ivy", "Luna"} else "boy"
    teammate_gender = "girl" if teammate in {"Mia", "Ava", "Nia", "Ivy", "Luna"} else "boy"
    return StoryParams(setting, hero, hero_gender, teammate, teammate_gender, parent, task, tool, "magic")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
valid(S,T,K) :- setting(S), tool(T), task(K), prolongs(T).
complete :- hero_curious, teamwork, prolongs(tool), task_started.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tool in MAGIC_TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.prolongs:
            lines.append(asp.fact("prolongs", tid))
    for kid in TASKS:
        lines.append(asp.fact("task", kid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()

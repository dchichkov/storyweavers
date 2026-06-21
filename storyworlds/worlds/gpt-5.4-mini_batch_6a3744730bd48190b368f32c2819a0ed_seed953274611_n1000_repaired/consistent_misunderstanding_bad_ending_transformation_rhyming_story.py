#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consistent_misunderstanding_bad_ending_transformation_rhyming_story.py
======================================================================================================

A tiny, standalone storyworld for a rhyming tale built from the seed words
"consistent", "Misunderstanding", "Bad Ending", and "Transformation".

Domain:
- A child and a helper are making batter for a small snack in a kitchen.
- A misunderstanding about the word "consistent" leads to a wrong action.
- The mistake ruins the batter and the snack plan ends badly.
- A later transformation shifts the child from rushing to patient, and the
  ruined batter becomes a lesson rather than a win.

The world uses typed entities with physical meters and emotional memes, a small
forward rule engine, a Python reasonableness gate, and an inline ASP twin.
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
CONSISTENT_WORD = "consistent"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    light: str
    smells: str
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
class Task:
    id: str
    verb: str
    rhythm: str
    action: str
    mess: str
    outcome: str
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
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    fail: str
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


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    if bowl is None or bowl.meters["lumpy"] < THRESHOLD:
        return out
    sig = ("sticky", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["stuck"] += 1
    world.get("child").memes["worry"] += 1
    out.append("The bowl grew stubborn and stuck.")
    return out


def _r_sour(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.entities.get("bowl")
    if bowl is None or bowl.meters["burned"] < THRESHOLD:
        return out
    sig = ("sour", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["sadness"] += 1
    out.append("The sweet smell turned sour.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child is None or child.memes["lesson"] < THRESHOLD:
        return out
    sig = ("transform", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["patience"] += 2
    child.memes["rush"] = 0.0
    out.append("The child changed from rushed to patient.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("sticky", _r_sticky),
    Rule("sour", _r_sour),
    Rule("transform", _r_transform),
]


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


def valid_pair(task: Task, tool: Tool) -> bool:
    return task.id in {"mix", "stir"} and tool.safe and "batter" in tool.tags


def reason_bad(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot make {task.action} turn out well.)"


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


PLACES = {
    "kitchen": Place("kitchen", "a bright kitchen", "sunlight", "warm bread", tags={"kitchen"}),
    "bakery": Place("bakery", "a tiny bakery", "oven light", "sweet flour", tags={"bakery"}),
}

TASKS = {
    "mix": Task("mix", "mix the batter", "mixing batter", "stir the bowl", "lumpy", "a smooth cake"),
    "stir": Task("stir", "stir the batter", "stirring batter", "whisk the bowl", "lumpy", "a soft cake"),
}

TOOLS = {
    "spoon": Tool("spoon", "a spoon", "the spoon", "stirring", safe=True, tags={"batter"}),
    "fork": Tool("fork", "a fork", "the fork", "stirring", safe=False, tags={"batter"}),
    "whisk": Tool("whisk", "a whisk", "the whisk", "whisking", safe=True, tags={"batter"}),
    "hammer": Tool("hammer", "a hammer", "the hammer", "hitting", safe=False, tags={"noise"}),
}

RESPONSES = {
    "add_water": Response("add_water", 3, 2, "poured in a little water and stirred until it flowed", "poured in water, but the bowl was too stiff to save"),
    "let_rest": Response("let_rest", 3, 3, "let the batter rest, then stirred it slow and steady", "waited, but the batter stayed thick and wrong"),
    "scrape": Response("scrape", 2, 2, "scraped the sides clean and kept going with calm hands", "scraped and scraped, but the batter still clung"),
}

NAMES = ["Mia", "Lena", "Nora", "Toby", "Ben", "Theo", "Ava", "Rose"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: misunderstanding, bad ending, transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, u) for p in PLACES for t in TASKS for u in TOOLS if valid_pair(TASKS[t], TOOLS[u])]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.tool and not valid_pair(TASKS[args.task], TOOLS[args.tool]):
        raise StoryError(reason_bad(TASKS[args.task], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place, task=task, tool=tool, response=response, child=name, child_gender="girl" if name in {"Mia", "Lena", "Nora", "Ava", "Rose"} else "boy", helper=helper, helper_gender="girl" if helper in {"Mia", "Lena", "Nora", "Ava", "Rose"} else "boy")


def _do_mistake(world: World, child: Entity, task: Task, tool: Tool) -> None:
    child.memes["rush"] += 1
    if tool.id == "fork":
        world.get("bowl").meters["lumpy"] += 2
    else:
        world.get("bowl").meters["lumpy"] += 1
    propagate(world)


def tell(place: Place, task: Task, tool: Tool, response: Response, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = w.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    bowl = w.add(Entity(id="bowl", type="thing", label="the bowl"))
    w.add(Entity(id=place.id, type="place", label=place.label))
    w.say(f"In {place.label}, {child_name} and {helper_name} set out to bake with a merry little cheer.")
    w.say(f"{child_name} wanted to {task.verb}, and the room rang like a bell so clear.")
    w.say(f"{child_name} held up {tool.phrase} and smiled at the day,")
    w.say(f"for {child_name} thought it would make the batter go the right way.")
    w.para()
    w.say(f'But {helper_name} frowned and said, "{CONSISTENT_WORD} means the same, not fast and loud;"')
    w.say(f"yet {child_name} heard it as " + '"keep it going, proud and loud!"')
    w.say(f"So {child_name} used {tool.phrase} the wrong, rough way,")
    _do_mistake(w, child, task, tool)
    if tool.id == "hammer":
        bowl.meters["burned"] += 1
    w.para()
    w.say("The batter turned clumpy, then bitter, then still.")
    resp = response.success if bowl.meters["burned"] < THRESHOLD else response.fail
    if bowl.meters["burned"] < THRESHOLD:
        w.say(f"{helper_name} tried to help: {resp}.")
        w.say("But the pan had gone cold, and the snack could not heal.")
    else:
        w.say("The oven gave a sigh, and the snack met a bad end for real.")
    w.para()
    child.memes["lesson"] += 1
    propagate(w)
    w.say(f"After the mess, {child_name} slowed down and took a new turn.")
    w.say(f"{child_name} learned to be careful, and patience began to return.")
    w.say(f"Now {child_name} used a whisk with a steady, gentle song,")
    w.say(f"and the lesson transformed {child_name} from hasty to strong.")
    w.facts.update(place=place, task=task, tool=tool, response=response, child=child, helper=helper, bowl=bowl, outcome="bad")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story that uses the word "{CONSISTENT_WORD}" and shows a misunderstanding in a kitchen.',
        f"Tell a sad little rhyming tale where {f['child'].label} thinks {CONSISTENT_WORD} means the wrong thing and ruins the batter.",
        "Write a short rhyming story with a bad ending that turns into a lesson about being steady and careful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    bowl = f["bowl"]
    return [
        QAItem(question="What word did the helper try to explain?", answer=f"The helper tried to explain the word {CONSISTENT_WORD}. It meant steady and the same, but the child misunderstood it."),
        QAItem(question="What went wrong with the batter?", answer="The batter became lumpy and wrong because the child used the tool the wrong way. The mistake made the snack plan end badly."),
        QAItem(question="How did the child change at the end?", answer=f"{child.label} changed from rushing to being patient and careful. That transformation turned the lesson into something useful, even though the ending was sad."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is batter?", answer="Batter is a wet mix for baking. People stir it before it goes in a pan or oven."),
        QAItem(question="What does it mean to be consistent?", answer="Being consistent means doing something the same way again and again. A steady, even mix or habit is consistent."),
        QAItem(question="Why should you use the right kitchen tool?", answer="The right tool helps the job go smoothly. The wrong tool can make a mess or ruin the food."),
    ]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,T,U) :- place(P), task(T), tool(U), safe(U), batter_tool(U), task_ok(T).
task_ok(mix).
task_ok(stir).
batter_tool(spoon).
batter_tool(whisk).
safe(spoon).
safe(whisk).
place(kitchen).
place(bakery).
task(mix).
task(stir).
tool(spoon).
tool(fork).
tool(whisk).
tool(hammer).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for u, tool in TOOLS.items():
        lines.append(asp.fact("tool", u))
        if tool.safe:
            lines.append(asp.fact("safe", u))
        if "batter" in tool.tags:
            lines.append(asp.fact("batter_tool", u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    m = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(m, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP gate differs from Python valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


CURATED = [
    StoryParams(place="kitchen", task="mix", tool="spoon", response="add_water", child="Mia", child_gender="girl", helper="Ben", helper_gender="boy"),
    StoryParams(place="bakery", task="stir", tool="whisk", response="let_rest", child="Toby", child_gender="boy", helper="Ava", helper_gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    for key in ("place", "task", "tool", "response"):
        if getattr(params, key) not in globals()[key.upper() + "S"]:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], TASKS[params.task], TOOLS[params.tool], RESPONSES[params.response], params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        for row in asp_valid_combos():
            print(row)
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
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(s, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()

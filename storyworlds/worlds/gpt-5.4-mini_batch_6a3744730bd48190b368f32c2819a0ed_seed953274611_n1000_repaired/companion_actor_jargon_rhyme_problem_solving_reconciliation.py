#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/companion_actor_jargon_rhyme_problem_solving_reconciliation.py
==============================================================================================

A small folk-tale storyworld about a child, a companion, a bit of jargon, a
problem to solve, and a reconciliation that mends the shared task.

The tale shape is simple:
- a traveling pair reaches a place where a task is blocked,
- the actor uses jargon that confuses the companion,
- the companion tries an unhelpful fix,
- they pause, explain the jargon, solve the problem together,
- and end reconciled, with a rhyme that marks the new harmony.

This script is standalone and uses only the Python standard library plus the
shared storyworld result containers. ASP support is inline and lazy-imported.
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
FOLK_TALE_TRAITS = ("kind", "patient", "curious", "steady", "gentle")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    sound: str
    problem: str
    folk_image: str
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
class Jargon:
    id: str
    word: str
    meaning: str
    use: str
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
    label: str
    blocked_by: str
    fix_hint: str
    solution: str
    rhyme: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["confusion"] < THRESHOLD:
            continue
        sig = ("confusion", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["distance"] += 1
        out.append(f"{ent.id} felt farther from the plan.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["reconcile"] < THRESHOLD:
            continue
        sig = ("reconcile", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["warmth"] += 1
        out.append(f"Their hearts softened as the day turned kinder.")
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("reconciliation", _r_reconciliation)]


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


SETTINGS = {
    "bridge": Setting("bridge", "an old stone bridge", "windy", "water hummed below",
                      "a missing bridge plank", "the river shining like a ribbon"),
    "mill": Setting("mill", "a sleepy mill road", "dusty", "wheels whispered softly",
                    "a jammed mill gate", "the mill hill under a gold sky"),
    "wood": Setting("wood", "the green wood path", "shady", "birds called overhead",
                    "a fallen log across the path", "the trees standing like elders"),
}

JARGONS = {
    "lantern": Jargon("lantern", "lantern-skip", "to make a small safe path-light",
                      "to step around the dark gap without fear", {"light"}),
    "knot": Jargon("knot", "knot-nudge", "a gentle untie-and-pull",
                   "to loosen the snag with careful fingers", {"rope"}),
    "song": Jargon("song", "song-count", "a counting rhyme used to keep time",
                   "to match the work to a rhythm", {"rhyme"}),
}

TASKS = {
    "gap": Task("gap", "crossing the gap", "a missing plank", "find a safe board",
                "lay a board across it", "step light, step right", {"bridge"}),
    "gate": Task("gate", "opening the gate", "a jammed gate latch", "use a small lever",
                 "free the latch with a little stick", "push slow, pull true", {"mill"}),
    "log": Task("log", "passing the log", "a fallen log", "choose the side path",
                "walk around the log", "round the root, find the route", {"wood"}),
}

ACTOR_NAMES = ["Mara", "Pip", "Anya", "Jon", "Tess", "Ben"]
COMPANION_NAMES = ["Nell", "Odo", "Rin", "Fae", "Bo", "Milo"]


@dataclass
class StoryParams:
    setting: str
    task: str
    jargon: str
    actor: str
    actor_gender: str
    companion: str
    companion_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if sid not in task.tags:
                continue
            for jid in JARGONS:
                combos.append((sid, tid, jid))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    if params.jargon not in JARGONS:
        raise StoryError("Unknown jargon.")
    if params.setting not in TASKS[params.task].tags:
        raise StoryError("That task does not belong in that setting.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    setting = SETTINGS[params.setting]
    task = TASKS[params.task]
    jargon = JARGONS[params.jargon]

    world = World()
    actor = world.add(Entity(id=params.actor, kind="character", type=params.actor_gender, role="actor"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion"))
    world.add(Entity(id="task", type="thing", label=task.label, role="block"))
    world.facts.update(setting=setting, task=task, jargon=jargon, actor=actor, companion=companion)

    actor.memes["confidence"] = 1.0
    companion.memes["hope"] = 1.0

    world.say(
        f"By the {setting.folk_image}, {actor.id} and {companion.id} walked together with "
        f"friendly steps. The air was {setting.mood}, and {setting.sound}."
    )
    world.say(
        f"They came to {task.label}, where {task.blocked_by} stood in the way."
        f" {actor.id} said, '{jargon.word}.'"
    )
    world.say(
        f"{companion.id} blinked. '{jargon.word}? That sounds like tall-talk to me,' "
        f"{companion.pronoun()} said, and tried to {task.fix_hint}."
    )
    companion.memes["confusion"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"{actor.id} smiled and spoke plain: '{jargon.meaning}.' "
        f"Then {actor.id} showed how to {task.solution}."
    )
    actor.memes["skill"] += 1
    companion.memes["trust"] += 1
    companion.memes["reconcile"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they did it, and the way opened at last. {task.rhyme.title()}."
    )
    world.say(
        f"{companion.id} laughed and said sorry for the muddled guess, and {actor.id} "
        f"laughed too. By sunset they were companions again, with no hard feeling left."
    )
    actor.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.facts["outcome"] = "reconciled"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story that uses the words "{f["actor"].id}" and '
        f'"{f["companion"].id}" and the jargon word "{f["jargon"].word}".',
        f"Tell a story where an actor uses the word {f['jargon'].word}, the companion "
        f"is confused, they solve a problem together, and they end reconciled.",
        f"Write a gentle story with a rhyme at the end, set by {f['setting'].place}, "
        f"about two travelers making peace after a misunderstanding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    actor = f["actor"]
    companion = f["companion"]
    jargon = f["jargon"]
    task = f["task"]
    setting = f["setting"]
    return [
        ("Who are the two main travelers?",
         f"The two main travelers are {actor.id} and {companion.id}. They walk together, argue a little, and then mend their mood."),
        ("What did the jargon word mean?",
         f"'{jargon.word}' meant {jargon.meaning}. {actor.id} explained it plainly so {companion.id} could help."),
        ("What problem did they solve?",
         f"They solved {task.label} by {task.solution}. That was the careful way to handle the trouble in the {setting.place}."),
        ("How did they end?",
         "They ended reconciled and cheerful. The misunderstanding was gone, and they were companions again by the close of the tale."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What is a companion?",
         "A companion is someone who goes with you, shares the road, and helps when the way gets hard."),
        ("What is an actor?",
         "An actor is a person who does the action in a story or play, often the one who starts the trouble or the fix."),
        ("What is jargon?",
         "Jargon is special talk used by a certain group. It can sound odd until someone explains it in plain words."),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="bridge", task="gap", jargon="lantern", actor="Mara", actor_gender="girl",
                companion="Nell", companion_gender="girl", trait="kind", seed=1),
    StoryParams(setting="mill", task="gate", jargon="knot", actor="Ben", actor_gender="boy",
                companion="Rin", companion_gender="girl", trait="patient", seed=2),
    StoryParams(setting="wood", task="log", jargon="song", actor="Tess", actor_gender="girl",
                companion="Odo", companion_gender="boy", trait="curious", seed=3),
]


ASP_RULES = r"""
same_setting(S,T) :- task(T), setting(S), valid(S,T).
confusion(C) :- companion(C), uses_jargon(C).
reconcile(A,C) :- actor(A), companion(C), explains(A), helps(A,C).
valid_story(S,T,J) :- setting(S), task(T), jargon(J), task_setting(T,S).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("task_setting", "gap", "bridge") if sid == "bridge" else "")
        lines.append(asp.fact("task_setting", "gate", "mill") if sid == "mill" else "")
        lines.append(asp.fact("task_setting", "log", "wood") if sid == "wood" else "")
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for jid in JARGONS:
        lines.append(asp.fact("jargon", jid))
    for _ in lines[:]:
        pass
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: companion, actor, jargon.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--jargon", choices=JARGONS)
    ap.add_argument("--actor")
    ap.add_argument("--actor-gender", choices=["girl", "boy", "mother", "father", "woman", "man"], dest="actor_gender")
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy", "mother", "father", "woman", "man"], dest="companion_gender")
    ap.add_argument("--trait", choices=FOLK_TALE_TRAITS)
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
              and (args.task is None or c[1] == args.task)
              and (args.jargon is None or c[2] == args.jargon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, jargon = rng.choice(sorted(combos))
    actor_gender = args.actor_gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    actor = args.actor or _pick_name(rng, ACTOR_NAMES)
    companion = args.companion or _pick_name(rng, COMPANION_NAMES, avoid=actor)
    trait = args.trait or rng.choice(FOLK_TALE_TRAITS)
    return StoryParams(setting=setting, task=task, jargon=jargon, actor=actor, actor_gender=actor_gender,
                       companion=companion, companion_gender=companion_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.jargon not in JARGONS:
        raise StoryError("Unknown StoryParams selection.")
    world = World()
    actor = world.add(Entity(id=params.actor, kind="character", type=params.actor_gender, role="actor"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion"))
    world.facts.update(setting=SETTINGS[params.setting], task=TASKS[params.task], jargon=JARGONS[params.jargon],
                       actor=actor, companion=companion, params=params)
    actor.memes["confidence"] = 1.0
    companion.memes["hope"] = 1.0
    world.say(
        f"Long ago, in {SETTINGS[params.setting].place}, {actor.id} and {companion.id} "
        f"went walking as companions do. The day was full of {SETTINGS[params.setting].mood} air, "
        f"and {SETTINGS[params.setting].sound}."
    )
    world.say(
        f"They found {TASKS[params.task].label}, blocked by {TASKS[params.task].blocked_by}. "
        f"{actor.id} spoke a bit of jargon: '{JARGONS[params.jargon].word}.'"
    )
    companion.memes["confusion"] += 1
    world.say(
        f"{companion.id} frowned and guessed wrong. 'I thought that meant something else,' "
        f"{companion.pronoun()} said, and tried a poor fix."
    )
    world.para()
    world.say(
        f"Then {actor.id} used plain words and explained: '{JARGONS[params.jargon].meaning}.' "
        f"With that, both of them could see the way."
    )
    actor.memes["skill"] += 1
    companion.memes["reconcile"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {TASKS[params.task].solution}. {TASKS[params.task].rhyme}. "
        f"In the end, {actor.id} and {companion.id} shared a smile and a fair apology."
    )
    world.say(
        f"By the time the {SETTINGS[params.setting].problem} was behind them, "
        f"they were true companions again."
    )
    world.facts["outcome"] = "reconciled"
    return world


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, task, jargon) combos:\n")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

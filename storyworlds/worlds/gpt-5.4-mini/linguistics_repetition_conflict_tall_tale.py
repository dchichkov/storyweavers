#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/linguistics_repetition_conflict_tall_tale.py
=============================================================================

A standalone storyworld for a tall-tale style story about **linguistics**,
**repetition**, and **conflict**.

Premise:
- A child and a grown-up build a tiny language game around a very loud place.
- Repetition matters: words echo, rhyme, and repeat across the story.
- Conflict arrives when repeated words are misunderstood.
- The turn comes when the speaker chooses clearer words and the listener uses
  the same language skill to repair the misunderstanding.
- The ending image proves the change: the place gets calm, the chant becomes
  a useful tool, and the characters keep talking instead of arguing.

The script follows the Storyweavers contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three Q&A sets from world state
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
SENSE_MIN = 2


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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "farmer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Locale:
    id: str
    place: str
    detail: str
    echo_word: str
    loudness: int = 1

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
class WordTool:
    id: str
    phrase: str
    repeat: str
    kind: str
    effect: str
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
class Conflict:
    id: str
    trigger: str
    misunderstanding: str
    repair: str
    resolution: str
    sense: int
    power: int
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
        clone = World()
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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["speaking"] < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("plaza").meters["echo"] += 1
        out.append("__echo__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["defiance"] >= THRESHOLD and world.get("adult").memes["worry"] >= THRESHOLD:
        sig = ("conflict", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("plaza").memes["tension"] += 1
            out.append("__conflict__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["clarity"] >= THRESHOLD and world.get("adult").memes["understanding"] >= THRESHOLD:
        sig = ("repair", "pair")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("plaza").memes["tension"] = 0.0
            world.get("child").memes["joy"] += 1
            world.get("adult").memes["relief"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule("echo", "physical", _r_echo),
    Rule("conflict", "social", _r_conflict),
    Rule("repair", "social", _r_repair),
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


def reasonableness_ok(locale: Locale, tool: WordTool, conflict: Conflict) -> bool:
    return locale.loudness >= 1 and tool.kind == "linguistics" and conflict.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid in LOCALES:
        for tid, tool in WORD_TOOLS.items():
            for cid, conflict in CONFLICTS.items():
                if reasonableness_ok(LOCALES[lid], tool, conflict):
                    combos.append((lid, tid, cid))
    return combos


def best_conflict() -> Conflict:
    return max(CONFLICTS.values(), key=lambda c: c.sense)


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    _speak(sim, sim.get("child"), sim.facts["tool"], narrate=False)
    _argue(sim, sim.get("adult"), sim.get("child"), sim.facts["conflict"], narrate=False)
    return {
        "tension": sim.get("plaza").memes["tension"],
        "echo": sim.get("plaza").meters["echo"],
    }


def _speak(world: World, child: Entity, tool: WordTool, narrate: bool = True) -> None:
    child.meters["speaking"] += 1
    child.memes["delight"] += 1
    world.say(
        f"{child.id} loved words, especially {tool.kind}. {child.id} kept a little "
        f"book of {tool.phrase}, because {tool.repeat} sounded like music in a canyon."
    )
    world.say(
        f"{child.id} tried the line again and again: \"{tool.phrase}! {tool.repeat}!\""
    )
    propagate(world, narrate=narrate)


def _argue(world: World, adult: Entity, child: Entity, conflict: Conflict, narrate: bool = True) -> None:
    adult.memes["worry"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"But when the words bounced off the stone, {adult.id} frowned. "
        f"\"{conflict.trigger},\" {adult.id} said. \"That can sound like the wrong thing.\""
    )
    world.say(
        f"{child.id} crossed {child.pronoun('possessive')} arms and said the words louder, "
        f"which only made the echo larger."
    )
    propagate(world, narrate=narrate)


def _repair(world: World, adult: Entity, child: Entity, conflict: Conflict) -> None:
    adult.memes["understanding"] += 1
    child.memes["clarity"] += 1
    world.say(
        f"Then {adult.id} pointed to the stone wall and said, "
        f"\"Let the words walk in a straight line.\""
    )
    world.say(
        f"{child.id} tried {conflict.repair} instead, slow and clear, and the plaza listened."
    )
    propagate(world, narrate=False)
    world.say(
        f"That was the trick: the same tall voice, but tidier, so the misunderstanding could not trip over itself."
    )


def _resolve(world: World, adult: Entity, child: Entity, locale: Locale, conflict: Conflict) -> None:
    world.say(
        f"At last the echo grew tame. The plaza stopped rattling, and the big air felt as calm as a sleeping hat rack."
    )
    world.say(
        f"{adult.id} laughed and said that linguistics was not just about big words; "
        f"it was about knowing how words mean different things in different places."
    )
    world.say(
        f"{child.id} grinned, tapped the {locale.echo_word}, and promised to use the clear chant whenever the stones began to gossip again."
    )
    world.say(
        f"Together they walked home, repeating {conflict.resolution}, and the town heard a story instead of an argument."
    )


def tell(locale: Locale, tool: WordTool, conflict: Conflict,
         child_name: str = "June", child_gender: str = "girl",
         adult_name: str = "Gran", adult_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    plaza = world.add(Entity(id="plaza", type="place", label=locale.place))
    world.facts.update(locale=locale, tool=tool, conflict=conflict, child=child, adult=adult, plaza=plaza)

    child.memes["curiosity"] += 1
    world.say(
        f"In {locale.place}, where the cliffs were so old they seemed to have whiskers, "
        f"{child.id} brought out a book about linguistics and a pocketful of repetition."
    )
    world.say(
        f"The whole place had a big echo, and every sentence came back wearing a hat."
    )
    _speak(world, child, tool, narrate=True)

    world.para()
    _argue(world, adult, child, conflict, narrate=True)

    world.para()
    _repair(world, adult, child, conflict)

    world.para()
    _resolve(world, adult, child, locale, conflict)

    world.facts["outcome"] = "resolved"
    return world


LOCALES = {
    "canyon": Locale("canyon", "the Blue Buffalo Canyon",
                     "The walls were high enough to make a whisper think it was a thunderstorm.",
                     "echo"),
    "square": Locale("square", "Old Bell Square",
                     "The stones underfoot were so round and smooth they could send a shout back with interest.",
                     "bell"),
    "harbor": Locale("harbor", "Wharfside Harbor",
                     "The water slapped the posts and bounced every sound around like marbles.",
                     "water"),
}

WORD_TOOLS = {
    "chant": WordTool("chant", "bright words for bright mornings", "bright words, bright words", "linguistics",
                      "a little rhythm that helped words travel straight", {"linguistics", "repetition"}),
    "tongue_twister": WordTool("tongue_twister", "four fuzzy frogs found five forks", "four fuzzy frogs, four fuzzy frogs",
                               "linguistics", "a slippery sentence that needed careful speaking", {"linguistics", "repetition"}),
    "definition": WordTool("definition", "a careful definition", "say it plain, say it plain", "linguistics",
                           "a clear way to keep meaning from slipping away", {"linguistics"}),
}

CONFLICTS = {
    "mixup": Conflict("mixup", "The echo made it sound like a different promise",
                      "everyone thought the child was calling a goat a king",
                      "speak slowly and point at the thing",
                      "clear words beat loud confusion", 3, 2, {"conflict", "repetition"}),
    "quarrel": Conflict("quarrel", "The grown-up worried the chanting would cause trouble",
                         "the adult thought the child was being reckless",
                         "repeat the line one word at a time",
                         "careful speech can turn a quarrel into a lesson", 2, 3, {"conflict", "repetition"}),
    "challenge": Conflict("challenge", "The child wanted to prove the words could out-shout the canyon",
                          "the child and adult both wanted the last word",
                          "let the adult read the meaning and let the child repeat it slowly",
                          "the loudest voice is not always the clearest one", 3, 2, {"conflict", "repetition"}),
}

NAMES_GIRL = ["June", "Mabel", "Nora", "Ivy", "Clara", "Ruby"]
NAMES_BOY = ["Will", "Otis", "Finn", "Eli", "Bram", "Jasper"]


@dataclass
@dataclass
class StoryParams:
    locale: str
    tool: str
    conflict: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that uses the word "linguistics" and shows repetition helping after a misunderstanding.',
        f"Tell a story where {f['child'].id} keeps repeating a phrase in a loud place, then learns to say it more clearly after a conflict.",
        f'Write a funny, grand-sounding story in which repetition causes trouble at first, but then becomes the way to fix the trouble.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, tool, conflict, locale = f["child"], f["adult"], f["tool"], f["conflict"], f["locale"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {adult.id}, who went to {locale.place} to play with words. The whole tale turns on how they used repetition and linguistics in the noisy place."),
        ("Why did the argument start?",
         f"The argument started because the echo made the repeated words sound like something else. {adult.id} worried the line could be misunderstood, so the same words began to feel like a conflict."),
        ("How was the problem fixed?",
         f"{child.id} repeated the idea more slowly and clearly, using {conflict.repair}. That gave the listener a better path through the meaning, and the conflict softened."),
        ("What did the child learn?",
         f"{child.id} learned that repetition can help words travel, but clear repetition helps them travel safely. In linguistics, how you say the words matters just as much as the words themselves."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["tool"].tags) | set(f["conflict"].tags) | {"linguistics"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


KNOWLEDGE = {
    "linguistics": [("What is linguistics?",
                     "Linguistics is the study of language. It looks at how words sound, what they mean, and how people use them.")],
    "repetition": [("What is repetition in a story?",
                    "Repetition means saying a word, phrase, or idea again. It can make a story musical, funny, or easier to remember.")],
    "conflict": [("What is conflict in a story?",
                  "Conflict is the trouble or disagreement that gives the story a problem to solve.")],
    "echo": [("What is an echo?",
              "An echo is a sound that bounces back after you make it. It can make words seem to come from the walls.")],
    "definition": [("What is a definition?",
                    "A definition explains what a word means. It helps people understand the same word in the same way.")],
    "chant": [("What is a chant?",
               "A chant is a short phrase or song said over and over, often with a beat.")],
    "tongue_twister": [("What is a tongue twister?",
                        "A tongue twister is a sentence with tricky sounds that is hard to say quickly.")],
}
KNOWLEDGE_ORDER = ["linguistics", "repetition", "conflict", "echo", "definition", "chant", "tongue_twister"]


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


def explain_rejection(locale: Locale, tool: WordTool, conflict: Conflict) -> str:
    if tool.kind != "linguistics":
        return "(No story: this world needs a word tool about linguistics, so the tale can turn on meaning and repetition.)"
    if conflict.sense < SENSE_MIN:
        return "(No story: the conflict idea is too weak to make a real turn in the story.)"
    if locale.loudness < 1:
        return "(No story: the place is too quiet for the echo-and-repetition problem this world needs.)"
    return "(No story: this combination does not make a worthy tall-tale problem.)"


def valid_story(params: StoryParams) -> bool:
    return params.tool in WORD_TOOLS and params.conflict in CONFLICTS and params.locale in LOCALES


ASP_RULES = r"""
valid(L, T, C) :- locale(L), word_tool(T), conflict(C), linguistics_tool(T), sense(C, S), sense_min(M), S >= M.
echo_problem(L, T, C) :- valid(L, T, C), loud(L, _), repeated(T), conflict(C).
resolved(L, T, C) :- echo_problem(L, T, C), repair(C), linguistics_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCALES.items():
        lines.append(asp.fact("locale", lid))
        lines.append(asp.fact("loud", lid, loc.loudness))
    for tid, tool in WORD_TOOLS.items():
        lines.append(asp.fact("word_tool", tid))
        lines.append(asp.fact("linguistics_tool", tid))
        lines.append(asp.fact("repeated", tid))
    for cid, c in CONFLICTS.items():
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in python:", sorted(py - cl))
        print("  only in clingo:", sorted(cl - py))

    # smoke test: ordinary generation must work
    try:
        params = resolve_params(build_parser().parse_args([]), _random.Random(7))
        sample = generate(params)
        _ = sample.story
        print("OK: default generate() smoke test succeeded.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about linguistics, repetition, and conflict.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--tool", choices=WORD_TOOLS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    combos = valid_combos()
    if args.tool and args.tool not in WORD_TOOLS:
        raise StoryError("(No story: unknown word tool.)")
    if args.conflict and args.conflict not in CONFLICTS:
        raise StoryError("(No story: unknown conflict.)")
    if args.locale and args.locale not in LOCALES:
        raise StoryError("(No story: unknown locale.)")
    if args.tool and WORD_TOOLS[args.tool].kind != "linguistics":
        raise StoryError(explain_rejection(LOCALES[args.locale or "canyon"], WORD_TOOLS[args.tool], CONFLICTS[args.conflict or "mixup"]))

    combos = [c for c in combos if (args.locale is None or c[0] == args.locale)
              and (args.tool is None or c[1] == args.tool)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    locale, tool, conflict = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child = args.child or _pick_name(rng, child_gender)
    adult = args.adult or _pick_name(rng, adult_gender, avoid=child)
    return StoryParams(locale, tool, conflict, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCALES[params.locale], WORD_TOOLS[params.tool], CONFLICTS[params.conflict],
                 params.child, params.child_gender, params.adult, params.adult_gender)
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


CURATED = [
    StoryParams("canyon", "chant", "mixup", "June", "girl", "Gran", "woman"),
    StoryParams("square", "definition", "quarrel", "Will", "boy", "Dad", "man"),
    StoryParams("harbor", "tongue_twister", "challenge", "Mabel", "girl", "Grandpa", "man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (locale, tool, conflict) combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.tool} in {p.locale} ({p.conflict})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

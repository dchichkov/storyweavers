#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/razzmatazz_platypus_conflict_tall_tale.py
==========================================================================

A standalone story world for a tall-tale-style conflict about a showy
razzmatazz performance, a platypus, and a quarrel that gets settled by a
clever repair.

The domain is small on purpose:
- A showy performer wants to add more razzmatazz to a barnyard act.
- A careful helper worries the glittery trick is too loud, too flashy, and too
  likely to spook the platypus.
- The disagreement turns into a conflict.
- A calm grown-up introduces a safer, smaller stage effect.
- The ending proves the change by showing the platypus steady again and the
  act even brighter in a safer way.

This script follows the shared Storyworld contract:
- stdlib only
- imports storyworlds/results.py eagerly
- lazy imports for storyworlds/asp.py inside ASP helpers
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, -n, --all,
  --seed
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
MILD_MIN = 1
CONFLICT_MIN = 1.0


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


@dataclass
class Crew:
    id: str
    title: str
    act: str
    set_piece: str
    target: str
    ending: str
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
class Spark:
    id: str
    label: str
    flash: str
    noise: str
    intensity: int
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
class Fix:
    id: str
    label: str
    action: str
    strength: int
    ending: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    p = world.entities.get("performer")
    h = world.entities.get("helper")
    if not p or not h:
        return out
    if p.memes["push"] < THRESHOLD or h.memes["pushback"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    p.memes["stubborn"] += 1
    h.memes["stubborn"] += 1
    out.append("__conflict__")
    return out


def _r_spook(world: World) -> list[str]:
    p = world.entities.get("platypus")
    spark = world.entities.get("spark")
    if not p or not spark:
        return []
    if spark.meters["flash"] < THRESHOLD or p.memes["calm"] <= 0:
        return []
    sig = ("spook",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    p.memes["startle"] += 1
    p.memes["calm"] = max(0.0, p.memes["calm"] - 1.0)
    return ["__startle__"]


def _r_fix(world: World) -> list[str]:
    p = world.entities.get("performer")
    h = world.entities.get("helper")
    fix = world.entities.get("fix")
    if not p or not h or not fix:
        return []
    if fix.meters["steady"] < THRESHOLD:
        return []
    sig = ("fixed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    p.memes["pride"] += 1
    h.memes["pride"] += 1
    return ["__steady__"]


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("spook", "social", _r_spook),
    Rule("fix", "social", _r_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(crew: Crew, spark: Spark, fix: Fix) -> bool:
    return spark.intensity >= MILD_MIN and fix.strength >= 1 and "platypus" in crew.tags


def python_outcome(crew: Crew, spark: Spark, fix: Fix) -> str:
    if spark.intensity >= 3 and fix.strength < 3:
        return "rattled"
    if fix.strength >= 3:
        return "steadied"
    return "noisy"


def forecast(world: World, spark: Spark, fix: Fix) -> dict:
    sim = world.copy()
    sim.get("spark").meters["flash"] += spark.intensity
    propagate(sim, narrate=False)
    sim.get("fix").meters["steady"] += fix.strength
    propagate(sim, narrate=False)
    return {
        "startled": sim.get("platypus").memes["startle"] >= THRESHOLD,
        "steady": sim.get("fix").meters["steady"] >= THRESHOLD,
    }


def add_conflict(scene: World, performer: Entity, helper: Entity, spark: Spark) -> None:
    performer.memes["push"] += 1
    helper.memes["pushback"] += 1
    scene.say(
        f"In the bright barn, {performer.id} planned a {spark.label} of razzmatazz, "
        f"all bells, banners, and a wink of gold."
    )
    scene.say(
        f"But {helper.id} frowned and said the show was too loud for the little platypus "
        f"waiting by the trough."
    )


def startle_platypus(scene: World, spark: Spark, platypus: Entity) -> None:
    spark_ent = scene.get("spark")
    spark_ent.meters["flash"] += spark.intensity
    spark_ent.meters["noise"] += 1
    propagate(scene, narrate=False)
    scene.say(
        f'Then the {spark.label} cracked open with a {spark.flash}, and the {spark.noise} '
        f"rolled through the rafters."
    )
    scene.say(
        f"The platypus hopped sideways, blinked twice, and tucked its bill down low."
    )


def calm_fix(scene: World, fix: Fix, performer: Entity, helper: Entity) -> None:
    fix_ent = scene.get("fix")
    fix_ent.meters["steady"] += fix.strength
    propagate(scene, narrate=False)
    scene.say(
        f"A calm grown-up stepped in and chose the {fix.label}: {fix.action} "
        f"so the same show could keep its sparkle without the racket."
    )
    scene.say(
        f"The helper nodded, the performer nodded, and the barn went quiet enough "
        f"to hear little hooves tap the floor."
    )


def ending(scene: World, crew: Crew, fix: Fix, platypus: Entity) -> None:
    platypus.memes["calm"] += 2
    scene.say(
        f"Before long, the platypus stood steady again, and the razzmatazz shone "
        f"like sunrise on a brass band."
    )
    scene.say(
        f"This time the whole act ended with {fix.ending}, and the barnyard crowd "
        f"cheered for the brave, safe shine of it all."
    )


def tell(crew: Crew, spark: Spark, fix: Fix, performer_name: str = "Mabel",
         helper_name: str = "Hank", parent_type: str = "father") -> World:
    world = World()
    performer = world.add(Entity(
        id=performer_name, kind="character", type="girl", role="performer",
        traits=["showy"], attrs={"crew": crew.id}
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type="boy", role="helper",
        traits=["careful"], attrs={"crew": crew.id}
    ))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, role="parent",
                              label="the grown-up"))
    platypus = world.add(Entity(id="platypus", kind="animal", type="platypus",
                               label="the platypus", role="center"))
    world.add(Entity(id="spark", kind="thing", type="effect", label=spark.label, role="effect"))
    world.add(Entity(id="fix", kind="thing", type="tool", label=fix.label, role="fix"))

    world.facts["crew"] = crew
    world.facts["spark"] = spark
    world.facts["fix"] = fix
    world.facts["performer"] = performer
    world.facts["helper"] = helper
    world.facts["parent"] = parent
    world.facts["platypus"] = platypus

    performer.memes["pride"] = 1
    helper.memes["calm"] = 1
    platypus.memes["calm"] = 1

    world.say(
        f"Once upon a tall tale afternoon, {performer.id} and {helper.id} were "
        f"setting up a barn show for {crew.title}."
    )
    world.say(
        f"{performer.id} wanted every bit of {crew.act}, {crew.set_piece}, and "
        f"{crew.target} to glitter with razzmatazz."
    )

    world.para()
    add_conflict(world, performer, helper, spark)

    world.para()
    if not reasonableness_gate(crew, spark, fix):
        raise StoryError("That story setup is too thin to hold a real conflict.")

    if spark.intensity <= 1:
        world.say("The helper's worry seemed small, and the show stayed gentle from the start.")
    else:
        startle_platypus(world, spark, platypus)

    world.para()
    calm_fix(world, fix, performer, helper)
    ending(world, crew, fix, platypus)

    world.facts["outcome"] = python_outcome(crew, spark, fix)
    world.facts["conflict"] = True
    world.facts["resolved"] = True
    return world


CREWS = {
    "barnyard": Crew(
        "barnyard", "the barnyard", "tap-dancing", "paper stars", "the little platypus",
        "the crowd went home smiling", tags={"platypus", "barn", "tall_tale"}
    ),
    "circus": Crew(
        "circus", "the traveling circus", "juggling", "streamers", "the sleepy platypus",
        "the tent ended in applause", tags={"platypus", "circus", "tall_tale"}
    ),
    "fair": Crew(
        "fair", "the county fair", "banjo playing", "sparkly signs", "the curious platypus",
        "the booths all glowed", tags={"platypus", "fair", "tall_tale"}
    ),
}

SPARKS = {
    "razz": Spark("razz", "razzmatazz lights", "a flash of silver", "a burst of trumpet-bright noise", 2,
                  tags={"razzmatazz", "flash"}),
    "glow": Spark("glow", "glow ribbons", "a shimmer of blue", "a swish of bright noise", 1,
                  tags={"glow"}),
    "fizz": Spark("fizz", "fizzing streamers", "a fizz of gold", "a pop of snappy noise", 3,
                  tags={"streamers"}),
}

FIXES = {
    "lanterns": Fix("lanterns", "paper lanterns", "hang paper lanterns instead of the noisy spark", 3,
                    "the crowd cheered under a sky of soft light", tags={"lantern"}),
    "drums": Fix("drums", "soft drum taps", "keep the rhythm with soft drum taps and no bursting flash", 2,
                 "the crowd clapped to a gentler beat", tags={"music"}),
    "stars": Fix("stars", "gold paper stars", "swap the burst for gold paper stars and twinkle string", 3,
                 "the crowd waved under a sky full of twinkles", tags={"stars"}),
}



@dataclass
class StoryParams:
    crew: str
    spark: str
    fix: str
    performer: str
    helper: str
    parent: str
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

CURATED = [
    ("barnyard", "razz", "lanterns", "Mabel", "Hank", "father"),
    ("circus", "fizz", "stars", "June", "Ollie", "mother"),
    ("fair", "glow", "drums", "Ruby", "Ben", "father"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for c in CREWS:
        for s in SPARKS:
            for f in FIXES:
                if reasonableness_gate(CREWS[c], SPARKS[s], FIXES[f]):
                    combos.append((c, s, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale conflict about razzmatazz and a platypus.")
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--performer")
    ap.add_argument("--helper")
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
    if args.spark and args.fix and not reasonableness_gate(CREWS[args.crew] if args.crew else CREWS["barnyard"],
                                                          SPARKS[args.spark], FIXES[args.fix]):
        raise StoryError("That razzmatazz is too weak to make a real conflict.")
    combos = [c for c in valid_combos()
              if (args.crew is None or c[0] == args.crew)
              and (args.spark is None or c[1] == args.spark)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    crew, spark, fix = rng.choice(sorted(combos))
    performer = args.performer or rng.choice(["Mabel", "June", "Ruby", "Nell", "Sadie"])
    helper = args.helper or rng.choice([n for n in ["Hank", "Ollie", "Ben", "Pete", "Wes"] if n != performer])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(crew, spark, fix, performer, helper, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, s, fx = f["crew"], f["spark"], f["fix"]
    return [
        f'Write a tall tale for a child that includes the word "razzmatazz" and a platypus in a barn show.',
        f"Tell a conflict story where {f['performer'].id} wants {s.label} but {f['helper'].id} worries it will spook the platypus.",
        f"Write a funny, big-hearted story with razzmatazz, a platypus, and a calm fix that settles the quarrel."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    p, h, fx, s = f["performer"], f["helper"], f["fix"], f["spark"]
    return [
        ("Who was the story about?",
         f"It was about {p.id}, {h.id}, and the platypus in {f['crew'].title}. Their big idea turned into a quarrel before it turned into a fix."),
        ("Why did the helper disagree?",
         f"{h.id} thought {s.label} would be too loud and too flashy for the platypus. That worry caused the conflict, because the helper wanted the show to stay safe."),
        ("How did they settle the conflict?",
         f"They used {fx.label} instead of the bursty trick. That kept the razzmatazz but made the barn quiet enough for the platypus to stay steady."),
        ("How did the story end?",
         f"It ended with the platypus steady again and the crowd cheering. The same show still sparkled, but the danger was gone.")
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["crew"].tags) | set(world.facts["spark"].tags) | set(world.facts["fix"].tags)
    knowledge = {
        "platypus": [("What is a platypus?",
                      "A platypus is a strange, real animal with a bill like a duck and a body like a furry swimmer.")],
        "razzmatazz": [("What does razzmatazz mean?",
                        "Razzmatazz means bright, showy excitement, with extra sparkle, flash, and noise.")],
        "barn": [("What is a barn?",
                  "A barn is a big farm building used for animals, tools, or hay.")],
        "lantern": [("What is a paper lantern?",
                      "A paper lantern is a light cover made of paper that can make a room glow softly.")],
        "music": [("Why can soft music help?",
                    "Soft music can keep a party cheerful without making it too loud or rough.")],
        "stars": [("Why use paper stars in a show?",
                    "Paper stars can make a scene look magical without any popping or flashing danger.")],
    }
    order = ["razzmatazz", "platypus", "barn", "lantern", "music", "stars"]
    out: list[tuple[str, str]] = []
    for key in order:
        if key in tags:
            out.extend(knowledge[key])
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in CREWS:
        lines.append(asp.fact("crew", k))
    for k, s in SPARKS.items():
        lines.append(asp.fact("spark", k))
        lines.append(asp.fact("intensity", k, s.intensity))
    for k, f in FIXES.items():
        lines.append(asp.fact("fix", k))
        lines.append(asp.fact("strength", k, f.strength))
    lines.append(asp.fact("has_platypus", "true"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,S,F) :- crew(C), spark(S), fix(F), intensity(S,I), strength(F,ST), I >= 1, ST >= 1, has_platypus(true).
outcome(rattled) :- spark(S), intensity(S,I), fix(F), strength(F,ST), I >= 3, ST < 3.
outcome(steadied) :- fix(F), strength(F,ST), ST >= 3.
outcome(noisy) :- spark(S), intensity(S,I), fix(F), strength(F,ST), I < 3, ST < 3.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_spark", params.spark),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    for p in CURATED:
        params = StoryParams(*p)
        if asp_outcome(params) != python_outcome(SPARKS[params.spark], FIXES[params.fix]):
            rc = 1
            print("MISMATCH in outcome:", params)
    try:
        sample = generate(resolve_params(argparse.Namespace(crew=None, spark=None, fix=None,
                                                           performer=None, helper=None, parent=None),
                                         random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print("MISMATCH in generate() smoke test:", e)
    return rc


def explain_rejection() -> str:
    return "(No story: that setup won't make a believable conflict for this tall tale.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(CREWS[params.crew], SPARKS[params.spark], FIXES[params.fix],
                 params.performer, params.helper, params.parent)
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c, s, f in asp_valid_combos():
            print(f"  {c:10} {s:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

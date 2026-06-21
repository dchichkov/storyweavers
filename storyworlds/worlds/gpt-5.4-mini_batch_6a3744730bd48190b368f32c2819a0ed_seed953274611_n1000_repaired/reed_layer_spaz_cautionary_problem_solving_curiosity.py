#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reed_layer_spaz_cautionary_problem_solving_curiosity.py
========================================================================================

A small storyworld for a Tall-Tale-style cautionary problem-solving curiosity story.

Premise:
- A curious child ignores a caution about a stack of reed mats.
- A wobbly "spaz" moment knocks a layered path into trouble.
- The grown-up warning is proven right, but the problem gets solved with calm help.
- The ending image shows the safe fix and the lesson learned.

This world is standalone, uses only the stdlib at runtime, and conforms to the
Storyweavers storyworld contract.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Setup:
    id: str
    place: str
    scene: str
    nickname: str
    tall_tale_line: str
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
class Trouble:
    id: str
    word: str
    label: str
    caution: str
    wobble: int = 1
    risky: bool = True
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
class LayerThing:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setup: str
    trouble: str
    layer: str
    fix: str
    hero: str
    hero_type: str
    cautioner: str
    cautioner_type: str
    grownup: str
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
    tag: str
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


def _r_spill(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["tipped"] < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "path" in world.entities:
            world.get("path").meters["blocked"] += 1
        for ent in list(world.entities.values()):
            if ent.role in {"hero", "cautioner"}:
                ent.memes["trouble"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend([g for g in got if g != "__spill__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(trouble: Trouble, layer: LayerThing) -> bool:
    return trouble.risky and layer.fragile


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_fixes():
        return combos
    for sid in SETUPS:
        for tid, tr in TROUBLES.items():
            for lid, ly in LAYERS.items():
                if hazard_at_risk(tr, ly):
                    combos.append((sid, tid, lid))
    return combos


def outcome_of(params: StoryParams) -> str:
    if params.fix not in FIXES or params.layer not in LAYERS or params.trouble not in TROUBLES:
        raise StoryError("Invalid story parameters.")
    return "contained" if FIXES[params.fix].power >= TROUBLES[params.trouble].wobble else "muddled"


def _warn_predict(world: World, trouble: Trouble, layer: LayerThing) -> bool:
    sim = world.copy()
    sim.get("trouble").meters["tipped"] += 1
    propagate(sim, narrate=False)
    return sim.get("path").meters["blocked"] >= THRESHOLD and layer.fragile


def do_setup(world: World, setup: Setup, hero: Entity, cautioner: Entity, grownup: Entity) -> None:
    hero.memes["curiosity"] += 1
    cautioner.memes["care"] += 1
    world.say(
        f"In {setup.place}, where the {setup.nickname} wind could sing through the reeds, "
        f"{hero.id} and {cautioner.id} had a day as wide as a wagon wheel."
    )
    world.say(
        f"They followed {setup.scene}, and the whole thing looked like a tall tale already. "
        f"{setup.tall_tale_line}"
    )
    world.say(
        f"'{hero.id} wanted to see what lay behind the {setup.nickname} bank,' "
        f"said {cautioner.id}, while {grownup.id} kept one eye on the sky."
    )


def do_caution(world: World, cautioner: Entity, trouble: Trouble, layer: LayerThing, grownup: Entity) -> None:
    cautioner.memes["caution"] += 1
    world.say(
        f"'{trouble.caution},' warned {cautioner.id}. 'That {trouble.label} can wobble a stack, "
        f"and a fallen {layer.label} can block the path.'"
    )


def do_curiosity(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"But {hero.id}'s curiosity leaped higher than a fence post. "
        f"'{trouble.word}! I want to see it close up!' {hero.id} cried."
    )


def do_spaz(world: World, hero: Entity, trouble: Trouble, layer: LayerThing) -> None:
    hero.memes["spaz"] += 1
    trouble_ent = world.get("trouble")
    trouble_ent.meters["tipped"] += 1
    world.say(
        f"Then came a spazzy little slip and a skitter, and the {trouble.label} toppled with a clatter. "
        f"The {layer.label} lurched sideways and the narrow way got messy in a blink."
    )
    propagate(world, narrate=False)


def do_alarm(world: World, cautioner: Entity, grownup: Entity, layer: LayerThing) -> None:
    world.say(
        f"'{grownup.id}!' shouted {cautioner.id}. 'The {layer.label} has gone crooked!'"
    )


def do_fix(world: World, grownup: Entity, fix: Fix, layer: LayerThing, trouble: Trouble) -> None:
    if fix.power < trouble.wobble:
        world.say(
            f"{grownup.id} tried to {fix.fail.replace('{layer}', layer.label)}, but the mess was too wild."
        )
        return
    world.get("trouble").meters["tipped"] = 0.0
    world.get("path").meters["blocked"] = 0.0
    world.say(
        f"{grownup.id} came striding in and {fix.text.replace('{layer}', layer.label)}. "
        f"The trouble settled down like a hound at supper."
    )


def do_lesson(world: World, grownup: Entity, hero: Entity, cautioner: Entity, trouble: Trouble, layer: LayerThing) -> None:
    hero.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f"{grownup.id} gave them both a nod and said, 'Curiosity is a bright lantern, "
        f"but caution keeps the lantern from falling in the creek.'"
    )
    world.say(
        f"{hero.id} promised to look first, ask second, and tug third. "
        f"{cautioner.id} grinned, because the path was open again and the {layer.label} was standing straight."
    )


def do_safe_finish(world: World, setup: Setup, hero: Entity, cautioner: Entity, layer: LayerThing) -> None:
    world.say(
        f"By sunset, the wind had gone soft, the {layer.label} was mended, and {hero.id} was laughing. "
        f"They walked home by the reed banks, small as sparrows and brave as blue jays."
    )


SETUPS = {
    "marsh": Setup(
        id="marsh",
        place="the marsh",
        scene="a boardwalk, a bucket, and a gull-eyed map",
        nickname="reed",
        tall_tale_line="A single reed could whistle like a whole train if the moon listened hard enough.",
    ),
    "riverbank": Setup(
        id="riverbank",
        place="the riverbank",
        scene="a crooked pier, a lunch pail, and a hat that bowed to the breeze",
        nickname="reed",
        tall_tale_line="The reeds stood tall as storybook soldiers, even when the water snored.",
    ),
    "meadow": Setup(
        id="meadow",
        place="the meadow",
        scene="a wagon wheel, a compass, and a trail of bright footprints",
        nickname="layer",
        tall_tale_line="The grass had layers of dew on it, each one shining like a tiny town of pearls.",
    ),
}

TROUBLES = {
    "reed": Trouble(
        id="reed",
        word="reed",
        label="reed bundle",
        caution="Don't shove that reed bundle",
        tags={"reed", "cautionary"},
    ),
    "layer": Trouble(
        id="layer",
        word="layer",
        label="layer stack",
        caution="Mind that layer stack",
        tags={"layer", "cautionary"},
    ),
    "spaz": Trouble(
        id="spaz",
        word="spaz",
        label="spazzy pile",
        caution="Steady now; that spazzy pile is eager to tumble",
        tags={"spaz", "curiosity"},
    ),
}

LAYERS = {
    "layer": LayerThing(
        id="layer",
        label="layer stack",
        phrase="a stacked layer of mats",
        region="path",
        tags={"layer"},
    ),
    "reed": LayerThing(
        id="reed",
        label="reed raft",
        phrase="a raft of reeds laid across the mud",
        region="path",
        tags={"reed"},
    ),
    "spaz": LayerThing(
        id="spaz",
        label="spaz pile",
        phrase="a spazzy little pile of brush",
        region="path",
        tags={"spaz"},
    ),
}

FIXES = {
    "bridge": Fix(
        id="bridge",
        sense=3,
        power=3,
        text="built a sturdier bridge of planks across the mud",
        fail="build a bridge of planks across the mud",
        qa_text="built a sturdier bridge of planks across the mud",
        tags={"problem_solving"},
    ),
    "hands": Fix(
        id="hands",
        sense=3,
        power=2,
        text="carried the reed bundle aside by hand and cleared the path",
        fail="carry the reed bundle aside by hand",
        qa_text="carried the reed bundle aside by hand and cleared the path",
        tags={"problem_solving"},
    ),
    "rope": Fix(
        id="rope",
        sense=2,
        power=2,
        text="tied a rope guide so the path could be followed safely",
        fail="tie a rope guide across the path",
        qa_text="tied a rope guide so the path could be followed safely",
        tags={"problem_solving"},
    ),
}

GROWNUPS = {"grandpa": "Grandpa", "aunt": "Aunt May", "dad": "Dad"}

GIRL_NAMES = ["Mina", "Tess", "Lora", "Nell", "Ivy", "June"]
BOY_NAMES = ["Otis", "Cal", "Bram", "Jules", "Pip", "Hank"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: reed, layer, spaz, caution, and a smart fix.")
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--layer", choices=LAYERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--cautioner")
    ap.add_argument("--cautioner-type", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=GROWNUPS)
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
              if (args.setup is None or c[0] == args.setup)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.layer is None or c[2] == args.layer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setup, trouble, layer = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(s.id for s in sensible_fixes()))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    cautioner_type = args.cautioner_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    cautioner = args.cautioner or rng.choice([n for n in (GIRL_NAMES if cautioner_type == "girl" else BOY_NAMES) if n != hero])
    grownup = args.grownup or rng.choice(list(GROWNUPS))
    if fix not in FIXES or FIXES[fix].sense < 2:
        raise StoryError("Unsafe or unknown fix.")
    return StoryParams(setup=setup, trouble=trouble, layer=layer, fix=fix, hero=hero, hero_type=hero_type, cautioner=cautioner, cautioner_type=cautioner_type, grownup=grownup)


def tell(params: StoryParams) -> World:
    if params.setup not in SETUPS or params.trouble not in TROUBLES or params.layer not in LAYERS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    cautioner = world.add(Entity(id=params.cautioner, kind="character", type=params.cautioner_type, role="cautioner"))
    grownup = world.add(Entity(id=GROWNUPS[params.grownup], kind="character", type="father", role="grownup"))
    world.add(Entity(id="trouble", kind="thing", type=params.trouble, label=TROUBLES[params.trouble].label))
    world.add(Entity(id="path", kind="thing", type="path", label="the path"))
    setup = SETUPS[params.setup]
    trouble = TROUBLES[params.trouble]
    layer = LAYERS[params.layer]
    fix = FIXES[params.fix]
    do_setup(world, setup, hero, cautioner, grownup)
    world.para()
    do_caution(world, cautioner, trouble, layer, grownup)
    do_curiosity(world, hero, trouble)
    do_spaz(world, hero, trouble, layer)
    do_alarm(world, cautioner, grownup, layer)
    world.para()
    do_fix(world, grownup, fix, layer, trouble)
    do_lesson(world, grownup, hero, cautioner, trouble, layer)
    world.para()
    do_safe_finish(world, setup, hero, cautioner, layer)
    world.facts.update(hero=hero, cautioner=cautioner, grownup=grownup, setup=setup, trouble=trouble, layer=layer, fix=fix, outcome=outcome_of(params))
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the words "{f["trouble"].word}", "{f["layer"].label}", and "spaz".',
        f"Tell a cautionary problem-solving story where {f['hero'].id} gets curious, causes a little trouble, and {f['grownup'].id} helps fix the {f['layer'].label}.",
        "Write a bright, child-friendly tale where curiosity leads to a wobble, a warning proves true, and the ending shows a safe repair.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, cautioner, grownup = f["hero"], f["cautioner"], f["grownup"]
    layer, trouble, fix = f["layer"], f["trouble"], f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {cautioner.id}, and {grownup.id}. {hero.id} is the curious one, and the others help keep the day safe."),
        (f"Why did {cautioner.id} warn {hero.id}?",
         f"{cautioner.id} warned {hero.id} because the {trouble.label} could tumble and the {layer.label} could block the path. That warning mattered because the world was already wobbly."),
        ("How was the problem solved?",
         f"{grownup.id} solved it by {fix.qa_text}. That fixed the path and turned the trouble into a safe ending."),
        ("How did the story end?",
         f"It ended with the {layer.label} standing straight and the children walking home happy. The scary wobble was gone, and the path was open again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["trouble"].tags) | set(world.facts["layer"].tags) | set(world.facts["fix"].tags)
    qas = []
    if "reed" in tags:
        qas.append(("What is a reed?", "A reed is a thin, tall plant that grows in wet places. Reeds can sway and whisper in the wind."))
    if "layer" in tags:
        qas.append(("What does layer mean?", "A layer is one level in a stack or one sheet on top of another. Layers can make a pile look neat or thick."))
    if "spaz" in tags:
        qas.append(("What does spazzy mean in this story?", "Here it means quick, wobbly, and hard to keep steady. It describes a messy little tumble, not a person."))
    if "problem_solving" in tags:
        qas.append(("What is problem solving?", "Problem solving means noticing what is wrong and choosing a smart way to fix it. It often means staying calm and using the right tool."))
    if "cautionary" in tags:
        qas.append(("What is a cautionary story?", "A cautionary story teaches a warning. It shows what can go wrong and how to be safer next time."))
    return qas


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
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETUPS:
        lines.append(asp.fact("setup", sid))
    for tid, tr in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if tr.risky:
            lines.append(asp.fact("risky", tid))
    for lid, ly in LAYERS.items():
        lines.append(asp.fact("layer", lid))
        if ly.fragile:
            lines.append(asp.fact("fragile", lid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
        lines.append(asp.fact("power", fid, fx.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(T, L) :- risky(T), fragile(L).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(S, T, L) :- setup(S), trouble(T), layer(L), hazard(T, L).
"""


def asp_program(extra: str = "", show: str = "#show valid/3.\n") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1.\n"))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    if set(asp_sensible()) == {f.id for f in sensible_fixes()}:
        print("OK: sensible fixes match.")
    else:
        rc = 1
        print("MISMATCH in sensible fixes.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setup=None, trouble=None, layer=None, fix=None, hero=None, hero_type=None, cautioner=None, cautioner_type=None, grownup=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-generated story renders.")
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    return rc


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def explain_rejection() -> str:
    return "(No story: that combination is too unreasonable for this little world.)"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    return f"(Refusing fix '{fid}': sense={f.sense} is too low; choose a smarter fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError(explain_fix(args.fix))
    combos = valid_combos()
    combos = [c for c in combos if (args.setup is None or c[0] == args.setup)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.layer is None or c[2] == args.layer)]
    if not combos:
        raise StoryError(explain_rejection())
    setup, trouble, layer = rng.choice(sorted(combos))
    return StoryParams(
        setup=setup,
        trouble=trouble,
        layer=layer,
        fix=args.fix or rng.choice(sorted(f.id for f in sensible_fixes())),
        hero=args.hero or rng.choice(GIRL_NAMES + BOY_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        cautioner=args.cautioner or rng.choice(GIRL_NAMES + BOY_NAMES),
        cautioner_type=args.cautioner_type or rng.choice(["girl", "boy"]),
        grownup=args.grownup or rng.choice(list(GROWNUPS)),
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
    StoryParams(setup="marsh", trouble="reed", layer="layer", fix="bridge", hero="Mina", hero_type="girl", cautioner="Otis", cautioner_type="boy", grownup="grandpa"),
    StoryParams(setup="riverbank", trouble="spaz", layer="reed", fix="hands", hero="Jules", hero_type="boy", cautioner="Ivy", cautioner_type="girl", grownup="aunt"),
    StoryParams(setup="meadow", trouble="layer", layer="spaz", fix="rope", hero="Nell", hero_type="girl", cautioner="Bram", cautioner_type="boy", grownup="dad"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, t, l in combos:
            print(f"  {s:10} {t:8} {l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/eva_glutton_funny_problem_solving_sound_effects.py
==================================================================================

A standalone storyworld for a tiny folk-tale domain: Eva meets a gluttonous
problem in the woods, the trouble makes silly sounds, and careful thinking turns
the mess into a funny ending.

This world keeps the Storyweavers contract:
- self-contained stdlib script
- typed entities with physical meters and emotional memes
- story-driven state changes, not frozen template swapping
- Python validity gate plus inline ASP twin
- Q&A grounded in simulated world state
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
HUNGER_MAX = 3.0


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
    edible: bool = False
    noisy: bool = False
    helpful: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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


def _r_glut(world: World) -> list[str]:
    out: list[str] = []
    baker = world.entities.get("bakery")
    gl = world.entities.get("glutton")
    if not baker or not gl:
        return out
    if gl.meters["hungry"] < THRESHOLD:
        return out
    sig = ("glut",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    baker.meters["emptied"] += 1
    gl.memes["greed"] += 1
    out.append("__glut__")
    return out


def _r_rumble(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("pot") and world.get("pot").meters["bubbly"] >= THRESHOLD:
        sig = ("rumble",)
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["surprise"] += 1
            out.append("The pot went glub-glub and made everybody jump.")
    return out


CAUSAL_RULES = [Rule("glut", "physical", _r_glut), Rule("rumble", "sound", _r_rumble)]


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


@dataclass
class Place:
    id: str
    label: str
    mood: str
    has_oven: bool = False
    has_tree: bool = False

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
class Trouble:
    id: str
    label: str
    thing: str
    sound: str
    hungry_need: int
    loud_need: int
    fix: str

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
    method: str
    sound: str
    power: int
    sense: int

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


PLACES = {
    "cottage": Place("cottage", "a little cottage", "warm", has_oven=True),
    "orchard": Place("orchard", "an old orchard", "bright", has_tree=True),
    "market": Place("market", "the village market", "busy", has_oven=True),
}

TROUBLES = {
    "pie": Trouble("pie", "a berry pie", "pie", "squish-squash", 3, 2, "share the pie"),
    "porridge": Trouble("porridge", "a pot of porridge", "porridge", "glub-glub", 2, 3, "stir in milk"),
    "apples": Trouble("apples", "a basket of apples", "apples", "thump-thump", 2, 2, "sort the apples"),
}

FIXES = {
    "share": Fix("share", "share the food", "cut it into fair pieces", "chop-chop", 3, 3),
    "compote": Fix("compote", "turn it into compote", "cook it down with water", "bubble-bubble", 4, 2),
    "basket": Fix("basket", "move it into a bigger basket", "carry it carefully", "rustle-rustle", 2, 2),
}

NAMES = ["Eva", "Mara", "Tilda", "Nina", "Sera", "Lena"]
HELPERS = ["a wise miller", "an old goose", "a baker", "a little fox"]


@dataclass
@dataclass
class StoryParams:
    place: str
    trouble: str
    fix: str
    name: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for t in TROUBLES.values():
            for f in FIXES.values():
                if t.loud_need <= f.power and f.sense >= SENSE_MIN:
                    combos.append((p.id, t.id, f.id))
    return combos


def reason_ok(trouble: Trouble, fix: Fix) -> bool:
    return trouble.loud_need <= fix.power and fix.sense >= SENSE_MIN


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about Eva, a glutton, and funny problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.trouble and args.fix and not reason_ok(TROUBLES[args.trouble], FIXES[args.fix]):
        raise StoryError("No story: that fix is not strong enough for the trouble.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        trouble=trouble,
        fix=fix,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def tell(params: StoryParams) -> World:
    world = World()
    p = PLACES[params.place]
    t = TROUBLES[params.trouble]
    f = FIXES[params.fix]

    eva = world.add(Entity(id=params.name, kind="character", type="girl", role="hero"))
    glutton = world.add(Entity(id="glutton", kind="character", type="thing", role="trouble", label="the glutton"))
    helper = world.add(Entity(id="helper", kind="character", type="thing", role="helper", label=params.helper))
    pot = world.add(Entity(id="pot", kind="thing", type="thing", label=t.thing, edible=True, noisy=True))
    bakery = world.add(Entity(id="bakery", kind="thing", type="thing", label="the food table", helpful=True))
    pot.meters["bubbly"] = 1.0 if params.trouble == "porridge" else 0.0
    glutton.meters["hungry"] = float(3)
    glutton.memes["wanting"] = 2.0
    world.facts.update(place=p, trouble=t, fix=f, eva=eva, glutton=glutton, helper=helper, pot=pot, bakery=bakery)

    world.say(f"In {p.label}, Eva met {glutton.label_word}, a glutton with a very funny nose and a bigger appetite than his shoes.")
    world.say(f"{params.helper.capitalize()} had a plan, but the day began with a sound: {t.sound}! It came from {t.thing}, and Eva's eyes went round.")
    world.para()
    glutton.memes["greed"] += 1
    world.say(f'"I want it all," said the glutton. "Nibble-nabble!" he went, and the food seemed to shrink in his hands.')
    world.say(f"Eva frowned, then thought like a fox in a tale. '{f.method.capitalize()},' she said, and looked at the {t.thing}.")
    world.say(f"{params.helper} nodded. 'We can solve this,' {helper.pronoun()} said. 'Not with scolding, but with a clever fix.'")

    if params.fix == "share":
        world.para()
        pot.meters["bubbly"] += 1
        propagate(world, narrate=True)
        world.say(f"Eva cut the {t.thing} into fair pieces. Chop-chop went the knife, and the glutton had no reason to gobble the whole thing.")
        glutton.memes["satisfied"] += 1
        eva.memes["relief"] += 1
    elif params.fix == "compote":
        world.para()
        pot.meters["bubbly"] += 1
        propagate(world, narrate=True)
        world.say(f"Eva poured in a little water. Bubble-bubble, simmer-simmer, and the hungry trouble turned into sweet compote.")
        glutton.meters["hungry"] = 0.0
        eva.memes["pride"] += 1
    else:
        world.para()
        world.say(f"Eva carried the {t.thing} into a bigger basket. Rustle-rustle went the reeds, and the glutton could no longer snatch from the middle.")
        glutton.memes["embarrassment"] += 1
        eva.memes["relief"] += 1

    world.para()
    world.say(f"At the end, {glutton.label_word} sat with a silly grin, and Eva laughed too. In that old folk-tale way, the problem had been solved without a fight, and even the wind seemed to chuckle.")
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child that includes the words "eva", "glutton", and "funny".',
        f"Tell a story about Eva facing a glutton and using {f['fix'].label} to solve the problem with a playful sound-effect feel.",
        f"Write a simple problem-solving tale in which Eva hears funny sound effects in a village and turns trouble into a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    t: Trouble = world.facts["trouble"]
    f: Fix = world.facts["fix"]
    return [
        QAItem("Who is the story about?", "It is about Eva, who meets a glutton and thinks her way through a silly problem."),
        QAItem("What sound did the trouble make?", f"It made a {t.sound} sound. That sound told Eva where the trouble was coming from."),
        QAItem("How did Eva solve the problem?", f"She used {f.label}. She did not shout or fight; she chose a clever fix and changed the situation."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a glutton mean?", "A glutton is someone who wants to eat too much and too quickly. In a story, that can make a funny or troublesome character."),
        QAItem("What is a folk tale?", "A folk tale is an old-style story passed along from mouth to mouth. It often has simple problems, clever answers, and a clear ending."),
        QAItem("Why are sound effects useful in stories?", "Sound effects help you imagine what is happening. They make the story feel lively and easy to hear in your mind."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(G) :- glutton(G).
solved :- problem(G), fix(F), power(F, P), need(G, N), P >= N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("need", tid, t.loud_need))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, trouble=None, fix=None, name=None, helper=None), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("cottage", "pie", "share", "Eva", "a wise miller"),
    StoryParams("orchard", "porridge", "compote", "Eva", "an old goose"),
    StoryParams("market", "apples", "basket", "Eva", "a baker"),
]


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
        print(f"{len(valid_combos())} compatible combos")
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
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

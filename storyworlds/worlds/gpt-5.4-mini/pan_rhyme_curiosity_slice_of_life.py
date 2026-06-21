#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pan_rhyme_curiosity_slice_of_life.py
====================================================================

A small standalone story world for a slice-of-life kitchen tale with
curiosity, a rhyme, and a pan.

Seed idea
---------
A child is curious about a pan in the kitchen while a grown-up cooks.
The child wants to get close, but the pan is hot, so the grown-up gives
a simple warning and a safer way to help. The child learns to ask first,
sings a little rhyme, and ends the scene with warm help and calm pride.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- reasonableness gate plus inline ASP twin
- three Q&A sets grounded in state, not in rendered prose
- stdlib only, with shared results imported eagerly and asp lazily
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
    table: str
    smell: str
    time: str
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
class Pan:
    id: str
    label: str
    phrase: str
    sound: str
    heat: str
    on_stove: bool = True
    hot: bool = True
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
class Rhyme:
    id: str
    line1: str
    line2: str
    line3: str
    action: str
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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
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


def _r_cool(world: World) -> list[str]:
    out: list[str] = []
    pan = world.entities.get("pan")
    if pan and pan.meters["hot"] >= THRESHOLD and world.get("cook").meters["done"] >= THRESHOLD:
        sig = ("cool", pan.id)
        if sig not in world.fired:
            world.fired.add(sig)
            pan.meters["hot"] = 0.0
            pan.hot = False
            out.append("__cool__")
    return out


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


CAUSAL_RULES = [Rule("cool", "state", _r_cool)]


def safe_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(setting: Setting, pan: Pan, response: Response) -> bool:
    return pan.hot and response.sense >= SENSE_MIN and "kitchen" in setting.tags


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PANS.items():
            for rid, r in RESPONSES.items():
                if valid_combo(s, p, r):
                    out.append((sid, pid, rid))
    return out


def reasonableness_gate(setting: Setting, pan: Pan, response: Response) -> None:
    if "kitchen" not in setting.tags:
        raise StoryError("No story: this world needs a kitchen setting.")
    if not pan.hot:
        raise StoryError("No story: the pan is not hot, so there is no curious warning to tell.")
    if response.sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{response.id}': it is too weak to feel wise in this world.)")


def _touch_pan(world: World) -> None:
    world.get("child").memes["curiosity"] += 1
    world.get("child").memes["worry"] += 1


def _do_cook(world: World) -> None:
    cook = world.get("cook")
    cook.meters["done"] += 1
    cook.memes["pride"] += 1


def tell(setting: Setting, pan: Pan, rhyme: Rhyme, response: Response,
         child_name: str = "Milo", child_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                              role="child", traits=["curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the grown-up"))
    cook = world.add(Entity(id="cook", kind="character", type=parent_type,
                            role="cook", label="the cook"))
    pan_ent = world.add(Entity(id="pan", type="pan", label=pan.label))
    pan_ent.meters["hot"] = 1.0
    _do_cook(world)

    world.say(
        f"In {setting.place}, the table was set for a quiet little meal, and "
        f"{child.id} could smell {setting.smell} in the air. "
        f"{child.id} listened to {pan.phrase} making its soft {pan.sound} sound."
    )
    world.say(
        f'"{rhyme.line1}" {child.id} sang, and {child.id} leaned closer to the pan, '
        f'curious about everything.'
    )
    world.para()
    _touch_pan(world)
    world.say(
        f'{parent.label_word.capitalize()} smiled, then held up a hand. '
        f'"The pan is hot," {parent.pronoun()} said. "If you want to help, '
        f"please {response.text}."
    )
    world.say(
        f"{child.id} blinked, thought about it, and asked a question instead of "
        f"reaching. That made the kitchen feel calm again."
    )
    world.para()
    world.say(
        f'{child.id} did the safer job and repeated the rhyme: '
        f'"{rhyme.line2} {rhyme.line3}"'
    )
    world.say(
        f"{child.id} helped from the side while {parent.label_word} watched the pan. "
        f"When the cooking was finished, the pan slowly cooled on the stove."
    )
    propagate(world, narrate=False)
    if not pan_ent.hot:
        world.say(
            f"By the end, {child.id} could tap the cool pan with one finger and grin. "
            f"It was still the same pan, but now it was part of a safe, happy morning."
        )

    world.facts.update(
        child=child,
        parent=parent,
        cook=cook,
        pan=pan_ent,
        setting=setting,
        rhyme=rhyme,
        response=response,
        outcome="calm",
        cooled=not pan_ent.hot,
        curiosity=child.memes["curiosity"],
        worry=child.memes["worry"],
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the wooden table", "warm toast", "morning", {"kitchen"}),
    "small_apartment": Setting("small_apartment", "the little kitchen", "the tiny table", "buttered bread", "afternoon", {"kitchen"}),
    "grandma_house": Setting("grandma_house", "Grandma's kitchen", "the checked tablecloth", "fresh soup", "noon", {"kitchen"}),
}

PANS = {
    "pan": Pan("pan", "pan", "a little pan", "sizzle", "hot"),
    "frypan": Pan("frypan", "frying pan", "a frying pan", "tsssss", "hot"),
}

RHYMES = {
    "bells": Rhyme("bells", "Round and round, the spoon goes tap,", "Little hands wait, then clap and clap,", "Hot things rest and cool at last.", "wait", {"rhyme"}),
    "nest": Rhyme("nest", "Mix and stir and listen near,", "Ask first, ask kindly, ask with cheer,", "Curious hearts can still be safe.", "ask", {"rhyme"}),
}

RESPONSES = {
    "stir": Response("stir", 3, "stir the batter with the wooden spoon", "stir the batter with the wooden spoon", {"safe"}),
    "wait": Response("wait", 3, "wait until the pan cools and then help", "wait until the pan cools and then help", {"safe"}),
    "set_back": Response("set_back", 2, "set the pan back on the stove and step away for a moment", "set the pan back on the stove and step away for a moment", {"safe"}),
    "touch": Response("touch", 1, "touch the pan right now", "touch the pan right now", {"unsafe"}),
}

SENSE_MIN = 2

BOY_NAMES = ["Milo", "Theo", "Finn", "Ben", "Leo", "Noah"]
GIRL_NAMES = ["Ruby", "Maya", "Luna", "Ivy", "Nora", "Elsa"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    pan: str
    rhyme: str
    response: str
    child_name: str
    child_gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the word "pan" and a gentle rhyme.',
        f"Tell a quiet kitchen story where {f['child'].id} is curious about a pan, listens to a grown-up, and learns a safer way to help.",
        f'Write a simple everyday story with curiosity, a rhyme, and a pan that ends in a calm kitchen scene.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, pan = f["child"], f["parent"], f["pan"]
    rhyme = f["rhyme"]
    resp = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.label_word}, in a kitchen where a pan was being used for cooking."),
        ("Why did the child lean closer to the pan?",
         f"{child.id} was curious about the pan and wanted to know what it sounded like. Curiosity made {child.pronoun('object')} move closer before {parent.label_word} spoke up."),
        ("What did the grown-up say to do instead of touching the pan?",
         f"{parent.label_word.capitalize()} said to {resp.qa_text}. That gave {child.id} a safe way to help without getting too near the heat."),
        ("How did the story end?",
         f"The pan cooled, the kitchen stayed calm, and {child.id} ended up helping safely. The child even learned the little rhyme while waiting."),
    ]
    if f["cooled"]:
        qa.append(("What changed by the end?",
                   f"The pan was no longer hot, so it could be tapped safely at the end. That small change proved the waiting had worked."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a pan?",
         "A pan is a cooking tool used on the stove. Grown-ups use it to heat or cook food."),
        ("Why should you be careful with a hot pan?",
         "A hot pan can burn your hand very quickly. It is safer to ask a grown-up and wait."),
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look, ask, and learn about things."),
        ("What is a rhyme?",
         "A rhyme is a little bit of poetry or a song where the words sound alike at the end."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "pan", "bells", "wait", "Milo", "boy", "mother"),
    StoryParams("small_apartment", "frypan", "nest", "stir", "Ruby", "girl", "father"),
    StoryParams("grandma_house", "pan", "bells", "set_back", "Nora", "girl", "mother"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid))
    for pid, p in PANS.items():
        lines.append(asp.fact("pan", pid))
        if p.hot:
            lines.append(asp.fact("hot", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, R) :- setting(S), pan(P), hot(P), response(R), sense(R, N), sense_min(M), N >= M.
cooled(P) :- hot(P).
"""

def asp_program(extra: str, show: str) -> str:
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
        print("MISMATCH in valid combos.")
    # smoke test on curated sample
    try:
        s = generate(CURATED[0])
        _ = s.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a curious child, a pan, and a rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pan", choices=PANS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("No story: that response is too silly for this calm kitchen world.")
    setting = args.setting or rng.choice(list(SETTINGS))
    pan = args.pan or rng.choice(list(PANS))
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    response = args.response or rng.choice([r.id for r in safe_responses()])
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father"])
    reasonableness_gate(SETTINGS[setting], PANS[pan], RESPONSES[response])
    return StoryParams(setting, pan, rhyme, response, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PANS[params.pan], RHYMES[params.rhyme],
                 RESPONSES[params.response], params.child_name, params.child_gender, params.parent)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, pan, response) combos:\n")
        for s, p, r in combos:
            print(f"  {s:16} {p:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

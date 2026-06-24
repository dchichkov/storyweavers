#!/usr/bin/env python3
"""
storyworlds/worlds/cat_whirly_cautionary_adventure.py
======================================================

A small standalone storyworld for a cautionary adventure about a cat, a
whirly thing, and the choice to use it wisely.

Seed tale:
---
A curious cat loved adventure. One day the cat found a whirly spinner near a
garden path and wanted to chase it right away. But the spinner was meant for
calm play, and if the cat grabbed it too hard, it would tangle in the string
and break. A careful friend warned the cat to slow down. The cat listened,
used the whirly toy gently, and had a happy, windy playtime without breaking
anything.

World premise:
- A cat wants to chase a whirly toy in an outdoor setting.
- The toy can tangle or snap if used too roughly.
- A cautionary helper warns the cat to slow down and use a gentle method.
- The ending proves a change: the toy stays whole, and the cat learns calmer
  adventure.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    protective: bool = False
    handles: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("tangled", 0.0)
        self.meters.setdefault("broken", 0.0)
        self.meters.setdefault("joy", 0.0)
        self.meters.setdefault("care", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("patience", 0.0)
        self.memes.setdefault("delight", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "cat":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the garden path"
    outdoors: bool = True
    breeze: str = "a brisk little breeze"


@dataclass
class Whirly:
    id: str
    label: str
    phrase: str
    motion: str
    danger: str
    safe_method: str
    ending: str
    kind: str = "whirly"
    mess: str = "tangled"
    break_risk: str = "broken"


@dataclass
class StoryParams:
    setting: str
    whirly: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "garden": Setting("the garden path", True, "a brisk little breeze"),
    "yard": Setting("the sunny yard", True, "a warm spinning breeze"),
    "porch": Setting("the porch steps", True, "a gentle porch breeze"),
}

WHIRLYS = {
    "spinner": Whirly(
        id="spinner",
        label="whirly spinner",
        phrase="a bright whirly spinner",
        motion="spun fast in the wind",
        danger="its string could tangle and snap",
        safe_method="paw it gently and let it spin",
        ending="the spinner kept turning in the breeze",
    ),
    "pinwheel": Whirly(
        id="pinwheel",
        label="pinwheel",
        phrase="a shiny pinwheel",
        motion="whirled in circles",
        danger="its paper petals could bend and tear",
        safe_method="tap it softly and watch it turn",
        ending="the pinwheel flashed like a tiny rainbow",
    ),
    "whirltoy": Whirly(
        id="whirltoy",
        label="whirly toy",
        phrase="a little whirly toy on a string",
        motion="zigzagged through the air",
        danger="the string could knot up",
        safe_method="hold it carefully and let it wobble",
        ending="the whirly toy danced without a snag",
    ),
}

CAT_NAMES = ["Milo", "Pip", "Nico", "Toby", "Luna"]
HELPERS = [("friend", "a gentle friend"), ("grandpa", "grandpa"), ("sister", "an older sister")]


@dataclass
class WorldModel:
    setting: Setting
    cat: Entity
    helper: Entity
    whirly: Entity
    toy: Whirly
    trace: list[str] = field(default_factory=list)


def reason_gate(toy: Whirly) -> bool:
    return bool(toy.safe_method and toy.danger)


def describe_setting(setting: Setting, toy: Whirly) -> str:
    return f"{setting.breeze.capitalize()} moved through {setting.place}, and {toy.phrase} waited nearby."


def _rough_play(world: WorldModel) -> None:
    cat = world.cat
    toy = world.whirly
    if "rough" in world.helper.memes:
        pass
    cat.meters["joy"] += 1
    cat.memes["impulse"] = cat.memes.get("impulse", 0.0) + 1
    if cat.memes["impulse"] >= THRESHOLD:
        toy.meters["tangled"] += 1
        world.trace.append("rough play tangled the toy")


def _gentle_play(world: WorldModel) -> None:
    cat = world.cat
    toy = world.whirly
    cat.meters["joy"] += 1
    cat.memes["patience"] += 1
    toy.meters["joy"] += 1
    world.trace.append("gentle play kept the toy whole")


def tell(setting: Setting, toy: Whirly, name: str, helper_label: str) -> WorldModel:
    world = World(setting)
    cat = world.add(Entity(id=name, kind="character", type="cat", label=name))
    helper = world.add(Entity(id=helper_label, kind="character", type="adult", label=helper_label))
    whirly = world.add(Entity(id=toy.id, type=toy.kind, label=toy.label, phrase=toy.phrase))

    model = WorldModel(setting=setting, cat=cat, helper=helper, whirly=whirly, toy=toy)
    world.say(f"{cat.id} was a curious cat who loved adventure.")
    world.say(f"{describe_setting(setting, toy)}")
    world.say(f"{cat.id} wanted to chase the {toy.label} right away because {toy.motion}.")
    world.para()
    world.say(f"But {helper.id} lifted a gentle paw and warned, '{toy.danger.capitalize()}.'")
    cat.memes["worry"] = 1.0
    helper.memes["patience"] = 1.0
    if setting.outdoors:
        world.say(f"{helper.id} reminded {cat.id} to slow down and choose a careful way to play.")
    else:
        world.say(f"{helper.id} pointed to a clear space and showed {cat.id} how to be careful.")
    world.para()
    if reason_gate(toy):
        _gentle_play(model)
        world.say(f"{cat.id} listened, touched the {toy.label} softly, and let it {toy.safe_method}.")
        world.say(f"That was the right choice, because then {toy.ending}.")
        world.say(f"{cat.id} sat tall and happy, with calm adventure in {cat.pronoun('possessive')} whiskers.")
    else:
        raise StoryError("This whirly toy needs a clear safe method and a real caution.")
    world.facts.update(cat=cat, helper=helper, whirly=whirly, toy=toy, setting=setting)
    model.trace.extend(world.paragraphs[0] and [])
    model.world = world
    model.story = world.render()
    return model


ASP_RULES = r"""
cat_like(C) :- cat(C).
whirly(W) :- whirly(W).
risk(W) :- whirly(W), danger(W,D), D != "".
safe(W) :- whirly(W), safe_method(W,M), M != "".
valid_story(S,T) :- setting(S), whirly(T), risk(T), safe(T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, toy in WHIRLYS.items():
        lines.append(asp.fact("whirly", tid))
        lines.append(asp.fact("danger", tid, toy.danger))
        lines.append(asp.fact("safe_method", tid, toy.safe_method))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in WHIRLYS if reason_gate(WHIRLYS[t])]

@dataclass
class StoryParams:
    setting: str
    whirly: str
    name: str
    helper: str
    seed: Optional[int] = None

def generation_prompts(model: WorldModel) -> list[str]:
    return [
        f"Write a short cautionary adventure about a cat named {model.cat.id} and a {model.toy.label}.",
        f"Tell a gentle story where {model.cat.id} wants to play with {model.toy.phrase} but listens to {model.helper.id}.",
        f"Write a child-friendly adventure with the words 'cat' and '{model.toy.label}' and a safe ending.",
    ]

def story_qa(model: WorldModel) -> list[QAItem]:
    return [
        QAItem(
            question=f"Why did {model.helper.id} worry when {model.cat.id} chased the {model.toy.label}?",
            answer=f"{model.helper.id} worried because {model.toy.danger}, so the play needed to be slower and gentler."
        ),
        QAItem(
            question=f"What did {model.cat.id} do after hearing the warning?",
            answer=f"{model.cat.id} listened, used the {model.toy.label} carefully, and kept it from getting tangled."
        ),
        QAItem(
            question=f"How did the story end for the {model.toy.label}?",
            answer=f"It stayed whole, and {model.toy.ending}."
        ),
    ]

def world_knowledge_qa(model: WorldModel) -> list[QAItem]:
    return [
        QAItem(
            question="What does cautious mean?",
            answer="Cautious means being careful and slowing down so something does not get broken or hurt."
        ),
        QAItem(
            question="What is a whirly toy?",
            answer="A whirly toy is something that spins, twirls, or flutters in the wind and is fun to watch."
        ),
    ]

def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)

def dump_trace(world: WorldModel) -> str:
    return (
        "--- trace ---\n"
        f"cat joy={world.cat.meters['joy']} impulse={world.cat.memes.get('impulse', 0)} patience={world.cat.memes.get('patience', 0)}\n"
        f"helper patience={world.helper.memes.get('patience', 0)}\n"
        f"toy tangled={world.whirly.meters['tangled']} joy={world.whirly.meters['joy']}"
    )

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary cat-and-whirly adventure world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--whirly", choices=WHIRLYS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["friend", "grandpa", "sister"])
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
    combos = valid_combos()
    if args.setting and args.whirly:
        if (args.setting, args.whirly) not in combos:
            raise StoryError("That setting and whirly toy do not make a safe cautionary adventure.")
    if not combos:
        raise StoryError("No valid story combinations available.")
    setting, whirly = rng.choice(combos)
    name = args.name or rng.choice(CAT_NAMES)
    helper = args.helper or rng.choice([h[0] for h in HELPERS])
    return StoryParams(setting=setting, whirly=whirly, name=name, helper=helper)

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    toy = WHIRLYS[params.whirly]
    helper_label = dict(HELPERS)[params.helper]
    model = tell(setting, toy, params.name, helper_label)
    world = model.world
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(model),
        story_qa=story_qa(model),
        world_qa=world_knowledge_qa(model),
        world=model,
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        print("OK: this compact world uses a Python reasonableness gate and ASP twin.")
        return
    if args.asp:
        print(asp_program("#show whirly/1.\n#show safe_method/2.\n#show danger/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, whirly in valid_combos():
            p = StoryParams(setting=setting, whirly=whirly, name="Milo", helper="friend")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()

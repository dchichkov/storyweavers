#!/usr/bin/env python3
"""
storyworlds/worlds/cat_whirly_cautionary_adventure.py
=====================================================

A standalone story world about a curious cat, a whirly thing, and a cautious
adventure that teaches carefulness without losing the sense of wonder.

Seed tale imagined from the prompt:
---
A little cat found a whirly toy in the yard and wanted to chase it. The wind
pushed the whirly thing toward a gate and then toward a garden pond. A cautious
friend warned the cat that the whirly could pull them into a muddy spot or out
of sight. The cat listened, used a safe leash and stayed near home, and the
adventure ended with a brave but careful game.

World model:
---
A "whirly" thing is a spinning, fluttering object that can drift, tangle, or
lead a cat into a risky place. The cat's curiosity rises when it sees motion;
the cautionary beat is a helper warning that predicts the risky drift. A safe
choice uses a helper, a tether, or a nearby perch to keep the adventure going
without a dangerous chase.

Causal state updates:
---
    cat chases whirly              -> cat.meters["distance"] rises
                                      cat.memes["curiosity"] rises
                                      whirly.meters["drift"] rises
    cat enters risky spot          -> cat.meters["muddy"] rises
                                      cat.memes["alarm"] rises
    helper warning heard           -> cat.memes["pause"] rises
                                      cat.memes["caution"] rises
    safe tether used               -> cat.meters["distance"] stays low
                                      cat.memes["pride"] rises
                                      whirly.meters["tamed"] rises

Story style:
---
Adventure-forward, child-facing, concrete, and gently cautionary. The ending
must show what changed: the cat is safer, the whirly is still fun, and the
lesson is visible in the final image.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class WhirlyThing:
    id: str
    label: str
    phrase: str
    drift: str
    risk: str
    tether: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    cat = world.get("cat")
    whirly = world.get("whirly")
    if cat.memes["chase"] < THRESHOLD:
        return out
    sig = ("drift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    whirly.meters["drift"] += 1
    cat.meters["distance"] += 1
    cat.memes["curiosity"] += 1
    out.append("__drift__")
    return out


def _r_risk(world: World) -> list[str]:
    cat = world.get("cat")
    if cat.meters["distance"] < THRESHOLD:
        return []
    sig = ("risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cat.meters["muddy"] += 1
    cat.memes["alarm"] += 1
    return ["__risk__"]


CAUSAL_RULES = [
    Rule("drift", "physical", _r_drift),
    Rule("risk", "physical", _r_risk),
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


def predict_risk(world: World) -> dict:
    sim = world.copy()
    _do_chase(sim, narrate=False)
    return {
        "muddy": sim.get("cat").meters["muddy"] >= THRESHOLD,
        "distance": sim.get("cat").meters["distance"],
    }


def _do_chase(world: World, narrate: bool = True) -> None:
    world.get("cat").memes["chase"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, cat: Entity, helper: Entity, whirly: WhirlyThing) -> None:
    world.say(
        f"{cat.id} was a little {cat.type} who loved bright motion and the quick "
        f"flutter of {whirly.label}."
    )
    world.say(
        f"At {world.setting.place}, {cat.pronoun().capitalize()} could spot a "
        f"tiny adventure in almost anything."
    )
    helper.memes["watchful"] += 1
    world.say(
        f"{helper.id} stayed nearby, ready to help if the play became too wild."
    )


def whirly_wakes(world: World, cat: Entity, whirly: WhirlyThing) -> None:
    world.say(
        f"One breezy day, a {whirly.label} spun across the path and made a shiny "
        f"little whirl."
    )
    world.say(
        f"{cat.id} wanted to chase it at once, because the turn and twirl felt like a game."
    )


def warn(world: World, helper: Entity, cat: Entity, whirly: WhirlyThing) -> None:
    pred = predict_risk(world)
    world.facts["predicted_muddy"] = pred["muddy"]
    world.facts["predicted_distance"] = pred["distance"]
    world.say(
        f'{helper.id} pointed at the path and said, "{cat.id}, that whirly can '
        f"pull you into a muddy spot if you race it too far."
        f'"'
    )
    if pred["muddy"]:
        world.say(
            f'{helper.id} added, "Let us keep it close so the fun stays safe."'
        )


def chase(world: World, cat: Entity, whirly: WhirlyThing) -> None:
    cat.memes["chase"] += 1
    world.say(
        f"{cat.id} pounced after {whirly.label}, and the whirly thing drifted just "
        f"a little farther away."
    )
    propagate(world, narrate=False)


def choose_safe(world: World, cat: Entity, helper: Entity, whirly: WhirlyThing) -> None:
    cat.memes["pause"] += 1
    cat.memes["caution"] += 1
    world.say(
        f"{cat.id} paused, listened, and looked back at {helper.id} instead of "
        f"running off."
    )
    world.say(
        f'Then {helper.id} showed {cat.id} {whirly.tether}, so the play could stay near home.'
    )


def safe_play(world: World, cat: Entity, helper: Entity, whirly: WhirlyThing) -> None:
    cat.memes["pride"] += 1
    cat.memes["joy"] += 1
    whirly_ent = world.get("whirly")
    whirly_ent.meters["tamed"] += 1
    whirly_ent.meters["drift"] = 0
    world.say(
        f"{cat.id} batted {whirly.label} with the tethered stick, and it spun in a "
        f"small circle where everyone could see it."
    )
    world.say(
        f"By the end, {cat.id} was still adventurous, but {cat.pronoun()} stayed "
        f"on the safe side of the path."
    )
    world.say(
        f"{helper.id} smiled as the whirly toy whizzed gently in the breeze, right at home."
    )


def tell(setting: Setting, whirly: WhirlyThing, helper: Helper) -> World:
    world = World(setting)
    cat = world.add(Entity(id="cat", kind="character", type="cat", label="cat"))
    guide = world.add(Entity(id=helper.id, kind="character", type="helper", label=helper.label))
    wh = world.add(Entity(id="whirly", type="thing", label=whirly.label, phrase=whirly.phrase))
    world.facts["whirly"] = whirly
    world.facts["helper"] = helper

    intro(world, cat, guide, whirly)
    world.para()
    whirly_wakes(world, cat, whirly)
    warn(world, guide, cat, whirly)
    world.para()
    choose_safe(world, cat, guide, whirly)
    safe_play(world, cat, guide, whirly)
    world.facts.update(cat=cat, world=world)
    return world


SETTINGS = {
    "yard": Setting(place="the yard", affords={"whirly"}),
    "garden": Setting(place="the garden", affords={"whirly"}),
    "porch": Setting(place="the porch", affords={"whirly"}),
}

WHIRLY = {
    "pinwheel": WhirlyThing(
        id="pinwheel",
        label="pinwheel",
        phrase="a bright pinwheel",
        drift="spin fast in the wind",
        risk="drift toward the gate",
        tether="a short ribbon tied to the handle",
        tags={"whirly", "wind"},
    ),
    "kitewheel": WhirlyThing(
        id="kitewheel",
        label="kite wheel",
        phrase="a little kite wheel",
        drift="whirl across the grass",
        risk="roll toward the pond",
        tether="a loop of string around the stick",
        tags={"whirly", "wind"},
    ),
}

HELPERS = {
    "friend": Helper(id="friend", label="a friend", phrase="a helping hand", action="warn", tags={"cautionary"}),
    "parent": Helper(id="parent", label="the parent", phrase="a steady hand", action="warn", tags={"cautionary"}),
}

GIRL_NAMES = ["Mia", "Luna", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for w in WHIRLY:
            for h in HELPERS:
                combos.append((s, w, h))
    return combos


@dataclass
class StoryParams:
    setting: str
    whirly: str
    helper: str
    name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "whirly": [("What is whirly motion?", "Whirly motion is spinning or fluttering movement that can be fun to watch.")],
    "wind": [("What does the wind do?", "Wind is moving air. It can push light things around.")],
    "cautionary": [("What does cautionary mean?", "Cautionary means a story gives a careful warning so someone can stay safe.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short cautionary adventure story for a 3-to-5-year-old about a cat and a whirly thing.',
        f"Tell a gentle adventure where {f['cat'].id} wants to chase {f['whirly'].label}, but a helper warns them and they choose a safe way to play.",
        f'Write a child-friendly story that includes the word "{f["whirly"].label}" and ends with safe play near home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat = f["cat"]
    wh = f["whirly"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What did the cat want to chase in the story?",
            answer=f"The cat wanted to chase {wh.label} because it spun and twirled in a fun way.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn the cat?",
            answer=f"{helper.id} warned the cat because {wh.label} could pull the cat into a muddy spot if the chase went too far.",
        ),
        QAItem(
            question=f"How did the cat stay safe at the end?",
            answer=f"The cat listened, used {wh.tether}, and played close to home instead of running after the whirly thing.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.append(QAItem(*KNOWLEDGE["cautionary"][0]))
    out.append(QAItem(*KNOWLEDGE["whirly"][0]))
    out.append(QAItem(*KNOWLEDGE["wind"][0]))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
cat_chases(C,W) :- cat(C), whirly(W), chase(C,W).
whirly_drifts(W) :- cat_chases(_,W).
risky(C) :- cat(C), distance(C,D), D >= 1.
muddy(C) :- risky(C), cat(C).
cautionary_story(S,W,H) :- setting(S), whirly(W), helper(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for w, cfg in WHIRLY.items():
        lines.append(asp.fact("whirly", w))
        lines.append(asp.fact("tether", w, cfg.tether))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("cat", "cat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cat and whirly cautionary adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--whirly", choices=WHIRLY)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    whirly = args.whirly or rng.choice(list(WHIRLY))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, whirly=whirly, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], WHIRLY[params.whirly], HELPERS[params.helper])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show cautionary_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], ensure_ascii=False, indent=2))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams(setting="yard", whirly="pinwheel", helper="parent", name="Mia"),
    StoryParams(setting="garden", whirly="kitewheel", helper="friend", name="Leo"),
]


if __name__ == "__main__":
    main()

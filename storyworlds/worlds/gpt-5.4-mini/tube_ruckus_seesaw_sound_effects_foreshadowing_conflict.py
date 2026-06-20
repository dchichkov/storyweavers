#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tube_ruckus_seesaw_sound_effects_foreshadowing_conflict.py
===========================================================================================

A standalone storyworld for a small adventure-domain playground tale built from
the seed words tube, ruckus, and seesaw.

Premise:
- Two children are exploring a playground like a tiny adventure site.
- A tube tunnel and a seesaw create sound effects that foreshadow a conflict.
- One child rushes ahead, a ruckus starts, and a careful helper resolves it.

This world models:
- typed entities with physical meters and emotional memes
- state-driven causal progression
- sound-effect narration that reflects actual world events
- foreshadowing via a predicted mechanical problem before conflict
- a Python reasonableness gate plus an inline ASP twin
- Q&A grounded in world state rather than rendered text

Run examples:
    python storyworlds/worlds/gpt-5.4-mini/tube_ruckus_seesaw_sound_effects_foreshadowing_conflict.py
    python storyworlds/worlds/gpt-5.4-mini/tube_ruckus_seesaw_sound_effects_foreshadowing_conflict.py --qa
    python storyworlds/worlds/gpt-5.4-mini/tube_ruckus_seesaw_sound_effects_foreshadowing_conflict.py --all
    python storyworlds/worlds/gpt-5.4-mini/tube_ruckus_seesaw_sound_effects_foreshadowing_conflict.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    adventure: str
    echo: str
    soundscape: str
    risky: bool = False


@dataclass
class Feature:
    id: str
    label: str
    sound: str
    foreshadow: str
    conflict_line: str
    resolution: str
    tags: set[str] = field(default_factory=set)


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_rumble(world: World) -> list[str]:
    out: list[str] = []
    tube = world.entities.get("tube")
    seesaw = world.entities.get("seesaw")
    if tube and tube.meters["shaking"] >= THRESHOLD and "tube_rumble" not in world.fired:
        world.fired.add(("tube_rumble",))
        tube.meters["noise"] += 1
        out.append("__tube_rumble__")
    if seesaw and seesaw.meters["creak"] >= THRESHOLD and "seesaw_creak" not in world.fired:
        world.fired.add(("seesaw_creak",))
        seesaw.meters["noise"] += 1
        out.append("__seesaw_creak__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    tube = world.entities.get("tube")
    if not tube or tube.meters["jammed"] < THRESHOLD or "conflict" in world.fired:
        return out
    world.fired.add(("conflict",))
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["stress"] += 1
    out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    tube = world.entities.get("tube")
    if not tube or tube.meters["fixed"] < THRESHOLD or "relief" in world.fired:
        return out
    world.fired.add(("relief",))
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["joy"] += 1
            e.memes["stress"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("rumble", "sound", _r_rumble),
    Rule("conflict", "social", _r_conflict),
    Rule("relief", "social", _r_relief),
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


def predict_tube(world: World) -> dict:
    sim = world.copy()
    sim.get("tube").meters["shaking"] += 1
    propagate(sim, narrate=False)
    return {
        "rumbles": sim.get("tube").meters["noise"] >= THRESHOLD,
        "conflict": sim.get("tube").meters["jammed"] >= THRESHOLD,
    }


def predict_seesaw(world: World) -> dict:
    sim = world.copy()
    sim.get("seesaw").meters["creak"] += 1
    propagate(sim, narrate=False)
    return {"creak": sim.get("seesaw").meters["noise"] >= THRESHOLD}


def shake_tube(world: World, tube: Entity) -> None:
    tube.meters["shaking"] += 1
    world.say("The long tube went wiggle-wiggle. Fwip! It gave a funny little rumble.")
    propagate(world)


def cross_tube(world: World, hero: Entity, tube: Entity, other: Entity) -> None:
    hero.memes["bold"] += 1
    tube.meters["shaking"] += 1
    world.say(
        f'{hero.id} leaned into the tube tunnel. "Shhh," {hero.pronoun()} whispered, '
        f'but the tube answered with a hollow whooosh.'
    )
    if other.id:
        world.say(f"{other.id} stopped and listened.")


def foreshadow(world: World, helper: Entity, tube: Entity, seesaw: Entity) -> None:
    pred = predict_tube(world)
    se = predict_seesaw(world)
    helper.memes["care"] += 1
    world.facts["predicted"] = pred
    if pred["rumbles"] or se["creak"]:
        world.say(
            f'{helper.id} heard the tube go "thunk-thunk" and saw the seesaw lean with a '
            f'long eeek. "{tube.label} sounds stuck," {helper.pronoun()} said. '
            f'"That could turn into a ruckus."'
        )


def make_ruckus(world: World, hero: Entity, tube: Entity, seesaw: Entity) -> None:
    hero.memes["defiance"] += 1
    tube.meters["jammed"] += 1
    seesaw.meters["creak"] += 1
    world.say(
        f'{"CRACKLE!"} The seesaw gave a loud creak and the tube made a clatter-clack. '
        f'That was the start of a ruckus.'
    )
    propagate(world)


def call_stop(world: World, helper: Entity, hero: Entity, tube: Entity) -> None:
    helper.memes["courage"] += 1
    world.say(
        f'"Stop!" {helper.id} called. "{tube.label.capitalize()} can pinch fingers if it jams."'
    )


def fix_tube(world: World, helper: Entity, tube: Entity, seesaw: Entity) -> None:
    tube.meters["jammed"] = 0.0
    tube.meters["fixed"] = 1.0
    seesaw.meters["creak"] = 0.0
    world.say(
        f"{helper.id} crouched down, pulled a twig from the tube mouth, and set the cap "
        f"straight. Click. The jam let go."
    )
    propagate(world)


def ending(world: World, hero: Entity, helper: Entity, tube: Entity, seesaw: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'After that, the tube only said "woosh" and the seesaw only said "boing." '
        f'{hero.id} and {helper.id} grinned and ran on to their next adventure.'
    )
    if seesaw.meters["noise"] >= THRESHOLD:
        world.say("The playground felt quieter now, like it was smiling again.")


def tell(
    place: Place,
    feature: Feature,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    helper_name: str = "Noah",
    helper_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    tube = world.add(Entity(id="tube", type="thing", label="the tube tunnel"))
    seesaw = world.add(Entity(id="seesaw", type="thing", label="the seesaw"))
    gate = world.add(Entity(id="gate", type="thing", label="the playground gate"))

    world.say(
        f"{hero.id} and {helper.id} reached {place.label} like tiny adventurers on a map. "
        f"{place.adventure}"
    )
    world.say(
        f"They found the tube tunnel by the seesaw. {feature.sound} sounded under their shoes, "
        f"and the whole place felt ready for a quest."
    )
    world.say(
        f'Then the tube gave a little warning sound: "{feature.foreshadow}"'
    )
    foreshadow(world, helper, tube, seesaw)

    world.para()
    world.say(
        f'{hero.id} wanted to dash through anyway, but {helper.id} pointed at the tube. '
        f'"{feature.conflict_line}"'
    )
    make_ruckus(world, hero, tube, seesaw)
    call_stop(world, helper, hero, tube)

    world.para()
    world.say(
        f'{parent.label_word.capitalize()} came closer, calm and steady, while the ruckus echoed '
        f'off the wooden boards.'
    )
    fix_tube(world, helper, tube, seesaw)
    world.say(feature.resolution)
    ending(world, hero, helper, tube, seesaw)

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        place=place,
        feature=feature,
        tube=tube,
        seesaw=seesaw,
        gate=gate,
        outcome="resolved",
    )
    return world


PLACES = {
    "playground": Place(
        "playground",
        "the playground",
        "The sandbox felt like a treasure field, the slide like a tower, and the tube tunnel like a cave entrance.",
        "The tube and the seesaw made the kind of echo that made brave kids listen twice.",
        "The whole place hummed with adventure.",
        risky=True,
    ),
    "park": Place(
        "park",
        "the park",
        "The trees stood like guards, the path looked like a trail, and the tube tunnel hid beside the climbing frame.",
        "The tube and the seesaw made the kind of echo that made brave kids listen twice.",
        "The whole place hummed with adventure.",
        risky=True,
    ),
    "yard": Place(
        "yard",
        "the big yard",
        "The grass was wide like a green sea, and the tube and seesaw waited near a bright red bench.",
        "The tube and the seesaw made the kind of echo that made brave kids listen twice.",
        "The whole place hummed with adventure.",
        risky=True,
    ),
}

FEATURES = {
    "sound_effects": Feature(
        "sound_effects",
        "sound effects",
        'The tube went "whoosh" and the seesaw went "boing-boing".',
        "The tube had a hush before the rattle, like it was warning someone.",
        "The noise turned into a ruckus when the child rushed in too fast.",
        "Once the jam was fixed, the sounds became playful again.",
        tags={"sound", "tube", "seesaw"},
    ),
    "foreshadowing": Feature(
        "foreshadowing",
        "foreshadowing",
        'A tiny squeak from the seesaw made the next problem feel close.',
        "The seesaw complained with a small eeeek before anything went wrong.",
        "That squeak turned into a ruckus when nobody listened.",
        "After the repair, the squeak disappeared and the adventure could continue.",
        tags={"foreshadowing", "tube", "seesaw"},
    ),
    "conflict": Feature(
        "conflict",
        "conflict",
        'The tube was narrow, and the seesaw was already busy, so both children wanted the same path.',
        "The tube looked cramped, like it might snag a sleeve, and the seesaw tipped like it had a secret.",
        "The fight over who should go first became a ruckus.",
        "When they agreed to take turns, the ruckus ended and the path opened again.",
        tags={"conflict", "tube", "seesaw"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nina", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Finn", "Max", "Theo", "Sam"]


@dataclass
class StoryParams:
    place: str
    feature: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, f) for p in PLACES for f in FEATURES if PLACES[p].risky]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: tube, ruckus, seesaw, and a playground adventure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--feature", choices=FEATURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.feature is None or c[1] == args.feature)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, feature = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    hero = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, feature, hero, gender, helper, helper_gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a preschooler that includes the words "tube", "ruckus", and "seesaw".',
        f"Tell a playground adventure where {f['hero'].id} and {f['helper'].id} explore a tube tunnel, hear foreshadowing sounds, and face a ruckus.",
        f"Write a gentle conflict story with sound effects where the seesaw and tube help create the problem and the ending shows a calm fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    feature = f["feature"]
    tube, seesaw = f["tube"], f["seesaw"]
    return [
        QAItem(
            question="What were the children exploring?",
            answer=f"They were exploring a playground adventure area with {tube.label} and {seesaw.label}. The place felt like a tiny quest before the trouble started.",
        ),
        QAItem(
            question="What warned that a problem might happen?",
            answer=f"The small sounds from {seesaw.label} and the tube tunnel warned that something was getting stuck. That foreshadowing came before the ruckus.",
        ),
        QAItem(
            question=f"What caused the ruckus?",
            answer=f"{hero.id} rushed ahead, the tube jammed, and the seesaw creaked louder. The conflict turned into a ruckus because both the sound and the crowding got worse.",
        ),
        QAItem(
            question=f"How did {parent.label_word} help?",
            answer=f"{parent.label_word.capitalize()} stayed calm while {helper.id} fixed the tube. That helped the children settle down and made the playground safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a tube tunnel?", "A tube tunnel is a play structure you can crawl through. It is part of a playground adventure and can make hollow sounds."),
        QAItem("What does a seesaw do?", "A seesaw rocks up and down when children sit on it. It can squeak or creak when it moves."),
        QAItem("What is a ruckus?", "A ruckus is a loud, messy commotion. It often happens when noise, movement, and conflict all pile up."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("playground", "sound_effects", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("park", "foreshadowing", "Leo", "boy", "Ava", "girl", "father"),
    StoryParams("yard", "conflict", "Nina", "girl", "Finn", "boy", "mother"),
]


def tell_story(params: StoryParams) -> World:
    return tell(
        PLACES[params.place],
        FEATURES[params.feature],
        params.hero,
        params.hero_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
tube_rumble :- tube_shaking.
seesaw_creak :- seesaw_creaking.
conflict :- tube_jammed.
relief :- tube_fixed.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for f in FEATURES:
        lines.append(asp.fact("feature", f))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.feature} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pretzel_parking_lot_foreshadowing_mystery.py
============================================================================

A standalone storyworld for a small mystery set in a parking lot, built from the
seed words and instruments: pretzel, foreshadowing, and a child-facing mystery
tone. The domain is simple: a child notices odd clues in a parking lot, follows
them carefully, discovers that a lost pretzel has been hiding the reason for the
mystery, and the small problem is solved with a gentle reveal.

The storyworld is state-driven: entities have physical meters and emotional
memes, clues accumulate, suspicion grows, and the ending image proves what
changed.
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
SUSPICION_RISE = 1.0


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


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    features: list[str] = field(default_factory=list)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    hidden: str
    kind: str = "thing"
    edible: bool = False
    clue: bool = False
    shiny: bool = False
    breakable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("suspicion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    out.append("__suspicion__")
    return out


def _r_resolve(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("found_pretzel") and not world.facts.get("resolved"):
        sig = ("resolve",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.entities["child"].memes["relief"] += 1
        world.facts["resolved"] = True
        out.append("__resolve__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "social", _r_suspicion),
    Rule("resolve", "social", _r_resolve),
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


def clue_risk(setting: Setting, item: ObjectCfg) -> bool:
    return setting.id == "parking_lot" and item.clue


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if clue_risk(setting, obj):
                combos.append((sid, oid))
    return combos


@dataclass
class StoryParams:
    setting: str
    object: str
    child: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld in a parking lot with a pretzel clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=["mom", "dad"])
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


def _pick_name(rng: random.Random) -> str:
    return rng.choice(NAMES)


def explain_rejection(setting: Setting, obj: ObjectCfg) -> str:
    if setting.id != "parking_lot":
        return "(No story: this mystery is only set in a parking lot.)"
    return "(No story: the chosen object is not a usable clue for this mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting != "parking_lot":
        raise StoryError("(No story: this mystery only happens in a parking lot.)")
    if args.object and args.object not in OBJECTS:
        raise StoryError("(No story: unknown object.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj = rng.choice(sorted(combos))
    child = args.child or _pick_name(rng)
    parent = args.parent or rng.choice(["mom", "dad"])
    return StoryParams(setting, obj, child, parent)


def _do_find(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["suspicion"] += SUSPICION_RISE
    child.meters["steps"] += 1
    world.get("clue").meters["noticed"] += 1
    world.facts["found_pretzel"] = True
    propagate(world, narrate=False)


def tell(setting: Setting, obj: ObjectCfg, child_name: str, parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl" if child_name in GIRL_NAMES else "boy",
                             label=child_name, role="detective", traits=["curious"]))
    child.id = child_name
    child.label = child_name
    world.entities[child_name] = child
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="helper"))
    lot = world.add(Entity(id="lot", kind="place", type="parking lot", label="the parking lot"))
    clue = world.add(Entity(id="clue", kind="thing", type="pretzel", label=obj.label))
    world.facts["setting"] = setting
    world.facts["object"] = obj
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["lot"] = lot
    world.facts["clue_entity"] = clue

    world.say(f"On a quiet afternoon, {child_name} and {parent.label} crossed the parking lot.")
    world.say(f"The lot looked ordinary, but {setting.mood} details kept catching {child_name}'s eye.")
    world.say(
        f"Near a painted line, {child_name} spotted {obj.phrase}. "
        f"It seemed out of place, like it had been left behind on purpose."
    )
    world.para()
    world.say(
        f"{child_name} followed the tiny clue between two cars and around a cart return."
    )
    world.say(
        f"There, tucked near a wheel stop, was the answer: {obj.hidden}. "
        f"The little clue made the mystery feel less scary and more interesting."
    )
    _do_find(world, child, obj)
    world.para()
    world.say(
        f'{parent.label} laughed softly. "So that was the mystery," {parent.pronoun()} said. '
        f"'"A pretzel was hiding the trail all along."'
    )
    world.say(
        f"{child_name} smiled and held up the crumbly pretzel piece like a prize. "
        f"The parking lot was still the same place, but now it felt solved."
    )
    world.facts["outcome"] = "solved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"].label
    return [
        'Write a child-friendly mystery story set in a parking lot that includes the word "pretzel" and uses foreshadowing.',
        f"Tell a short mystery about {child} in a parking lot where a pretzel is an important clue and the ending explains the clue.",
        "Write a gentle, puzzly story where something ordinary in a parking lot turns out to matter later, with clues that hint at the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"].label
    obj = world.facts["object"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a small mystery story. The clues make the reader wonder what is going on before the answer is shown at the end."
        ),
        QAItem(
            question=f"What did {child} notice in the parking lot?",
            answer=f"{child} noticed {obj.phrase}. It seemed odd at first, and that oddness helped the mystery build."
        ),
        QAItem(
            question="How was foreshadowing used?",
            answer="The story gave small hints before the answer. The pretzel looked strange early on, and later that clue made sense when the hidden reason was revealed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pretzel?",
            answer="A pretzel is a baked snack with a twisty shape. It can be crunchy or soft, and people sometimes eat it warm."
        ),
        QAItem(
            question="What is a parking lot?",
            answer="A parking lot is a place where cars are parked. People walk through it to get to shops, homes, or other places."
        ),
        QAItem(
            question="What does foreshadowing mean?",
            answer="Foreshadowing means giving little hints about something that will matter later. It helps the reader feel the mystery before the answer arrives."
        ),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "parking_lot": Setting("parking_lot", "the parking lot", "mysterious", ["cars", "lines", "wheel stops"]),
}

OBJECTS = {
    "pretzel": ObjectCfg("pretzel", "pretzel", "a half-eaten pretzel", "a hidden napkin trail", clue=True, edible=True, shiny=False, breakable=True, tags={"pretzel", "mystery"}),
}

NAMES = ["Mia", "Lily", "Nora", "Theo", "Ben", "Ava"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava"]


ASP_RULES = r"""
valid(S, O) :- setting(S), object(O), clue_object(O), parking_lot(S).
outcome(solved) :- valid(_, _).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "parking_lot"), asp.fact("parking_lot", "parking_lot")]
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.clue:
            lines.append(asp.fact("clue_object", oid))
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
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: smoke test crashed: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], params.child, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, object) combos:")
        for s, o in asp_valid_combos():
            print(f"  {s:12} {o}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, o, "Mia", "mom")) for s, o in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

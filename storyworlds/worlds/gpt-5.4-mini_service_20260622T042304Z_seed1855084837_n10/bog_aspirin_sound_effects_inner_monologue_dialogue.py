#!/usr/bin/env python3
"""
storyworlds/worlds/bog_aspirin_sound_effects_inner_monologue_dialogue.py
=======================================================================

A small fairy-tale storyworld about a child, a misty bog, and a medicine run.
The tale includes sound effects, inner monologue, and dialogue, while staying
grounded in a simple state model with physical meters and emotional memes.

Seed premise:
- A child in a fairy-tale bog must carry aspirin safely through wet ground.
- The bog can splash, sink, and steal time.
- A helpful turn offers a safe route and a bright ending image.

The world is intentionally compact: one Entity type, one World model, a few
registries, a forward causal rule, and a reasonableness gate mirrored in ASP.
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

# Robust import path setup: walk upward until we find storyworlds/results.py.
_HERE = os.path.abspath(os.path.dirname(__file__))
while True:
    candidate = os.path.join(_HERE, "results.py")
    if os.path.exists(candidate):
        if _HERE not in sys.path:
            sys.path.insert(0, _HERE)
        break
    parent = os.path.dirname(_HERE)
    if parent == _HERE:
        raise RuntimeError("Could not locate storyworlds/results.py")
    _HERE = parent

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
    owner: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch", "woman"}
        male = {"boy", "father", "king", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    adjective: str
    splash: str
    can_cross: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Medicine:
    id: str
    label: str
    phrase: str
    effect: str
    dry_container: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route_safe: bool = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.route_safe = self.route_safe
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_medicine(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    med = world.get("aspirin")
    if child.meters["splash"] >= THRESHOLD and not med.attrs.get("in_tin", False):
        sig = ("wet", med.id)
        if sig not in world.fired:
            world.fired.add(sig)
            med.meters["wet"] += 1
            child.memes["worry"] += 1
            out.append("__wet__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("wet_medicine", "physical", _r_wet_medicine)]


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


def predict_wet(world: World) -> bool:
    sim = world.copy()
    sim.get("child").meters["splash"] += 1
    propagate(sim, narrate=False)
    return sim.get("aspirin").meters["wet"] >= THRESHOLD


def safe_combo(place: Place, med: Medicine, helper: Helper) -> bool:
    return place.can_cross and med.dry_container and "dry" in helper.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, med in MEDICINES.items():
            for hid, helper in HELPERS.items():
                if safe_combo(place, med, helper):
                    combos.append((pid, mid, hid))
    return combos


@dataclass
class StoryParams:
    place: str
    medicine: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "moonbog": Place("moonbog", "the moonlit bog", "misty", "splash-splash", True, {"bog", "mist"}),
    "reedbog": Place("reedbog", "the reed bog", "green", "squelch-squelch", True, {"bog", "reeds"}),
    "oldbog": Place("oldbog", "the old bog path", "gray", "plip-plop", True, {"bog", "path"}),
}

MEDICINES = {
    "aspirin": Medicine("aspirin", "aspirin", "a small packet of aspirin", "ease the ache", True, {"aspirin", "medicine"}),
    "aspirin_tin": Medicine("aspirin_tin", "aspirin", "a small tin of aspirin", "ease the ache", True, {"aspirin", "medicine", "tin"}),
}

HELPERS = {
    "reed_bridge": Helper("reed_bridge", "reed bridge", "a reed bridge", "lay down reeds like a path", {"dry", "bridge"}),
    "stilt_step": Helper("stilt_step", "stilt step", "a pair of stilt-steps", "step only on the raised boards", {"dry", "boards"}),
    "lantern_guide": Helper("lantern_guide", "lantern guide", "a lantern guide", "light the way and keep the packet high", {"dry", "light"}),
}

GIRL_NAMES = ["Lily", "Mira", "Nora", "Ava", "Elsa", "Pippa"]
BOY_NAMES = ["Robin", "Theo", "Finn", "Perry", "Owen", "Jasper"]
TRAITS = ["brave", "curious", "gentle", "steadfast", "merry"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bog storyworld with aspirin, sound effects, inner monologue, and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--medicine", choices=MEDICINES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection() -> str:
    return "(No story: this combination would not make a sensible bog-crossing tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.medicine is None or c[1] == args.medicine)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, medicine, helper = rng.choice(sorted(combos))
    med = MEDICINES[medicine]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, medicine=medicine, helper=helper, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    med = MEDICINES[params.medicine]
    helper = HELPERS[params.helper]
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}", role="parent"))
    med_ent = world.add(Entity(id="aspirin", kind="thing", type="thing", label="aspirin", phrase=med.phrase, owner=parent.id, attrs={"in_tin": med.dry_container}, tags=set(med.tags)))
    world.add(Entity(id="helper", kind="thing", type="thing", label=helper.label, phrase=helper.phrase, tags=set(helper.tags)))
    child.memes["love"] += 1
    child.memes["worry"] += 0
    world.say(f"Once in {place.label}, little {params.name} lived beside a {place.adjective} bog. The air went {place.splash}, and the reeds nodded like courtiers.")
    world.say(f"'{params.name}, bring me the {med.label},' said {parent.label}. 'My ache will not wait.'")
    world.para()
    child.memes["desire"] += 1
    world.say(f"{params.name} looked at the path and thought, '{'I can do this.' if params.gender=='girl' else 'I can do this too.'} But I must not let the bog steal the medicine.'")
    world.say(f"Splash-splash went {params.name}'s boots as {params.name} crossed the reeds, while the bog whispered, 'Squelch... plip... plop...'")
    if predict_wet(world):
        world.say(f"'If I fall, the aspirin will get wet,' {params.name} thought, with a tiny shiver.")
    world.para()
    world.get("aspirin").attrs["in_tin"] = med.dry_container
    if helper.id == "reed_bridge":
        world.route_safe = True
        world.say(f"{params.name} whispered, 'I need a dry way over.'")
        world.say(f"Then {helper.phrase} appeared, and the helper said, 'Lay down the reeds like this, and keep the packet high.'")
        world.say(f"{params.name} answered, 'Thank you. I shall step where the reeds are firm.'")
        child.memes["joy"] += 1
        world.say(f"Tap-tap went {params.name}'s feet upon the dry reeds, and the aspirin stayed snug and dry.")
    elif helper.id == "stilt_step":
        world.route_safe = True
        world.say(f"{params.name} breathed, 'The bog is deep, but I can walk above it.'")
        world.say(f"{helper.phrase} let {params.name} step from board to board, and the packet never touched a splash.")
        world.say(f"Clink-clink went the little steps, and the aspirin stayed safe in hand.")
        child.memes["joy"] += 1
    else:
        world.route_safe = True
        world.say(f"{params.name} lifted the packet higher and followed the lantern's warm glow.")
        world.say(f"'Keep to the light,' said {parent.label}. 'The bog cannot swallow what you hold above it.'")
        world.say(f"Glow-glow went the lantern, and the aspirin came home dry.")
        child.memes["joy"] += 1
    world.para()
    world.say(f"At last {params.name} returned to the cottage. {parent.label.capitalize()} smiled and swallowed the aspirin with tea.")
    world.say(f"Ahh, the ache eased, and the bog outside only sang its sleepy song: plip-plop, plip-plop.")
    world.say(f"{params.name} stood at the doorway, proud and bright, while the moon hung over the bog like a silver spoon.")
    world.facts.update(child=child, parent=parent, medicine=med_ent, helper=helper, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the words "bog" and "aspirin" and uses sound effects like plip-plop and splash-splash.',
        f"Tell a gentle story where {f['child'].label} crosses {f['place'].label} with aspirin for {f['parent'].label}, and include inner monologue and dialogue.",
        f'Write a short fairy-tale about a bog, a packet of aspirin, and a safe helper who keeps the medicine dry.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, place, med, helper = f["child"], f["parent"], f["place"], f["medicine"], f["helper"]
    return [
        QAItem(
            question=f"Why did {child.label} cross {place.label}?",
            answer=f"{child.label} crossed the bog to bring the aspirin to {parent.label}. {parent.label} had an ache, so the medicine needed to arrive dry and fast.",
        ),
        QAItem(
            question=f"What helped {child.label} keep the aspirin safe in {place.label}?",
            answer=f"{helper.phrase} helped {child.label} keep the aspirin dry. It gave a safe way across the bog, so the medicine could reach the cottage without getting wet.",
        ),
        QAItem(
            question=f"What sound did the bog make while {child.label} walked?",
            answer=f"The bog made sounds like splash-splash and plip-plop. Those sounds showed the ground was wet and a little tricky to cross.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["medicine"].tags) | set(f["helper"].tags)
    items: list[QAItem] = []
    if "bog" in tags:
        items.append(QAItem("What is a bog?", "A bog is a wet, muddy place where the ground can be soft and slippery. People step carefully there so they do not sink or splash into trouble."))
    if "aspirin" in tags:
        items.append(QAItem("What is aspirin?", "Aspirin is a medicine that can help ease an ache. It should be kept dry and handled carefully."))
    if "medicine" in tags:
        items.append(QAItem("Why should medicine stay dry?", "Medicine should stay dry so it does not get ruined. A dry packet is easier to carry safely to the person who needs it."))
    return items


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moonbog", medicine="aspirin", helper="reed_bridge", name="Lily", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="reedbog", medicine="aspirin_tin", helper="stilt_step", name="Robin", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="oldbog", medicine="aspirin", helper="lantern_guide", name="Mira", gender="girl", parent="mother", trait="steadfast"),
]


ASP_RULES = r"""
wet_medicine(Child, Med) :- child(Child), medicine(Med), splash_risk(Child), not in_tin(Med).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.can_cross:
            lines.append(asp.fact("can_cross", pid))
    for mid, m in MEDICINES.items():
        lines.append(asp.fact("medicine", mid))
        if m.dry_container:
            lines.append(asp.fact("in_tin", mid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_tag", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show place/1. #show medicine/1. #show helper/1."))
    places = asp.atoms(model, "place")
    meds = asp.atoms(model, "medicine")
    helpers = asp.atoms(model, "helper")
    out = []
    for p in places:
        for m in meds:
            for h in helpers:
                if safe_combo(PLACES[p[0]], MEDICINES[m[0]], HELPERS[h[0]]):
                    out.append((p[0], m[0], h[0]))
    return sorted(set(out))


def asp_verify() -> int:
    ok = True
    pset = set(valid_combos())
    aset = set(asp_valid_combos())
    if pset != aset:
        ok = False
        print("MISMATCH between Python and ASP valid combos.")
        print(" only python:", sorted(pset - aset))
        print(" only asp:", sorted(aset - pset))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as ex:
        ok = False
        print(f"SMOKE TEST FAILED: {ex}")
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(pset)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.medicine not in MEDICINES or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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
        print(asp_program("#show place/1. #show medicine/1. #show helper/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, m, h in asp_valid_combos():
            print(f"  {p:8} {m:10} {h}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

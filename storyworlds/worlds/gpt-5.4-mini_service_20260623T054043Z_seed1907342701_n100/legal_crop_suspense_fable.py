#!/usr/bin/env python3
"""
storyworlds/worlds/legal_crop_suspense_fable.py
===============================================

A standalone storyworld for a small fable-like suspense tale about a legal
rule, a crop, and a careful night watch.

The world is intentionally tiny: one child farmer, one helper, one crop,
one legal rule, and one nighttime disturbance. The state changes from
calm planning to a tense watch to a quiet resolution, and the prose is
driven by those changes rather than by a frozen template.
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
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    key: str
    label: str
    setting_line: str
    crop_line: str
    legal_line: str
    night_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Crop:
    key: str
    label: str
    phrase: str
    at_risk_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Disturbance:
    key: str
    label: str
    sound: str
    source: str
    danger_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    key: str
    label: str
    use_line: str
    success_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    crop: str
    disturbance: str
    method: str
    name: str
    gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


PLACES = {
    "orchard": Place(
        key="orchard",
        label="the orchard",
        setting_line="The orchard slept under a silver moon, and the rows of trees stood still.",
        crop_line="Every branch carried a careful crop, and the baskets waited by the shed.",
        legal_line="A wooden sign by the gate said the crop was legal to pick only after dawn.",
        night_line="At night, the orchard felt wider, and every twig seemed to listen.",
        tags={"orchard", "night"},
    ),
    "field": Place(
        key="field",
        label="the field",
        setting_line="The field lay flat and dark, with long rows of sleeping plants.",
        crop_line="A ripe crop leaned low, shining softly in the moonlight.",
        legal_line="A paper notice on the fence said the crop was legal to gather only with a grown-up present.",
        night_line="At night, the field made every whisper sound close by.",
        tags={"field", "night"},
    ),
    "garden": Place(
        key="garden",
        label="the garden",
        setting_line="The garden was small and neat, with paths like narrow ribbons.",
        crop_line="A tidy crop grew in bright patches beside the beans and herbs.",
        legal_line="A sign on the gate said the crop was legal to take only on market morning.",
        night_line="At night, the garden smelled wet and green, and shadows hid under the leaves.",
        tags={"garden", "night"},
    ),
    "village_plot": Place(
        key="village_plot",
        label="the village plot",
        setting_line="The village plot rested behind the last house, quiet as a held breath.",
        crop_line="A proud crop stood in little squares, kept neat by patient hands.",
        legal_line="A posted rule near the path said the crop was legal to share only after the tally was done.",
        night_line="At night, the village plot was so quiet that even a pebble sounded bold.",
        tags={"village", "night"},
    ),
}

CROPS = {
    "corn": Crop(
        key="corn",
        label="corn",
        phrase="sweet corn",
        at_risk_line="The corn bent under the wind, and the dark made each stalk look like a stranger.",
        ending_image="The corn stood bundled in baskets, tall and bright above the straw.",
        tags={"corn"},
    ),
    "apples": Crop(
        key="apples",
        label="apples",
        phrase="red apples",
        at_risk_line="The apples shone like small lanterns, and it was hard to tell a thief from a branch.",
        ending_image="The apples filled two baskets, shining clean beside the shed door.",
        tags={"apples"},
    ),
    "peas": Crop(
        key="peas",
        label="peas",
        phrase="green peas",
        at_risk_line="The pea pods rattled softly, like tiny feet in the leaves.",
        ending_image="The peas rested safe in a bowl, their shells neat and untouched.",
        tags={"peas"},
    ),
    "wheat": Crop(
        key="wheat",
        label="wheat",
        phrase="golden wheat",
        at_risk_line="The wheat brushed the child's knees, whispering as if it knew a secret.",
        ending_image="The wheat stood tied in sheaves, shining like a little sun on the ground.",
        tags={"wheat"},
    ),
}

DISTURBANCES = {
    "raccoon": Disturbance("raccoon", "raccoon", "a soft rustle", "a raccoon", "sneaky", tags={"night", "animal"}),
    "goat": Disturbance("goat", "goat", "a clatter of hooves", "a goat", "hungry", tags={"night", "animal"}),
    "wind": Disturbance("wind", "wind", "a long moan through the leaves", "the wind", "sly", tags={"night", "weather"}),
    "crow": Disturbance("crow", "crow", "a sharp caw from the fence", "a crow", "watchful", tags={"night", "bird"}),
}

METHODS = {
    "lantern": Method(
        key="lantern",
        label="a lantern",
        use_line="They took a lantern from the hook and carried it carefully between them.",
        success_line="The lantern showed every path and every paw-print, and the fear faded.",
        fail_line="The lantern was small and steady, but not enough to calm the whole dark.",
        tags={"light"},
    ),
    "rope_bell": Method(
        key="rope_bell",
        label="a rope bell",
        use_line="They tied a little bell to a rope by the gate so the next sound would ring clearly.",
        success_line="The bell sang at once, and the children knew the movement was only a visitor passing through.",
        fail_line="The bell rang, but the shape in the dark kept coming closer.",
        tags={"sound"},
    ),
    "dog_whistle": Method(
        key="dog_whistle",
        label="a whistle",
        use_line="They blew a small whistle that their dog knew, and then they waited still.",
        success_line="The whistle brought the dog trotting over, tail wagging, and the trouble stopped.",
        fail_line="The whistle only made the dark feel tighter.",
        tags={"sound", "animal"},
    ),
    "scarecrow_lamp": Method(
        key="scarecrow lamp",
        label="a scarecrow lamp",
        use_line="They switched on a little lamp beside the scarecrow, hoping the bright face would help.",
        success_line="The lamp made the shadow plain, and the mystery became harmless at once.",
        fail_line="The lamp glowed, but the trouble did not leave.",
        tags={"light"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Maya", "Elin"]
BOY_NAMES = ["Tomas", "Bram", "Noel", "Eli", "Jules", "Sami"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for crop in CROPS:
            for dist in DISTURBANCES:
                for method in METHODS:
                    if place in {"orchard", "field", "garden", "village_plot"}:
                        combos.append((place, crop, dist, method))
    return combos


def explain_rejection() -> str:
    return "(No story: that combination does not fit this tiny legal-crop suspense world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: legal crop suspense in a fable style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.crop is None or c[1] == args.crop)
              and (args.disturbance is None or c[2] == args.disturbance)
              and (args.method is None or c[3] == args.method)]
    if not combos:
        raise StoryError(explain_rejection())
    place, crop, disturbance, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper_name == name:
        helper_name = (rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != name]))
    return StoryParams(place=place, crop=crop, disturbance=disturbance, method=method,
                       name=name, gender=gender, helper_name=helper_name, helper_gender=helper_gender)


def _make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name,
                            role="watcher", meters={}, memes={"worry": 0.0, "hope": 0.0}, attrs={}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name,
                              role="helper", meters={}, memes={"worry": 0.0, "hope": 0.0}, attrs={}))
    crop = world.add(Entity(id="crop", kind="thing", type="crop", label=CROPS[params.crop].label,
                            phrase=CROPS[params.crop].phrase, owner=hero.id,
                            meters={"risk": 0.0, "safe": 0.0}, memes={}, attrs={}))
    dist = world.add(Entity(id="disturbance", kind="thing", type="disturbance",
                            label=DISTURBANCES[params.disturbance].label,
                            phrase=DISTURBANCES[params.disturbance].source,
                            meters={"near": 0.0}, memes={}, attrs={}))
    method = world.add(Entity(id="method", kind="thing", type="method",
                              label=METHODS[params.method].label,
                              phrase=METHODS[params.method].use_line,
                              meters={"used": 0.0}, memes={}, attrs={}))
    world.facts = {
        "hero": hero, "helper": helper, "crop": crop, "disturbance": dist,
        "method": method, "place": PLACES[params.place], "crop_cfg": CROPS[params.crop],
        "dist_cfg": DISTURBANCES[params.disturbance], "method_cfg": METHODS[params.method],
        "mystery": False, "resolved": False, "ending": "",
    }
    return world


def propagate(world: World, narrate: bool = True) -> None:
    if ("mystery", "set") in world.fired:
        return
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    crop = world.facts["crop"]
    dist = world.facts["disturbance"]
    method = world.facts["method"]
    if dist.meters.get("near", 0.0) >= THRESHOLD and crop.meters.get("risk", 0.0) >= THRESHOLD:
        world.fired.add(("mystery", "set"))
        hero.memes["worry"] += 1
        helper.memes["worry"] += 1
        if narrate:
            world.say("The dark sound stayed near the crop, and both children grew quiet.")
    if method.meters.get("used", 0.0) >= THRESHOLD and dist.meters.get("near", 0.0) >= THRESHOLD:
        world.fired.add(("method", "used"))
        helper.memes["hope"] += 1


def tell(world: World) -> None:
    p = world.place
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    crop = world.facts["crop"]
    dist = world.facts["disturbance"]
    method = world.facts["method"]
    cfg = world.facts
    world.say(f"{hero.label} and {helper.label} worked in {p.label} when the evening turned quiet.")
    world.say(f"{p.setting_line} {p.crop_line} {p.legal_line}")
    world.para()
    world.say(f"{crop.phrase.capitalize()} was the crop they watched most closely, because {crop.label} was the family's pride.")
    world.say(f"Then a sound came: {dist.sound}. It did not sound large, but it did sound wrong.")
    crop.meters["risk"] = 1.0
    dist.meters["near"] = 1.0
    propagate(world)
    world.para()
    world.say(f"{hero.label} wanted to stay brave, yet {hero.pronoun().capitalize()} listened to the dark instead of rushing ahead.")
    world.say(f"{method.phrase if method.phrase else METHODS[cfg['method_cfg'].key].use_line}")
    world.say(METHODS[cfg["method_cfg"].key].use_line)
    method.meters["used"] = 1.0
    if cfg["dist_cfg"].key == "wind":
        hero.memes["worry"] += 1
    propagate(world)
    world.para()
    if cfg["method_cfg"].key in {"lantern", "scarecrow_lamp"}:
        world.say(METHODS[cfg["method_cfg"].key].success_line)
        world.say(f"When the light reached the rows, the mystery was only {dist.source} moving through the leaves.")
        world.say(f"{hero.label} and {helper.label} smiled, and the {crop.label} stayed legal and safe for morning.")
        crop.meters["safe"] = 1.0
        world.facts["resolved"] = True
        world.facts["ending"] = "safe"
        world.say(f"{crop.ending_image}")
    else:
        world.say(METHODS[cfg["method_cfg"].key].fail_line)
        world.say(f"They waited still, and then saw that the noise was only {dist.source}, not a thief at all.")
        world.say(f"The night passed, and the {crop.label} remained legal to gather when dawn came.")
        crop.meters["safe"] = 1.0
        world.facts["resolved"] = True
        world.facts["ending"] = "quiet"


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like suspense story that uses the words "legal" and "crop" and takes place in {f["place"].label}.',
        f"Tell a short story where {f['hero'].label} and {f['helper'].label} hear a strange sound near the crop and choose a careful way to check it.",
        f'Write a child-friendly suspense tale about a legal rule, a crop, and a small mystery that turns out safe by the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    crop = f["crop_cfg"]
    dist = f["dist_cfg"]
    method = f["method_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Why did {hero.label} and {helper.label} not pick the {crop.label} right away?",
            answer=f"They saw that it was legal to take the crop only under the rule on the sign, so they waited. The night sound made them more careful instead of more hasty.",
        ),
        QAItem(
            question=f"What made the night feel suspenseful near {place.label}?",
            answer=f"A sound from {dist.source} came close to the crop, and no one knew at first what it was. That made the children hold still and listen before acting.",
        ),
        QAItem(
            question=f"How did {method.label} help the children handle the mystery?",
            answer=f"{METHODS[method.key].use_line} It gave them a safe way to check the dark without hurting the crop.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does legal mean in this story world?",
            answer="Legal means allowed by the rule that was posted in the story. It tells the children when they may pick the crop safely and fairly.",
        ),
        QAItem(
            question="What is a crop?",
            answer="A crop is a plant or food people grow and later gather. In this world, the crop is the thing the children protect and wait to harvest.",
        ),
        QAItem(
            question="Why do children use a lantern or lamp at night?",
            answer="A lantern or lamp helps them see without guessing in the dark. That makes it easier to stay calm and choose a careful path.",
        ),
    ]
    return out


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
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orchard", crop="apples", disturbance="raccoon", method="lantern", name="Mina", gender="girl", helper_name="Bram", helper_gender="boy"),
    StoryParams(place="field", crop="corn", disturbance="wind", method="rope_bell", name="Noel", gender="boy", helper_name="Ivy", helper_gender="girl"),
    StoryParams(place="garden", crop="peas", disturbance="crow", method="scarecrow_lamp", name="Lila", gender="girl", helper_name="Eli", helper_gender="boy"),
    StoryParams(place="village_plot", crop="wheat", disturbance="goat", method="dog_whistle", name="Tomas", gender="boy", helper_name="Maya", helper_gender="girl"),
]


ASP_RULES = r"""
valid(P,C,D,M) :- place(P), crop(C), disturbance(D), method(M).
legal_allowed(P) :- place(P).
crop_risk(C) :- crop(C).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CROPS:
        lines.append(asp.fact("crop", c))
    for d in DISTURBANCES:
        lines.append(asp.fact("disturbance", d))
    for m in METHODS:
        lines.append(asp.fact("method", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: ASP parity and story generation smoke test passed.")
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(1 << 30))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng0.randrange(1 << 30)))
            params.seed = args.seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

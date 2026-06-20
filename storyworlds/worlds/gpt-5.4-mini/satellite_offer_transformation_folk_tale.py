#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/satellite_offer_transformation_folk_tale.py
============================================================================

A standalone story world sketch for a tiny folk-tale domain: a village child
finds a fallen satellite, a tempting offer is made, and the child transforms the
object from a strange sky-metal burden into a kindly lantern for the village.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a story-driven transformation turn
- grounded QA from world state
- an inline ASP twin for parity checking
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
DELIGHT_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "king", "smith"}
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
class FolkSetting:
    id: str
    place: str
    dwellers: str
    night_line: str
    morning_line: str

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
class Offer:
    id: str
    giver_line: str
    promise: str
    cost: str
    gentle: bool
    turns_on: str
    turns_to: str
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
class Satellite:
    id: str
    label: str
    fallen_phrase: str
    shine: str
    metal: bool = True
    lonely: bool = True
    transform_to: str = "lantern"
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
class Remedy:
    id: str
    label: str
    method: str
    result: str
    power: int
    sense: int
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
    def __init__(self, setting: FolkSetting) -> None:
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for k in list(world.entities.values()):
            if k.kind == "character":
                k.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_blight(world: World) -> list[str]:
    out: list[str] = []
    sat = world.entities.get("satellite")
    if sat and sat.meters["changed"] >= THRESHOLD:
        sig = ("blight", sat.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__changed__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("blight", "transformation", _r_blight)]


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


def transform_possible(sat: Satellite) -> bool:
    return sat.metal and sat.lonely


def good_offer(offer: Offer) -> bool:
    return offer.gentle


def can_remedy(remedy: Remedy, sat: Satellite) -> bool:
    return remedy.power >= 1 and sat.metal


def folk_voice(name: str) -> str:
    return f"dear {name}"


def setup(world: World, child: Entity, elder: Entity, setting: FolkSetting, sat: Satellite) -> None:
    child.memes["curiosity"] += 1
    elder.memes["patience"] += 1
    world.say(
        f"Once, in {setting.place}, {child.id} and {elder.id} lived among {setting.dwellers}. "
        f"{setting.night_line}"
    )
    world.say(
        f"At the edge of the wood, they found a {sat.label} lying in the grass, its {sat.shine}."
    )


def offer_scene(world: World, child: Entity, elder: Entity, offer: Offer, sat: Satellite) -> None:
    world.para()
    child.memes["hope"] += 1
    world.say(
        f"A wandering voice made an offer: {offer.giver_line} {offer.promise} {offer.cost}."
    )
    world.say(
        f"{child.id} touched the {sat.label} and thought of {sat.fallen_phrase}."
    )


def warn(world: World, elder: Entity, child: Entity, sat: Satellite, offer: Offer) -> None:
    if not transform_possible(sat):
        raise StoryError("The satellite in this world cannot be transformed.")
    world.say(
        f"{elder.id} shook {elder.pronoun('possessive')} head. "
        f'"This sky-thing is not meant to stay broken," {elder.pronoun()} said. '
        f'"A kinder use is better than a greedy one."'
    )
    if offer.gentle:
        world.say(
            f"{child.id} listened, because the offer sounded gentle and the old tale had room for mercy."
        )


def choose(world: World, child: Entity, offer: Offer, sat: Satellite) -> None:
    child.memes["resolve"] += 1
    world.say(
        f'{child.id} took a breath and answered, "No. I will not trade this wonder away."'
    )
    world.say(
        f"Instead, {child.id} carried the {sat.label} home under both arms, as carefully as a loaf of bread."
    )


def transform(world: World, child: Entity, sat: Entity, remedy: Remedy) -> None:
    sat.meters["changed"] += 1
    sat.meters["bright"] += 1
    child.memes["joy"] += 1
    world.say(
        f"By the hearth, {child.id} used {remedy.method}, and the {sat.label} began to change."
    )
    world.say(
        f"It was still the same sky-metal, but now it answered with {remedy.result}."
    )
    propagate(world, narrate=False)


def reveal(world: World, elder: Entity, sat: Satellite, remedy: Remedy, setting: FolkSetting) -> None:
    world.para()
    elder.memes["joy"] += 1
    world.say(
        f"{setting.morning_line} the house held a new light. The {sat.label} had become a {remedy.label}."
    )
    world.say(
        f"{elder.id} smiled and said it was better to keep a gift that could shine for everyone."
    )


def tell(setting: FolkSetting, offer: Offer, sat: Satellite, remedy: Remedy,
         child_name: str = "Anya", child_gender: str = "girl",
         elder_name: str = "Grandmother", elder_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    sky = world.add(Entity(id="satellite", kind="thing", type="thing", label=sat.label))
    setup(world, child, elder, setting, sat)
    offer_scene(world, child, elder, offer, sat)
    warn(world, elder, child, sat, offer)
    choose(world, child, offer, sat)
    world.para()
    transform(world, child, sky, remedy)
    reveal(world, elder, sat, remedy, setting)
    world.facts.update(
        child=child,
        elder=elder,
        satellite=sat,
        offer=offer,
        remedy=remedy,
        setting=setting,
        transformed=True,
        accepted_offer=False,
    )
    return world


SETTINGS = {
    "hill_village": FolkSetting(
        "hill_village",
        "a hill village",
        "grandmothers, goat herders, and lantern makers",
        "At dusk, the bells sang softly over the roofs.",
        "At dawn, the whole lane smelled of bread and pine smoke.",
    ),
    "river_village": FolkSetting(
        "river_village",
        "a river village",
        "fishers, reed weavers, and story-singers",
        "At dusk, the water glimmered like a secret path.",
        "At dawn, the river flashed gold under the first sun.",
    ),
    "pine_village": FolkSetting(
        "pine_village",
        "a pine village",
        "woodcutters, berry pickers, and old storytellers",
        "At dusk, the pines whispered as the moon climbed.",
        "At dawn, birds woke the chimneys one by one.",
    ),
}

OFFERS = {
    "buy_it": Offer(
        "buy_it",
        "a rich trader came by and said",
        "they would buy the fallen sky-thing for silver",
        "if the child would give it up at once",
        True,
        "turning it into coins",
        "turning it into a shared feast",
        {"trade", "coins"},
    ),
    "hide_it": Offer(
        "hide_it",
        "a fox-faced peddler whispered",
        "they could hide the sky-thing in a sack",
        "to keep it for the peddler alone",
        False,
        "turning it into a secret",
        "turning it into a trick",
        {"trick"},
    ),
    "gift_it": Offer(
        "gift_it",
        "a kindly baker offered",
        "they could place the sky-thing above the oven",
        "to help the whole village see at night",
        True,
        "turning it into a lamp",
        "turning it into a blessing",
        {"gift", "light"},
    ),
}

SATELLITES = {
    "fallen_starship": Satellite(
        "fallen_starship",
        "satellite",
        "fallen from the clouds",
        "silver and cold",
        transform_to="lantern",
        tags={"satellite", "metal"},
    ),
    "sleeping_orb": Satellite(
        "sleeping_orb",
        "satellite",
        "sent down by the sky",
        "dim as a shell",
        transform_to="mirror-lantern",
        tags={"satellite", "metal"},
    ),
}

REMEDIES = {
    "hearth_oil": Remedy("hearth_oil", "lantern", "lamp oil and a wick", "a warm gold glow", 1, 3, {"light"}),
    "mender_song": Remedy("mender_song", "mirror-lantern", "a song of mending and a polished bowl", "a bright moon-glimmer", 1, 3, {"light"}),
}

GIRL_NAMES = ["Anya", "Mira", "Iris", "Lina"]
BOY_NAMES = ["Bram", "Nico", "Jory", "Pavel"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    offer: str
    satellite: str
    remedy: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for o in OFFERS:
            for sat in SATELLITES:
                if transform_possible(SATELLITES[sat]) and good_offer(OFFERS[o]):
                    combos.append((s, o, sat))
    return combos


def explain_rejection(offer: Offer) -> str:
    return f"(No story: the offer is too sharp and ungentle for a folk tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld with a satellite offer and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--offer", choices=OFFERS)
    ap.add_argument("--satellite", choices=SATELLITES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    if args.offer and not OFFERS[args.offer].gentle:
        raise StoryError(explain_rejection(OFFERS[args.offer]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.offer is None or c[1] == args.offer)
              and (args.satellite is None or c[2] == args.satellite)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, offer, satellite = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder_name = args.elder_name or rng.choice(["Grandmother", "Grandfather", "Auntie", "Uncle"])
    remedy = args.remedy or rng.choice(sorted(REMEDIES))
    return StoryParams(setting, offer, satellite, remedy, child_name, child_gender, elder_name, elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a small child that includes the words "satellite" and "offer".',
        f"Tell a gentle village story where {f['child'].id} finds a satellite and must answer a tempting offer without giving up the wonder.",
        f"Write a transformation story in a folk-tale voice where an elder and child turn a fallen satellite into a helpful light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    sat = f["satellite"]
    offer = f["offer"]
    remedy = f["remedy"]
    return [
        QAItem(
            question="Who found the satellite?",
            answer=f"{child.id} found it near the edge of the village, and {elder.id} stayed close to help.",
        ),
        QAItem(
            question="What was the offer about?",
            answer=f"It was about taking the satellite away for a selfish use. The gentle answer was to keep it and make it helpful instead.",
        ),
        QAItem(
            question="How did the satellite change?",
            answer=f"It changed from a fallen sky-metal thing into a {remedy.label}. By using {remedy.method}, the child gave it a new life as a light for everyone.",
        ),
        QAItem(
            question="Why did the story end happily?",
            answer=f"{child.id} chose the kinder path and listened to {elder.id}. That choice turned the strange object into a shared blessing instead of a loss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satellite?",
            answer="A satellite is an object that goes around in the sky or space. In stories, it can be a strange metal thing that falls near people.",
        ),
        QAItem(
            question="What is an offer?",
            answer="An offer is when someone says they can give, trade, or do something. A kind offer helps; a greedy one can try to trick people.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or becomes useful in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hill_village", "gift_it", "fallen_starship", "hearth_oil", "Anya", "girl", "Grandmother", "woman"),
    StoryParams("river_village", "buy_it", "sleeping_orb", "mender_song", "Bram", "boy", "Grandfather", "man"),
    StoryParams("pine_village", "gift_it", "sleeping_orb", "hearth_oil", "Mira", "girl", "Auntie", "woman"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OFFERS[params.offer],
        SATELLITES[params.satellite],
        REMEDIES[params.remedy],
        params.child_name,
        params.child_gender,
        params.elder_name,
        params.elder_gender,
    )
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
gentle_offer(O) :- offer(O), gentle(O).
valid(S, O, Sat) :- setting(S), offer(O), satellite(Sat), gentle_offer(O), metal(Sat).
changed(Sat) :- chosen_satellite(Sat), chosen_remedy(R), remedy(R), power(R, P), P >= 1.
outcome(transformed) :- changed(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o, off in OFFERS.items():
        lines.append(asp.fact("offer", o))
        if off.gentle:
            lines.append(asp.fact("gentle", o))
    for sid, sat in SATELLITES.items():
        lines.append(asp.fact("satellite", sid))
        if sat.metal:
            lines.append(asp.fact("metal", sid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, REMEDIES[rid].power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_satellite", params.satellite), asp.fact("chosen_remedy", params.remedy)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    cases = list(CURATED)
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        return 1
    if any(asp_outcome(p) != "transformed" for p in cases):
        rc = 1
        print("MISMATCH in outcome logic.")
    else:
        print("OK: outcome logic parity looks good.")
    return rc


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.setting} / {p.offer} / {p.satellite}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bicycle_incapacitate_basil_sound_effects_folk_tale.py
=====================================================================================

A small folk-tale storyworld about a bicycle courier, a basil bundle, and a
comic mishap that leaves the rider too wobbly to continue. The tale is driven by
state changes, includes sound effects, and ends with a practical remedy and a
gentle lesson.

Seed words:
- bicycle
- incapacitate
- basil

Features:
- Sound effects
- Folk-tale style

The world is intentionally tiny: one rider, one bicycle, one basket of basil,
and a few sensible responses. The story can end in either a near-miss or a
messy mishap, depending on whether the bicycle is already safe to ride.
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
CAPABLE_MIN = 1.0


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
    broken: bool = False
    safe: bool = False

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
class Place:
    id: str
    label: str
    has_hill: bool
    has_stone_path: bool
    has_herb_garden: bool
    has_market: bool


@dataclass
class Bicycle:
    id: str
    label: str
    phrase: str
    rattle: str
    wobble: str
    has_basket: bool = True
    can_carry: bool = True
    speed: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class Basil:
    id: str
    label: str
    phrase: str
    scent: str
    slip: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    rider = world.entities.get("rider")
    bike = world.entities.get("bicycle")
    if not rider or not bike:
        return out
    if bike.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.memes["fear"] += 1
    rider.meters["unsteady"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bike = world.entities.get("bicycle")
    basil = world.entities.get("basil")
    if not bike or not basil:
        return out
    if bike.meters["crash"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basil.meters["scattered"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("wobble", "physical", _r_wobble), Rule("spill", "physical", _r_spill)]


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


def sound(text: str) -> str:
    return f"{text}"


def reasonableness_gate(bicycle: Bicycle, basil: Basil, place: Place) -> bool:
    return bicycle.can_carry and place.has_herb_garden and basil.label == "basil"


def severity_of(delay: int) -> int:
    return 1 + delay


def contained(response: Response, delay: int) -> bool:
    return response.power >= severity_of(delay)


def predict_mishap(world: World, delay: int) -> dict:
    sim = world.copy()
    bike = sim.get("bicycle")
    bike.meters["wobble"] += 1
    bike.meters["crash"] += delay
    propagate(sim, narrate=False)
    rider = sim.get("rider")
    basil = sim.get("basil")
    return {
        "wobbly": rider.meters["unsteady"] >= THRESHOLD,
        "basil_spilled": basil.meters["scattered"] >= THRESHOLD,
    }


def ride_setup(world: World, rider: Entity, bike: Entity, basil: Entity, place: Place) -> None:
    rider.memes["hope"] += 1
    world.say(
        f"Once in a green valley, {rider.id} found {bike.phrase} beside the path to "
        f"{place.label}. In the basket sat {basil.phrase}, smelling sweet as summer."
    )


def listen_for_road(world: World, bike: Entity) -> None:
    world.say(
        f"{bike.id} went {bike.rattle} on the stones, and the spokes sang {bike.wobble} "
        f"under the morning sky."
    )


def trouble(world: World, rider: Entity, bike: Entity, basil: Entity, place: Place) -> None:
    rider.memes["boldness"] += 1
    world.say(
        f'"I will take the bicycle to the market," {rider.id} said, though the hill by '
        f"{place.label} was steep and the path was slick. The wheel went "
        f"{bike.rattle}, and the basket swayed."
    )
    world.say(
        f'"Mind the basil!" warned the old gatekeeper. "A tumble would make it scatter."'
    )


def accident(world: World, rider: Entity, bike: Entity, basil: Entity, delay: int) -> None:
    bike.meters["wobble"] += 1
    bike.meters["crash"] += delay
    propagate(world, narrate=False)
    world.say(
        f"Then came a sudden bump -- {sound('clatter-clack!')} -- and the bicycle lurched. "
        f"The rider bobbed left, then right, and at last slid into the grass."
    )
    world.say(
        f"The basket tipped with a soft {sound('fwoof')}, and the basil leaves fluttered like green birds."
    )


def help_arrives(world: World, helper: Entity, response: Response, basil: Basil, place: Place) -> None:
    body = response.text.replace("{target}", basil.label)
    world.say(
        f"By and by, {helper.label_word} came along the path and {body}."
    )
    world.say(
        f"The little storm settled. The bicycle was still, the hill was quiet, and the basil smelled fresh again."
    )


def lesson(world: World, helper: Entity, rider: Entity, basil: Basil, response: Response) -> None:
    rider.memes["relief"] += 1
    rider.memes["lesson"] += 1
    world.say(
        f"Then {helper.label_word} laughed kindly and said, "
        f'"A bicycle is a fine friend, but a safe wheel keeps the day from turning wobbly."'
    )
    world.say(
        f"{rider.id} nodded and gathered the basil back into the basket, each leaf "
        f"neat and bright."
    )


def ending_safe(world: World, rider: Entity, bicycle: Entity, basil: Basil) -> None:
    rider.memes["joy"] += 1
    bicycle.safe = True
    world.say(
        f"So {rider.id} walked the bicycle slowly home, and the basil rode upright and proud. "
        f"The valley kept its peace, and the story ended with a basket full of fragrant green leaves."
    )


def ending_unsafe(world: World, rider: Entity, helper: Entity, basil: Basil) -> None:
    rider.memes["fear"] += 1
    world.say(
        f"So {helper.label_word} led {rider.id} home on foot, while the basil rested in a cloth bundle. "
        f"Nothing worse happened, and the road grew quiet behind them."
    )


def tell(place: Place, bicycle: Bicycle, basil: Basil, response: Response, delay: int = 0) -> World:
    world = World()
    rider = world.add(Entity(id="Robin", kind="character", type="girl", role="rider"))
    helper = world.add(Entity(id="Gatekeeper", kind="character", type="man", label="the gatekeeper", role="helper"))
    bike = world.add(Entity(id="bicycle", type="thing", label=bicycle.label))
    herb = world.add(Entity(id="basil", type="thing", label=basil.label))
    world.facts["place"] = place
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["bicycle"] = bicycle
    world.facts["basil"] = basil
    world.facts["rider"] = rider
    world.facts["helper"] = helper
    world.facts["bicycle_ent"] = bike
    world.facts["basil_ent"] = herb

    ride_setup(world, rider, bike, herb, place)
    world.para()
    listen_for_road(world, bicycle)
    trouble(world, rider, bike, herb, place)

    world.para()
    if not reasonableness_gate(bicycle, basil, place):
        raise StoryError("This tale needs a real bicycle carrier, a herb garden, and basil.")

    # Near-miss vs mishap is chosen by delay and response power.
    if delay == 0 and response.power >= 2:
        world.say(f"At the last moment, the gatekeeper called, {sound('whoa!')} and the rider stopped.")
        help_arrives(world, helper, response, basil, place)
        lesson(world, helper, rider, basil, response)
        world.para()
        ending_safe(world, rider, bike, herb)
        outcome = "safe"
    else:
        accident(world, rider, bike, herb, delay)
        if contained(response, delay):
            help_arrives(world, helper, response, basil, place)
            lesson(world, helper, rider, basil, response)
            world.para()
            ending_safe(world, rider, bike, herb)
            outcome = "safe"
        else:
            world.say(
                f"The gatekeeper tried to help, but the bicycle was too wild and the basket had already spilled."
            )
            world.say(
                f"{rider.id} had to rest on a stump until the wobble passed; she was too dizzy to continue, almost incapacitated by the tumble."
            )
            world.para()
            ending_unsafe(world, rider, helper, herb)
            outcome = "incapacitated"

    world.facts["outcome"] = outcome
    world.facts["helper_entity"] = helper
    return world


PLACES = {
    "village": Place(id="village", label="the village lane", has_hill=True, has_stone_path=True, has_herb_garden=True, has_market=True),
    "orchard": Place(id="orchard", label="the orchard road", has_hill=False, has_stone_path=True, has_herb_garden=True, has_market=True),
    "moor": Place(id="moor", label="the moor path", has_hill=True, has_stone_path=False, has_herb_garden=True, has_market=False),
}

BICYCLES = {
    "cartwheel": Bicycle(id="cartwheel", label="a little bicycle", phrase="a little bicycle with a bright bell", rattle="rat-a-tat", wobble="wibble-wobble", speed=3),
    "market": Bicycle(id="market", label="a sturdy bicycle", phrase="a sturdy bicycle with a wicker basket", rattle="clink-clink", wobble="wobble-wobble", speed=4),
}

BASILS = {
    "bundle": Basil(id="bundle", label="basil", phrase="a bundle of basil", scent="sweet", slip="slip-slide", tags={"basil"}),
    "sprig": Basil(id="sprig", label="basil", phrase="fresh basil", scent="bright", slip="flutter", tags={"basil"}),
}

RESPONSES = {
    "catch": Response(id="catch", sense=3, power=3, text="caught the bicycle and steadied the basket", fail="tried to catch the bicycle, but it was already down in the grass", qa_text="caught the bicycle and steadied the basket", tags={"help"}),
    "lift": Response(id="lift", sense=2, power=2, text="lifted the basket and set the basil to rights", fail="lifted the basket too late", qa_text="lifted the basket and set the basil to rights", tags={"help"}),
    "rest": Response(id="rest", sense=1, power=1, text="told the rider to rest a while", fail="told the rider to rest a while, but that was too little help", qa_text="told the rider to rest a while", tags={"help"}),
}

NAMES = ["Robin", "Mara", "Tessa", "Elin", "Anya", "Iris"]
TRAITS = ["careful", "curious", "kind", "steady"]


@dataclass
class StoryParams:
    place: str
    bicycle: str
    basil: str
    response: str
    name: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for bid, bike in BICYCLES.items():
            for hid, herb in BASILS.items():
                if place.has_herb_garden and bike.can_carry and herb.label == "basil":
                    combos.append((pid, bid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale bicycle story with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bicycle", choices=BICYCLES)
    ap.add_argument("--basil", choices=BASILS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.place and args.bicycle and args.basil and (args.place, args.bicycle, args.basil) not in combos:
        raise StoryError("No valid bicycle-and-basil tale matches those options.")
    place = args.place or rng.choice(sorted(PLACES))
    bicycle = args.bicycle or rng.choice(sorted(BICYCLES))
    basil = args.basil or rng.choice(sorted(BASILS))
    response = args.response or rng.choice(sorted(RESPONSES))
    name = rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place=place, bicycle=bicycle, basil=basil, response=response, name=name, trait=trait, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story that includes the words "bicycle", "incapacitate", and "basil".',
        f"Tell a child-friendly story where {f['rider'].id} rides a bicycle past {f['place'].label} and a mishap leaves her too wobbly to go on, but basil is saved.",
        f"Write a gentle story with sound effects and a clear ending image about a bicycle, basil, and a small accident on a village road.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rider = f["rider"]
    helper = f["helper"]
    place = f["place"]
    response = f["response"]
    outcome = f["outcome"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"The story is about {rider.id}, who rides a bicycle through {place.label}. The helper comes along when the road turns wobbly.",
        ),
        QAItem(
            question="What was in the bicycle basket?",
            answer="There was basil in the basket. Its green leaves mattered because the ride could spill them if the bicycle tipped.",
        ),
    ]
    if outcome == "safe":
        answers.append(QAItem(
            question="How was the problem fixed?",
            answer=f"{helper.label_word.capitalize()} {response.qa_text} and steadied the ride. That kept the basil safe and let the story end calmly.",
        ))
        answers.append(QAItem(
            question="What happened to the rider at the end?",
            answer=f"{rider.id} was no longer in danger and could go home safely. She ended the tale walking the bicycle slowly and carrying the basil upright.",
        ))
    else:
        answers.append(QAItem(
            question="Why did the rider have to stop?",
            answer=f"The bicycle wobble was so strong that {rider.id} became too dizzy to continue. In other words, the tumble nearly incapacitated her, so she had to rest before moving again.",
        ))
        answers.append(QAItem(
            question="How did the tale end?",
            answer="It ended with a careful walk home and a quiet road behind them. The basil was gathered up again, and the danger was over even though the ride did not continue.",
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is basil?",
            answer="Basil is a fragrant herb with green leaves. People use it in food, and it can be carried in a basket if treated gently.",
        ),
        QAItem(
            question="What should you do if a bicycle gets too wobbly to ride?",
            answer="You should stop riding and get to a safe place. A wobbly bicycle can throw you off balance, so rest and get help.",
        ),
        QAItem(
            question="Why do sound effects help a folk tale?",
            answer="Sound effects make the action feel lively and old-fashioned. Words like rat-a-tat or clatter-clack help a listener hear the moment in their imagination.",
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,S) :- place(P), bicycle(B), basil(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BICYCLES:
        lines.append(asp.fact("bicycle", b))
    for s in BASILS:
        lines.append(asp.fact("basil", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed and smoke test rendered a story.")
    return rc


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    bicycle = BICYCLES.get(params.bicycle)
    basil = BASILS.get(params.basil)
    response = RESPONSES.get(params.response)
    if not all([place, bicycle, basil, response]):
        raise StoryError("Invalid params for this storyworld.")
    world = tell(place, bicycle, basil, response, params.delay)
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


CURATED = [
    StoryParams(place="village", bicycle="market", basil="bundle", response="catch", name="Robin", trait="careful", delay=0),
    StoryParams(place="orchard", bicycle="cartwheel", basil="sprig", response="lift", name="Mara", trait="kind", delay=1),
    StoryParams(place="moor", bicycle="market", basil="bundle", response="rest", name="Tessa", trait="curious", delay=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wind": 0.0, "trouble": 0.0, "mud": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "relief": 0.0, "joy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "uncle", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl", "aunt", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    wind_strength: int
    has_mud: bool
    has_bridge: bool
    has_barn: bool
    has_river: bool


@dataclass
class Oath:
    id: str
    chant: str
    repeated_line: str
    fix_line: str
    helpful_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ActorSpec:
    id: str
    label: str
    type: str
    pronoun_name: str


@dataclass
class StoryParams:
    place: str = "riverbend"
    oath: str = "tug"
    actor: str = "Tilly"
    helper: str = "Bo"
    actor_type: str = "girl"
    helper_type: str = "boy"
    seed: Optional[int] = None


PLACES = {
    "riverbend": Place("riverbend", "the river bend", 3, True, True, True, True),
    "prairie": Place("prairie", "the prairie edge", 4, False, False, True, False),
    "harbor": Place("harbor", "the harbor road", 5, True, True, False, True),
}
OATHS = {
    "tug": Oath("tug", "Tug, tug, tug!", "tugged and tugged", "pulled the cart free", "called for the mule team", tags={"tug", "rope"}),
    "honk": Oath("honk", "Honk, honk, honk!", "honked and honked", "ducked the wagon under the awning", "held the lantern steady", tags={"honk", "horn"}),
    "brag": Oath("brag", "Big, bigger, biggest!", "bragged and bragged", "tied down the flapping sign", "laughed and listened", tags={"brag", "sign"}),
}
ACTORS = {
    "Tilly": ActorSpec("Tilly", "Tilly", "girl", "Tilly"),
    "Bo": ActorSpec("Bo", "Bo", "boy", "Bo"),
    "Mira": ActorSpec("Mira", "Mira", "girl", "Mira"),
    "Jeb": ActorSpec("Jeb", "Jeb", "boy", "Jeb"),
}


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def hazard(place: Place, oath: Oath) -> bool:
    return place.wind_strength >= 3 and place.has_river and oath.id in {"tug", "brag"}


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, o.id) for p in PLACES.values() for o in OATHS.values() if hazard(p, o)]


def _spread(world: World) -> None:
    if "kite" in world.entities and world.entities["kite"].meters["wind"] >= THRESHOLD:
        world.entities["kite"].memes["worry"] += 1


def _do_oath(world: World, oath: Oath, actor: Entity) -> None:
    actor.memes["pride"] += 1
    actor.meters["wind"] += 1
    world.say(f'{actor.id} sang out, "{oath.chant}" and then "{oath.chant}" again, bold as brass.')
    world.say(f"{actor.id} {oath.repeated_line}, and the whole place answered back.")
    if world.place.has_mud:
        world.entities["mud"].meters["trouble"] += 1
    _spread(world)


def _fix(world: World, oath: Oath, actor: Entity, helper: Entity) -> None:
    helper.memes["relief"] += 1
    actor.memes["joy"] += 1
    world.say(f"Then {helper.id} came loping along and {oath.fix_line}.")
    world.say(f'Together, {actor.id} and {helper.id} {oath.helpful_line}, and the day turned from wild to wise.')


def _setup(world: World, actor: Entity, helper: Entity, oath: Oath) -> None:
    world.say(f"At {world.place.label}, there lived a tall-tale {actor.id}, a real scallywag with a grin like sunrise.")
    world.say(f"{actor.id} loved to repeat a thing three times, for that was {oath.chant.lower()}")
    world.say(f"{helper.id} knew that when {actor.id} started repeating words, trouble was usually trotting close behind.")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    oath = OATHS[params.oath]
    actor_spec = ACTORS[params.actor]
    helper_spec = ACTORS[params.helper]
    world = World(place)
    actor = world.add(Entity(id=actor_spec.id, kind="character", type=actor_spec.type, role="scallywag"))
    helper = world.add(Entity(id=helper_spec.id, kind="character", type=helper_spec.type, role="helper"))
    world.add(Entity(id="mud", label="mud", kind="thing"))
    world.add(Entity(id="kite", label="kite", kind="thing"))
    _setup(world, actor, helper, oath)
    world.para()
    _do_oath(world, oath, actor)
    if place.has_mud:
        world.say(f"The wind chased the mud in little swirls, then bigger swirls, then biggest swirls.")
        world.say(f"{actor.id} skidded, laughed, and got a speck of mud right on {actor.pronoun('possessive')} boot.")
    world.para()
    _fix(world, oath, actor, helper)
    world.say(f"In the end, the scallywag stopped boasting long enough to listen, and the whole place went still as a hat on a peg.")
    world.facts.update(actor=actor, helper=helper, oath=oath, place=place, outcome="fixed")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the word "scallywag" and repeats a phrase three times.',
        f'Tell a funny, exaggerated story where {f["actor"].id} is a scallywag who keeps saying "{f["oath"].chant}" until a helper steadies things.',
        f'Write a repetition-heavy tall tale with a scallywag, a windy place, and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["actor"]
    h = world.facts["helper"]
    oath = world.facts["oath"]
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {a.id}, a scallywag, and {h.id}, who helps keep things steady."),
        QAItem(question="What did the scallywag keep saying?", answer=f"{a.id} kept saying “{oath.chant}” over and over. The repetition makes the story sound like a tall tale being blown by the wind."),
        QAItem(question="How did the trouble get handled?", answer=f"{h.id} came in and helped with the sensible fix, so the noisy trouble settled down. By the end, the big bragging turned into calm teamwork."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a scallywag?", answer="A scallywag is a mischievous or roguish person. In a tall tale, a scallywag is often funny, bold, and a little hard to tame."),
        QAItem(question="Why do stories repeat words in tall tales?", answer="Repetition makes a tale feel bigger, louder, and more playful. It also helps children hear the rhythm of the story and remember it."),
        QAItem(question="What does wind do in a story like this?", answer="Wind can make things wobble, flap, and feel larger than life. That helps a tall tale sound wild without needing the story to become confusing."),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.oath not in OATHS or params.actor not in ACTORS or params.helper not in ACTORS:
        raise StoryError("Unknown story parameter.")
    if params.actor == params.helper:
        raise StoryError("The scallywag and the helper must be different characters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with repetition and a scallywag.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--oath", choices=OATHS)
    ap.add_argument("--actor", choices=ACTORS)
    ap.add_argument("--helper", choices=ACTORS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.oath:
        combos = [c for c in combos if c[1] == args.oath]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, oath = rng.choice(combos)
    actor = args.actor or rng.choice(list(ACTORS))
    helper = args.helper or rng.choice([k for k in ACTORS if k != actor])
    return StoryParams(place=place, oath=oath, actor=actor, helper=helper, seed=None)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbend", oath="tug", actor="Tilly", helper="Bo"),
    StoryParams(place="harbor", oath="honk", actor="Mira", helper="Jeb"),
    StoryParams(place="prairie", oath="brag", actor="Jeb", helper="Tilly"),
]


ASP_RULES = r"""
valid(P,O) :- place(P), oath(O), windy(P), river(P), (O = tug; O = brag).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.wind_strength >= 3:
            lines.append(asp.fact("windy", p.id))
        if p.has_river:
            lines.append(asp.fact("river", p.id))
    for o in OATHS.values():
        lines.append(asp.fact("oath", o.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        s = generate(CURATED[0])
        if not s.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    else:
        print("OK: ASP parity and generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible combos:")
        for p, o in asp_valid_combos():
            print(f"  {p} {o}")
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(rng_base + i))
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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

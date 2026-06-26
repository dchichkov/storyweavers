#!/usr/bin/env python3
"""
A small folk-tale storyworld about a whirly thing, a kindly helper, and a
tricky problem that turns into a gentle gift.

Premise:
- In a little village by a creek, a whirly windmill keeps the flour mill turning.
- The mill wheel is precious because it grinds grain into flour for bread.
- A gusty day can spin it too fast and shake the gear teeth loose.
- A child with a kind heart worries about the mill, and the village elder
  suggests a patient, helpful fix instead of a harsh one.

State model:
- Characters and objects carry both physical meters and emotional memes.
- The whirly wheel has spin, strain, and wear.
- A helper can use kindness to steady fear, invite a repair, and share the work.
- The ending proves what changed: the wheel turns safely, bread is made, and
  the village feels warmer for the kindness shown.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "elder_woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "elder_man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    creek_side: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Wheel:
    id: str
    label: str
    tells: str
    grain: str
    risky_wind: str
    safe_wind: str
    zone: str = "hub"
    keyword: str = "whirly"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    method: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    if wheel.meters.get("spin", 0) < THRESHOLD:
        return out
    if wheel.meters.get("strain", 0) < THRESHOLD:
        return out
    if ("strain", wheel.id) in world.fired:
        return out
    world.fired.add(("strain", wheel.id))
    wheel.meters["wear"] = wheel.meters.get("wear", 0) + 1
    out.append(f"The whirly wheel groaned, and its wooden teeth began to wear.")
    return out


def _r_kindness_settle(world: World) -> list[str]:
    out: list[str] = []
    for person in world.people():
        if person.memes.get("kindness", 0) < THRESHOLD:
            continue
        if person.memes.get("fear", 0) < THRESHOLD:
            continue
        sig = ("settle", person.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        person.memes["fear"] = 0
        person.memes["hope"] = person.memes.get("hope", 0) + 1
        out.append(f"{person.label} spoke softly, and fear in the air grew smaller.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    if wheel.meters.get("wear", 0) < THRESHOLD:
        return out
    for person in world.people():
        if person.memes.get("kindness", 0) < THRESHOLD:
            continue
        if person.meters.get("tools", 0) < THRESHOLD:
            continue
        sig = ("repair", person.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        wheel.meters["wear"] = max(0.0, wheel.meters.get("wear", 0) - 1)
        wheel.meters["balance"] = wheel.meters.get("balance", 0) + 1
        out.append(f"With careful hands, {person.label} mended the loose gear.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_strain, _r_kindness_settle, _r_repair):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_problem(world: World, wheel: Wheel) -> dict:
    sim = world.copy()
    sim.get("wheel").meters["spin"] = 1
    sim.get("wheel").meters["strain"] = 1
    propagate(sim, narrate=False)
    return {
        "wear": sim.get("wheel").meters.get("wear", 0),
        "balance": sim.get("wheel").meters.get("balance", 0),
    }


def setting_line(place: Place) -> str:
    return {
        "millyard": "The mill stood by the creek, where reeds bent low and the water sang over stones.",
        "village": "The village lane was small and bright, with a bakery at one end and the mill at the other.",
        "grove": "The grove was green and quiet, though the old mill wheel could still be heard from afar.",
    }.get(place.name, f"{place.name.capitalize()} waited under a soft sky.")


def tell(world: World, hero: Entity, elder: Entity, wheel: Entity, tool: Tool) -> World:
    world.say(f"Once there was {hero.label}, a little {hero.type} with a kind heart.")
    world.say(f"{hero.pronoun().capitalize()} loved the {wheel.label} because it fed the village with bread.")
    world.say(f"{setting_line(world.place)}")
    world.para()

    world.say(f"One windy morning, the {wheel.label} began to spin too fast.")
    wheel.meters["spin"] = 1
    wheel.meters["strain"] = 1
    hero.memes["fear"] = 1
    hero.memes["kindness"] = 1
    world.say(f"{hero.label} saw the whirly wheel shudder and worried it might break.")
    world.say(f"{elder.label} said, \"A kind hand is better than a sharp word when a thing is frightened by the wind.\"")
    world.say(f"{hero.label} listened and brought {tool.phrase}.")
    hero.meters["tools"] = 1
    world.para()

    propagate(world, narrate=True)
    world.say(f"{hero.label} used {tool.method}, and {tool.tail}.")
    if wheel.meters.get("wear", 0) < THRESHOLD:
        world.say(f"The wheel settled into an even whir, not too fast and not too slow.")
    else:
        world.say(f"The wheel still needed care, so {elder.label} joined in and showed the right fix.")
        wheel.meters["wear"] = 0
        wheel.meters["balance"] = 1
        world.say(f"Together they made the wheel true again.")
    world.para()

    world.say(f"By evening, the mill had ground a sack of grain into soft flour.")
    world.say(f"The baker baked warm loaves, and {hero.label} shared them with the neighbors.")
    world.say(f"Even the wind seemed gentler, as if it had learned to play nicely with the whirly wheel.")

    world.facts.update(hero=hero, elder=elder, wheel=wheel, tool=tool, place=world.place)
    return world


PLACES = {
    "millyard": Place(name="millyard", creek_side=True, affords={"wheel", "bread"}),
    "village": Place(name="village", creek_side=False, affords={"wheel", "bread"}),
    "grove": Place(name="grove", creek_side=False, affords={"wheel"}),
}

WHEELS = {
    "whirly_mill": Wheel(
        id="wheel",
        label="whirly mill wheel",
        tells="feeds the flour mill",
        grain="grain",
        risky_wind="gusty wind",
        safe_wind="steady breeze",
        tags={"whirly", "wheel", "grain", "bread"},
    )
}

TOOLS = {
    "wrench": Tool(
        id="wrench",
        label="wooden wrench",
        phrase="a wooden wrench and a small tin of oil",
        helps={"repair"},
        method="loosening the tight bolts and oiling the axle",
        tail="the wheel turned in a smoother circle",
    ),
    "rope": Tool(
        id="rope",
        label="soft rope",
        phrase="a soft rope and a wedge of pine",
        helps={"steady"},
        method="tying the brake and steadying the side beam",
        tail="the wheel slowed to a careful hum",
    ),
}

NAMES = ["Mira", "Tobin", "Elsa", "Nell", "Pip", "Rowan", "Anya", "Bram"]
ELDER_NAMES = ["Grandmother Rye", "Old Harlan", "Aunt Sable", "Master Reed"]
TRAITS = ["kind", "gentle", "brave", "helpful", "patient"]


@dataclass
class StoryParams:
    place: str
    hero_name: str
    elder_name: str
    trait: str
    tool: str
    seed: Optional[int] = None


ASP_RULES = r"""
hero_kind(H) :- hero(H), kindness(H).
problem(W) :- wheel(W), spin(W), strain(W).
settles(H) :- hero_kind(H), fear(H), kindness(H).
fixes(H,W) :- hero_kind(H), has_tool(H), problem(W), repair_tool(H).
good_story(P,H,W) :- place(P), hero(H), wheel(W), problem(W), settles(H), fixes(H,W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        if PLACES[p].creek_side:
            lines.append(asp.fact("creek_side", p))
    for wid in WHEELS:
        lines.append(asp.fact("wheel", wid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if "repair" in TOOLS[tid].helps:
            lines.append(asp.fact("repair_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whirly kindness folk tale.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--tool", choices=TOOLS)
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(NAMES)
    elder_name = args.elder or rng.choice(ELDER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(place=place, hero_name=hero_name, elder_name=elder_name, trait=trait, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id="hero", kind="character", type="child", label=params.hero_name))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder_name))
    wheel = world.add(Entity(id="wheel", type="wheel", label="whirly mill wheel"))
    tool = TOOLS[params.tool]

    hero.memes["kindness"] = 1
    hero.memes["fear"] = 1
    hero.meters["tools"] = 0

    tell(world, hero, elder, wheel, tool)

    prompts = [
        'Write a short folk tale about a whirly mill wheel, a kind child, and a problem solved with patience.',
        f"Tell a gentle story where {params.hero_name} helps a whirly wheel at the {params.place}.",
    ]

    story_qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {params.hero_name}, a little child with a kind heart, and the whirly mill wheel by the {params.place}.",
        ),
        QAItem(
            question=f"What worried {params.hero_name} on the windy morning?",
            answer=f"{params.hero_name} worried that the whirly mill wheel would wear out because the wind made it spin too fast.",
        ),
        QAItem(
            question=f"What did {params.hero_name} bring to help?",
            answer=f"{params.hero_name} brought {tool.phrase}, which helped care for the wheel in a careful way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The wheel turned safely again, the mill made flour, and the village shared warm bread together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a whirly wheel?",
            answer="A whirly wheel is a wheel that turns around and around in the wind or water.",
        ),
        QAItem(
            question="Why is kindness important in a folk tale?",
            answer="Kindness matters because it helps people listen, solve problems gently, and care for one another.",
        ),
        QAItem(
            question="What does flour become?",
            answer="Flour can be used to bake bread, cakes, and other soft baked foods.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = {(p, h, w) for p in PLACES for h in ["hero"] for w in ["wheel"]}
    cl = set(asp_valid())
    if cl:
        print(f"OK: ASP produced {len(cl)} story pattern(s).")
        return 0
    print("MISMATCH or empty ASP result.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="millyard", hero_name="Mira", elder_name="Grandmother Rye", trait="kind", tool="wrench"),
            StoryParams(place="village", hero_name="Tobin", elder_name="Old Harlan", trait="gentle", tool="rope"),
            StoryParams(place="grove", hero_name="Nell", elder_name="Aunt Sable", trait="patient", tool="wrench"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

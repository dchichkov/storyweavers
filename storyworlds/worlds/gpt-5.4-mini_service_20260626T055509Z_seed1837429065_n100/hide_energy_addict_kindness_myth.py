#!/usr/bin/env python3
"""
A standalone storyworld script for a small myth-like tale about hiding a
dangerous source of energy, an energy addict, and the power of kindness.

The domain:
- A child or small keeper finds a glowing ember in a mythic place.
- An energy-addicted character wants to take it and keep going forever.
- The keeper hides the ember, then uses kindness to offer a safer path.
- The ending proves the change in the world: energy is no longer hoarded;
  it is shared carefully, and the addicted character chooses rest.

This script follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    visible: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    hidden_spot: str
    myth_detail: str


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    glow: str
    dangerous: bool = False


@dataclass
class StoryParams:
    place: str
    relic: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "temple": Place(
        name="the old temple",
        hidden_spot="behind a cracked moon-stone altar",
        myth_detail="Its pillars were carved with vines and stars.",
    ),
    "cave": Place(
        name="the whispering cave",
        hidden_spot="under a black stone ledge",
        myth_detail="Cool water shone like glass on the floor.",
    ),
    "grove": Place(
        name="the sacred grove",
        hidden_spot="inside a hollow tree with silver bark",
        myth_detail="Fireflies hovered like tiny wandering prayers.",
    ),
}

RELICS = {
    "ember": Relic(
        label="ember",
        phrase="a bright ember of power",
        type="ember",
        glow="golden",
        dangerous=True,
    ),
    "spark": Relic(
        label="spark",
        phrase="a lively spark of old magic",
        type="spark",
        glow="blue-white",
        dangerous=True,
    ),
    "honeylight": Relic(
        label="honeylight",
        phrase="a warm bead of honey-colored light",
        type="honeylight",
        glow="honey-gold",
        dangerous=True,
    ),
}

GIRL_NAMES = ["Ayla", "Mira", "Nora", "Ira", "Lena", "Sera"]
BOY_NAMES = ["Taro", "Eli", "Kian", "Milo", "Orin", "Daren"]
TRAITS = ["gentle", "curious", "brave", "patient", "small", "quick"]


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: hide, energy, addict, and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle", "keeper"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    relic = args.relic or rng.choice(list(RELICS))
    gender = args.gender or rng.choice(["girl", "boy"])
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle", "keeper"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, name=name, gender=gender, guardian=guardian, trait=trait)


def name_title(guardian: str) -> str:
    return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle", "keeper": "keeper"}[guardian]


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.trait if hasattr(hero, 'trait') else 'small'} child who listened to the old stories.")
    world.say(f"{world.place.myth_detail}")


def story_text(world: World) -> str:
    return world.render()


def predict_hiding(world: World, hero: Entity, relic: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["protect"] = sim.get(hero.id).memes.get("protect", 0) + 1
    sim.get(relic.id).hidden = True
    addict = sim.get("Addict")
    if addict.meters.get("craving", 0) >= THRESHOLD:
        addict.memes["restless"] = addict.memes.get("restless", 0) + 1
    return {"hidden": sim.get(relic.id).hidden, "restless": addict.memes.get("restless", 0) > 0}


def tell(place: Place, relic_cfg: Relic, hero_name: str, gender: str, guardian: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["small", trait]))
    hero.trait = trait
    guardian_ent = world.add(Entity(id="Guardian", kind="character", type=guardian, label=f"the {guardian}", traits=["wise"]))
    addict = world.add(Entity(id="Addict", kind="character", type="spiritseller", label="the energy addict", traits=["hungry"]))
    relic = world.add(Entity(id="Relic", kind="thing", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase))
    relic.meters["energy"] = 1.0
    addict.meters["craving"] = 1.0
    addict.memes["restless"] = 1.0

    world.say(f"Long ago, in {place.name}, {hero.id} found {relic.phrase}.")
    world.say(f"The light was {relic_cfg.glow}, and it warmed {hero.pronoun('possessive')} hands.")
    world.say(f"But there was also {addict.label}, who was an energy addict and always wanted more power.")

    world.para()
    world.say(f"One dusk, {hero.id} carried {relic.label} toward {place.hidden_spot}.")
    world.say(f"{hero.id} meant to hide the glowing thing before {addict.label} could seize it.")
    relic.hidden = True
    relic.visible = False
    hero.memes["fear"] = 1.0
    hero.meters["care"] = 1.0

    world.say(f"{guardian_ent.label.capitalize()} saw the worry in {hero.id}'s face and asked what was wrong.")
    if predict_hiding(world, hero, relic)["hidden"]:
        world.say(f'{hero.id} whispered, "I must hide it. The energy addict will never stop if he gets this light."')
    addict.meters["craving"] += 1.0
    addict.memes["hunger"] = 1.0
    world.say(f"At once, {addict.label} smelled the magic and came close, eyes bright as lamps.")

    world.para()
    hero.memes["kindness"] = 1.0
    world.say(f"Then {hero.id} did a kinder thing than the addict expected.")
    world.say(f"{hero.id} stepped out, not with anger, but with kindness.")
    world.say(f'"{guardian_ent.pronoun("subject").capitalize()} can rest," {hero.id} said. "I will share a little light, but not enough to burn you up."')
    addict.meters["craving"] = max(0.0, addict.meters["craving"] - 1.0)
    addict.memes["restful"] = 1.0
    hero.meters["energy"] = 0.0
    world.say(f"{addict.label} paused. The hunger loosened, and for the first time, {addict.pronoun('subject')} looked tired instead of wild.")

    world.para()
    world.say(f"{guardian_ent.label.capitalize()} lit a small lamp from the relic and wrapped the rest in bark and moss.")
    world.say(f"So the power stayed hidden, the addict learned to breathe slowly, and {hero.id} carried kindness like a torch.")
    world.say(f"In {place.name}, the bright thing no longer belonged to greed. It belonged to careful hands and a peaceful night.")

    world.facts.update(
        hero=hero,
        guardian=guardian_ent,
        addict=addict,
        relic=relic,
        place=place,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    relic = f["relic"]
    return [
        'Write a short myth about a child who must hide energy from an addict and choose kindness.',
        f"Tell a mythic story where {hero.id} hides {relic.label}, but kindness helps the energy addict calm down.",
        f"Write a gentle legend set in {world.place.name} about {relic.label}, energy craving, and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    addict = f["addict"]
    relic = f["relic"]
    return [
        QAItem(
            question=f"What did {hero.id} hide in {world.place.name}?",
            answer=f"{hero.id} hid {relic.phrase} so the energy addict would not take it and make more trouble.",
        ),
        QAItem(
            question=f"Why was {addict.label} a problem in the story?",
            answer=f"{addict.label} was an energy addict, so {addict.pronoun('subject')} kept wanting more power and could not stop reaching for the glowing relic.",
        ),
        QAItem(
            question=f"What changed when {hero.id} chose kindness?",
            answer=f"Kindness helped the story turn peaceful. The addict calmed down, the relic was kept safe, and {guardian.label} could share the light carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to hide something?",
            answer="To hide something means to put it where other people cannot easily see or find it.",
        ),
        QAItem(
            question="What is energy?",
            answer="Energy is the power that helps things move, shine, grow, and do work.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin for the reasonableness gate:
% A valid myth-story needs a place, a relic that can be hidden, and a kindness turn.
valid_story(Place, Relic) :- place(Place), relic(Relic), hideable(Relic), kind_turn.

% The addict is central to the tension.
has_tension :- addict(energy_addict), craving(energy_addict).

% The ending requires kindness to reduce craving.
resolved :- has_tension, kindness_present.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid in RELICS:
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("hideable", rid))
    lines.append(asp.fact("addict", "energy_addict"))
    lines.append(asp.fact("craving", "energy_addict"))
    lines.append(asp.fact("kind_turn"))
    lines.append(asp.fact("kindness_present"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in PLACES for r in RELICS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP parity matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "No valid myth-story matched the requested options."


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
    StoryParams(place="temple", relic="ember", name="Ayla", gender="girl", guardian="mother", trait="gentle"),
    StoryParams(place="cave", relic="spark", name="Taro", gender="boy", guardian="uncle", trait="brave"),
    StoryParams(place="grove", relic="honeylight", name="Mira", gender="girl", guardian="keeper", trait="patient"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], RELICS[params.relic], params.name, params.gender, params.guardian, params.trait)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, relic in combos:
            print(f"  {place:10} {relic}")
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/rib_thunk_reconciliation_superhero_story.py
==============================================================

A small superhero story world built from the seed words "rib" and "thunk",
with a reconciliation turn at the center.

Premise:
- A hero is trying to keep a city calm.
- A loud thunk startles someone, and a rib gets bruised in the scramble.
- The misunderstanding grows into hurt feelings.
- The hero finds a way to listen, apologize, and reconcile.

The world uses typed entities with physical meters and emotional memes,
a small forward rule system, a reasonableness gate, and an ASP twin.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class City:
    name: str = "Bright Harbor"
    place: str = "the city square"
    setting: str = "a bright afternoon"

    def detail(self) -> str:
        return f"{self.name} was busy and sunlit, and {self.place} buzzed with little errands."


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    place: str
    seed: Optional[int] = None


@dataclass
class Hazard:
    id: str
    trigger: str
    sound: str
    mess: str
    risk: str
    impact: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, city: City) -> None:
        self.city = city
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


HAZARDS = {
    "thunk": Hazard(
        id="thunk",
        trigger="a metal crate toppled over",
        sound="THUNK!",
        mess="a loud thunk rolled through the square",
        risk="the thump startled everyone nearby",
        impact="a bruised rib",
        tags={"thunk", "noise"},
    ),
    "alarm": Hazard(
        id="alarm",
        trigger="a broken alarm box clicked on",
        sound="BEEP-BEEP!",
        mess="a harsh alarm cut across the square",
        risk="the noise made people rush and bump shoulders",
        impact="a sore rib",
        tags={"thunk", "noise"},
    ),
}

GEAR = {
    "shield": Gear(
        id="shield",
        label="a round shield",
        phrase="a round shield",
        helps="block the bump and keep the hero steady",
        tags={"shield", "hero"},
    ),
    "mask": Gear(
        id="mask",
        label="a calm mask",
        phrase="a calm mask",
        helps="help the hero breathe slowly and speak gently",
        tags={"mask", "calm"},
    ),
}

CITY = City()

GIRL_NAMES = ["Mira", "Tess", "Nia", "Luna", "Aria"]
BOY_NAMES = ["Kai", "Ezra", "Noah", "Jude", "Owen"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for hid, hazard in HAZARDS.items():
        for gear_id in GEAR:
            if hid == "thunk" and gear_id == "shield":
                out.append((hid, gear_id))
            if hid == "alarm" and gear_id == "mask":
                out.append((hid, gear_id))
    return out


def reasonableness_gate(hazard: Hazard, gear: Gear) -> bool:
    return (hazard.id, gear.id) in valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero reconciliation story world.")
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--partner")
    ap.add_argument("--partner-type", choices=["girl", "boy"], dest="partner_type")
    ap.add_argument("--place")
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
    hid = args.hazard or rng.choice(list(HAZARDS))
    gear = args.gear or rng.choice(list(GEAR))
    if args.hazard and args.gear and not reasonableness_gate(HAZARDS[args.hazard], GEAR[args.gear]):
        raise StoryError("That gear does not fit this hazard in a believable superhero story.")
    if (hid, gear) not in valid_combos():
        # keep the world tight: only a small set of plausible stories
        gear = "shield" if hid == "thunk" else "mask"
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(BOY_NAMES if partner_type == "boy" else GIRL_NAMES)
    if partner == hero:
        partner = "Nova"
    place = args.place or CITY.place
    return StoryParams(hero=hero, hero_type=hero_type, partner=partner, partner_type=partner_type, place=place)


def tell(params: StoryParams) -> World:
    world = World(CITY)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_type, role="partner"))
    hazard = HAZARDS["thunk"] if params.place == CITY.place else HAZARDS["alarm"]
    gear = GEAR["shield"] if hazard.id == "thunk" else GEAR["mask"]

    hero.memes["care"] = 1
    partner.memes["trust"] = 1
    world.say(f"{hero.id} was a city hero, and {partner.id} was the friend who kept pace at {params.place}.")
    world.say(CITY.detail())
    world.say(f"Then {hazard.mess.lower()}, and the air rang with {hazard.sound}")

    world.para()
    hero.meters["startle"] = 1
    partner.meters["pain"] = 1
    world.say(f"The {hazard.sound.strip()} startled {partner.id}, and {partner.pronoun()} clutched a side.")
    world.say(f"The fall left {partner.pronoun('possessive')} {hazard.impact} and a hurt look that made the hero slow down.")

    world.para()
    hero.memes["guilt"] = 1
    hero.memes["resolve"] = 1
    world.say(f"{hero.id} heard the hurt in {partner.id}'s voice and stopped using superhero words.")
    world.say(f"{hero.id} said sorry, then offered {gear.phrase} to {partner.id} so {gear.helps}.")
    partner.memes["hurt"] = 0
    partner.memes["trust"] = 1
    hero.memes["peace"] = 1
    world.say(f"{partner.id} took a breath, nodded, and the two friends reconciled with a small handshake and a grin.")
    world.say(f"After that, {hero.id} and {partner.id} walked home together, gentler than before, with the square quiet behind them.")

    world.facts.update(hero=hero, partner=partner, hazard=hazard, gear=gear, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story for a young child that uses the words \"{f['hazard'].id}\" and reconciliation.",
        f"Tell a story where {f['hero'].id} notices a {f['hazard'].sound} and helps {f['partner'].id} after a hurt feeling.",
        f"Write a gentle hero story in {f['params'].place} where a mistake leads to apology, repair, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, hazard, gear = f["hero"], f["partner"], f["hazard"], f["gear"]
    return [
        QAItem(
            question=f"Who was the superhero story about?",
            answer=f"It was about {hero.id}, who was trying to help at {f['params'].place}, and {partner.id}, who got hurt and then reconciled with the hero.",
        ),
        QAItem(
            question=f"What noisy thing happened in the story?",
            answer=f"A {hazard.id} happened: {hazard.sound} rang out and startled {partner.id}. That loud sound led to the bruise and the argument.",
        ),
        QAItem(
            question=f"What did {hero.id} offer to help make things better?",
            answer=f"{hero.id} offered {gear.phrase}. It helped because it could {gear.helps}, and it showed {partner.id} that the hero wanted to fix the moment.",
        ),
        QAItem(
            question=f"How did the two friends solve their hurt feelings?",
            answer=f"{hero.id} apologized, listened, and stayed calm, and then {partner.id} accepted the apology. That was the reconciliation that ended the story well.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset with each other, talk things through, and become friendly again.",
        ),
        QAItem(
            question="What can a thunk mean in a story?",
            answer="A thunk is a heavy, dull sound, like something bumping or falling. In a story it can startle people and cause trouble.",
        ),
        QAItem(
            question="What is a rib?",
            answer="A rib is one of the bones in the side of your chest. Ribs help protect the heart and lungs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(thunk,shield).
valid(alarm,mask).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP matches Python.")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(hero="Mira", hero_type="girl", partner="Kai", partner_type="boy", place="the city square"),
    StoryParams(hero="Noah", hero_type="boy", partner="Luna", partner_type="girl", place="the city square"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

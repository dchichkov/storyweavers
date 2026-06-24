#!/usr/bin/env python3
"""
A mythic storyworld about a pharmacy, a wedding, and a return.

A small healer, a bridal vow, and a foretold return are woven into a classical
simulation: the characters carry physical tokens in meters and feelings in
memes, and the story is narrated from those state changes.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "bride", "queen", "priestess"}
        male = {"boy", "man", "groom", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Pharmacy:
    name: str = "the pharmacy"
    setting: str = "at the edge of the town"
    rule: str = "a promise must be kept before nightfall"
    affords: set[str] = field(default_factory=lambda: {"mix", "return", "wed"})


@dataclass
class Potion:
    label: str
    phrase: str
    type: str
    needed_for: str
    omen: str
    foreshadow: str


@dataclass
class World:
    pharmacy: Pharmacy
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        return World(
            pharmacy=self.pharmacy,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

POTIONS = {
    "moonwater": Potion(
        label="moonwater",
        phrase="a silver flask of moonwater",
        type="moonwater",
        needed_for="the wedding blessing",
        omen="the moon showed a bright ring",
        foreshadow="the well-water had gone quiet",
    ),
    "rose-salve": Potion(
        label="rose-salve",
        phrase="a small jar of rose salve",
        type="salve",
        needed_for="the bride's hands",
        omen="rose petals fell against the window",
        foreshadow="the roses in the courtyard had opened early",
    ),
    "honey-draught": Potion(
        label="honey-draught",
        phrase="a warm cup of honey draught",
        type="draught",
        needed_for="the groom's throat",
        omen="bees circled the lantern like a gold crown",
        foreshadow="the hive had hummed before dawn",
    ),
}

PLACES = {
    "apothecary": Pharmacy(name="the pharmacy", setting="beside the old market", affords={"mix", "return", "wed"}),
    "chapel": Pharmacy(name="the chapel pharmacy", setting="under the bell tower", affords={"return", "wed"}),
}

HEROES = [
    ("Iris", "girl", "apprentice"),
    ("Milo", "boy", "apprentice"),
    ("Nera", "girl", "healer"),
    ("Tarin", "boy", "healer"),
]

GROOMS = [("the groom", "groom"), ("the bride", "bride")]


@dataclass
class StoryParams:
    place: str
    potion: str
    hero: str
    hero_type: str
    role: str
    wed_partner: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def _hero_title(role: str) -> str:
    return {"apprentice": "young apprentice", "healer": "old healer"}.get(role, role)


def _setup(world: World, hero: Entity, partner: Entity, potion: Potion) -> None:
    world.say(
        f"{hero.id} was a {_hero_title(hero.type)} who kept the jars in {world.pharmacy.name} in careful order."
    )
    world.say(
        f"People said {world.pharmacy.name} stood {world.pharmacy.setting}, because even there, a vow could begin with a remedy."
    )
    world.say(
        f"On the shelf lay {potion.phrase}, meant for {potion.needed_for}."
    )
    world.say(
        f"Long before anyone spoke of the wedding, the signs had already spoken: {potion.foreshadow}."
    )
    world.facts.update(hero=hero, partner=partner, potion=potion)


def _foreshadow(world: World, hero: Entity, potion: Potion) -> None:
    hero.memes["duty"] = hero.memes.get("duty", 0) + 1
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"{hero.id} noticed the omen and felt that the day was leaning toward something important."
    )
    world.say(
        f"Still, {hero.pronoun()} kept watch over the potion, because in myths, a thing foretold is a thing that can be saved."
    )


def _loss(world: World, hero: Entity, potion: Potion) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"Then a mess of footsteps and curtain-shadow passed through the room, and the potion was gone from the shelf."
    )
    world.say(
        f"{hero.id} looked down at the empty place where {potion.label} had been and felt the story turn sharp."
    )
    world.facts["lost"] = True


def _return(world: World, hero: Entity, potion: Potion) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    hero.meters["steps"] = hero.meters.get("steps", 0) + 1
    world.say(
        f"{hero.id} followed the only true trail: a smear of moonlight, a line of spilled herbs, and the faint smell of rain."
    )
    world.say(
        f"At the river gate, {hero.id} found the missing {potion.label} waiting in a reedside basket, as if the world had only borrowed it."
    )
    world.say(
        f"{hero.id} brought it back to {world.pharmacy.name}, and the return felt like the ending of a long-held breath."
    )
    world.facts["returned"] = True


def _wed(world: World, hero: Entity, partner: Entity, potion: Potion) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    partner.memes["joy"] = partner.memes.get("joy", 0) + 2
    world.say(
        f"By dusk, the wedding candles were lit, and {partner.id} held out {partner.pronoun('possessive')} hands."
    )
    world.say(
        f"{hero.id} gave the returned {potion.label} to the waiting pair, and the blessing could begin at last."
    )
    world.say(
        f"The bride and groom smiled as if they had known all along that the missing thing would come home."
    )
    world.say(
        f"So the vow was spoken, the potion was used, and {world.pharmacy.name} kept its place in the world's old order."
    )
    world.facts["wed"] = True


# ---------------------------------------------------------------------------
# Reasoning and generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.potion not in POTIONS:
        raise StoryError(f"Unknown potion: {params.potion}")
    world = World(pharmacy=PLACES[params.place])

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=_hero_title(params.role)))
    partner_label, partner_type = params.wed_partner, params.wed_partner
    if partner_label == "the bride":
        partner = world.add(Entity(id="Bride", kind="character", type="bride", label="the bride"))
    else:
        partner = world.add(Entity(id="Groom", kind="character", type="groom", label="the groom"))
    potion = POTIONS[params.potion]
    world.add(Entity(id="Potion", kind="thing", type=potion.type, label=potion.label, phrase=potion.phrase, owner=hero.id))
    _setup(world, hero, partner, potion)
    world.para()
    _foreshadow(world, hero, potion)
    _loss(world, hero, potion)
    world.para()
    _return(world, hero, potion)
    _wed(world, hero, partner, potion)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    potion: Potion = f["potion"]
    return [
        f'Write a short myth for children about {hero.id} at {world.pharmacy.name} where an omen points toward a return.',
        f'Tell a gentle story in which {hero.id} loses and then returns {potion.label} before a wedding can begin.',
        f'Write a simple mythic tale that includes a pharmacy, a wedding, and a promised return.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    potion: Potion = world.facts["potion"]
    partner: Entity = world.facts["partner"]
    return [
        QAItem(
            question=f"Who brought back the missing {potion.label}?",
            answer=f"{hero.id} brought back the missing {potion.label} to the pharmacy.",
        ),
        QAItem(
            question=f"Why did the story feel foretold before the wedding?",
            answer=f"It felt foretold because {potion.foreshadow}, and {potion.omen}.",
        ),
        QAItem(
            question=f"What did the return make possible at the end?",
            answer=f"The return made the wedding blessing possible for {partner.id} and the others waiting there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    potion: Potion = world.facts["potion"]
    return [
        QAItem(
            question="What is a pharmacy?",
            answer="A pharmacy is a place where medicines, herbs, and healing mixtures are kept or prepared.",
        ),
        QAItem(
            question="What does a wedding mean?",
            answer="A wedding is a ceremony where two people make a promise to live as a married pair.",
        ),
        QAItem(
            question="What does it mean to return something?",
            answer="To return something means to bring it back to the person or place where it belongs.",
        ),
        QAItem(
            question=f"Why can a potion like {potion.label} matter in a story?",
            answer="A potion can matter because it may help someone feel better, keep a promise, or finish an important ceremony.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:10}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(apothecary).
place(chapel).

potion(moonwater).
potion(rose_salve).
potion(honey_draught).

event(wed).
event(return).
event(foreshadowing).

compatible(P, E) :- place(P), event(E), P = apothecary.
compatible(P, E) :- place(P), event(E), P = chapel, E != foreshadowing.

story(P, E1, E2) :- compatible(P, E1), compatible(P, E2), E1 != E2.
#show compatible/2.
#show story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in POTIONS:
        lines.append(asp.fact("potion", p.replace("-", "_")))
    for e in ["wed", "return", "foreshadowing"]:
        lines.append(asp.fact("event", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = {(place, "wed") for place in PLACES} | {(place, "return") for place in PLACES}
    python_set |= {("apothecary", "foreshadowing")}
    asp_set = set(asp_valid_combos())
    if asp_set == python_set:
        print(f"OK: ASP and Python gates match ({len(asp_set)} facts).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP only:", sorted(asp_set - python_set))
    print("Python only:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryOptions:
    place: str = "apothecary"
    potion: str = "moonwater"
    hero: str = "Iris"
    hero_type: str = "girl"
    role: str = "apprentice"
    wed_partner: str = "the bride"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic pharmacy storyworld with foreshadowing, return, and wed.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--potion", choices=sorted(POTIONS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["apprentice", "healer"])
    ap.add_argument("--wed-partner", choices=["the bride", "the groom"])
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
    place = args.place or rng.choice(list(PLACES))
    potion = args.potion or rng.choice(list(POTIONS))
    hero, hero_type, role = None, None, None
    if args.hero and args.hero_type and args.role:
        hero, hero_type, role = args.hero, args.hero_type, args.role
    else:
        hero, hero_type, role = rng.choice(HEROES)
    wed_partner = args.wed_partner or rng.choice(["the bride", "the groom"])
    return StoryParams(place=place, potion=potion, hero=hero, hero_type=hero_type, role=role, wed_partner=wed_partner)


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
    StoryParams(place="apothecary", potion="moonwater", hero="Iris", hero_type="girl", role="apprentice", wed_partner="the bride"),
    StoryParams(place="chapel", potion="rose-salve", hero="Tarin", hero_type="boy", role="healer", wed_partner="the groom"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2.\n#show story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        vals = sorted(set(asp.atoms(model, "compatible")))
        print(vals)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.hero}: {p.potion} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

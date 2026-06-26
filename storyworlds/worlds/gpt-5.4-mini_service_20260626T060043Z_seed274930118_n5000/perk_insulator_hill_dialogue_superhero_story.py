#!/usr/bin/env python3
"""
Standalone storyworld: perk, insulator, hill, dialogue, superhero-style rescue.

A small child-facing world where a hero, a helpful gadget, and a hill create
a simple tension-and-fix story. The premise is a superhero protecting a perk
from a risky climb, with dialogue carrying the turn and resolution.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    on_hill: bool = False
    risks: set[str] = field(default_factory=set)


@dataclass
class Gadget:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    fits: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    perk: str
    insulator: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


PLACES = {
    "city_hill": Place(name="the city hill", on_hill=True, risks={"slip", "wind"}),
    "museum_roof": Place(name="the museum roof", on_hill=False, risks={"wind"}),
    "training_hill": Place(name="the training hill", on_hill=True, risks={"slip"}),
    "quiet_park": Place(name="the quiet park", on_hill=False, risks=set()),
}

PERKS = {
    "star_badge": Entity(id="perk_star_badge", type="perk", label="star badge", phrase="a bright star badge"),
    "power_cape": Entity(id="perk_power_cape", type="perk", label="power cape", phrase="a red power cape"),
    "city_key": Entity(id="perk_city_key", type="perk", label="city key", phrase="a tiny city key"),
}

INSULATORS = {
    "foam_wrap": Gadget(
        id="foam_wrap",
        label="foam insulator",
        phrase="a soft foam insulator",
        protects={"slip"},
        fits={"perk"},
        prep="wrap the perk in the foam insulator first",
        tail="carefully unwrapped the foam insulator",
    ),
    "wind_shield": Gadget(
        id="wind_shield",
        label="wind insulator",
        phrase="a clear wind insulator",
        protects={"wind"},
        fits={"perk"},
        prep="clip on the wind insulator first",
        tail="snapped off the wind insulator",
    ),
    "shock_box": Gadget(
        id="shock_box",
        label="shock insulator",
        phrase="a sturdy shock insulator",
        protects={"slip", "wind"},
        fits={"perk"},
        prep="lock the perk into the shock insulator first",
        tail="opened the shock insulator",
    ),
}

HERO_NAMES = ["Nova", "Spark", "Comet", "Mira", "Jet", "Luna", "Bolt", "Zara"]
SIDEKICK_NAMES = ["Pip", "Tess", "Milo", "Rin", "Bea", "Nia", "Otto", "Kai"]


def story_setup(place: Place, hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str, perk_key: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["brave", "quick"]))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, traits=["helpful", "bright"]))
    perk = world.add(Entity(id="perk", kind="thing", type="perk", label=PERKS[perk_key].label, phrase=PERKS[perk_key].phrase, owner=hero.id, caretaker=hero.id))
    world.facts.update(hero=hero, sidekick=sidekick, perk=perk, perk_key=perk_key)
    return world


def predict_risk(world: World, insulator: Gadget) -> bool:
    place = world.place
    return bool(place.risks & insulator.protects)


def choose_insulator(place: Place, perk: Entity, insulator_key: str) -> Optional[Gadget]:
    gadget = INSULATORS[insulator_key]
    if "perk" not in gadget.fits:
        return None
    if not place.risks & gadget.protects:
        return None
    return gadget


def tell_story(world: World, insulator_key: str) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    perk = world.facts["perk"]
    gadget = INSULATORS[insulator_key]

    world.say(f"{hero.id} was a superhero who watched over {hero.pronoun('possessive')} {perk.label}.")
    world.say(f"{sidekick.id} was the sidekick, always ready with a grin and a good idea.")
    world.say(f"One day, they climbed {world.place.name}.")
    world.para()
    world.say(f'"We can reach the top fast," said {hero.id}, "but the hill feels slippery today."')
    world.say(f'"Then we should protect the {perk.label}," said {sidekick.id}.')
    world.say(f'"I have a plan," said {hero.id}. "{gadget.prep}."')
    if predict_risk(world, gadget):
        world.say(f'"That should keep it safe," said {sidekick.id}, nodding at the windy path.')
    world.para()
    perk.meters["safe"] = 1.0
    hero.memes["pride"] = 1.0
    sidekick.memes["joy"] = 1.0
    world.say(f"They went up the hill together.")
    world.say(f"At the top, {hero.id} {gadget.tail} and held up the {perk.label}.")
    world.say(f'"Still shining!" said {sidekick.id}. "{That was a heroic save if I ever saw one!"'.replace("{That", "That"))
    world.say(f"{hero.id} smiled, and the windy hill suddenly felt like a place for victory.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the words "{f["perk"].label}", "insulator", and "hill".',
        f"Tell a dialogue-driven story where {f['hero'].id} and {f['sidekick'].id} protect a {f['perk'].label} on a hill.",
        f"Write a brave little rescue tale with a helpful insulator and a safe ending at the top of a hill.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    perk = world.facts["perk"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who protected the {perk.label} with help from {sidekick.id}.",
        ),
        QAItem(
            question=f"What did the hero protect on the hill?",
            answer=f"{hero.id} protected the {perk.label} while they climbed the hill.",
        ),
        QAItem(
            question=f"How did they keep the perk safe?",
            answer=f"They used the insulator first, so the {perk.label} stayed safe on the windy hill.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insulator?",
            answer="An insulator is something that helps protect a thing from danger like wind, bumps, or heat.",
        ),
        QAItem(
            question="What is a hill?",
            answer="A hill is a raised bit of ground that you can climb up and look over from the top.",
        ),
        QAItem(
            question="What is a perk?",
            answer="A perk is a special reward or bonus, like a little prize that feels extra nice to have.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place={world.place.name} risks={sorted(world.place.risks)}")
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: perk, insulator, hill, and dialogue.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--perk", choices=PERKS.keys())
    ap.add_argument("--insulator", choices=INSULATORS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_key, place in PLACES.items():
        for perk_key in PERKS:
            for ins_key, ins in INSULATORS.items():
                if place.risks & ins.protects:
                    out.append((place_key, perk_key, ins_key))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.perk is None or c[1] == args.perk)
              and (args.insulator is None or c[2] == args.insulator)]
    if not combos:
        raise StoryError("No valid story matches the requested place, perk, and insulator.")
    place, perk, insulator = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        hero_name=args.hero_name or rng.choice(HERO_NAMES),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        sidekick_name=args.sidekick_name or rng.choice(SIDEKICK_NAMES),
        sidekick_type=args.sidekick_type or rng.choice(["girl", "boy"]),
        perk=perk,
        insulator=insulator,
    )


def generate(params: StoryParams) -> StorySample:
    world = story_setup(PLACES[params.place], params.hero_name, params.hero_type, params.sidekick_name, params.sidekick_type, params.perk)
    tell_story(world, params.insulator)
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
place_risk(P, R) :- risk(P, R).
gadget_help(G, R) :- protects(G, R).
good_combo(P, K, G) :- place_risk(P, R), gadget_help(G, R), perk(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, place in PLACES.items():
        lines.append(asp.fact("place", p))
        for r in sorted(place.risks):
            lines.append(asp.fact("risk", p, r))
    for k in PERKS:
        lines.append(asp.fact("perk", k))
    for g in INSULATORS.values():
        lines.append(asp.fact("gadget", g.id))
        for r in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    asp_set = set(asp.atoms(model, "good_combo"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for p, perk, ins in valid_combos():
            params = StoryParams(
                place=p,
                hero_name="Nova",
                hero_type="girl",
                sidekick_name="Pip",
                sidekick_type="boy",
                perk=perk,
                insulator=ins,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

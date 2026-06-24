#!/usr/bin/env python3
"""
storyworlds/worlds/nummy_catalogue_tartar_happy_ending_space_adventure.py
========================================================================

A standalone storyworld about a small space adventure in which a child
explores a tiny starshop, a nummy catalogue, and a tartar-speckled lunch fix
that turns the day from worrying to wonderful.

Seed imagination:
---
A little space rover had a silly problem. Nova loved the nummy catalogue in the
moon shop, but the scanner kept sticking on a tartar crumb from lunch. The shop
helper worried the catalogue pages would smudge, and Nova worried the mission
would be ruined.

Then Nova used a clean cloth, tucked the tartar packet away, and gently turned
the pages one by one. The scanner worked again, the catalogue stayed neat, and
Nova found the snack the crew had been waiting for. The day ended with a happy
picnic under the station dome.

Design notes:
- Small, typed entities with physical meters and emotional memes.
- State changes drive the prose: stickiness, cleaning, scanning, browsing,
  and finding the prize.
- The happy ending depends on a real, simulated fix: cleaning the crumb and
  using careful page-turning.
- Includes the seed words "nummy", "catalogue", and "tartar".
- Style aims for child-facing space adventure with a gentle, bright ending.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    style: str
    indoors: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    nummy: bool = True
    tartar: bool = False
    clean_required: bool = True
    risk: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    use_line: str = ""
    end_line: str = ""


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        return clone


def clean_crumb(world: World, child: Entity, snack: Entity, cloth: Entity) -> None:
    if snack.meters["sticky"] >= THRESHOLD:
        snack.meters["sticky"] = 0
        snack.meters["clean"] += 1
        child.memes["relief"] += 1
        cloth.meters["used"] += 1


def scan_catalogue(world: World, child: Entity, catalogue: Entity, snack: Entity) -> None:
    if snack.meters["sticky"] >= THRESHOLD:
        return
    catalogue.meters["open"] += 1
    catalogue.meters["pages_seen"] += 3
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1


def find_treat(world: World, child: Entity, snack: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    snack.meters["found"] += 1
    helper.memes["joy"] += 1


def predict_sticky(world: World, snack: Entity) -> bool:
    sim = world.copy()
    sim.get(snack.id).meters["sticky"] += 1
    return sim.get(snack.id).meters["sticky"] >= THRESHOLD


def tell(place: Place, snack_cfg: Snack, tool_cfg: Tool,
         hero_name: str = "Nova", hero_type: str = "girl",
         helper_name: str = "Milo", helper_type: str = "boy") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    catalogue = world.add(Entity(id="catalogue", type="thing", label="catalogue", phrase="a bright nummy catalogue"))
    snack = world.add(Entity(id="snack", type="thing", label=snack_cfg.label, phrase=snack_cfg.phrase, caretaker=helper.id))
    cloth = world.add(Entity(id="cloth", type="thing", label="clean cloth", phrase="a clean cloth"))
    tool = world.add(Entity(id=tool_cfg.id, type="thing", label=tool_cfg.label, phrase=tool_cfg.phrase))

    hero.memes["curiosity"] += 1
    helper.memes["worry"] += 1

    world.say(f"{hero.id} and {helper.id} floated into {place.label}, where the walls glowed in soft space-blue light.")
    world.say(f"On the counter sat {catalogue.phrase}, full of {snack_cfg.label} treats and shiny stickers from the star crew.")
    world.say(f"{hero.id} loved the catalogue because it promised {snack_cfg.taste} snacks for a long moon day.")

    world.para()
    world.say(f"But the scanner blinked red whenever the pages moved, because a tiny tartar crumb had stuck to {snack_cfg.label}.")
    if predict_sticky(world, snack):
        helper.memes["worry"] += 1
        world.say(f'"The catalogue might smudge," {helper.id} said softly, "and we need it neat for the next customer."')
    world.say(f"{hero.id} peered at the crumb and wanted to fix the trouble instead of giving up.")

    world.para()
    snack.meters["sticky"] += 1
    world.say(f'{hero.id} used {tool_cfg.phrase} and {cloth.label_word if hasattr(cloth, "label_word") else "the cloth"} to wipe the tartar away.')
    clean_crumb(world, hero, snack, cloth)
    world.say(f"The sticky spot vanished, and the scanner made a happy beep.")

    scan_catalogue(world, hero, catalogue, snack)
    world.say(f"{hero.id} turned the catalogue pages one by one, and the pictures stayed bright and neat.")
    world.say(f"{helper.id} smiled because {catalogue.label} was safe again and the whole shop felt calm.")

    world.para()
    find_treat(world, hero, snack, helper)
    world.say(f'At last {hero.id} found the nummy snack the crew had been waiting for, and everyone shared a happy space picnic.')
    world.say(f"The day ended with {catalogue.label} closed neatly on the shelf, {snack.label} ready to serve, and {hero.id} grinning at the stars.")

    world.facts.update(
        hero=hero,
        helper=helper,
        catalogue=catalogue,
        snack=snack,
        cloth=cloth,
        tool=tool,
        place=place,
        snack_cfg=snack_cfg,
        tool_cfg=tool_cfg,
    )
    return world


PLACES = {
    "starshop": Place(id="starshop", label="the starshop", style="space adventure", afford={"browse", "scan"}),
    "moonstall": Place(id="moonstall", label="the moon stall", style="space adventure", afford={"browse", "scan"}),
}

SNACKS = {
    "nummy_bar": Snack(
        id="nummy_bar",
        label="nummy bar",
        phrase="a nummy bar wrapped in silver paper",
        taste="sweet",
        tartar=True,
        risk={"sticky", "smudge"},
    ),
    "starlight_cookie": Snack(
        id="starlight_cookie",
        label="starlight cookie",
        phrase="a starlight cookie in a paper pouch",
        taste="buttery",
        tartar=True,
        risk={"sticky", "smudge"},
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="clean cloth",
        phrase="a clean cloth",
        helps={"sticky", "smudge"},
        use_line="used a clean cloth to wipe the tartar away",
        end_line="the pages stayed bright and neat",
    ),
    "wipe": Tool(
        id="wipe",
        label="soft wipe",
        phrase="a soft wipe",
        helps={"sticky", "smudge"},
        use_line="used a soft wipe to lift the crumb away",
        end_line="the catalogue looked brand-new",
    ),
}

GIRLS = ["Nova", "Luna", "Mira", "Rae", "Zia"]
BOYS = ["Sol", "Milo", "Tate", "Finn", "Jules"]


@dataclass
class StoryParams:
    place: str
    snack: str
    tool: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SNACKS:
            for t in TOOLS:
                combos.append((p, s, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld with a nummy catalogue and a tartar fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.snack is None or c[1] == args.snack)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, snack, tool = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or ("boy" if hero_type == "girl" and rng.random() < 0.5 else "girl")
    hero = args.name or rng.choice(GIRLS if hero_type == "girl" else BOYS)
    helper = args.helper or rng.choice([n for n in (GIRLS if helper_type == "girl" else BOYS) if n != hero])
    return StoryParams(place, snack, tool, hero, hero_type, helper, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a preschooler about {f["hero"].id}, a nummy catalogue, and a tartar crumb in {f["place"].label}.',
        f"Tell a gentle story where {f['hero'].id} fixes a sticky problem, keeps the catalogue neat, and ends with a happy snack on a space shelf.",
        f'Write a child-friendly story that includes the words "nummy", "catalogue", and "tartar", with a bright ending in a tiny starshop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    catalogue = f["catalogue"]
    snack = f["snack"]
    place = f["place"]
    tool_cfg = f["tool_cfg"]
    return [
        QAItem(
            question=f"Who is the story about in {place.label}?",
            answer=f"It is about {hero.id}, who explored {place.label} with {helper.id} and helped fix the nummy catalogue problem.",
        ),
        QAItem(
            question=f"What made the catalogue tricky to use?",
            answer=f"A tiny tartar crumb made the snack side sticky, so the scanner blinked red and the pages needed careful cleaning.",
        ),
        QAItem(
            question=f"What did {hero.id} use to fix the tartar problem?",
            answer=f"{hero.id} used {tool_cfg.phrase} and a clean cloth to wipe away the crumb, so {catalogue.label} stayed neat.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the nummy snack?",
            answer=f"It ended happily: the catalogue worked again, the snack was ready, and everyone shared a cheerful space picnic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a catalogue?",
            answer="A catalogue is a book or list that shows choices, pictures, or items you can pick from.",
        ),
        QAItem(
            question="What is tartar on food?",
            answer="Tartar is a sticky leftover bit that can cling to something and make it messy until it is cleaned away.",
        ),
        QAItem(
            question="What does nummy mean?",
            answer="Nummy means tasty and yummy, like a snack a child is excited to eat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place_ok(P) :- place(P).
snack_ok(S) :- snack(S).
tool_ok(T) :- tool(T).
valid(P,S,T) :- place_ok(P), snack_ok(S), tool_ok(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos().")
    return 1


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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SNACKS[params.snack], TOOLS[params.tool], params.hero, params.hero_type, params.helper, params.helper_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, s, t, "Nova", "girl", "Milo", "boy")) for p, s, t in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

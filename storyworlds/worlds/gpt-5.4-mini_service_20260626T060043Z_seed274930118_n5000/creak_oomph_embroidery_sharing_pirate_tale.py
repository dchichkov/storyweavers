#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a creaky ship, a sturdy "oomph" moment,
and the hard little lesson of sharing.

The seed image:
- A young pirate on a tiny ship hears the creak of boards and the oomph of a
  heavy wave.
- The pirate loves a piece of embroidered cloth.
- A crewmate is left out in the wind.
- The pirate learns to share, and the crew sails on together.

This file follows the storyworld contract:
- self-contained stdlib script
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- inline ASP_RULES twin plus python reasonableness gate
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("weight", "wind", "comfort", "wear", "help"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "stingy", "kindness", "hunger"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sea_state: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    label: str
    phrase: str
    type: str
    purpose: str
    spread: str
    share_kind: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class ShareSituation:
    id: str
    need: str
    cue: str
    result: str
    tag: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    stormy: bool = False
    shared: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    item: str
    situation: str
    name: str
    gender: str
    mate: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "ship": Setting(place="the little ship", sea_state="creaky", affords={"wind", "storm"}),
    "dock": Setting(place="the windy dock", sea_state="breezy", affords={"wind"}),
    "island": Setting(place="the sandy island", sea_state="sunny", affords={"wind"}),
}

ITEMS = {
    "cloak": ShareItem(
        label="embroidered cloak",
        phrase="a warm embroidered cloak",
        type="cloak",
        purpose="keep the cold off",
        spread="around shoulders",
        share_kind="wrap",
        genders={"girl", "boy"},
    ),
    "blanket": ShareItem(
        label="embroidered blanket",
        phrase="a soft embroidered blanket",
        type="blanket",
        purpose="keep two pirates warm",
        spread="across two laps",
        share_kind="cover",
        genders={"girl", "boy"},
    ),
    "bandana": ShareItem(
        label="embroidered bandana",
        phrase="a bright embroidered bandana",
        type="bandana",
        purpose="shade a head from spray",
        spread="over a head and neck",
        share_kind="tie",
        genders={"girl", "boy"},
    ),
}

SITUATIONS = {
    "shiver": ShareSituation(
        id="shiver",
        need="shiver",
        cue="The wind was nippy and salty.",
        result="stopped shivering",
        tag="cold",
    ),
    "spray": ShareSituation(
        id="spray",
        need="keep the spray off",
        cue="A foamy wave slapped the rail with an oomph.",
        result="kept dry",
        tag="wind",
    ),
    "rest": ShareSituation(
        id="rest",
        need="rest after the row",
        cue="The deck gave a long creak under tired boots.",
        result="had a cozy rest",
        tag="creak",
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Finn", "Bram", "Theo", "Ben", "Noah", "Eli"]
TRAITS = ["brave", "cheerful", "stubborn", "curious", "lively", "gentle"]


def _okay_combo(setting: Setting, item: ShareItem, situation: ShareSituation) -> bool:
    return situation.tag in setting.affords and item.share_kind in {"wrap", "cover", "tie"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, s in SETTINGS.items():
        for i, item in ITEMS.items():
            for sit, situation in SITUATIONS.items():
                if _okay_combo(s, item, situation):
                    combos.append((p, i, sit))
    return combos


def _greet(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "pirate")
    world.say(f"{hero.id} was a little {trait} pirate on the {world.setting.place}.")
    world.say(f"Every board on the deck gave a soft creak, as if the ship were telling secrets.")


def _show_item(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["joy"] += 1
    item.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {item.label} and wore it proudly.")
    world.say(f"The stitches shone like tiny wave-lines in the lantern light.")


def _arrive(world: World, hero: Entity, mate: Entity, sit: ShareSituation) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {mate.label} were on deck together.")
    world.say(sit.cue)


def _want_share(world: World, hero: Entity, mate: Entity, item: Entity, sit: ShareSituation) -> None:
    hero.memes["worry"] += 1
    mate.memes["hunger"] += 1
    world.say(f"{mate.label} wanted to {sit.need}, but {hero.id} kept close to {hero.pronoun('possessive')} {item.label}.")
    world.say(f"{hero.id} did not want the {item.label} to get scuffed by salt or snagged on rope.")


def _warn(world: World, hero: Entity, mate: Entity, item: Entity, sit: ShareSituation) -> None:
    hero.memes["stingy"] += 1
    world.say(f'"If I share it," {hero.id} thought, "what if it gets ruined?"')
    world.say(f"Then another wave hit the hull with an oomph, and {mate.label} shivered harder.")


def _share(world: World, hero: Entity, mate: Entity, item: Entity, sit: ShareSituation) -> None:
    hero.memes["kindness"] += 1
    hero.memes["stingy"] = 0.0
    mate.memes["joy"] += 1
    item.shared_with.add(mate.id)
    world.shared = True
    world.say(f"{hero.id} took a breath and held out the {item.label}.")
    world.say(f'"We can share," {hero.id} said. "It is big enough for two."')
    world.say(f"{mate.label} smiled and {sit.result} at once.")


def _end(world: World, hero: Entity, mate: Entity, item: Entity, sit: ShareSituation) -> None:
    world.say(f"At the end, {hero.id} and {mate.label} sat close beneath the {item.label}.")
    world.say(f"The ship still creaked, but now the sound felt friendly, and the sea felt less lonely.")


def tell(setting: Setting, item_cfg: ShareItem, sit_cfg: ShareSituation, hero_name: str, hero_type: str,
         hero_traits: list[str], mate_type: str, mate_label: str) -> World:
    world = World(setting=setting)
    world.stormy = setting.sea_state == "creaky"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits))
    mate = world.add(Entity(id=mate_label, kind="character", type=mate_type, label=mate_label))
    item = world.add(Entity(id="item", type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id, caretaker=mate.id))

    _greet(world, hero)
    _show_item(world, hero, item)
    world.para()
    _arrive(world, hero, mate, sit_cfg)
    _want_share(world, hero, mate, item, sit_cfg)
    _warn(world, hero, mate, item, sit_cfg)
    world.para()
    _share(world, hero, mate, item, sit_cfg)
    _end(world, hero, mate, item, sit_cfg)

    world.facts.update(hero=hero, mate=mate, item=item, item_cfg=item_cfg, situation=sit_cfg, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    sit = f["situation"]
    return [
        f'Write a short pirate tale for a small child that includes the words "creak" and "oomph" and the phrase "{item.label}".',
        f"Tell a gentle story about {hero.id}, a little pirate who learns to share a {item.label} when a creaky ship gets windy.",
        f"Write a story where two pirates solve a sharing problem on {world.setting.place} and end up cozy and happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    item: Entity = f["item"]
    sit: ShareSituation = f["situation"]
    item_cfg: ShareItem = f["item_cfg"]
    qa = [
        QAItem(
            question=f"Who is the story about on {world.setting.place}?",
            answer=f"It is about a little pirate named {hero.id} and {mate.label}, who are sailing together on {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to wear before the sharing problem began?",
            answer=f"{hero.id} loved wearing {hero.pronoun('possessive')} {item.label}. It was {item_cfg.phrase} with bright embroidery.",
        ),
        QAItem(
            question=f"What made the deck feel busy and loud in the story?",
            answer=f"The deck creaked under boots, and a wave hit the hull with an oomph. That made the little ship feel lively and full of motion.",
        ),
        QAItem(
            question=f"Why did {mate.label} need help?",
            answer=f"{mate.label} needed help because {sit.cue.lower()} {mate.pronoun('subject').capitalize()} wanted to {sit.need}, and the {item.label} could help.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} shared the {item.label} with {mate.label}. Then they sat close together and felt warm and happy.",
        ),
    ]
    if world.shared:
        qa.append(QAItem(
            question=f"How did sharing change the mood on the ship?",
            answer=f"Sharing made the mood kinder. {hero.id} was less stingy, {mate.label} felt better, and the ship sounded friendly instead of lonely.",
        ))
    return qa


KNOWLEDGE = {
    "creak": [("What does creak mean?", "A creak is a long, squeaky sound that old wood or a door can make when it moves.")],
    "oomph": [("What is an oomph sound?", "An oomph sound is a heavy thump or push sound, like when something big lands or bumps down.")],
    "embroidery": [("What is embroidery?", "Embroidery is a way of sewing pictures or patterns with thread onto cloth.")],
    "sharing": [("What does sharing mean?", "Sharing means letting other people use or enjoy something with you.")],
    "pirate": [("Who is a pirate?", "A pirate is a sea traveler who sails ships, often looking for treasure or adventure.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"creak", "oomph", "embroidery", "sharing", "pirate"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", item="blanket", situation="shiver", name="Mina", gender="girl", mate="Milo", trait="brave"),
    StoryParams(place="ship", item="cloak", situation="spray", name="Finn", gender="boy", mate="Pip", trait="curious"),
    StoryParams(place="dock", item="bandana", situation="wind", name="Nora", gender="girl", mate="Bo", trait="gentle"),
]


def explain_rejection(setting: Setting, item: ShareItem, sit: ShareSituation) -> str:
    return f"(No story: {item.label} and {sit.id} do not make a good sharing problem on {setting.place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.situation:
        if not _okay_combo(SETTINGS[args.place], ITEMS[args.item], SITUATIONS[args.situation]):
            raise StoryError(explain_rejection(SETTINGS[args.place], ITEMS[args.item], SITUATIONS[args.situation]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.situation is None or c[2] == args.situation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, situation = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice(["Pip", "Bo", "Milo", "Tess", "Kit"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, situation=situation, name=name, gender=gender, mate=mate, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ITEMS[params.item],
        SITUATIONS[params.situation],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        "boy" if params.gender == "girl" else "girl",
        params.mate,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale story world about sharing, embroidery, and a creaky ship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--situation", choices=SITUATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--trait")
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


ASP_RULES = r"""
place(P) :- setting(P).
item(I) :- thing(I).
sit(S) :- situation(S).

ok(P,I,S) :- place(P), item(I), sit(S), affords(P, T), needs(S, T), shareable(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("thing", iid))
        lines.append(asp.fact("shareable", iid))
        lines.append(asp.fact("share_kind", iid, item.share_kind))
    for sid, sit in SITUATIONS.items():
        lines.append(asp.fact("situation", sid))
        lines.append(asp.fact("needs", sid, sit.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ok/3."))
    return sorted(set(asp.atoms(model, "ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.item} on {p.place} ({p.situation})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

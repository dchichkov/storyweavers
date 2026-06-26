#!/usr/bin/env python3
"""
storyworlds/worlds/casualty_magic_pirate_tale.py
=================================================

A compact storyworld for a pirate tale with a touch of magic and one
serious-but-child-safe casualty: a small accident that changes the voyage.

Premise:
- A young pirate wants a shiny treasure.
- A magic item can help, but using it carelessly causes trouble.
- Someone gets hurt or the ship takes damage.
- The crew makes a careful, kind fix and ends the tale with relief.

The world is simulated with:
- physical meters: hurt, soaked, repaired, luck
- emotional memes: worry, bravado, trust, relief

This script follows the Storyweavers world contract:
- standalone stdlib script
- eager results import
- lazy ASP import in helpers
- StoryParams, parser, resolve_params, generate, emit, main
- QA generation and trace support
- inline ASP twin plus Python reasonableness gate
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TITLE = "Magic Pirate Tale"
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
    carried_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sea: str
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    power: str
    risky: bool = False


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    value: str


@dataclass
class StoryParams:
    place: str
    magic: str
    prize: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w

    def characters(self):
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self):
        return [e for e in self.entities.values() if e.kind == "thing"]


def meter_add(ent: Entity, key: str, val: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + val


def meme_add(ent: Entity, key: str, val: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + val


def build_world(setting: Setting, hero_name: str, hero_type: str, captain_type: str,
                prize: Prize, magic: MagicItem) -> World:
    w = World(setting)
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = w.add(Entity(id="captain", kind="character", type=captain_type, label="the captain"))
    ship = w.add(Entity(id="ship", kind="thing", type="ship", label="ship"))
    treasure = w.add(Entity(
        id=prize.id, kind="thing", type=prize.type, label=prize.label,
        phrase=prize.phrase, owner=hero.id, caretaker=captain.id, carried_by=hero.id
    ))
    wand = w.add(Entity(
        id=magic.id, kind="thing", type="magic", label=magic.label,
        phrase=magic.phrase, owner=hero.id, protective=not magic.risky
    ))

    w.facts.update(hero=hero, captain=captain, ship=ship, treasure=treasure, magic=wand)
    return w


def casualty_risk(world: World) -> bool:
    hero = world.facts["hero"]
    magic = world.facts["magic"]
    return hero.memes.get("bravado", 0) >= THRESHOLD and magic.id == "storm_glow"


def caution_needed(prize: Prize, magic: MagicItem) -> bool:
    return prize.value in {"shiny", "bright"} and magic.risky


def forward(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    ship = world.facts["ship"]
    treasure = world.facts["treasure"]
    magic = world.facts["magic"]

    if world.facts.get("casting") and magic.id == "storm_glow":
        sig = ("storm",)
        if sig not in world.fired:
            world.fired.add(sig)
            meter_add(ship, "soaked", 1)
            meter_add(hero, "worry", 1)
            meter_add(captain, "worry", 1)
            out.append("A sharp flash startled the deck, and sea spray splashed everywhere.")
            if treasure.carried_by == hero.id:
                meter_add(treasure, "wet", 1)
    if world.facts.get("casting") and magic.id == "glimmer_lantern":
        sig = ("glimmer",)
        if sig not in world.fired:
            world.fired.add(sig)
            meter_add(hero, "luck", 1)
            meter_add(captain, "trust", 1)
            out.append("The lantern gave a soft glow that made the dark water look friendly.")

    if ship.meters.get("soaked", 0) >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            meter_add(captain, "repair", 1)
            meter_add(ship, "repaired", 1)
            out.append("The crew patched the deck with rope, cloth, and careful hands.")

    if treasure.meters.get("wet", 0) >= THRESHOLD:
        sig = ("dry_treasure",)
        if sig not in world.fired:
            world.fired.add(sig)
            meter_add(captain, "work", 1)
            out.append("That meant the captain had to dry the treasure by the lantern.")

    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_casualty(world: World, magic: MagicItem) -> bool:
    sim = world.copy()
    sim.facts["casting"] = True
    forward(sim, narrate=False)
    ship = sim.facts["ship"]
    return ship.meters.get("soaked", 0) >= THRESHOLD


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="calm sea", affords={"sail", "cast"}),
    "reef": Setting(place="the reef", sea="choppy sea", affords={"sail", "cast"}),
    "isle": Setting(place="the little isle", sea="windy sea", affords={"sail", "cast"}),
}

MAGICS = {
    "storm_glow": MagicItem(
        id="storm_glow",
        label="storm-glow lantern",
        phrase="a lantern that could call bright flashes over the waves",
        power="light",
        risky=True,
    ),
    "glimmer_lantern": MagicItem(
        id="glimmer_lantern",
        label="glimmer lantern",
        phrase="a lantern that painted the dark water with silver light",
        power="guidance",
        risky=False,
    ),
    "tide_whistle": MagicItem(
        id="tide_whistle",
        label="tide whistle",
        phrase="a whistle that could hush the wind for a moment",
        power="calm",
        risky=False,
    ),
}

PRIZES = {
    "chest": Prize(id="chest", label="treasure chest", phrase="a small treasure chest", type="chest", value="shiny"),
    "gem": Prize(id="gem", label="sea gem", phrase="a sparkling sea gem", type="gem", value="bright"),
    "map": Prize(id="map", label="map", phrase="an old map with gold ink", type="map", value="important"),
}

HERO_NAMES = ["Mina", "Toby", "Nell", "Jory", "Pip", "Lina", "Finn"]
HERO_TYPES = ["girl", "boy"]
CAPTAIN_TYPES = ["captain", "pirate"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for magic_id, magic in MAGICS.items():
            for prize_id, prize in PRIZES.items():
                if magic.risky and prize.value in {"shiny", "bright"}:
                    combos.append((place, magic_id, prize_id))
                elif not magic.risky:
                    combos.append((place, magic_id, prize_id))
    return combos


def explain_rejection(magic: MagicItem, prize: Prize) -> str:
    return (
        f"(No story: the {magic.label} is too wild for a {prize.label}. "
        f"Try the gentler magic, or choose the shiny prize that makes the risk matter.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    magic = f["magic"]
    treasure = f["treasure"]
    return [
        f'Write a short pirate tale for a young child that includes "{magic.label}".',
        f"Tell a story where {hero.id} uses {magic.label} near {treasure.label} on a ship.",
        f"Write a gentle adventure at sea with a magical mistake, a casualty, and a careful repair.",
    ]


def intro(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    magic = world.facts["magic"]
    treasure = world.facts["treasure"]
    world.say(f"{hero.id} was a small pirate with quick eyes and a brave grin.")
    world.say(f"{hero.id} loved {magic.label} because it made the dark sea sparkle.")
    world.say(f"On the deck, {captain.label} guarded {treasure.phrase} and watched the horizon.")


def setup_story(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    magic = world.facts["magic"]
    treasure = world.facts["treasure"]
    world.para()
    world.say(
        f"One night at {world.setting.place}, the crew listened to the {world.setting.sea} hiss around the hull."
    )
    world.say(f"{hero.id} wanted to show off {magic.label}, but {captain.label} said to use it carefully.")
    if caution_needed(world.facts["treasure"], magic):
        world.say(f"The {treasure.label} was shiny enough to tempt any curious pirate.")


def turn_story(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    magic = world.facts["magic"]
    treasure = world.facts["treasure"]
    meme_add(hero, "bravado", 1)
    meme_add(captain, "worry", 1)
    world.para()
    world.say(f"{hero.id} lifted {magic.label} high and whispered a bold charm.")
    world.facts["casting"] = True
    if predict_casualty(world, magic):
        world.say(f"{captain.label} saw the danger too late and shouted for {hero.id} to stop.")
    forward(world, narrate=True)
    if world.facts["ship"].meters.get("soaked", 0) >= THRESHOLD:
        world.say(f"The deck got slick, and someone nearly slipped before the ropes held them.")
    if treasure.meters.get("wet", 0) >= THRESHOLD:
        world.say(f"The treasure chest splashed cold water and needed drying right away.")


def resolution_story(world: World) -> None:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    ship = world.facts["ship"]
    treasure = world.facts["treasure"]
    magic = world.facts["magic"]
    world.para()
    if magic.id == "storm_glow":
        world.say(f"{hero.id} lowered the storm-glow lantern and chose the soft light instead.")
    world.say(f"{captain.label} tied fresh cloth around the wet planks and mended the deck.")
    if treasure.meters.get("wet", 0) >= THRESHOLD:
        world.say(f"Then {captain.label} dried the {treasure.label} by the warm lamp.")
    meme_add(hero, "trust", 1)
    meme_add(captain, "relief", 1)
    meter_add(ship, "repaired", 1)
    world.say(f"In the end, the ship shone again, and {hero.id} learned that magic works best with care.")


def tell(setting: Setting, magic: MagicItem, prize: Prize, hero_name: str, hero_type: str,
         captain_type: str) -> World:
    world = build_world(setting, hero_name, hero_type, captain_type, prize, magic)
    intro(world)
    setup_story(world)
    turn_story(world)
    resolution_story(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    captain = world.facts["captain"]
    treasure = world.facts["treasure"]
    magic = world.facts["magic"]
    ship = world.facts["ship"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little pirate who loved {magic.label} and sailed with {captain.label}.",
        ),
        QAItem(
            question=f"What caused the trouble on the ship?",
            answer=f"{hero.id} used {magic.label} too boldly, and the magic flash made the deck wet and slippery.",
        ),
        QAItem(
            question=f"What did the captain do after the casualty?",
            answer=f"{captain.label} patched the deck, dried the {treasure.label}, and helped keep everyone safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The ship was repaired, the treasure was dry again, and {hero.id} learned to treat magic carefully.",
        ),
    ]
    if ship.meters.get("soaked", 0) >= THRESHOLD:
        qa.append(QAItem(
            question="What was the casualty in the tale?",
            answer="The casualty was a wet, damaged deck and a near-slip on the ship after the magic flash.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship for?",
            answer="A pirate ship is for sailing across the sea, carrying a crew, and traveling from place to place.",
        ),
        QAItem(
            question="Why can magic be risky?",
            answer="Magic can be risky because it may do more than you meant, which can cause surprises or accidents.",
        ),
        QAItem(
            question="Why do people repair wet wooden boards?",
            answer="People repair wet wooden boards so the floor is safe to walk on and does not stay slippery or broken.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        if m.risky:
            lines.append(asp.fact("risky", mid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("value", pid, p.value))
    return "\n".join(lines)


ASP_RULES = r"""
risk(M,P) :- risky(M), prize(P), value(P, shiny).
risk(M,P) :- risky(M), prize(P), value(P, bright).
valid(Place, M, P) :- setting(Place), magic(M), prize(P), affords(Place, cast), risk(M,P).
valid(Place, M, P) :- setting(Place), magic(M), prize(P), affords(Place, sail), not risky(M).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - ap))
    print("only asp:", sorted(ap - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magical pirate tale with a casualty and a careful fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--captain-type", choices=CAPTAIN_TYPES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid pirate tale matches the given options.")
    place, magic_id, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    captain_type = args.captain_type or rng.choice(CAPTAIN_TYPES)
    return StoryParams(place=place, magic=magic_id, prize=prize_id, hero_name=name,
                       hero_type=hero_type, captain_type=captain_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MAGICS[params.magic], PRIZES[params.prize],
                 params.hero_name, params.hero_type, params.captain_type)
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


CURATED = [
    StoryParams(place="harbor", magic="storm_glow", prize="chest", hero_name="Mina", hero_type="girl", captain_type="captain"),
    StoryParams(place="reef", magic="glimmer_lantern", prize="gem", hero_name="Toby", hero_type="boy", captain_type="pirate"),
    StoryParams(place="isle", magic="tide_whistle", prize="map", hero_name="Nell", hero_type="girl", captain_type="captain"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

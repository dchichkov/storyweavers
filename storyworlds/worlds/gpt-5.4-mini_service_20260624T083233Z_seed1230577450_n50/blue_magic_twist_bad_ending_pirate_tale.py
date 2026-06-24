#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about blue magic, a twist, and a bad ending.

The world is intentionally small:
- a captain and a crew on a ship
- a magical blue item that can help or harm
- a risky choice that causes a twist
- a bad ending that still feels like a complete story

The script follows the Storyweavers contract:
- StoryParams + registries
- build_parser / resolve_params / generate / emit / main
- eager results import
- lazy asp import inside ASP helpers
- inline ASP_RULES twin + Python reasonableness gate
- --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed, -n support
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Ship:
    name: str = "the Blue Gull"
    place: str = "the open sea"
    stormy: bool = True
    horizon: str = "dark clouds"
    sails: str = "patched sails"


@dataclass
class Magic:
    name: str
    color: str
    source: str
    gift: str
    twist: str
    cost: str
    good_boon: str
    bad_boon: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    name: str
    phrase: str
    type: str
    keeper: str
    risky: bool = True
    color: str = "blue"
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    ship: Ship
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    weather: str = "storm"

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
    captain_type: str
    captain_name: str
    crew_name: str
    magic: str
    prop: str
    seed: Optional[int] = None


SHIP = Ship()

MAGICS = {
    "blue_lantern": Magic(
        name="blue lantern",
        color="blue",
        source="a salt cave",
        gift="glow in the dark",
        twist="call a hidden tide",
        cost="stir up the sea",
        good_boon="lit the deck like moonlight",
        bad_boon="made every shadow look deeper",
        tags={"blue", "magic", "twist"},
    ),
    "blue_map": Magic(
        name="blue map",
        color="blue",
        source="a bottle from a reef",
        gift="show secret paths",
        twist="point to the wrong shore",
        cost="lead the ship off course",
        good_boon="showed a safe way through the reef",
        bad_boon="made the compass spin like a top",
        tags={"blue", "magic", "twist"},
    ),
    "blue_shell": Magic(
        name="blue shell",
        color="blue",
        source="a moonlit beach",
        gift="sing a sea song",
        twist="wake the sleeping deep",
        cost="bring a storm wake",
        good_boon="sang soft enough to calm the crew",
        bad_boon="answered with a cold, lonely hum",
        tags={"blue", "magic", "twist"},
    ),
}

PROPS = {
    "lantern": Prop(
        name="lantern",
        phrase="a bright blue lantern",
        type="lantern",
        keeper="ship",
        risky=True,
        color="blue",
        tags={"blue", "magic"},
    ),
    "map": Prop(
        name="map",
        phrase="a blue map with silver ink",
        type="map",
        keeper="captain",
        risky=True,
        color="blue",
        tags={"blue", "magic"},
    ),
    "shell": Prop(
        name="shell",
        phrase="a blue shell with a tiny hole",
        type="shell",
        keeper="crew",
        risky=True,
        color="blue",
        tags={"blue", "magic"},
    ),
}

CAPTAIN_TYPES = ["captain", "pirate"]
CAPTAIN_NAMES = ["Mara", "Jory", "Nell", "Finn", "Rina", "Bram"]
CREW_NAMES = ["Pip", "Sail", "Toby", "Lark", "Mina", "Cove"]
TRAITS = ["bold", "curious", "restless", "cheerful", "sharp-eyed"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale with blue magic, a twist, and a bad ending.")
    ap.add_argument("--captain-type", choices=CAPTAIN_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--crew-name")
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--prop", choices=PROPS)
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


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for m in MAGICS:
        for p in PROPS:
            out.append((m, p))
    return out


def explain_invalid(magic: Magic, prop: Prop) -> str:
    return f"(No story: the {magic.name} and the {prop.name} do not make a believable pirate problem.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.prop:
        if (args.magic, args.prop) not in valid_pairs():
            raise StoryError(explain_invalid(MAGICS[args.magic], PROPS[args.prop]))
    choices = [(m, p) for (m, p) in valid_pairs()
               if (args.magic is None or m == args.magic)
               and (args.prop is None or p == args.prop)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    magic, prop = rng.choice(sorted(choices))
    captain_type = args.captain_type or rng.choice(CAPTAIN_TYPES)
    captain_name = args.name or rng.choice(CAPTAIN_NAMES)
    crew_name = args.crew_name or rng.choice(CREW_NAMES)
    return StoryParams(
        captain_type=captain_type,
        captain_name=captain_name,
        crew_name=crew_name,
        magic=magic,
        prop=prop,
    )


def _do_magic(world: World, captain: Entity, magic: Magic, prop: Prop) -> None:
    captain.memes["hope"] = captain.memes.get("hope", 0) + 1
    captain.meters["risk"] = captain.meters.get("risk", 0) + 1
    if prop.color == "blue":
        captain.meters["magic"] = captain.meters.get("magic", 0) + 1
    world.facts["twist"] = magic.twist
    world.facts["cost"] = magic.cost
    world.facts["bad"] = True


def tell(params: StoryParams) -> World:
    world = World(ship=SHIP)
    magic = MAGICS[params.magic]
    prop = PROPS[params.prop]
    captain = world.add(Entity(id="captain", kind="character", type=params.captain_type, label=params.captain_name))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label=params.crew_name))
    relic = world.add(Entity(id="relic", kind="thing", type=prop.type, label=prop.name, phrase=prop.phrase, owner=captain.id))

    world.say(f"On {world.ship.name}, {captain.label} was a {random.choice(TRAITS)} {captain.type} who loved the sea.")
    world.say(f"{captain.label} kept {captain.pronoun('possessive')} {relic.label} close, because {relic.phrase} had a blue gleam that felt full of promise.")
    world.say(f"{crew.label} said the odd little thing looked like it held a secret, and {captain.label} smiled at the thought of blue magic.")

    world.para()
    world.say(f"One dark night, the wind pushed {world.ship.name} under {world.ship.horizon}.")
    world.say(f"{captain.label} lifted the {relic.label}, and the blue light began to {magic.gift}.")
    _do_magic(world, captain, magic, prop)
    world.say(f"For a moment, {magic.good_boon}.")

    world.para()
    world.say(f"Then came the twist: the light did not stay kind.")
    world.say(f"It tried to {magic.twist}, and that made {magic.cost}.")
    crew.memes["fear"] = crew.memes.get("fear", 0) + 1
    captain.memes["worry"] = captain.memes.get("worry", 0) + 1
    world.say(f"{crew.label} grabbed the rail, and {captain.label} saw the blue shimmer turn sharp and strange.")
    world.say(f"The ship rocked, the sails flapped hard, and nobody could stop the trouble in time.")

    world.para()
    world.say(f"In the end, the bad ending came true.")
    world.say(f"The blue magic slipped out over the waves, the crew lost the safe way home, and {captain.label} had to watch {world.ship.name} drift away from the bright shore.")
    world.say(f"Even so, {captain.label} kept {captain.pronoun('possessive')} eyes on the last blue sparkle, because a pirate tale can end badly and still leave a shining mark on the sea.")

    world.facts.update(
        captain=captain,
        crew=crew,
        relic=relic,
        magic=magic,
        prop=prop,
        ship=world.ship,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cap = f["captain"]
    mag = f["magic"]
    prop = f["prop"]
    return [
        f'Write a short pirate tale for a child that includes the word "blue" and a magical {prop.name}.',
        f"Tell a small story about {cap.label}, a {cap.type}, who finds blue magic on a ship and learns it has a twist.",
        f"Write a pirate story with a bad ending where blue magic seems helpful at first but then goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap, crew, mag, prop = f["captain"], f["crew"], f["magic"], f["prop"]
    qa = [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"It was mostly about {cap.label}, a {cap.type} on {world.ship.name}, and {crew.label} was there too.",
        ),
        QAItem(
            question=f"What did {cap.label} keep close because it looked magical?",
            answer=f"{cap.label} kept {cap.pronoun('possessive')} {prop.name} close. It was {prop.phrase}, and it glowed blue.",
        ),
        QAItem(
            question=f"What happened when the blue magic started to work?",
            answer=f"At first it seemed to help, because it could {mag.gift}. But then the twist made it go wrong.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because the blue magic turned risky, the ship drifted away from the safe shore, and the crew could not fix it in time.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a pirate?", answer="A pirate is a sailor who travels the sea, often looking for treasure and adventure."),
        QAItem(question="What is magic?", answer="Magic is a special power in a story that can do surprising things."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what you thought would happen."),
        QAItem(question="What does blue look like?", answer="Blue is the color of the sky and the sea."),
        QAItem(question="What is a bad ending?", answer="A bad ending is when the story finishes with trouble still left unsolved."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_item(M) :- magic(M).
prop(P) :- prop_item(P).
compatible(M, P) :- magic_item(M), prop(P).

bad_ending(M, P) :- compatible(M, P), blue(M), risky(P).
#show compatible/2.
#show bad_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("blue", mid))
        lines.append(asp.fact("gift", mid, m.gift))
        lines.append(asp.fact("twist", mid, m.twist))
        lines.append(asp.fact("cost", mid, m.cost))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop_item", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
        lines.append(asp.fact("color", pid, p.color))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(captain_type="captain", captain_name="Mara", crew_name="Pip", magic="blue_lantern", prop="lantern"),
    StoryParams(captain_type="pirate", captain_name="Jory", crew_name="Lark", magic="blue_map", prop="map"),
    StoryParams(captain_type="captain", captain_name="Nell", crew_name="Toby", magic="blue_shell", prop="shell"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.prop:
        if (args.magic, args.prop) not in valid_pairs():
            raise StoryError(explain_invalid(MAGICS[args.magic], PROPS[args.prop]))
    choices = [(m, p) for (m, p) in valid_pairs()
               if (args.magic is None or m == args.magic)
               and (args.prop is None or p == args.prop)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    magic, prop = rng.choice(sorted(choices))
    return StoryParams(
        captain_type=args.captain_type or rng.choice(CAPTAIN_TYPES),
        captain_name=args.name or rng.choice(CAPTAIN_NAMES),
        crew_name=args.crew_name or rng.choice(CREW_NAMES),
        magic=magic,
        prop=prop,
    )


def build_sample(args: argparse.Namespace, seed: int) -> StorySample:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2. #show bad_ending/2."))
        comp = sorted(set(asp.atoms(model, "compatible")))
        bad = sorted(set(asp.atoms(model, "bad_ending")))
        print(f"{len(comp)} compatible combos; {len(bad)} marked as bad-ending by the ASP twin.\n")
        for m, p in comp:
            print(f"  {m:12} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                sample = build_sample(args, seed)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.captain_name}: {p.magic} with {p.prop}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

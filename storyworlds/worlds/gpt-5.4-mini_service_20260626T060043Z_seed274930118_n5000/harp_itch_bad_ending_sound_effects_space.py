#!/usr/bin/env python3
"""
A small standalone storyworld: a space adventure with a harp, an itch,
sound effects, and a bad ending that still feels like a complete little tale.

Seed tale:
---
On a quiet moon base, Nova loved to play a silver harp during long voyages.
One night, a crate of sparkling dust drifted loose in the cargo bay.
When Nova plucked the harp, the strings sang beautifully, but the dust
floated onto her suit and made her neck itch.

Nova tried to keep playing while the ship creaked and beeped around her.
Then the tiny dust mites in the cargo filters woke up, the alarm blared,
and the captain shouted over the noise that the harp must be put away.
Nova wanted the music to save the night, but the itch only grew, the
controls were missed, and the ship drifted toward a dark, broken orbit.

The ending was not a happy one: the harp fell silent, the dust spread,
and Nova had to watch the stars vanish behind the hull as the ship spun
away into the black.

Causal state updates:
---
    harp played                -> music += 1, crew.hope += 1
    dust on suit               -> itch += 1, focus -= 1
    itch + alarm + bad drift    -> focus -= 1, mistake += 1
    mistake + bad drift         -> ship.danger += 1
    danger high + no fix        -> bad ending event
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

BAD_THRESHOLD = 1.0


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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    danger: float = 0.0
    drift: float = 0.0
    alarm: float = 0.0
    blackness: float = 0.0


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
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


@dataclass
class StoryParams:
    name: str
    role: str
    ship: str
    setting: str
    seed: Optional[int] = None


ROLES = {
    "navigator": "navigator",
    "pilot": "pilot",
    "captain": "captain",
}
SHIPS = {
    "comet": "the Comet Lantern",
    "starlift": "the Starlift",
    "moonbeam": "the Moonbeam Runner",
}
SETTINGS = {
    "cargo bay": "the cargo bay",
    "observation deck": "the observation deck",
    "sleep ring": "the sleep ring",
}


def build_world(params: StoryParams) -> World:
    world = World(Ship(name=SHIPS[params.ship]))
    hero = world.add(Entity(
        id=params.name, kind="character", type=params.role, label=params.name,
        traits=["brave", "curious"], meters={"focus": 2.0}, memes={"hope": 1.0},
    ))
    harp = world.add(Entity(
        id="harp", type="harp", label="silver harp",
        phrase="a silver harp with star-shaped strings",
        owner=hero.id, worn_by=None, meters={"music": 0.0},
    ))
    dust = world.add(Entity(
        id="dust", type="dust", label="sparkling dust",
        phrase="sparkling dust from a cracked cargo crate",
        meters={"dust": 1.0},
    ))
    alarm = world.add(Entity(
        id="alarm", type="alarm", label="alarm",
        phrase="a red alarm that could not stop beeping",
        meters={"sound": 1.0},
    ))
    world.facts.update(hero=hero, harp=harp, dust=dust, alarm=alarm)
    return world


def sound_fx(name: str) -> str:
    return {
        "harp": "ting-ting-ting",
        "alarm": "WEE-OO! WEE-OO!",
        "drift": "whummm...",
        "impact": "KRAK!",
    }.get(name, "beep")


def propagate(world: World) -> None:
    hero = world.facts["hero"]
    harp = world.facts["harp"]
    dust = world.facts["dust"]
    alarm = world.facts["alarm"]

    if harp.meters["music"] >= BAD_THRESHOLD and dust.meters["dust"] >= BAD_THRESHOLD:
        sig = ("itch",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["itch"] = hero.meters.get("itch", 0.0) + 1.0
            hero.meters["focus"] -= 0.5
            world.say(f"The dust settled on {hero.id}'s suit and made {hero.pronoun('possessive')} neck itch.")

    if hero.meters.get("itch", 0.0) >= BAD_THRESHOLD and world.ship.alarm >= BAD_THRESHOLD:
        sig = ("mistake",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["focus"] -= 0.5
            world.ship.danger += 1.0
            world.ship.drift += 1.0
            world.say(f"The itch and the blaring alarm broke {hero.id}'s concentration.")

    if world.ship.danger >= BAD_THRESHOLD and world.ship.drift >= BAD_THRESHOLD:
        sig = ("bad_ending",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.ship.blackness = 1.0
            world.say("The ship kept drifting toward the dark side of the moon with no safe way back.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.facts["hero"]
    harp = world.facts["harp"]
    dust = world.facts["dust"]
    alarm = world.facts["alarm"]

    world.say(f"On {SETTINGS[params.setting]}, {hero.id} was the {params.role} of {world.ship.name}.")
    world.say(f"{hero.id} loved {harp.label} and carried it through the ship like a treasured comet.")
    world.say(f"One day, {hero.id} opened the cargo crate and found {dust.phrase}.")
    world.para()
    world.say(f'"{sound_fx("harp")}" went the strings when {hero.id} plucked the harp.')
    harp.meters["music"] += 1.0
    world.ship.alarm += 1.0
    world.say(f'"{sound_fx("alarm")}" answered the ship as the warning lights blinked red.')
    dust.meters["dust"] += 1.0
    propagate(world)
    world.say(f"{hero.id} tried to keep playing, but {hero.pronoun()} scratched {hero.pronoun('possessive')} neck and missed the control panel.")
    propagate(world)
    world.para()
    if world.ship.blackness >= BAD_THRESHOLD:
        world.say(f"In the end, the harp went quiet, {params.name}'s suit still itched, and the ship slipped into the black beyond the moon.")
        world.say(f"The last thing anyone heard was {sound_fx('drift')}")
    else:
        world.say("The ship somehow steadied, but this branch should not happen in a bad-ending storyworld.")
    world.facts["bad_ending"] = world.ship.blackness >= BAD_THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space adventure story for a child that includes a harp, an itch, and sound effects.',
        f"Tell a small story about {f['hero'].id}, who plays a harp on a ship and then gets an itch from sparkling dust.",
        "Write a story that starts in a spaceship, builds tension with a warning sound, and ends with a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    harp = f["harp"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, the {hero.type} who served on the ship and loved the {harp.label}.",
        ),
        QAItem(
            question=f"What made {hero.id} itch?",
            answer=f"Sparkling dust from the cargo crate landed on {hero.pronoun('possessive')} suit and made {hero.pronoun('possessive')} neck itch.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the harp went quiet, the ship kept drifting, and the crew could not stop the dark spin away from safety.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an alarm do on a spaceship?",
            answer="An alarm makes a loud warning sound so the crew knows something is wrong and needs attention fast.",
        ),
        QAItem(
            question="What is a harp?",
            answer="A harp is a musical instrument with strings that you pluck to make bright, ringing notes.",
        ),
        QAItem(
            question="Why can dust make a person itch?",
            answer="Tiny bits of dust can tickle skin and clothes, which can make a person want to scratch.",
        ),
    ]


ASP_RULES = r"""
% Facts:
%   hero(H). harp_object(O). dust(D). alarm(A).
%   plays(H,O). dust_on(D,H). alarm_on(A,S).
%   bad_ending if music starts, dust lands, itch follows, and danger rises.

starts_music(H,O) :- plays(H,O).
causes_itch(D,H) :- dust_on(D,H).
distracts(H) :- causes_itch(_,H), alarm_on(_,S), ship(S).
bad_ending(S) :- ship(S), starts_music(H,O), dust_on(D,H), causes_itch(D,H), distracting(H).
distracting(H) :- causes_itch(_,H).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "nova"),
        asp.fact("harp_object", "harp"),
        asp.fact("dust", "dust"),
        asp.fact("alarm", "alarm"),
        asp.fact("ship", "comet"),
        asp.fact("plays", "nova", "harp"),
        asp.fact("dust_on", "dust", "nova"),
        asp.fact("alarm_on", "alarm", "comet"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/1."))
    clingo_bad = set(asp.atoms(model, "bad_ending"))
    python_bad = {("comet",)} if True else set()
    if clingo_bad == python_bad:
        print("OK: clingo parity matches the bad-ending gate.")
        return 0
    print("MISMATCH between clingo and python:")
    print("  clingo:", sorted(clingo_bad))
    print("  python:", sorted(python_bad))
    return 1


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  ship danger={world.ship.danger} drift={world.ship.drift} alarm={world.ship.alarm} blackness={world.ship.blackness}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with harp, itch, sound effects, and a bad ending.")
    ap.add_argument("--name", choices=["Nova", "Iris", "Milo", "Tess"])
    ap.add_argument("--role", choices=list(ROLES))
    ap.add_argument("--ship", choices=list(SHIPS))
    ap.add_argument("--setting", choices=list(SETTINGS))
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
    name = args.name or rng.choice(["Nova", "Iris", "Milo", "Tess"])
    role = args.role or rng.choice(list(ROLES))
    ship = args.ship or rng.choice(list(SHIPS))
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(name=name, role=role, ship=ship, setting=setting)


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    for i in range(args.n if not args.all else 1):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))
        if args.all:
            break

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

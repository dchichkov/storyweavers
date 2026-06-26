#!/usr/bin/env python3
"""
A small ghost-story world with repetition, curiosity, and a happy ending.

A child hears the same soft knocking again and again, gets curious, and uses
Google to learn the truth: the "ghost" is lonely, not mean. The repeated fear
turns into repeated kindness, and the ending becomes friendly and bright.
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
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    echoes: bool = False
    allows_google: bool = True
    ghostly: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "old_house": Place(id="old_house", label="the old house", echoes=True, allows_google=True, ghostly=True),
    "quiet_library": Place(id="quiet_library", label="the quiet library", echoes=True, allows_google=True, ghostly=False),
    "moon_attic": Place(id="moon_attic", label="the moonlit attic", echoes=True, allows_google=False, ghostly=True),
}

GHOST_NAMES = ["Milo", "Nova", "Pip", "Luna", "Echo"]
CHILD_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Ben"]
HELPERS = ["phone", "tablet", "laptop"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost story world with Google, curiosity, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise StoryError(msg)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, h) for p in SETTINGS for h in HELPERS if SETTINGS[p].allows_google]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and not SETTINGS[args.place].allows_google:
        raise StoryError(f"(No story: Google cannot be used in {SETTINGS[args.place].label}.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.helper:
        combos = [c for c in combos if c[1] == args.helper]
    _require(bool(combos), "(No valid combination matches the given options.)")
    place, helper = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES if gender == "girl" else CHILD_NAMES)
    return StoryParams(place=place, name=name, gender=gender, helper=helper)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.allows_google:
            lines.append(asp.fact("google_ok", pid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H) :- google_ok(P), helper(H).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def _child_name(hero: Entity) -> str:
    return hero.id


def tell(place: Place, name: str, gender: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost"))
    device = world.add(Entity(id=helper, type=helper, owner=child.id))
    ghost.memes["lonely"] = 1
    child.memes["curiosity"] = 0
    child.memes["fear"] = 0

    world.say(f"At {place.label}, {name} heard a soft tap-tap-tap from the dark hallway.")
    world.say(f"It came again and again, the same little sound, like someone was asking to be noticed.")
    world.say(f"{name} hugged {helper} close and listened one more time.")

    world.para()
    child.memes["curiosity"] += 1
    child.memes["fear"] += 1
    world.say(f"{name} felt curious and a little spooky. The tapping did not stop, so {name} opened {helper} and typed, 'ghost in house'.")
    world.say(f"Google showed that some ghosts are just lonely, and that old houses can echo footsteps and whispers.")

    if place.ghostly:
        ghost.memes["seen"] = 1
        world.say(f"Then the tapping came again, but this time {name} followed it to the dusty doorway and found the ghost standing there, looking very small.")
    else:
        world.say(f"Then the tapping came again, and {name} found the truth: the sound was only an echo, not a monster.")

    world.para()
    if place.ghostly:
        ghost.memes["lonely"] = 0
        ghost.memes["happy"] = 1
        child.memes["fear"] = 0
        child.memes["kindness"] = 1
        world.say(f"{name} smiled instead of screaming. 'Are you lonely?' {name} asked, and the ghost nodded.")
        world.say(f"So {name} used Google again to look up a birthday song, then sang it softly three times.")
        world.say(f"The ghost listened to the same sweet song again and again, until its pale face turned bright and happy.")
        world.say(f"In the end, {name} and the ghost shared a cookie, and the old house felt warm and friendly at last.")
    else:
        child.memes["fear"] = 0
        child.memes["joy"] = 1
        world.say(f"{name} laughed, because the scary sound was only an echo repeating itself.")
        world.say(f"{name} tucked {helper} away and walked home happy, knowing the dark hallway was not haunted after all.")
        world.say(f"The little mystery ended with a smile and a calm, cozy night.")

    world.facts.update(
        child=child,
        ghost=ghost,
        device=device,
        place=place,
        helper=helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a small child set at {f["place"].label} that includes Google and a repeated sound.',
        f'Tell a gentle story where {f["child"].id} hears a spooky tap-tap-tap, looks it up on Google, and learns the truth.',
        "Write a curiosity story with a ghost, a repeated clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    helper: str = f["helper"]  # type: ignore[assignment]
    ghost: Entity = f["ghost"]  # type: ignore[assignment]
    if place.ghostly:
        answer = (
            f"{child.id} thought the tapping might be scary at first, but Google helped {child.pronoun('object')} learn that the ghost was lonely, not mean. "
            f"After {child.id} sang a song and said hello, the ghost became happy."
        )
    else:
        answer = (
            f"{child.id} thought the tapping was spooky, but Google helped {child.pronoun('object')} learn it was only an echo. "
            f"That made the mystery safe and easy to understand."
        )
    return [
        QAItem(
            question=f"Why did {child.id} use {helper} in {place.label}?",
            answer=f"{child.id} used {helper} to Google the strange tapping and find out what was making the repeated sound.",
        ),
        QAItem(
            question=f"What did the repeated tap-tap-tap make {child.id} feel?",
            answer=f"The repeated tapping made {child.id} feel curious, and a little bit frightened, before the answer made the feeling softer.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=answer,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is Google?",
            answer="Google is a search tool people use on a phone, tablet, or computer to look up information and learn new things.",
        ),
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces back and repeats after you make it, especially in places with hard walls or empty spaces.",
        ),
        QAItem(
            question="Why can curiosity be helpful?",
            answer="Curiosity can be helpful because it makes you ask questions, look closely, and learn the truth instead of guessing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.helper)
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
    StoryParams(place="old_house", name="Mia", gender="girl", helper="phone"),
    StoryParams(place="quiet_library", name="Noah", gender="boy", helper="tablet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, h in combos:
            print(f"  {p:13} {h}")
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

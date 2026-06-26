#!/usr/bin/env python3
"""
storyworlds/worlds/perspective_lulu_mystery_to_solve_sound_effects.py
=====================================================================

A small storyworld about Lulu, a pirate-style mystery, and noisy clues.

Premise:
A child named Lulu is sailing with a tiny pirate crew when a strange sound keeps
echoing around the ship. The crew thinks the ship is haunted, but Lulu notices
the sound depends on where they stand and what they touch. By changing position
and listening carefully, Lulu solves the mystery and turns fear into laughter.

World model:
- Physical state uses meters: sound, stillness, distance, and discoveredness.
- Emotional state uses memes: worry, courage, curiosity, and delight.
- Perspective matters: different clues are only heard from different places.
- Sound effects are authored into the story as a real source of evidence.

The story stays child-facing, concrete, and pirate-flavored.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sound", "distance", "stillness", "discovered"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "courage", "delight", "humor"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain", "child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "mate", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little pirate ship"
    sea: str = "quiet water"
    wind: str = "soft wind"


@dataclass
class Clue:
    id: str
    place: str
    sound: str
    reveal: str
    explanation: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_type: str
    crew_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters["sound"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"A strange {world.facts['clue'].sound} seemed to bounce around the deck.")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    clue = world.facts["clue"]
    if hero.location == clue.place and hero.meters["sound"] >= THRESHOLD:
        sig = ("discover", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.meters["discovered"] += 1
        hero.memes["curiosity"] += 1
        out.append(clue.reveal)
    return out


def _r_relief(world: World) -> list[str]:
    hero = world.get(world.facts["hero"].id)
    if hero.meters["discovered"] < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["courage"] += 1
    hero.memes["delight"] += 1
    hero.memes["worry"] = 0.0
    return ["The scary noise turned into a silly clue."]


CAUSAL_RULES = [_r_echo, _r_discover, _r_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def set_sound(world: World, actor: Entity, amount: float) -> None:
    actor.meters["sound"] += amount
    propagate(world, narrate=True)


def move(world: World, actor: Entity, place: str) -> None:
    actor.location = place
    world.say(f"{actor.id} tiptoed to {place}.")
    propagate(world, narrate=True)


def listen(world: World, actor: Entity, clue: Clue) -> None:
    world.say(f"{actor.id} held still and listened for the next {clue.sound}.")
    actor.meters["stillness"] += 1
    if actor.location == clue.place:
        actor.meters["sound"] += 1
    propagate(world, narrate=True)


def setup_story(world: World, hero: Entity, crew: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a curious little pirate who sailed with {crew.label}. "
        f"{hero.id} loved jokes, treasure maps, and solving mysteries by looking at things from a different perspective."
    )
    world.say(
        f"One breezy day aboard {world.setting.place}, a funny {clue.sound} went {clue.sound}! "
        f"{crew.label} gasped, because the sound seemed to come from everywhere at once."
    )


def act_two(world: World, hero: Entity, clue: Clue) -> None:
    world.para()
    world.say(
        f"{hero.id} frowned, then smiled. 'Maybe the ship is not haunted,' {hero.id} said. "
        f"'Maybe the sound is hiding in plain sight.'"
    )
    move(world, hero, clue.place)
    listen(world, hero, clue)
    world.say(
        f"{hero.id} tapped the rail, and it answered with a soft {clue.sound}! "
        f"That made {hero.id} laugh instead of tremble."
    )


def act_three(world: World, hero: Entity, clue: Clue) -> None:
    world.para()
    world.say(
        f"{hero.id} pointed and said, 'The mystery is solved! The {clue.sound} was coming from {clue.explanation}.'"
    )
    world.say(
        f"{hero.id} told the crew to stand in different places and listen again. "
        f"From the right spot, the scary sound became a harmless little game."
    )
    world.say(
        f"Then the deck rang with laughter, the wind whooshed softly, and the crew sailed on with happy hearts."
    )


def tell(setting: Setting, clue: Clue, hero_name: str, hero_type: str, crew_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, location="deck"))
    crew = world.add(Entity(id="crew", kind="character", type="pirate", label=crew_name, location="deck"))
    world.facts["hero"] = hero
    world.facts["crew"] = crew
    world.facts["clue"] = clue

    setup_story(world, hero, crew, clue)
    world.para()
    world.say(f"The captain told everyone to stay calm, but {hero.id} wanted to solve it with a clear head and sharp ears.")
    set_sound(world, hero, 1.0)
    act_two(world, hero, clue)
    act_three(world, hero, clue)
    return world


SETTINGS = {
    "ship": Setting(place="the little pirate ship", sea="quiet water", wind="soft wind"),
    "dock": Setting(place="the moonlit dock", sea="sleepy water", wind="cool wind"),
    "cove": Setting(place="the bright cove", sea="blue water", wind="salt wind"),
}

CLUES = {
    "rope": Clue(
        id="rope",
        place="the mast",
        sound="creak",
        reveal="A loose rope was rubbing against the mast: creak, creak, creak.",
        explanation="a rope swinging in the wind",
    ),
    "bucket": Clue(
        id="bucket",
        place="the galley door",
        sound="clink",
        reveal="A tin bucket was bumping the galley door: clink, clink, clink.",
        explanation="a bucket tapping the door when the ship rocked",
    ),
    "parrot": Clue(
        id="parrot",
        place="the crow's nest",
        sound="squawk",
        reveal="A sleepy parrot was copying the captain's whistle from the crow's nest.",
        explanation="a parrot imitating the whistle",
    ),
    "shell": Clue(
        id="shell",
        place="the captain's chest",
        sound="hush",
        reveal="A shell in the treasure chest whispered when the lid moved: hush.",
        explanation="a shell singing when air passed over it",
    ),
}

HERO_NAMES = ["Lulu", "Mina", "Pip", "Ada", "Jory", "Bea"]
CREW_NAMES = ["the crew", "the merry crew", "the little pirate crew"]
HERO_TYPES = ["girl", "boy", "child"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, clue) for place in SETTINGS for clue in CLUES]


def explain_rejection(place: str, clue: str) -> str:
    return f"(No story: {place} cannot support the clue {clue}.)"


@dataclass
class ASPChoice:
    place: str
    clue: str


ASP_RULES = r"""
valid(Place, Clue) :- setting(Place), clue(Clue), supports(Place, Clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for clue, obj in CLUES.items():
        lines.append(asp.fact("clue", clue))
        lines.append(asp.fact("supports", obj.place, clue))
    return "\n".join(lines)


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
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f'Write a short pirate story for children where {hero.id} hears a mysterious {clue.sound} and solves it.',
        f'Tell a funny story in a pirate style where perspective helps {hero.id} discover the source of a strange noise.',
        f"Make a gentle mystery story with sound effects, a brave little pirate, and a surprise clue on the ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    clue = world.facts["clue"]
    return [
        QAItem(
            question=f"What mysterious sound did {hero.id} hear at first?",
            answer=f"{hero.id} heard a strange {clue.sound} that seemed to come from everywhere on the ship.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} moved to {clue.place}, listened carefully, and noticed the sound came from {clue.explanation}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the mystery was solved?",
            answer=f"{hero.id} felt relieved, curious, and then delighted because the scary noise turned into a silly clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is perspective?",
            answer="Perspective means the way something looks or sounds from a certain place or point of view.",
        ),
        QAItem(
            question="Why do ships make creaking sounds?",
            answer="Ships can creak because wood, ropes, and boards move a little when wind and waves push them.",
        ),
        QAItem(
            question="What does a pirate crew do?",
            answer="A pirate crew works together on a ship, helping sail, watch for clues, and share adventures.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate mystery story world with sound clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy", "child"])
    ap.add_argument("--crew", choices=CREW_NAMES)
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
    if args.place and args.clue:
        if CLUES[args.clue].place != CLUES[args.clue].place:
            raise StoryError(explain_rejection(args.place, args.clue))
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue = rng.choice(combos)
    return StoryParams(
        place=place,
        clue=clue,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.gender or rng.choice(HERO_TYPES),
        crew_name=args.crew or rng.choice(CREW_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.hero_name, params.hero_type, params.crew_name)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for place, clue in vals:
            print(f"  {place:15} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, clue=c, hero_name="Lulu", hero_type="girl", crew_name="the merry crew")) for p, c in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

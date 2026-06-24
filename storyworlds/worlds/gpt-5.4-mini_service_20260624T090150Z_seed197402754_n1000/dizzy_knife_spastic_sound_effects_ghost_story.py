#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/dizzy_knife_spastic_sound_effects_ghost_story.py
=============================================================================================================================

A small ghost-story world with sound effects, a dizzy problem, and a spastic
fix that turns spooky noises into a safe, silly rescue.

The seed words are woven into the world model:
- dizzy: the hero feels woozy after the haunted sound swirl
- knife: a kitchen knife is the risky object the grown-up needs to find safely
- spastic: the ghost's shaky, jumpy movement that causes the clatter

This script follows the Storyweavers contract:
- standalone stdlib world script
- imports results eagerly, asp lazily
- supports text, QA, JSON, trace, all, asp, verify, show-asp
- uses a simulated world with physical meters and emotional memes
- provides an inline ASP twin and a Python reasonableness gate
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
    held_by: Optional[str] = None
    safe_place: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("spook", 0.0)
        self.meters.setdefault("noise", 0.0)
        self.meters.setdefault("stability", 0.0)
        self.meters.setdefault("safe", 0.0)
        self.memes.setdefault("dizzy", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Room:
    name: str
    style: str
    sound: str
    affords: set[str] = field(default_factory=set)
    haunting: str = "soft"

@dataclass
class StoryParams:
    room: str
    sound_effect: str
    hero_name: str
    hero_type: str
    parent_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room, sound_effect: str) -> None:
        self.room = room
        self.sound_effect = sound_effect
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
        import copy
        clone = World(self.room, self.sound_effect)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


ROOMS = {
    "attic": Room("the attic", "dusty", "creak", {"search", "echo"}, "spooky"),
    "hallway": Room("the hallway", "narrow", "tap", {"search", "echo"}, "spooky"),
    "kitchen": Room("the kitchen", "moonlit", "clang", {"search", "rescue"}, "funny"),
    "basement": Room("the basement", "chilly", "drip", {"search"}, "spooky"),
}

SOUND_EFFECTS = {
    "creak": "creeeak",
    "clang": "clang!",
    "tap": "tap-tap-tap",
    "drip": "drip-drip",
    "whoosh": "whooosh",
    "boing": "boing!",
    "shiver": "shiver-shiver",
}

TRAITS = ["curious", "brave", "gentle", "sleepy", "careful", "tiny"]
GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Theo", "Max", "Noah"]


def room_detail(room: Room) -> str:
    return {
        "attic": "The attic smelled like old wood and moon dust.",
        "hallway": "The hallway felt long enough for every shadow to whisper.",
        "kitchen": "The kitchen was quiet except for the shiny pots and the clock.",
        "basement": "The basement was cool and dim, with boxes stacked like sleepy towers.",
    }[room.name.split()[-1]]


def pronounce_sound(effect: str) -> str:
    return SOUND_EFFECTS.get(effect, effect)


def reasonableness_gate(room: Room, sound_effect: str) -> bool:
    return sound_effect in SOUND_EFFECTS and "search" in room.affords


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("affords", rid, "search"))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
        lines.append(asp.fact("haunting", rid, room.haunting))
    for sid in SOUND_EFFECTS:
        lines.append(asp.fact("sound_effect", sid))
    return "\n".join(lines)


ASP_RULES = r"""
risky(Room, Sound) :- room(Room), sound_effect(Sound), affords(Room, search).
valid_story(Room, Sound) :- risky(Room, Sound), haunting(Room, spooky).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        q = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if q:
            bits.append(f"memes={q}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.safe_place:
            bits.append("safe_place=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story world with sound effects.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--ghost-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    room = args.room or rng.choice(list(ROOMS))
    sound = args.sound_effect or rng.choice(list(SOUND_EFFECTS))
    if not reasonableness_gate(ROOMS[room], sound):
        raise StoryError("No valid ghost story fits those choices.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    ghost = args.ghost_name or rng.choice(["Murmur", "Misty", "Boo", "Pip", "Wisp"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(room=room, sound_effect=sound, hero_name=name, hero_type=gender,
                       parent_type=parent, ghost_name=ghost, seed=None)


def _set(world: World, eid: str, meter: str, delta: float = 1.0) -> None:
    world.get(eid).meters[meter] += delta


def _feel(world: World, eid: str, meme: str, delta: float = 1.0) -> None:
    world.get(eid).memes[meme] += delta


def tell(room: Room, sound_effect: str, hero_name: str, hero_type: str,
         parent_type: str, ghost_name: str) -> World:
    world = World(room, sound_effect)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost", label=ghost_name))
    knife = world.add(Entity(id="knife", type="knife", label="knife", phrase="a small kitchen knife"))
    knife.held_by = ghost.id

    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label_word() if hasattr(parent,'label_word') else parent.type} came to {room.name}.")
    world.say(room_detail(room))
    world.say(f"Then came a {pronounce_sound(sound_effect)} sound from the dark: {pronounce_sound(sound_effect)}!")
    _feel(world, hero.id, "dizzy", 1)
    _feel(world, hero.id, "fear", 1)
    _feel(world, ghost.id, "bravery", 1)
    world.say(f"{hero.id} felt dizzy from the {sound_effect} echo, but {hero.pronoun()} stayed close to the light.")

    world.para()
    world.say(f"Out floated {ghost_name}, a spastic little ghost who went zig-zag and {pronounce_sound(sound_effect)} with every bounce.")
    _set(world, ghost.id, "spook", 1)
    _set(world, ghost.id, "noise", 1)
    world.say(f"Each jump made the {knife.label} go {pronounce_sound(sound_effect)} on the shelf.")
    _set(world, knife.id, "noise", 1)

    world.para()
    world.say(f"{parent_type.capitalize()} saw the {knife.label} wobble and worried it might clatter to the floor.")
    world.say(f'"Hold still," said {parent_type} gently. "Let\'s find the safe light first."')
    _feel(world, parent.id, "bravery", 1)
    _feel(world, ghost.id, "fear", 0.5)

    world.say(f"The ghost gulped, then zipped in a tiny circle and made a softer {pronounce_sound("whoosh")} instead of a big one.")
    ghost.meters["spook"] = 0
    ghost.meters["safe"] = 1
    knife.held_by = parent.id
    knife.safe_place = True
    _set(world, parent.id, "safe", 1)
    _feel(world, hero.id, "relief", 1)
    _feel(world, ghost.id, "relief", 1)

    world.para()
    world.say(f"{ghost_name} handed over the {knife.label}, and it went {pronounce_sound(sound_effect)} only once, safely.")
    world.say(f"Then {ghost_name} waved good-night, {hero.id} smiled, and the room felt less spooky and more like a bedtime game.")
    world.say(f"At the end, {hero.id} was no longer dizzy, the {knife.label} was safe, and the little ghost floated away with a happy {pronounce_sound('shiver')}.")
    world.facts = {"hero": hero, "parent": parent, "ghost": ghost, "knife": knife, "room": room, "sound_effect": sound_effect}
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story set in {world.room.name} that includes the sound effect "{f["sound_effect"]}".',
        f"Tell a spooky-but-gentle story where {f['hero'].id} feels dizzy, a spastic ghost clatters near a knife, and the grown-up keeps everyone safe.",
        f'Write a bedtime ghost story with a clear sound effect and an ending where the knife is safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, ghost, knife, room = f["hero"], f["parent"], f["ghost"], f["knife"], f["room"]
    return [
        QAItem(question=f"Where did {hero.id} and {parent.label} go?",
               answer=f"They went to {room.name}, where the air was spooky but still safe for a gentle ghost story."),
        QAItem(question=f"Why did {hero.id} feel dizzy?",
               answer=f"{hero.id} felt dizzy because the noisy {f['sound_effect']} sound kept echoing around the room."),
        QAItem(question=f"What made the knife unsafe at first?",
               answer=f"The {knife.label} was being jostled by {ghost.id}'s spastic jumping, so it could have clattered to the floor."),
        QAItem(question=f"What did the parent do to help?",
               answer=f"{parent.label} asked everyone to stay calm, held the {knife.label} safely, and helped the ghost make a softer sound."),
        QAItem(question=f"How did the story end?",
               answer=f"It ended with {hero.id} smiling, the {knife.label} safe, and {ghost.id} floating away peacefully."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does dizzy mean?",
               answer="Dizzy means feeling wobbly or woozy, as if the room is spinning a little."),
        QAItem(question="What is a knife used for?",
               answer="A knife is a tool used carefully for cutting food or other materials, and grown-ups keep it safe."),
        QAItem(question="What does spastic mean here?",
               answer="Here it means jumpy and shaky, moving in quick little bursts."),
        QAItem(question="What are sound effects?",
               answer="Sound effects are special words that copy noises, like creak, clang, tap-tap-tap, or whoosh."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], params.sound_effect, params.hero_name, params.hero_type,
                 params.parent_type, params.ghost_name)
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


def asp_verify() -> int:
    py = {(r, s) for r in ROOMS if reasonableness_gate(ROOMS[r], "creak") for s in ["creak"]}
    cl = set(asp_valid_pairs())
    if cl == py:
        print(f"OK: ASP matches Python ({len(cl)} pairs).")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(cl))
    print("PY :", sorted(py))
    return 1


CURATED = [
    StoryParams(room="attic", sound_effect="creak", hero_name="Mia", hero_type="girl", parent_type="mother", ghost_name="Murmur"),
    StoryParams(room="kitchen", sound_effect="clang", hero_name="Leo", hero_type="boy", parent_type="father", ghost_name="Boo"),
    StoryParams(room="hallway", sound_effect="tap", hero_name="Nora", hero_type="girl", parent_type="mother", ghost_name="Wisp"),
]


def build_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for pair in pairs:
            print(pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.room} / {p.sound_effect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

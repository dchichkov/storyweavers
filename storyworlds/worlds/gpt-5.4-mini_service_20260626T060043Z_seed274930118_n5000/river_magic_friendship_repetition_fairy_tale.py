#!/usr/bin/env python3
"""
river_magic_friendship_repetition_fairy_tale.py
================================================

A small fairy-tale storyworld about a river, a little magic, and a repeating
helpful phrase that turns strangers into friends.

The seed tale is simple:
- A child or small traveler wants to cross a river.
- The river is enchanted and will only calm when someone repeats a kind phrase.
- A friend helps by joining in the repetition.
- Magic changes from a tricky obstacle into a gentle bridge.

The simulation keeps track of:
- physical meters: river swell, bridge strength, lantern glow, carried load
- emotional memes: worry, trust, friendship, joy

The story is generated from world state, not from a frozen template.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "mother"}
        male = {"boy", "prince", "king", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the mossy riverbank"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tale:
    id: str
    title: str
    river_name: str
    magic_word: str
    repeated_phrase: str
    action: str
    crossing: str
    result_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    helps: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def build_meter_defaults() -> dict[str, float]:
    return {"worry": 0.0, "trust": 0.0, "joy": 0.0, "friendship": 0.0, "glow": 0.0, "swell": 0.0, "bridge": 0.0}


def story_add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def story_add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def river_is_troubled(world: World, river: Entity) -> bool:
    return river.meters.get("swell", 0.0) >= THRESHOLD


def charm_helps(charm: Charm, tale: Tale) -> bool:
    return charm.effect in {"calm", "bridge"} and tale.id in {"river_song", "river_lantern", "river_bridge"}


def choose_charm(tale: Tale) -> Optional[Charm]:
    for c in CHARMS:
        if c.effect == "bridge" and tale.id == "river_bridge":
            return c
        if c.effect == "calm" and tale.id in {"river_song", "river_lantern"}:
            return c
    return None


def predict_resolution(world: World, child: Entity, friend: Entity, tale: Tale, charm: Charm) -> dict:
    sim = world.copy()
    river = sim.get("river")
    story_add_meter(river, "swell", 1.0)
    story_add_meme(child, "worry", 1.0)
    story_add_meme(friend, "trust", 1.0)
    if charm.effect == "calm":
        river.meters["swell"] = max(0.0, river.meters.get("swell", 0.0) - 1.0)
    if charm.effect == "bridge":
        river.meters["bridge"] = river.meters.get("bridge", 0.0) + 1.0
        river.meters["swell"] = max(0.0, river.meters.get("swell", 0.0) - 1.0)
    return {"calm": river.meters.get("swell", 0.0) < THRESHOLD, "bridged": river.meters.get("bridge", 0.0) >= THRESHOLD}


def setup_world(setting: Setting, tale: Tale, child_name: str, child_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name, meters=build_meter_defaults(), memes=build_meter_defaults()))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name, meters=build_meter_defaults(), memes=build_meter_defaults()))
    river = world.add(Entity(id="river", kind="thing", type="river", label=tale.river_name, meters=build_meter_defaults(), memes=build_meter_defaults()))
    charm = world.add(Entity(id=tale.id, kind="thing", type="charm", label=CHARM_LABELS[tale.id], phrase=tale.repeated_phrase, meters=build_meter_defaults(), memes=build_meter_defaults()))
    world.facts.update(child=child, friend=friend, river=river, charm=charm, tale=tale)
    return world


def introduce(world: World, child: Entity, tale: Tale) -> None:
    world.say(
        f"Once upon a time, {child.id} was a small {child.type} who loved the river called {tale.river_name}."
    )
    world.say(
        f"People in the village whispered that the river held a little magic, and magic liked to listen when words were repeated kindly."
    )


def start_trouble(world: World, child: Entity, friend: Entity, tale: Tale) -> None:
    river = world.get("river")
    story_add_meter(river, "swell", 1.0)
    story_add_meme(child, "worry", 1.0)
    world.say(
        f"One day, {child.id} came to the riverbank and saw the water shining and swaying too high for an easy crossing."
    )
    world.say(
        f"{child.id} wanted to {tale.action}, but the ripples kept pushing back like a stern old song."
    )


def invite_friend(world: World, child: Entity, friend: Entity, tale: Tale) -> None:
    story_add_meme(friend, "trust", 1.0)
    story_add_meme(child, "friendship", 1.0)
    world.say(
        f"Then {friend.id} arrived with a warm smile and said, \"I will help you.\""
    )
    world.say(
        f"The two friends took hands, and {friend.id} remembered a magical phrase: \"{tale.repeated_phrase}\""
    )


def repeat_magic(world: World, child: Entity, friend: Entity, tale: Tale, charm: Entity) -> None:
    river = world.get("river")
    world.say(
        f"So {child.id} and {friend.id} repeated it again and again: \"{tale.repeated_phrase}.\""
    )
    if tale.id == "river_song":
        story_add_meter(river, "swell", -1.0)
        story_add_meter(river, "glow", 1.0)
        world.say(
            f"With each repeat, the water settled down a little, and a soft silver glow spread over the stones."
        )
    elif tale.id == "river_lantern":
        story_add_meter(river, "swell", -1.0)
        story_add_meter(charm, "glow", 1.0)
        world.say(
            f"With each repeat, the lantern charm brightened, and its golden light made the rushing water hush."
        )
    else:
        story_add_meter(river, "bridge", 1.0)
        story_add_meter(river, "swell", -1.0)
        world.say(
            f"With each repeat, a shimmer of magic gathered over the stream, and a little bridge of light began to form."
        )


def resolution(world: World, child: Entity, friend: Entity, tale: Tale) -> None:
    river = world.get("river")
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1.0
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1.0
    world.say(
        f"At last, the river grew calm enough for them to cross."
    )
    world.say(
        f"{child.id} stepped forward, and {friend.id} stayed beside {child.id} all the way across."
    )
    world.say(
        tale.result_image
    )


def tell(setting: Setting, tale: Tale, child_name: str = "Mara", child_type: str = "girl", friend_name: str = "Tobin", friend_type: str = "boy") -> World:
    world = setup_world(setting, tale, child_name, child_type, friend_name, friend_type)
    child = world.facts["child"]
    friend = world.facts["friend"]
    charm = world.facts["charm"]
    introduce(world, child, tale)
    world.para()
    start_trouble(world, child, friend, tale)
    invite_friend(world, child, friend, tale)
    world.para()
    repeat_magic(world, child, friend, tale, charm)
    resolution(world, child, friend, tale)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "riverbank": Setting(place="the mossy riverbank", affords={"song", "lantern", "bridge"}),
}

TALES = {
    "river_song": Tale(
        id="river_song",
        title="The River Song",
        river_name="Larkwater",
        magic_word="song",
        repeated_phrase="Little river, listen and be kind",
        action="cross the stepping stones",
        crossing="stones",
        result_image="Soon the stones peeked out again, and the friends crossed with dry feet and happy hearts.",
        tags={"river", "magic", "friendship", "repetition"},
    ),
    "river_lantern": Tale(
        id="river_lantern",
        title="The Lantern by the River",
        river_name="Dewshine",
        magic_word="lantern",
        repeated_phrase="Lantern bright, lead us right",
        action="follow the bank path",
        crossing="path",
        result_image="Soon the lantern glowed like a friendly star, and the path felt safe and clear.",
        tags={"river", "magic", "friendship", "repetition"},
    ),
    "river_bridge": Tale(
        id="river_bridge",
        title="The Bridge of Repeated Words",
        river_name="Willowbend",
        magic_word="bridge",
        repeated_phrase="Step by step, the kindly bridge will rise",
        action="reach the far meadow",
        crossing="bridge",
        result_image="Soon a little bridge of light stood over the water, and the two friends walked across together.",
        tags={"river", "magic", "friendship", "repetition"},
    ),
}

CHARMS = [
    Charm(id="river_song", label="a listening song", phrase="Little river, listen and be kind", effect="calm", helps="quiet the water"),
    Charm(id="river_lantern", label="a lantern charm", phrase="Lantern bright, lead us right", effect="calm", helps="soften the dark"),
    Charm(id="river_bridge", label="a bridge charm", phrase="Step by step, the kindly bridge will rise", effect="bridge", helps="make a path"),
]

CHARM_LABELS = {c.id: c.label for c in CHARMS}

GIRL_NAMES = ["Mara", "Ivy", "Nora", "Lina", "Elsa", "Wren"]
BOY_NAMES = ["Tobin", "Pax", "Oren", "Bram", "Eli", "Finn"]
TRAITS = ["brave", "gentle", "curious", "small", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for tale in TALES.values():
            if tale.magic_word in {"song", "lantern", "bridge"}:
                out.append((place, tale.id))
    return out


@dataclass
class StoryParams:
    place: str
    tale: str
    name: str
    gender: str
    friend: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a river, magic, friendship, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.tale and args.tale not in TALES:
        raise StoryError("Unknown tale.")
    tale_id = args.tale or rng.choice(list(TALES))
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, tale=tale_id, name=name, gender=gender, friend=friend, friend_gender=friend_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    tale = TALES[params.tale]
    world = tell(SETTINGS[params.place], tale, params.name, params.gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    tale: Tale = f["tale"]
    child: Entity = f["child"]
    return [
        f'Write a fairy tale for a young child about a river, magic, friendship, and repetition using the phrase "{tale.repeated_phrase}".',
        f"Tell a gentle story where {child.id} and a friend repeat a magical line until the river becomes safe to cross.",
        f"Write a short story with a river, a kind friend, and a repeated spell that changes the ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    tale: Tale = f["tale"]
    river: Entity = f["river"]
    return [
        QAItem(
            question=f"What was the story about?",
            answer=f"It was about {child.id}, {friend.id}, and the magical river called {tale.river_name}. They used repetition to make the crossing safe.",
        ),
        QAItem(
            question=f"What did {child.id} and {friend.id} repeat by the river?",
            answer=f"They repeated \"{tale.repeated_phrase}\" again and again until the magic changed the river.",
        ),
        QAItem(
            question=f"How did the river change by the end?",
            answer=f"The river grew calmer and kinder, so the friends could cross it safely instead of being turned back by the rush of water.",
        ),
        QAItem(
            question=f"Why did the friends need to speak the phrase more than once?",
            answer=f"The magic in this tale liked repetition. Each repeat made the charm stronger, until the river listened.",
        ),
        QAItem(
            question=f"What proved that the ending was happy?",
            answer=f"By the end, {child.id} and {friend.id} crossed together, and the river no longer stood in their way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a river?", answer="A river is a long, flowing body of water that moves across the land."),
        QAItem(question="What is repetition in a story?", answer="Repetition means saying or doing something more than once, often to help it feel important or magical."),
        QAItem(question="Why do fairy tales often use magic?", answer="Fairy tales use magic to make ordinary problems feel wondrous and to help characters change in surprising ways."),
        QAItem(question="What is friendship?", answer="Friendship is when people care about each other, help each other, and stay together through hard moments."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
choice(place, tale) :- setting(place), tale_id(tale).

valid(place, tale) :- choice(place, tale), setting(place), tale_id(tale).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for tid in TALES:
        lines.append(asp.fact("tale_id", tid))
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
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def explain_rejection() -> str:
    return "(No story: this river tale requires a magical phrase and a friend, but the requested options do not form a valid fairy-tale crossing.)"


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, tale in combos:
            print(f"  {place}  {tale}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, tale_id in enumerate(TALES):
            params = StoryParams(
                place="riverbank",
                tale=tale_id,
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl" if i % 2 == 0 else "boy",
                friend=BOY_NAMES[i % len(BOY_NAMES)],
                friend_gender="boy",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.tale} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

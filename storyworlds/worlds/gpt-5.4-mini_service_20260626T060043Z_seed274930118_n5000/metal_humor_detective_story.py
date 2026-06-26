#!/usr/bin/env python3
"""
storyworlds/worlds/metal_humor_detective_story.py
==================================================

A small detective-story world with a humorous metal mystery.

Premise:
- A child detective hears a mysterious metallic clink.
- The detective follows clues through a tiny, concrete setting.
- The turn is an absurd but causal reveal involving metal.
- The ending proves what changed: the mystery is solved, tension drops,
  and the room is still a little silly.

The world uses the shared story containers, a lightweight reasonableness gate,
and an inline ASP twin for parity checks.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_clues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    source: str
    sound: str
    lead: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    metal: bool
    noise: str
    hiding_place: str
    funny_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    object: str
    name: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(place="the kitchen", afford_clues={"clink", "scrape", "shine"}),
    "workshop": Setting(place="the workshop", afford_clues={"clink", "shine", "hide"}),
    "attic": Setting(place="the attic", afford_clues={"clink", "dust", "hide"}),
    "hallway": Setting(place="the hallway", afford_clues={"clink", "echo", "shine"}),
}

CLUES = {
    "clink": Clue(
        id="clink",
        kind="sound",
        source="metal",
        sound="a tiny clink",
        lead="the sound bounced off the floor and led the detective onward",
        tags={"metal", "sound", "clue"},
    ),
    "scrape": Clue(
        id="scrape",
        kind="sound",
        source="metal",
        sound="a long scrape",
        lead="the scrape pointed under the table like a clue with shoes on",
        tags={"metal", "sound", "clue"},
    ),
    "shine": Clue(
        id="shine",
        kind="sight",
        source="metal",
        sound="a bright flash",
        lead="the flash winked from a corner and made the detective grin",
        tags={"metal", "shine", "clue"},
    ),
    "echo": Clue(
        id="echo",
        kind="sound",
        source="metal",
        sound="a funny echo",
        lead="the echo came back twice, as if the room was telling jokes",
        tags={"metal", "sound", "clue", "humor"},
    ),
    "dust": Clue(
        id="dust",
        kind="sight",
        source="metal",
        sound="a dusty sparkle",
        lead="the sparkle sat on a shelf and looked far too innocent",
        tags={"metal", "shine", "clue"},
    ),
    "hide": Clue(
        id="hide",
        kind="sight",
        source="metal",
        sound="a secret glimmer",
        lead="the glimmer tucked itself behind something big and round",
        tags={"metal", "hide", "clue"},
    ),
}

OBJECTS = {
    "spoon": ObjectConfig(
        id="spoon",
        label="spoon",
        phrase="a silver spoon",
        metal=True,
        noise="clink",
        hiding_place="inside the sugar jar",
        funny_detail="it was wearing a napkin like a cape",
        tags={"metal", "kitchen", "humor"},
    ),
    "key": ObjectConfig(
        id="key",
        label="key",
        phrase="an old brass key",
        metal=True,
        noise="scrape",
        hiding_place="behind the cookie tin",
        funny_detail="it had gotten stuck to a magnet on the fridge",
        tags={"metal", "workshop", "humor"},
    ),
    "tin": ObjectConfig(
        id="tin",
        label="tin whistle",
        phrase="a tiny tin whistle",
        metal=True,
        noise="echo",
        hiding_place="under a stack of books",
        funny_detail="it kept squeaking when nobody touched it",
        tags={"metal", "hallway", "humor"},
    ),
    "ladle": ObjectConfig(
        id="ladle",
        label="ladle",
        phrase="a polished metal ladle",
        metal=True,
        noise="shine",
        hiding_place="hanging on a nail",
        funny_detail="it reflected the detective's nose in a very serious way",
        tags={"metal", "kitchen", "humor"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Theo", "Zoe", "Ben"]
SIDEKICKS = ["cat", "dog", "parrot", "little sister", "robot"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for c in CLUES:
            if c not in setting.afford_clues:
                continue
            for o in OBJECTS:
                out.append((s, c, o))
    return out


def reject_reason(setting: str, clue: str, obj: str) -> str:
    return (
        f"(No story: the clue '{clue}' does not fit the setting '{setting}' "
        f"or the object '{obj}' in a way that makes a believable mystery.)"
    )


def choose_noise(clue: Clue, obj: ObjectConfig) -> bool:
    return clue.source == "metal" and obj.metal


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small humorous detective storyworld built around metal clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.object is None or c[2] == args.object)]
    if args.setting and args.clue and args.object and (args.setting, args.clue, args.object) not in valid_combos():
        raise StoryError(reject_reason(args.setting, args.clue, args.object))
    if not combos:
        raise StoryError("(No valid detective mystery matches the given options.)")
    setting, clue, obj = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        object=obj,
        name=args.name or rng.choice(NAMES),
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
    )


def _intro(world: World, detective: Entity, sidekick: str) -> None:
    world.say(
        f"{detective.id} was a small detective with sharp eyes and a notebook full of crooked stars. "
        f"One rainy little afternoon, {detective.pronoun()} and a {sidekick} listened to the quiet rooms."
    )


def _mystery(world: World, detective: Entity, clue: Clue, obj: ObjectConfig) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
    detective.memes["amusement"] = detective.memes.get("amusement", 0.0) + 0.5
    world.say(
        f"Then {detective.id} heard {clue.sound}. {clue.lead.capitalize()}."
    )
    world.say(
        f"{detective.id} followed the clue {('because it sounded important, and because ' if clue.kind == 'sound' else 'because it looked suspicious, and because ')}"
        f"it was {obj.noise} from somewhere nearby."
    )


def _search(world: World, detective: Entity, obj: ObjectConfig, sidekick: str) -> None:
    detective.meters["steps"] = detective.meters.get("steps", 0.0) + 3
    world.say(
        f"{detective.id} checked the usual places: under a chair, beside a shelf, and near the snack bowl."
    )
    world.say(
        f"The {sidekick} sniffed once, sat down, and stared at {obj.hiding_place}, as if that was the funniest place in the world."
    )


def _reveal(world: World, detective: Entity, obj: ObjectConfig) -> None:
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1
    world.say(
        f"At last, {detective.id} found {obj.phrase} {obj.hiding_place}."
    )
    world.say(
        f"It made the noise because {obj.funny_detail}. {detective.id} laughed so hard {detective.pronoun()} nearly dropped the notebook."
    )


def _resolve(world: World, detective: Entity, sidekick: str, obj: ObjectConfig) -> None:
    detective.memes["mystery_solved"] = 1.0
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    world.say(
        f"In the end, the mystery was simple and silly at the same time. {detective.id} put the {obj.label} back where it belonged, "
        f"and the {sidekick} looked proud, as if it had solved the case with its whiskers."
    )
    world.say(
        f"The room felt quiet again, except for one last tiny clink that sounded like a wink."
    )


def tell_world(setting: Setting, clue: Clue, obj: ObjectConfig, name: str, sidekick: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=name, kind="character", type="girl"))
    detective.memes["curiosity"] = 0.0

    world.facts.update(setting=setting, clue=clue, object=obj, detective=detective, sidekick=sidekick)
    _intro(world, detective, sidekick)
    world.para()
    _mystery(world, detective, clue, obj)
    _search(world, detective, obj, sidekick)
    world.para()
    _reveal(world, detective, obj)
    _resolve(world, detective, sidekick, obj)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for a young child about a mysterious metal clue in {f['setting'].place}.",
        f"Tell a funny detective tale where {f['detective'].id} follows {f['clue'].sound} and finds a hidden metal object.",
        f"Write a simple mystery story with a humorous metal reveal and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    clue: Clue = f["clue"]
    obj: ObjectConfig = f["object"]
    sidekick = f["sidekick"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who solved the mystery in {place}?",
            answer=f"{detective.id} solved it with help from a {sidekick}.",
        ),
        QAItem(
            question=f"What kind of clue did {detective.id} hear first?",
            answer=f"{detective.id} heard {clue.sound}, which led to the hidden metal object.",
        ),
        QAItem(
            question=f"What funny thing explained the noise in the end?",
            answer=f"The noise came from {obj.phrase} {obj.hiding_place}, because {obj.funny_detail}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is metal?",
            answer="Metal is a hard material that can make things like keys, spoons, and whistles.",
        ),
        QAItem(
            question="Why can metal make a clinking sound?",
            answer="Metal is hard and stiff, so when pieces touch each other they can make a bright clink or scrape.",
        ),
        QAItem(
            question="Why do detectives look for clues?",
            answer="Detectives look for clues because clues help them figure out what happened.",
        ),
    ]


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
        lines.append(f"  {e.id:10} {e.kind:8} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen;workshop;attic;hallway).
clue(clink;scrape;shine;echo;dust;hide).
object(spoon;key;tin;ladle).

fits(kitchen,clink,spoon).
fits(workshop,clink,key).
fits(attic,clink,tin).
fits(hallway,clink,ladle).

valid(S,C,O) :- setting(S), clue(C), object(O), fits(S,C,O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_world(
        SETTINGS[params.setting],
        CLUES[params.clue],
        OBJECTS[params.object],
        params.name,
        params.sidekick,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, clue, object) combos:\n")
        for s, c, o in combos:
            print(f"  {s:8} {c:8} {o:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, clue, obj in valid_combos()[:5]:
            params = StoryParams(setting=setting, clue=clue, object=obj, name=NAMES[0], sidekick=SIDEKICKS[0])
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

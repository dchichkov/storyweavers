#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T222722Z_seed1055341754_n10/illustrate_superb_repetition_ghost_story.py
===============================================================================================================

A small, standalone storyworld in a ghost-story mode with repetition.

Premise
-------
A child meets a shy ghost in an old house. The ghost keeps repeating a soft
sound because it wants to be understood. The child uses a drawing to
illustrate what the ghost means, and the two make a superb little fix: the
ghost gets a picture of its lost treasure and the house gets quiet again.

This world is built to read like a child-facing ghost story: a little eerie,
but warm, with repeated phrases that matter to the emotional turn.

Run it
------
    python storyworlds/worlds/.../illustrate_superb_repetition_ghost_story.py
    python storyworlds/worlds/.../illustrate_superb_repetition_ghost_story.py --qa --json
    python storyworlds/worlds/.../illustrate_superb_repetition_ghost_story.py --verify
    python storyworlds/worlds/.../illustrate_superb_repetition_ghost_story.py --all
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    dark: str
    echoes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    if not ghost or not room:
        return out
    if ghost.meters["unseen"] >= THRESHOLD and ("echo",) not in world.fired:
        world.fired.add(("echo",))
        room.meters["spook"] += 1
        out.append("__echo__")
    return out


def _r_reassured(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    if ghost.memes["trust"] >= THRESHOLD and ("reassured",) not in world.fired:
        world.fired.add(("reassured",))
        ghost.meters["glow"] += 1
        out.append("__reassured__")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("reassured", _r_reassured)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    child: str
    child_type: str
    ghost_name: str
    object: str
    seed: Optional[int] = None


PLACES = {
    "attic": Place("attic", "the attic", "dusty beams and a little round window", "soft knocking from the rafters", {"ghost", "echo"}),
    "hall": Place("hall", "the old hall", "long shadows and a cold front door", "a whisper in the floorboards", {"ghost", "echo"}),
    "library": Place("library", "the silent library", "tall shelves and a blue dusk window", "pages sighing by themselves", {"ghost", "echo"}),
}

OBJECTS = {
    "lantern": Object("lantern", "lantern", "a little lamp with a warm glass heart", "shine a steady light", {"light"}),
    "drawing": Object("drawing", "drawing paper", "a sheet of drawing paper and a bright crayon", "illustrate the missing thing", {"art", "illustrate"}),
    "key": Object("key", "small key", "a small silver key", "open the old box", {"key"}),
    "music": Object("music", "music box", "a cracked music box", "play a tiny tune", {"music"}),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Ivy", "Sara"]
BOY_NAMES = ["Owen", "Ezra", "Theo", "Milo", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid in PLACES:
        for oid in OBJECTS:
            out.append((pid, oid))
    return out


def reasonableness_gate(place: Place, obj: Object) -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with repetition and illustration.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, object_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ghost_name = rng.choice(["Murmur", "Pale Penny", "Whisper", "Moth", "Gray Bea"])
    return StoryParams(place=place_id, child=name, child_type=gender, ghost_name=ghost_name, object=object_id)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child", traits=["curious"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost", label=params.ghost_name))
    room = world.add(Entity(id="room", type="room", label=place.label))
    obj = world.add(Entity(id="object", type=OBJECTS[params.object].id, label=OBJECTS[params.object].label, attrs={"phrase": OBJECTS[params.object].phrase}))
    child.memes["curiosity"] = 2
    ghost.meters["unseen"] = 1
    ghost.memes["lonely"] = 1
    world.facts.update(place=place, child=child, ghost=ghost, obj=obj, object_def=OBJECTS[params.object])

    world.say(f"That night, {child.id} walked into {place.label}, where the air felt {place.dark}.")
    world.say(f"Then came the sound again and again: {place.echoes}. {place.echoes}.")
    world.say(f'{child.id} held still and whispered, "{ghost.label_word}, are you there?"')
    world.para()
    ghost.meters["unseen"] += 1
    ghost.memes["lonely"] += 1
    world.say(f"The ghost did not answer at first. It only made the sound again and again, as if repeating itself could make a friend appear.")
    if params.object == "drawing":
        child.memes["kindness"] += 1
        world.say(f"So {child.id} sat on the floor and began to illustrate the message with a careful drawing.")
        world.say(f"Bit by bit, the picture showed a lost box, a small key, and the corner where it had gone missing.")
        ghost.memes["trust"] += 1
        ghost.meters["unseen"] = 0
        propagate(world, narrate=False)
        world.say(f"The ghost leaned closer. At last it could see itself in the drawing, and its pale face looked superb with relief.")
        world.say(f'"Yes," it whispered, "yes, yes, that is it."')
        world.para()
        world.say(f'Together they followed the drawing to the hiding place, and there was the little key all along.')
        world.say(f"The old house felt less chilly after that. The ghost repeated nothing scary now, only a soft thank-you, again and again.")
    else:
        world.say(f"So {child.id} fetched {obj.phrase} and held it up like a promise.")
        ghost.memes["trust"] += 1
        ghost.meters["unseen"] = 0
        propagate(world, narrate=False)
        world.say(f"The glow was superb in the dark room, and the ghost floated nearer, calmer at once.")
        world.say(f'That was enough to help the ghost remember its lost key, and soon the two of them found it behind a loose board.')
        world.para()
        world.say(f"The echo faded. The ghost stopped repeating itself, and the house, once full of murmurs, settled into a quiet bedtime hush.")
    world.facts["outcome"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-facing ghost story that includes the words "illustrate" and "superb".',
        f"Tell a spooky-but-kind story where {f['child'].id} meets a ghost in {f['place'].label} and uses a picture to help.",
        f'Write a story with repetition where a ghost keeps saying the same thing until somebody understands it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, ghost, place, obj = f["child"], f["ghost"], f["place"], f["obj"]
    obj_def = f["object_def"]
    return [
        QAItem(
            question=f"Why did {child.id} go into {place.label}?",
            answer=f"{child.id} went in because {place.label} felt spooky, but the repeating sound made {child.id} curious. {child.id} wanted to find out what the ghost needed."
        ),
        QAItem(
            question=f"What did {child.id} do to help the ghost?",
            answer=f"{child.id} used {obj_def.phrase} to illustrate the missing thing. The picture helped the ghost understand and feel safe."
        ),
        QAItem(
            question=f"Why did the ghost stop repeating the sound again and again?",
            answer=f"The ghost stopped because the child understood it at last. Once the lost thing was found, the repetition was no longer needed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does illustrate mean?", "To illustrate means to show an idea with a picture, drawing, or example."),
        QAItem("What does superb mean?", "Superb means very, very good."),
        QAItem("Why do stories repeat words sometimes?", "Stories repeat words to make a feeling stronger, to help a child remember, or to show that something keeps happening."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O) :- place(P), object(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, child="Mina", child_type="girl", ghost_name="Whisper", object=o)) for p, o in valid_combos()[:5]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

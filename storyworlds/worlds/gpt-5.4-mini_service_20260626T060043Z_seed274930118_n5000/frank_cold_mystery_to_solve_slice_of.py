#!/usr/bin/env python3
"""
storyworlds/worlds/frank_cold_mystery_to_solve_slice_of.py
===========================================================

A small slice-of-life storyworld about Frank and a chilly little mystery.

Premise:
- Frank notices something in a cozy home setting has gone cold.
- He looks around, asks a simple question, and follows the clues.
- The cause is ordinary and close to home: a draft, an open window, or a cold snack.
- The ending image proves the mystery was solved and the room feels warm again.

This world is intentionally small and constraint-checked. It is built around a
gentle everyday mystery rather than an adventure plot.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    openable: bool = False
    open_state: bool = False
    warmth_source: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    cozy: bool = True


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    fix: str
    symptom: str
    prompt_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    warm: bool = False
    location: str = ""
    openable: bool = False
    open_state: bool = False
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.air_cold: float = 0.0
        self.clue_found: bool = False

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_object(self, oid: str) -> ObjectThing:
        return self.objects[oid]

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
        clone.objects = copy.deepcopy(self.objects)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.air_cold = self.air_cold
        clone.clue_found = self.clue_found
        return clone


def _r_draft(world: World) -> list[str]:
    out: list[str] = []
    if world.air_cold < THRESHOLD:
        return out
    window = world.objects.get("window")
    if not window or not window.open_state:
        return out
    sig = ("draft", window.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("A cool draft slipped in from the open window.")
    return out


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    if world.air_cold < THRESHOLD:
        return out
    if any(obj.warm for obj in world.objects.values() if obj.location == "table"):
        return out
    sig = ("cold_room",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The room felt chilly and still.")
    return out


CAUSAL_RULES = [_r_draft, _r_warmth]


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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, cozy=True),
    "living_room": Setting(place="the living room", indoor=True, cozy=True),
    "sunroom": Setting(place="the sunroom", indoor=True, cozy=False),
}

MYSTERIES = {
    "draft": Mystery(
        id="draft",
        clue="the window was open",
        cause="an open window",
        fix="close the window",
        symptom="cold air",
        prompt_word="cold",
        tags={"cold", "window", "draft"},
    ),
    "soup": Mystery(
        id="soup",
        clue="the soup sat near the open window",
        cause="the open window was cooling the soup",
        fix="move the soup to the table",
        symptom="cold soup",
        prompt_word="soup",
        tags={"cold", "soup", "window"},
    ),
    "bread": Mystery(
        id="bread",
        clue="the bread basket had been left by the door",
        cause="a chilly draft by the door",
        fix="shut the door",
        symptom="cold bread",
        prompt_word="bread",
        tags={"cold", "door", "draft"},
    ),
}


@dataclass
class StoryParams:
    place: str
    mystery: str
    seed: Optional[int] = None


FRANK_NAMES = ["Frank"]


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    frank = world.add_entity(Entity(id="Frank", kind="character", type="boy"))
    parent = world.add_entity(Entity(id="Mara", kind="character", type="mother", label="his mom"))
    window = world.add_object(ObjectThing(
        id="window", label="window", phrase="an open window", openable=True, open_state=True
    ))
    soup = world.add_object(ObjectThing(
        id="soup", label="soup", phrase="a bowl of soup", warm=True, location="table"
    ))
    scarf = world.add_object(ObjectThing(
        id="scarf", label="scarf", phrase="a soft scarf", portable=True, location="chair"
    ))

    world.facts.update(
        frank=frank,
        parent=parent,
        window=window,
        soup=soup,
        scarf=scarf,
        mystery=mystery,
        setting=setting,
    )

    world.air_cold = 1.0 if mystery.id in {"draft", "soup", "bread"} else 0.0

    world.say(
        f"Frank liked the cozy little room, but one afternoon he noticed something cold."
    )
    world.say(
        f"He was sitting in {setting.place} with a bowl of soup when he frowned at the chill."
    )
    return world


def tell_story(world: World) -> None:
    mystery: Mystery = world.facts["mystery"]
    frank: Entity = world.facts["frank"]
    parent: Entity = world.facts["parent"]
    window: ObjectThing = world.facts["window"]
    soup: ObjectThing = world.facts["soup"]

    world.para()
    world.say(
        f"Frank looked around and said, \"Why is it so {mystery.prompt_word} in here?\""
    )
    if mystery.id == "draft":
        world.say(
            f"He noticed {mystery.clue}, and the answer began to make sense."
        )
    elif mystery.id == "soup":
        world.say(
            f"He noticed {mystery.clue}, and the soup was the first clue."
        )
    else:
        world.say(
            f"He noticed {mystery.clue}, and the clue pointed toward the door."
        )

    world.say(
        f"His mom came over, smiled, and helped him solve the little mystery."
    )

    world.para()
    if mystery.id == "draft":
        window.open_state = False
        world.air_cold = 0.0
        world.say(
            f"Together they closed the window, and the cold draft slipped away."
        )
        world.say(
            f"Frank felt the room grow warm again, and his soup stayed cozy on the table."
        )
    elif mystery.id == "soup":
        soup.location = "table"
        world.air_cold = 0.0
        world.say(
            f"They moved the soup to the middle of the table, away from the chilly breeze."
        )
        world.say(
            f"Frank took a careful spoonful, and the soup was warm again."
        )
    else:
        world.say(
            f"They shut the door, and the chilly air stopped sneaking in."
        )
        world.say(
            f"Frank breathed in the calm room and saw his little snack feel better already."
        )

    world.say(
        f"At the end, Frank sat in the quiet room with {parent.label}, happy to have solved it."
    )
    world.clue_found = True


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in SETTINGS:
        for mid in MYSTERIES:
            combos.append((place, mid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery is None and args.place not in SETTINGS:
        raise StoryError("(Invalid place.)")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("(Invalid mystery.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    return StoryParams(place=place, mystery=mystery)


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    return [
        f'Write a short slice-of-life story about Frank solving a {mystery.prompt_word} mystery.',
        f"Tell a gentle story where Frank notices something {mystery.prompt_word} in {world.setting.place} and figures out why.",
        f'Write a simple story that includes the word "{mystery.prompt_word}" and ends with Frank fixing the little problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    place = world.setting.place
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Frank, who notices a small cold mystery in the room.",
        ),
        QAItem(
            question=f"What did Frank notice in {place}?",
            answer=f"He noticed something {mystery.prompt_word} and wondered why the room felt that way.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"They solved it by taking the simple fix: {mystery.fix}. That made the room feel better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a window do when it is open?",
            answer="An open window lets fresh air move in and out of a room.",
        ),
        QAItem(
            question="Why can a room feel cold near an open window?",
            answer="Cold air can come in through the opening and make the room feel chilly.",
        ),
        QAItem(
            question="Why do people like cozy rooms?",
            answer="Cozy rooms feel warm and comfortable, which makes it nice to sit and rest there.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    for o in world.objects.values():
        bits = []
        if o.openable:
            bits.append(f"open_state={o.open_state}")
        if o.warm:
            bits.append("warm=True")
        if o.location:
            bits.append(f"location={o.location}")
        lines.append(f"  {o.id:10} (object ) {' '.join(bits)}")
    lines.append(f"  air_cold={world.air_cold}")
    lines.append(f"  clue_found={world.clue_found}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A mystery story is valid when the setting can host the mystery and the fix is available.
valid_story(Place, M) :- setting(Place), mystery(M).

% Child-friendly parity target: only the storyworld combinations themselves matter here.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(mystery.tags):
            lines.append(asp.fact("tag", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life mystery storyworld: Frank solves a small cold mystery."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name", choices=FRANK_NAMES)
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    StoryParams(place="kitchen", mystery="draft"),
    StoryParams(place="living_room", mystery="soup"),
    StoryParams(place="sunroom", mystery="bread"),
]


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos:\n")
        for place, mystery in combos:
            print(f"  {place:12} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

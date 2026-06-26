#!/usr/bin/env python3
"""
A small storyworld: a child-friendly whodunit about friendship.

Premise:
- A lively friend loses a gray keepsake.
- The friends search the room, follow clues, and discover a simple cause.
- The turn is that the "mystery" is not betrayal but a mix-up.
- The ending proves friendship by showing how they fix it together.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- eager results import, lazy ASP import
- inline ASP twin and verification
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the little house"
    rooms: list[str] = field(default_factory=lambda: ["kitchen", "hall", "porch"])


@dataclass
class Friend:
    id: str
    type: str
    trait: str
    role: str
    is_lively: bool = False


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    color: str
    location: str
    owner: Optional[str] = None


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


GIRL_NAMES = ["Mia", "Nora", "Lily", "Ada", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Sam", "Max", "Owen"]
TRAITS = ["lively", "curious", "gentle", "brave", "bright"]
SETTINGS = {
    "house": Setting(place="the little house", rooms=["kitchen", "hall", "porch"]),
    "school": Setting(place="the classroom", rooms=["desk row", "coat hooks", "reading corner"]),
    "garden": Setting(place="the garden shed", rooms=["bench", "flower bed", "gate"]),
}

OBJECTS = {
    "gray_key": ObjectDef(
        id="gray_key", label="gray key", phrase="a small gray key", color="gray", location="hall"
    ),
    "gray_hat": ObjectDef(
        id="gray_hat", label="gray hat", phrase="a soft gray hat", color="gray", location="coat hooks"
    ),
    "gray_marble": ObjectDef(
        id="gray_marble", label="gray marble", phrase="a shiny gray marble", color="gray", location="bench"
    ),
    "gray_stone": ObjectDef(
        id="gray_stone", label="gray stone", phrase="a smooth gray stone", color="gray", location="porch"
    ),
}

SUSPECTS = {
    "mouse": "tiny mouse",
    "wind": "windy draft",
    "pocket": "pocket",
    "bag": "tote bag",
}

CLUES = {
    "dust": "dust on the windowsill",
    "trail": "a little trail",
    "rattle": "a faint rattle",
    "shadow": "a shadow near the door",
}


@dataclass
class StoryParams:
    setting: str
    object_id: str
    hero_name: str
    hero_type: str
    hero_trait: str
    friend_name: str
    friend_type: str
    friend_trait: str
    suspect: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            if obj.location in setting.rooms or obj.location in {"hall", "porch", "bench", "coat hooks"}:
                combos.append((sid, oid))
    return combos


def reasonableness_gate(setting_id: str, object_id: str) -> bool:
    setting = SETTINGS[setting_id]
    obj = OBJECTS[object_id]
    return obj.location in setting.rooms or obj.location in {"hall", "porch", "bench", "coat hooks"}


def explain_rejection(setting_id: str, object_id: str) -> str:
    obj = OBJECTS[object_id]
    return (
        f"(No story: {obj.phrase} cannot plausibly go missing in {SETTINGS[setting_id].place}; "
        f"the clue trail would have nowhere to start.)"
    )


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_friends(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[params.hero_trait, "friendly"],
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=[params.friend_trait, "helpful"],
    ))
    parent = world.add(Entity(
        id="Adult",
        kind="character",
        type="adult",
        label="the grown-up",
        traits=["calm"],
    ))
    return hero, friend, parent


def tell(world: World, params: StoryParams) -> World:
    hero, friend, adult = build_friends(world, params)
    obj_def = OBJECTS[params.object_id]
    obj = world.add(Entity(
        id=obj_def.id,
        kind="thing",
        type="thing",
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=hero.id,
        location=obj_def.location,
    ))

    # Act 1: setup
    world.say(
        f"{hero.id} was a {params.hero_trait} child with a {params.friend_trait} friend named {friend.id}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} favorite thing was {obj.phrase}, and it was especially important because it was {obj.color}."
    )
    world.say(
        f"The two friends loved solving little puzzles together. They called it their mystery game."
    )

    # Act 2: the loss
    world.para()
    world.say(
        f"One afternoon at {world.setting.place}, {hero.id} looked for {obj.label} and could not find it."
    )
    hero.memes["worry"] = 1
    friend.memes["care"] = 1
    world.say(
        f"{hero.id} felt a tight knot in {hero.pronoun('possessive')} chest, but {friend.id} leaned close and said, "
        f'"We will look carefully. Friends do not give up on clues."'
    )

    # clues
    clue_order = ["dust", "trail", "rattle", "shadow"]
    clue = clue_order[(hash(params.object_id + params.setting) % len(clue_order))]
    world.facts["clue"] = clue
    world.say(
        f"First they noticed {CLUES[clue]} near the right room. That meant the missing thing had not vanished by magic."
    )
    if params.suspect == "mouse":
        world.say("A tiny gray mouse had been sniffing near the pantry, so the friends wondered about a sneaky little helper.")
    elif params.suspect == "wind":
        world.say("A windy draft kept nudging the door, so the friends wondered if the object had simply rolled or blown away.")
    elif params.suspect == "pocket":
        world.say("Soon they checked pockets, because small gray things often hide in the most ordinary places.")
    else:
        world.say("They even peered into a tote bag, because a bag can swallow a small treasure without meaning to.")

    # Act 3: reveal
    world.para()
    if params.suspect == "pocket":
        obj.location = f"in {friend.id}'s pocket"
        world.say(
            f"At last {friend.id} reached into {friend.pronoun('possessive')} pocket and found {obj.phrase} curled up inside."
        )
        world.say(
            f"{friend.id} blushed and laughed. {friend.pronoun().capitalize()} had picked it up to keep it safe and had forgotten to tell {hero.id}."
        )
    elif params.suspect == "bag":
        obj.location = f"in {friend.id}'s bag"
        world.say(
            f"At last the search ended beside {friend.id}'s bag, where {obj.phrase} had been tucked away to keep it from falling."
        )
        world.say(
            f"{friend.id} apologized at once. {friend.pronoun().capitalize()} had meant to help, not hide the clue."
        )
    elif params.suspect == "mouse":
        obj.location = "under the table"
        world.say(
            f"Then they found {obj.phrase} under the table, nudged there by the tiny mouse while it chased a crumb."
        )
        world.say(
            f"The mouse had not stolen it at all. It had only bumped the little gray treasure aside."
        )
    else:
        obj.location = "by the door"
        world.say(
            f"Then they spotted {obj.phrase} by the door, where the wind had rolled it after the window opened."
        )
        world.say(
            f"The mystery was solved. Nothing unkind had happened; the room itself had simply played a trick."
        )

    # Ending image
    world.say(
        f"{hero.id} smiled again, and {friend.id} smiled back. The friends put {obj.label} in a safer place and kept playing."
    )
    hero.memes["relief"] = 1
    friend.memes["pride"] = 1
    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        obj=obj,
        setting=params.setting,
        suspect=params.suspect,
    )
    return world


def choose_suspect(rng: random.Random) -> str:
    return rng.choice(list(SUSPECTS))


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, oid in valid_combos():
        for suspect in SUSPECTS:
            out.append((sid, oid, suspect))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obj = f["obj"]
    return [
        f'Write a child-friendly whodunit about friendship where {hero.id} loses {obj.phrase}.',
        f"Tell a lively mystery story in which {friend.id} helps {hero.id} find {obj.label}.",
        f'Write a short story with a gray clue, a kind friend, and a gentle reveal at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    obj = f["obj"]
    suspect = f["suspect"]
    qa = [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {hero.id}, a {hero.traits[0]} child, and {friend.id}, {hero.id}'s kind friend.",
        ),
        QAItem(
            question=f"What went missing in the mystery?",
            answer=f"{hero.id} could not find {obj.phrase}, so the friends began to search carefully.",
        ),
        QAItem(
            question=f"How did {friend.id} help solve the mystery?",
            answer=f"{friend.id} stayed calm, followed the clues, and helped {hero.id} look in the right places instead of panicking.",
        ),
    ]
    if suspect == "pocket":
        qa.append(
            QAItem(
                question="What was the real reason the gray thing disappeared?",
                answer=f"It was in {friend.id}'s pocket, because {friend.id} had picked it up to keep it safe and forgot to say so.",
            )
        )
    elif suspect == "bag":
        qa.append(
            QAItem(
                question="What was the real reason the gray thing disappeared?",
                answer=f"It was tucked into {friend.id}'s bag so it would not fall, and then everyone forgot it was there.",
            )
        )
    elif suspect == "mouse":
        qa.append(
            QAItem(
                question="What was the real reason the gray thing disappeared?",
                answer="A tiny mouse nudged it under the table while chasing crumbs, so the object only looked lost.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What was the real reason the gray thing disappeared?",
                answer="The wind rolled it by the door, so the mystery had a simple, harmless answer.",
            )
        )
    qa.append(
        QAItem(
            question="What changed at the end of the story?",
            answer=f"{hero.id} stopped worrying, {friend.id} apologized or helped explain, and the friends kept playing together with the gray item safely put away.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does it mean to be a friend?",
            answer="A friend is someone who helps, listens, and stays kind even when something goes wrong.",
        ),
        QAItem(
            question="Why do people look carefully in a whodunit?",
            answer="People look carefully because mysteries are solved by noticing small details that other people might miss.",
        ),
        QAItem(
            question="What does gray look like?",
            answer="Gray is a soft color between black and white, like a cloudy sky or a stone.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class ASPParams:
    setting: str
    object_id: str
    suspect: str


ASP_RULES = r"""
setting(S) :- setting_fact(S).
object(O) :- object_fact(O).
suspect(X) :- suspect_fact(X).
compatible(S,O) :- setting(S), object(O), valid_location(S,O).
valid_story(S,O,X) :- compatible(S,O), suspect(X).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for room in setting.rooms:
            lines.append(asp.fact("room", sid, room))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object_fact", oid))
        lines.append(asp.fact("valid_location", next(sid for sid, s in SETTINGS.items() if obj.location in s.rooms or obj.location in {"hall", "porch", "bench", "coat hooks"}), oid))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect_fact", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A lively gray friendship whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-trait")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--friend-trait")
    ap.add_argument("--suspect", choices=list(SUSPECTS))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    if args.setting and args.object_id and not reasonableness_gate(args.setting, args.object_id):
        raise StoryError(explain_rejection(args.setting, args.object_id))
    if args.hero_type is None:
        args.hero_type = rng.choice(["girl", "boy"])
    if args.friend_type is None:
        args.friend_type = "boy" if args.hero_type == "girl" and rng.random() < 0.5 else "girl"
    hero_name = args.hero_name or select_name(args.hero_type, rng)
    friend_name = args.friend_name or select_name(args.friend_type, rng)
    hero_trait = args.hero_trait or "lively"
    friend_trait = args.friend_trait or rng.choice([t for t in TRAITS if t != hero_trait])
    suspect = args.suspect or choose_suspect(rng)
    return StoryParams(
        setting=setting,
        object_id=object_id,
        hero_name=hero_name,
        hero_type=args.hero_type,
        hero_trait=hero_trait,
        friend_name=friend_name,
        friend_type=args.friend_type,
        friend_trait=friend_trait,
        suspect=suspect,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    world = tell(world, params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print("  ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid, oid in valid_combos():
            for suspect in SUSPECTS:
                params = StoryParams(
                    setting=sid,
                    object_id=oid,
                    hero_name="Mia",
                    hero_type="girl",
                    hero_trait="lively",
                    friend_name="Theo",
                    friend_type="boy",
                    friend_trait="kind",
                    suspect=suspect,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

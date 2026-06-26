#!/usr/bin/env python3
"""
A comedy storyworld about a clunky little sound mix-up that turns into a brave
friendship fix.

Seed image:
- A child hears a clunk.
- Someone says a vowel wrong.
- A nearby homerophone-style helper gets misunderstood.
- The joke lands, then the friends help each other and laugh.

The world is intentionally small:
- one setting: the music room
- one confusing sound toy
- one brave friend
- one misunderstanding that can be resolved by speaking clearly and helping

The story is built from live state:
- objects can be loud, tipped, or repaired
- characters can feel puzzled, embarrassed, brave, and friendly
- the ending proves the change by showing the repaired sound and the repaired mood
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
    worn_by: Optional[str] = None
    plural: bool = False
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
class Room:
    name: str
    setting_word: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    can_clunk: bool = False
    can_vowel: bool = False
    can_help: bool = False


@dataclass
class StoryParams:
    room: str
    name: str
    gender: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


ROOMS = {
    "music_room": Room(name="the music room", setting_word="music room", affords={"clunk", "vowel", "homer"}),
}

# A tiny comedy cast.
NAMES_GIRL = ["Mina", "Luna", "Tess", "Ivy", "Maya"]
NAMES_BOY = ["Owen", "Eli", "Noah", "Finn", "Theo"]
FRIEND_NAMES = ["Pip", "Rory", "Bela", "Zed", "Nia"]

# Seed words as domain elements.
PROPS = {
    "clunkbox": Prop(
        id="clunkbox",
        label="clunk box",
        phrase="a bright red clunk box",
        sound="clunk",
        can_clunk=True,
    ),
    "vowelwhistle": Prop(
        id="vowelwhistle",
        label="vowel whistle",
        phrase="a squeaky vowel whistle",
        sound="vowel",
        can_vowel=True,
    ),
    "homer": Prop(
        id="homer",
        label="Homer",
        phrase="a tiny helper named Homer",
        sound="homer",
        can_help=True,
    ),
}

FRIENDSHIP_TAGS = {"friendship", "helping", "kindness"}
BRAVERY_TAGS = {"bravery", "trying", "speaking_up"}
COMEDY_TAGS = {"comedy", "mixup", "silly"}


def room_detail(room: Room) -> str:
    return {
        "music_room": "The music room had a small rug, three stools, and one shelf that always looked ready to wobble.",
    }[room.setting_word]


def activity_delight(name: str) -> str:
    return {
        "clunk": "It sounded so goofy that even the chairs seemed to listen.",
        "vowel": "It made a squeaky sound that felt like a cartoon sneeze.",
        "homer": "It was such a strange little name that it made everyone smile.",
    }.get(name, "It made the room feel extra silly.")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("room", "music_room"),
        asp.fact("affords", "music_room", "clunk"),
        asp.fact("affords", "music_room", "vowel"),
        asp.fact("affords", "music_room", "homer"),
        asp.fact("prop", "clunkbox"),
        asp.fact("prop", "vowelwhistle"),
        asp.fact("prop", "homer"),
        asp.fact("can_clunk", "clunkbox"),
        asp.fact("can_vowel", "vowelwhistle"),
        asp.fact("can_help", "homer"),
        asp.fact("tags", "misunderstanding"),
        asp.fact("tags", "friendship"),
        asp.fact("tags", "bravery"),
        asp.fact("style", "comedy"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_scene(R) :- room(R), affords(R, clunk), affords(R, vowel), affords(R, homer).
comic_mixup :- can_clunk(clunkbox), can_vowel(vowelwhistle), can_help(homer).
"""
def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def validate_reasonableness(room: Room) -> None:
    if not {"clunk", "vowel", "homer"}.issubset(room.affords):
        raise StoryError("This comedy world needs clunk, vowel, and homer in the same room.")


def setup_world(params: StoryParams) -> World:
    room = ROOMS[params.room]
    validate_reasonableness(room)
    world = World(room)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sound": 0.0},
        memes={"curious": 1.0, "brave": 0.2, "puzzled": 0.0, "friendly": 0.5},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="boy",
        meters={"sound": 0.0},
        memes={"friendly": 1.0, "brave": 0.3, "puzzled": 0.0},
    ))
    clunkbox = world.add(Entity(
        id="clunkbox",
        type="thing",
        label="clunk box",
        phrase="a bright red clunk box",
        caretaker=friend.id,
        meters={"tilt": 0.0, "noise": 0.0},
        memes={"attention": 0.2},
    ))
    vowelwhistle = world.add(Entity(
        id="vowelwhistle",
        type="thing",
        label="vowel whistle",
        phrase="a squeaky vowel whistle",
        caretaker=hero.id,
        meters={"noise": 0.0},
        memes={"attention": 0.2},
    ))
    homer = world.add(Entity(
        id="homer",
        type="thing",
        label="Homer",
        phrase="a tiny helper named Homer",
        caretaker=hero.id,
        meters={"help": 0.0, "stump": 0.0},
        memes={"helpful": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, clunkbox=clunkbox, vowelwhistle=vowelwhistle, homer=homer)
    return world


def narrate_setup(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    world.say(f"{h.id} was in {world.room.name}, where the air smelled faintly like paper, dust, and music lessons.")
    world.say(room_detail(world.room))
    world.say(f"{h.id} liked little sounds, because tiny sounds often turned into big laughs.")
    world.say(f"{f.id} was {h.pronoun('possessive')} friend, and {f.id} always stayed near when the room got tricky.")


def do_clunk(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["clunkbox"]
    h.meters["sound"] += 1
    c.meters["noise"] += 1
    c.meters["tilt"] += 1
    h.memes["puzzled"] += 1
    world.say(f"Then the clunk box gave a loud clunk, and {h.id} blinked twice.")
    world.say(f"It was the kind of clunk that made a child look under the table just to be sure the table was okay.")
    world.say(activity_delight("clunk"))


def do_vowel_mixup(world: World) -> None:
    h = world.facts["hero"]
    v = world.facts["vowelwhistle"]
    h.meters["sound"] += 1
    v.meters["noise"] += 1
    h.memes["puzzled"] += 1
    h.memes["embarrassed"] = h.memes.get("embarrassed", 0.0) + 0.5
    world.say(f"Next, the vowel whistle went peep, but {h.id} said the vowel the wrong way on purpose by accident.")
    world.say(f"That only made the sound stranger, so {h.id} and {h.id}'s friend both froze for one funny second.")
    world.say(activity_delight("vowel"))


def do_misunderstanding(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    homer = world.facts["homer"]
    h.memes["misunderstood"] = h.memes.get("misunderstood", 0.0) + 1
    f.memes["misunderstood"] = f.memes.get("misunderstood", 0.0) + 1
    homer.meters["stump"] += 1
    world.say(f"Then Homer rolled in, and everyone misunderstood Homer at once.")
    world.say(f"{h.id} thought Homer had caused the clunk, but Homer only pointed at the whistle with a very tiny, very serious nod.")
    world.say(f"{f.id} nearly laughed, because Homer looked like a librarian for birds.")


def do_bravery_and_fix(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    c = world.facts["clunkbox"]
    v = world.facts["vowelwhistle"]
    homer = world.facts["homer"]
    h.memes["brave"] += 1
    f.memes["brave"] += 1
    h.memes["misunderstood"] = 0.0
    f.memes["misunderstood"] = 0.0
    c.meters["tilt"] = 0.0
    c.meters["noise"] = 0.0
    v.meters["noise"] = 0.0
    homer.meters["help"] += 1
    world.say(f"After that, {h.id} took a brave breath and said, 'Wait. I think I mixed up the sounds.'")
    world.say(f"{f.id} grinned and helped steady the clunk box while Homer pointed at the right button.")
    world.say("The room made one last clunk, then a clean vowel sound, and then everybody laughed because the mystery had been smaller than a shoebox.")


def ending_image(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    homer = world.facts["homer"]
    world.say(f"In the end, the clunk box stood straight, the vowel whistle sounded clear, and Homer got a grateful pat on the top.")
    world.say(f"{h.id} and {f.id} were smiling so hard that even the rug seemed cheerful.")
    world.say(f"The funny mix-up was gone, and the friendship was louder than the clunk.")


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    narrate_setup(world)
    world.para()
    do_clunk(world)
    do_vowel_mixup(world)
    do_misunderstanding(world)
    world.para()
    do_bravery_and_fix(world)
    ending_image(world)
    return world


def generation_prompts(world: World) -> list[str]:
    h = world.facts["hero"]
    f = world.facts["friend"]
    return [
        f"Write a short comedy story for a child where {h.id} hears a clunk, says a vowel wrong, and learns to be brave.",
        f"Tell a funny friendship story in the music room where {h.id} and {f.id} fix a misunderstanding with help from Homer.",
        "Write a child-friendly comedy about a clunky sound, a vowel mistake, and a brave apology that ends in laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    f = world.facts["friend"]
    return [
        QAItem(
            question=f"Where did {h.id} and {f.id} have their silly mix-up?",
            answer=f"They had it in the music room, where little sounds could bounce around and become funny very fast.",
        ),
        QAItem(
            question=f"What first made everyone look around in surprise?",
            answer="The clunk box made a loud clunk first, so everyone thought something important had happened.",
        ),
        QAItem(
            question=f"Why did the vowel whistle make the scene even sillier?",
            answer="Because the vowel sound came out wrong, which made the mistake feel extra funny and extra confusing.",
        ),
        QAItem(
            question=f"How did Homer help solve the misunderstanding?",
            answer="Homer pointed at the right button and the right sound, which helped everyone see that the mix-up was just a silly mistake.",
        ),
        QAItem(
            question=f"What brave thing did {h.id} do at the end?",
            answer=f"{h.id} admitted the mistake out loud and asked for help, which was a brave and friendly thing to do.",
        ),
        QAItem(
            question=f"How did the story end for {h.id} and {f.id}?",
            answer=f"They ended up smiling and laughing together, because the clunk box and vowel whistle were both fixed and the misunderstanding was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clunk?",
            answer="A clunk is a heavy, dull sound, like something knocking or bumping into place.",
        ),
        QAItem(
            question="What is a vowel?",
            answer="A vowel is a speech sound like a, e, i, o, or u, and words use vowels to help make them easy to say.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and staying kind even when things get funny or hard.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something important even when you feel nervous, like admitting a mistake or asking for help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_scene/1.\n#show comic_mixup/0."))
    atoms = set((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)) for sym in model)
    expected = {("valid_scene", ("music_room",)), ("comic_mixup", ())}
    if atoms == expected:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP gate did not match expectations.")
    print("ASP atoms:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about clunk, vowel, homer, misunderstanding, friendship, and bravery.")
    ap.add_argument("--room", choices=ROOMS.keys(), default="music_room")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--friend")
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
    room = args.room
    name = args.name
    gender = args.gender
    if gender is None:
        gender = rng.choice(["girl", "boy"])
    if name is None:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    if friend == name:
        raise StoryError("The friend must be a different character from the hero.")
    return StoryParams(room=room, name=name, gender=gender, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_scene/1.\n#show comic_mixup/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_scene/1.\n#show comic_mixup/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(room="music_room", name="Mina", gender="girl", friend="Pip"),
            StoryParams(room="music_room", name="Owen", gender="boy", friend="Rory"),
            StoryParams(room="music_room", name="Tess", gender="girl", friend="Bela"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

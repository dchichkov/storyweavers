#!/usr/bin/env python3
"""
storyworlds/worlds/artistic_lesson_learned_bravery_detective_story.py
======================================================================

A standalone storyworld for a small detective-style tale about an artistic clue,
bravery, and a lesson learned.

Premise:
A child detective follows a trail of art-room clues to find a missing picture.
The trail looks scary at first, but brave, careful thinking solves the mystery.
The ending proves the lesson: asking for help and checking details is braver
than rushing into the dark.

This world is intentionally compact: fewer moving parts, but every story is
state-driven, with typed entities, physical meters, and emotional memes.
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
BRAVERY_MIN = 2.0


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
class Setting:
    id: str
    place: str
    dark_spot: str
    clue_spot: str
    mood: str


@dataclass
class Clue:
    id: str
    label: str
    place_phrase: str
    reveals: str
    artistic: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    text: str
    method: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["mystery"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.entities.values():
        if kid.role in {"detective", "helper"}:
            kid.memes["unease"] += 1
            kid.memes["bravery"] += 1
    out.append("__fear__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    rules = [Rule("fear", _r_fear)]
    while changed:
        changed = False
        for rule in rules:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_risky(clue: Clue, setting: Setting) -> bool:
    return clue.artistic and "dark" in setting.mood


def sensible_lesson() -> list[Lesson]:
    return [l for l in LESSONS.values() if l.sense >= BRAVERY_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for lid, lesson in LESSONS.items():
                if clue_risky(clue, setting) and lesson.sense >= BRAVERY_MIN:
                    combos.append((sid, cid, lid))
    return combos


def predict_mystery(world: World, clue_id: str) -> dict:
    sim = world.copy()
    _follow_clue(sim, sim.get(clue_id), narrate=False)
    return {
        "mystery": sim.get("room").meters["mystery"],
        "found": bool(sim.facts.get("found")),
    }


def _follow_clue(world: World, clue: Entity, narrate: bool = True) -> None:
    clue.meters["noticed"] += 1
    world.get("room").meters["mystery"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"On a quiet afternoon, {detective.id} and {helper.id} were in {setting.place}, "
        f"where {setting.mood} air made every shadow look like a secret."
    )
    world.say(
        f"{detective.id} was a small detective with an {setting.id} way of noticing details, "
        f"and {helper.id} kept the notebook ready."
    )


def case_opener(world: World, detective: Entity, clue: Entity, setting: Setting) -> None:
    world.say(
        f"Then they found {clue.place_phrase}. It looked ordinary, but it was the first clue "
        f"to the missing picture."
    )
    world.say(
        f"{detective.id} squinted at it. '{clue.label.capitalize()}' {detective.pronoun()} said, "
        f"'{clue.reveals}'"
    )


def warn(world: World, helper: Entity, detective: Entity, clue: Entity) -> None:
    pred = predict_mystery(world, "clue")
    helper.memes["bravery"] += 1
    world.facts["predicted_mystery"] = pred["mystery"]
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip. 'We should be careful,' "
        f"{helper.pronoun()} said. 'That clue feels artistic, and the room is getting stranger.'"
    )


def act_brave(world: World, detective: Entity) -> None:
    detective.memes["bravery"] += 1
    world.say(
        f"{detective.id} took a deep breath. Even with a spooky shadow nearby, "
        f"{detective.pronoun()} kept looking instead of running away."
    )


def find_picture(world: World, detective: Entity, helper: Entity) -> None:
    world.facts["found"] = True
    world.get("room").meters["mystery"] = 0.0
    world.say(
        f"Together, they followed the clue to a small art shelf, behind a stack of bright paper."
    )
    world.say(
        f"Under a cloth sat the missing painting -- a colorful, artistic picture with a blue moon "
        f"and a red kite."
    )


def lesson(world: World, helper: Entity, detective: Entity, lesson_def: Lesson) -> None:
    detective.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"'{lesson_def.text}' {helper.pronoun()} said softly. "
        f"'{lesson_def.method}, and that was the brave way to solve it.'"
    )
    world.say(
        f"{detective.id} nodded. {detective.pronoun().capitalize()} had learned that bravery "
        f"could mean slowing down, checking clues, and asking for help."
    )


def ending_image(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f"By the end, the shelf was neat again, the painting was safe, and the two detectives "
        f"stood side by side with their notebook closed and their hearts steady."
    )
    world.say(
        f"{detective.id} smiled at {helper.id}. The mystery was solved, and the brave little "
        f"investigation had turned into a lesson learned."
    )


SETTINGS = {
    "studio": Setting(
        id="studio",
        place="the little art studio",
        dark_spot="the corner behind the canvas rack",
        clue_spot="under a paint-stained table",
        mood="dim and sleepy",
    ),
    "museum": Setting(
        id="museum",
        place="the quiet museum room",
        dark_spot="the hall by the tall frames",
        clue_spot="behind a folded display sign",
        mood="soft and echoing",
    ),
    "attic": Setting(
        id="attic",
        place="the dusty attic",
        dark_spot="the space under the rafters",
        clue_spot="inside a wicker box",
        mood="dark and creaky",
    ),
}

CLUES = {
    "painted_note": Clue(
        id="painted_note",
        label="a painted note",
        place_phrase="a painted note tucked near the easel",
        reveals="The note says the picture was moved, not lost.",
        artistic=True,
        tags={"artistic", "paint"},
    ),
    "color_strip": Clue(
        id="color_strip",
        label="a strip of color",
        place_phrase="a strip of red paper on the floor",
        reveals="The color points toward the art shelf.",
        artistic=True,
        tags={"artistic", "color"},
    ),
    "frame_tag": Clue(
        id="frame_tag",
        label="a frame tag",
        place_phrase="a tiny tag hanging from an old frame",
        reveals="The tag points to the place where the picture was kept safe.",
        artistic=False,
        tags={"frame"},
    ),
}

LESSONS = {
    "ask_for_help": Lesson(
        id="ask_for_help",
        text="Asking for help is brave",
        method="They asked the helper to read the clue out loud",
        power=3,
        sense=3,
        tags={"help", "bravery"},
    ),
    "slow_and_look": Lesson(
        id="slow_and_look",
        text="Slowing down can solve a mystery",
        method="They stopped, looked carefully, and followed the clue one step at a time",
        power=3,
        sense=4,
        tags={"bravery", "careful"},
    ),
    "check_details": Lesson(
        id="check_details",
        text="Little details can lead to the answer",
        method="They checked the colors, the paper, and the shelf before guessing",
        power=2,
        sense=2,
        tags={"artistic", "details"},
    ),
}

DETECTIVE_NAMES = ["Mia", "Nora", "Leo", "Ava", "Theo", "Lily", "Ben", "Zoe"]
HELPER_NAMES = ["Mum", "Dad", "Sam", "Ivy", "Jae", "Noah"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    lesson: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="studio",
        clue="painted_note",
        lesson="slow_and_look",
        detective="Mia",
        detective_gender="girl",
        helper="Mum",
        helper_gender="woman",
    ),
    StoryParams(
        setting="museum",
        clue="color_strip",
        lesson="ask_for_help",
        detective="Leo",
        detective_gender="boy",
        helper="Dad",
        helper_gender="man",
    ),
    StoryParams(
        setting="attic",
        clue="frame_tag",
        lesson="check_details",
        detective="Ava",
        detective_gender="girl",
        helper="Sam",
        helper_gender="man",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    clue = f["clue"]
    return [
        f'Write a detective story for a young child set in {setting.place} that uses the word "artistic".',
        f"Tell a brave little mystery where {f['detective'].id} follows {clue.label} and learns a lesson.",
        f"Write a gentle detective story about a missing picture, careful clues, and bravery in {setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    setting = f["setting"]
    lesson_def = f["lesson_def"]
    qa = [
        QAItem(
            question=f"Who were the detectives in {setting.place}?",
            answer=f"It was {det.id} and {helper.id}. They worked together to solve the mystery and keep each other brave.",
        ),
        QAItem(
            question=f"What clue did {det.id} find?",
            answer=f"{det.id} found {clue.place_phrase}. It seemed small, but it pointed them toward the missing picture.",
        ),
        QAItem(
            question=f"Why did {helper.id} tell {det.id} to be careful?",
            answer=f"{helper.id} noticed the room felt stranger and darker. The clue was artistic, and the mystery could not be solved by rushing.",
        ),
    ]
    if world.facts.get("found"):
        qa.append(
            QAItem(
                question="What did the detectives discover at the end?",
                answer="They found the missing painting on the art shelf. It was safe under a cloth, and the search turned into a lesson learned.",
            )
        )
        qa.append(
            QAItem(
                question="What brave thing did the detective do?",
                answer=f"{det.id} kept looking instead of running away. That courage helped them solve the mystery the careful way.",
            )
        )
        qa.append(
            QAItem(
                question="What lesson did they learn?",
                answer=f"They learned that {lesson_def.text.lower()}. That made the ending calm and proud instead of scared.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["lesson_def"].tags)
    out = []
    if "artistic" in tags:
        out.append(QAItem(
            question="What does artistic mean?",
            answer="Artistic means made with art or having to do with art. It can mean something colorful, creative, or made by drawing and painting.",
        ))
    if "bravery" in tags:
        out.append(QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary anyway. A brave person can stay calm and keep trying.",
        ))
    out.append(QAItem(
        question="Why do detectives look for clues?",
        answer="Detectives look for clues because clues help them figure out what happened. Small details can lead to the answer.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(setting: Setting, clue: Clue, lesson_def: Lesson,
         detective_name: str = "Mia", detective_gender: str = "girl",
         helper_name: str = "Mum", helper_gender: str = "woman") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        attrs={"setting": setting.id},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=setting.place,
    ))
    clue_ent = world.add(Entity(
        id="clue",
        type="clue",
        label=clue.label,
        tags=set(clue.tags),
    ))
    clue_ent.attrs["place_phrase"] = clue.place_phrase

    detective.memes["bravery"] = 1.0
    helper.memes["bravery"] = 1.0
    room.meters["mystery"] = 0.0
    world.facts["found"] = False

    setup(world, detective, helper, setting)
    world.para()
    case_opener(world, detective, clue, setting)
    warn(world, helper, detective, clue)
    act_brave(world, detective)

    world.para()
    _follow_clue(world, clue_ent)
    find_picture(world, detective, helper)
    lesson(world, helper, detective, lesson_def)
    world.para()
    ending_image(world, detective, helper)

    world.facts.update(
        setting=setting,
        clue=clue,
        lesson_def=lesson_def,
        detective=detective,
        helper=helper,
        room=room,
    )
    return world


def valid_story(params: StoryParams) -> bool:
    return clue_risky(CLUES[params.clue], SETTINGS[params.setting]) and LESSONS[params.lesson].sense >= BRAVERY_MIN


def explain_rejection(setting: Setting, clue: Clue, lesson_def: Lesson) -> str:
    if not clue_risky(clue, setting):
        return "(No story: this clue does not create enough mystery for a detective-style turn.)"
    if lesson_def.sense < BRAVERY_MIN:
        return "(No story: the lesson is too weak for the brave ending this world wants.)"
    return "(No story: this combination is not reasonable.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.clue and args.lesson:
        setting = SETTINGS[args.setting]
        clue = CLUES[args.clue]
        lesson_def = LESSONS[args.lesson]
        if not valid_story(StoryParams(
            setting=args.setting,
            clue=args.clue,
            lesson=args.lesson,
            detective="Mia",
            detective_gender="girl",
            helper="Mum",
            helper_gender="woman",
        )):
            raise StoryError(explain_rejection(setting, clue, lesson_def))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.lesson is None or c[2] == args.lesson)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, clue_id, lesson_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper_gender = rng.choice(["woman", "man"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting_id,
        clue=clue_id,
        lesson=lesson_id,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.lesson not in LESSONS:
        raise StoryError("Invalid story parameters.")
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        LESSONS[params.lesson],
        params.detective,
        params.detective_gender,
        params.helper,
        params.helper_gender,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective storyworld about artistic clues, bravery, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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


ASP_RULES = r"""
risky(S,C) :- setting(S), clue(C), artistic(C), dark_setting(S).
good(L) :- lesson(L), sense(L,S), sense_min(M), S >= M.
valid(S,C,L) :- risky(S,C), good(L).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", BRAVERY_MIN)]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.artistic:
            lines.append(asp.fact("artistic", cid))
    for lid, lesson_def in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("sense", lid, lesson_def.sense))
    for sid in {"studio", "museum", "attic"}:
        lines.append(asp.fact("dark_setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def asp_list() -> None:
    combos = asp_valid_combos()
    print(f"{len(combos)} compatible (setting, clue, lesson) combos:")
    for setting, clue, lesson in combos:
        print(f"  {setting:8} {clue:14} {lesson}")


def generate_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def tell_story(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

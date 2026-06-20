#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py
==============================================================================

A standalone story world for a tiny bedtime tale: a child cannot settle down,
keeps repeating the same sleepy words, and a small "dingbat" toy or trinket
turns out to be the missing piece that helps the room become calm again.

The world is built for child-facing bedtime-story prose:
- dialogue carries the action,
- repetition marks the sleepy spiral,
- physical state and emotional state both change,
- the ending image proves the room is quieter and safer than it was.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/dingbat_dialogue_repetition_bedtime_story.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class BedtimeSetting:
    id: str
    room: str
    light: str
    hush: str
    bed: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Dingbat:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    description: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class RepetitionCue:
    id: str
    line: str
    count: int
    emotional_shift: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    parent_type: str
    dingbat: str
    cue: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "nursery": BedtimeSetting(
        "nursery",
        "the nursery",
        "a small lamp",
        "soft and hush-hush",
        "a snug little bed",
        "the lamp glowed low and the blanket sat smooth and still",
    ),
    "bedroom": BedtimeSetting(
        "bedroom",
        "the bedroom",
        "a moon lamp",
        "warm and sleepy",
        "a cozy bed",
        "the moon lamp made a pale little puddle of light on the wall",
    ),
    "attic_room": BedtimeSetting(
        "attic_room",
        "the attic room",
        "a tiny night-light",
        "quiet as a feather",
        "a high tucked-in bed",
        "the night-light blinked once and the whole room looked drowsy",
    ),
}

DINGBATS = {
    "toy": Dingbat("toy", "dingbat toy", "the dingbat toy", "under the pillow", "a tiny plush dingbat with one floppy wing", {"toy", "dingbat"}),
    "bell": Dingbat("bell", "dingbat bell", "the dingbat bell", "on the windowsill", "a little bedtime bell that made a soft ting", {"bell", "dingbat"}),
    "star": Dingbat("star", "dingbat star", "the dingbat star", "in the blanket fold", "a shiny paper star with a cheerful grin", {"star", "dingbat"}),
}

CUES = {
    "repeat_sleepy": RepetitionCue(
        "repeat_sleepy",
        '"I am sleepy," {child} said. "I am sleepy, I am sleepy."',
        2,
        "sleepier",
        {"repetition", "sleepy"},
    ),
    "repeat_water": RepetitionCue(
        "repeat_water",
        '"One more sip," {child} said. "One more sip, one more sip."',
        2,
        "calmer",
        {"repetition", "water"},
    ),
    "repeat_story": RepetitionCue(
        "repeat_story",
        '"One more story," {child} said. "One more story, one more story."',
        2,
        "cozier",
        {"repetition", "story"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ella", "Ivy", "June", "Rose", "Lily"]
BOY_NAMES = ["Theo", "Finn", "Max", "Eli", "Noah", "Ben", "Owen", "Jack"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, d, c) for s in SETTINGS for d in DINGBATS for c in CUES]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with dialogue and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--dingbat", choices=DINGBATS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.dingbat is None or c[1] == args.dingbat)
              and (args.cue is None or c[2] == args.cue)]
    if not combos:
        raise StoryError("(No valid bedtime-story combination matches the given options.)")
    setting, dingbat, cue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, child_name, gender, parent, dingbat, cue)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["sleep"] >= THRESHOLD and ("sleep", ent.id) not in world.fired:
            world.fired.add(("sleep", ent.id))
            ent.meters["rest"] += 1
            out.append("__sleep__")
    if narrate:
        for s in out:
            if s != "__sleep__":
                world.say(s)
    return out


def tell(setting: BedtimeSetting, dingbat: Dingbat, cue: RepetitionCue,
         child_name: str, child_gender: str, parent_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    toy = world.add(Entity(id="dingbat", type="thing", label=dingbat.label))
    child.memes["tired"] = 1.0
    child.memes["sleep"] = 0.0
    child.memes["comfort"] = 0.0
    world.facts["setting"] = setting
    world.facts["dingbat"] = dingbat
    world.facts["cue"] = cue
    world.facts["child"] = child
    world.facts["parent"] = parent

    world.say(f"At bedtime, {child_name} climbed into {setting.bed} in {setting.room}.")
    world.say(f"{parent.label_word.capitalize()} dimmed {setting.light}, and the room felt {setting.hush}.")
    world.say(f"{child_name} reached for {dingbat.phrase}. It was {dingbat.description}.")
    world.say(f'"Good night, little dingbat," {child_name} whispered, and the whisper made the room feel even softer.')

    world.para()
    world.say(cue.line.format(child=child_name))
    child.memes["repeat"] += cue.count
    child.memes["worry"] += 1
    world.say(f'"Good night, little dingbat," {child_name} said again. "Good night, good night."')
    world.say(f"{parent.label_word.capitalize()} smiled and listened. The same words came back like a tiny lullaby.")

    world.para()
    if dingbat.id == "toy":
        toy.meters["hidden"] += 1
        world.say(f"Then {child_name} noticed the dingbat toy was gone from under the pillow.")
        world.say(f'"My dingbat," {child_name} said. "My dingbat, my dingbat."')
        world.say(f"{parent.label_word.capitalize()} knelt down, lifted the blanket, and found it tucked under the pillow at last.")
    elif dingbat.id == "bell":
        toy.meters["hidden"] += 1
        world.say(f"Then the dingbat bell gave one tiny sound from the windowsill.")
        world.say(f'"There you are," {child_name} said. "There you are, there you are."')
        world.say(f"{parent.label_word.capitalize()} moved it to the shelf beside the bed, where it could rest and stay quiet.")
    else:
        toy.meters["hidden"] += 1
        world.say(f"Then {child_name} remembered the dingbat star was hiding in the blanket fold.")
        world.say(f'"My star," {child_name} said. "My star, my star."')
        world.say(f"{parent.label_word.capitalize()} smoothed the blanket and set the shiny star on the bedside table.")

    child.memes["comfort"] += 1
    child.memes["sleep"] += 2
    propagate(world, narrate=False)

    world.para()
    world.say(f'"Now," {parent.label_word.capitalize()} whispered, "the dingbat is safe, the bed is warm, and the room is quiet."')
    world.say(f'{child_name} hugged {dingbat.label} close and yawned a long, round yawn.')
    world.say(f"Again and again, the last little words went softer and softer: \"Good night, little dingbat.\"")
    world.say(f"And at the end, {setting.ending_image}, while {child_name} drifted off with {dingbat.label} tucked in close.")

    world.facts["toy"] = toy
    world.facts["ending"] = setting.ending_image
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dingbat = f["dingbat"]
    cue = f["cue"]
    return [
        f'Write a bedtime story for a young child that includes the word "dingbat" and uses dialogue and repetition.',
        f"Tell a sleepy story where {child.id} keeps repeating a phrase at bedtime until {dingbat.label} is found and the room settles down.",
        f"Write a gentle bedtime tale in which someone says {cue.line.split(',')[0].strip()!r} and the ending feels calm and cozy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    dingbat = f["dingbat"]
    cue = f["cue"]
    setting = f["setting"]
    toy = f["toy"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {parent.label_word}, at bedtime in {setting.room}. The story follows the small sleepy problem and how they fixed it together."
        ),
        QAItem(
            question="What kept getting repeated?",
            answer=f"The words about the dingbat kept coming back again and again. {cue.line.format(child=child.id)} became a little repeating bedtime refrain, which showed how sleepy and focused {child.id} was."
        ),
        QAItem(
            question="What happened when they looked for the dingbat?",
            answer=f"They found that {dingbat.label} had been hiding nearby, and that made {child.id} feel comforted. Once it was found and put where it belonged, the room could grow quiet and {child.id} could rest."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    dingbat = f["dingbat"]
    qa = [
        QAItem(
            question="What does bedtime mean?",
            answer="Bedtime is the time to slow down, get cozy, and get ready for sleep. People usually dim the lights, use soft voices, and settle into bed."
        ),
        QAItem(
            question="Why can repeating words feel soothing?",
            answer="Repeating the same words can feel soothing because the pattern is familiar and calm. It can help a sleepy child settle their thoughts and relax."
        ),
    ]
    if "dingbat" in dingbat.tags:
        qa.append(
            QAItem(
                question="What is a dingbat in this story?",
                answer="In this story, a dingbat is a small bedtime treasure with a funny name. It is not a problem; it is a tiny comforting thing that helps the child feel settled."
            )
        )
    return qa


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, D, C) :- setting(S), dingbat(D), cue(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for d in DINGBATS:
        lines.append(asp.fact("dingbat", d))
    for c in CUES:
        lines.append(asp.fact("cue", c))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, dingbat=None, cue=None, name=None, gender=None, parent=None), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generated story is empty.")
        rc = 1
    return rc


CURATED = [
    StoryParams("nursery", "Mia", "girl", "mother", "toy", "repeat_sleepy"),
    StoryParams("bedroom", "Theo", "boy", "father", "bell", "repeat_story"),
    StoryParams("attic_room", "Luna", "girl", "mother", "star", "repeat_water"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DINGBATS[params.dingbat], CUES[params.cue], params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    dingbat = args.dingbat or rng.choice(sorted(DINGBATS))
    cue = args.cue or rng.choice(sorted(CUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, name, gender, parent, dingbat, cue)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

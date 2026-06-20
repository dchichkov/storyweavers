#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/photo_descendant_volcano_repetition_happy_ending_adventure.py
=============================================================================================

A standalone storyworld for a tiny adventure about a child, an old photo, and a
descendant's clue near a volcano.  The world is built around repetition, a
hazardous choice, and a happy ending: the characters follow the same clue
again and again, make it safely to the top, and discover that the descendant's
photo was really a map to a family treasure.

The core domain:
- an old photo shows a marked trail
- a descendant wants to prove they can climb the volcano
- the climb becomes risky when they wander too close to hot steam
- a steady helper repeats the safety rule and guides them to a better route
- they reach the lookout, take a new photo, and end happily

The story is generated from simulated state, not from a frozen paragraph.
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
CAUTION_MIN = 1.0
RISK_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma",
                "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Setting:
    id: str
    name: str
    view: str
    repeated_phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Hazard:
    id: str
    label: str
    phrase: str
    hot: bool = True
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class GuideMove:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    volcano = world.entities.get("volcano")
    child = world.entities.get("descendant")
    if not volcano or not child:
        return out
    if child.meters["too_close"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    volcano.meters["danger"] += 1
    child.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("descendant")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if child.meters["safe_route"] < THRESHOLD:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] += 1
    guide.memes["pride"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("risk", "physical", _r_risk), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(hazard: Hazard) -> bool:
    return hazard.hot and hazard.risky


def sensible_moves() -> list[GuideMove]:
    return [m for m in GUIDE_MOVES.values() if m.sense >= CAUTION_MIN]


def outcome_of(params: "StoryParams") -> str:
    return "happy"


def setup(world: World, child: Entity, guide: Entity, setting: Setting, photo: Artifact) -> None:
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    guide.memes["care"] += 1
    world.say(
        f"On a bright morning, {child.id} and {guide.id} started up the trail to {setting.name}. "
        f"{setting.view} The old {photo.label} was tucked safely in {child.pronoun('possessive')} pocket."
    )
    world.say(
        f'The picture showed the same clue again and again: "{setting.repeated_phrase}" '
        f'It felt like a family secret waiting to be found.'
    )


def repeat_clue(world: World, setting: Setting, photo: Artifact) -> None:
    world.say(
        f'{setting.repeated_phrase} the photo said. {setting.repeated_phrase} the guide repeated. '
        f'{setting.repeated_phrase} the path seemed to whisper back.'
    )


def discover(world: World, child: Entity, photo: Artifact, setting: Setting) -> None:
    child.memes["excitement"] += 1
    world.say(
        f"{child.id} pointed at the mark on the {photo.label}. "
        f'It matched the stones beside the path, and the trail curved toward the volcano lookout.'
    )


def tempt(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["boldness"] += 1
    world.say(
        f"{child.id} wanted to climb closer to the {hazard.label}, because the steam looked brave and exciting."
    )


def warn(world: World, guide: Entity, child: Entity, hazard: Hazard, setting: Setting) -> None:
    child.memes["warning"] += 1
    world.say(
        f'"{setting.repeated_phrase}," {guide.id} said, pointing to the safe stones. '
        f'"Stay on the path. Hot steam can hide a hard drop near the {hazard.label}."'
    )


def hesitate(world: World, child: Entity) -> None:
    child.meters["too_close"] += 1
    world.say(f"{child.id} stopped short and looked at the steaming rock wall.")
    world.say(f"The clue was still there, but the risky edge was right beside it.")


def choose_safe(world: World, guide: Entity, child: Entity, move: GuideMove) -> None:
    child.meters["safe_route"] += 1
    child.memes["trust"] += 1
    world.say(move.text)
    world.say(
        f"{child.id} listened, stepped back, and found the safe bend in the trail instead."
    )


def finish(world: World, child: Entity, guide: Entity, photo: Artifact, setting: Setting) -> None:
    child.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"At the lookout, they found a little stone chest under the sign. Inside was a bright shell and a note from a descendant long ago."
    )
    world.say(
        f'{child.id} lifted the {photo.label} again and took a new picture of the view. '
        f'{setting.repeated_phrase} had led them to the right place all along.'
    )
    world.say(
        f"They laughed, waved at the open sky, and walked home with the treasure, happy and safe."
    )


def tell(setting: Setting, hazard: Hazard, photo: Artifact, move: GuideMove,
         child_name: str = "Mina", child_gender: str = "girl",
         guide_name: str = "Grandma", guide_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="descendant"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender,
                             role="guide"))
    volcano = world.add(Entity(id="volcano", kind="thing", type="volcano",
                               label=hazard.label))
    world.add(Entity(id="photo", kind="thing", type="photo", label=photo.label))

    setup(world, child, guide, setting, photo)
    world.para()
    repeat_clue(world, setting, photo)
    discover(world, child, photo, setting)
    tempt(world, child, hazard)
    warn(world, guide, child, hazard, setting)
    hesitate(world, child)
    world.para()
    choose_safe(world, guide, child, move)
    propagate(world, narrate=False)
    world.para()
    finish(world, child, guide, photo, setting)

    world.facts.update(
        child=child,
        guide=guide,
        volcano=volcano,
        photo=photo,
        setting=setting,
        hazard=hazard,
        move=move,
        outcome="happy",
        safe=True,
    )
    return world


SETTINGS = {
    "ridge": Setting(
        "ridge", "the mountain ridge",
        "The ridge opened into a wide sky, and the path climbed in a gentle zigzag.",
        "follow the red stones",
        tags={"adventure", "photo", "repetition"},
    ),
    "trail": Setting(
        "trail", "the lava trail",
        "The trail twisted between black rocks, and distant birds circled overhead.",
        "keep to the silver path",
        tags={"adventure", "photo", "repetition"},
    ),
    "viewpoint": Setting(
        "viewpoint", "the lookout hill",
        "The lookout hill stood above the trees, and the air smelled warm and clean.",
        "walk toward the carved mark",
        tags={"adventure", "photo", "repetition"},
    ),
}

HAZARDS = {
    "steam": Hazard("steam", "volcano steam", "hot steam rising from cracks", True, True,
                    tags={"volcano"}),
    "rocks": Hazard("rocks", "volcano rocks", "sharp rocks near the rim", True, True,
                    tags={"volcano"}),
}

PHOTO_CLUES = {
    "old_photo": Artifact("old_photo", "photo", "old photo", "a faded photo with a red arrow",
                          tags={"photo"}),
    "map_photo": Artifact("map_photo", "photo", "photo", "a photo of the trail markers",
                          tags={"photo"}),
}

GUIDE_MOVES = {
    "repeat": GuideMove("repeat", 2, 2,
                        "They followed the marked stones, then the next marked stones, then the next until the path widened.",
                        "They repeated the safe rule until they reached the right bend.",
                        tags={"repetition"}),
    "back_up": GuideMove("back_up", 2, 2,
                         "The guide asked for one step back, then another, then a careful turn to the side.",
                         "Stepping back kept them away from the dangerous edge.",
                         tags={"repetition"}),
    "look_again": GuideMove("look_again", 2, 2,
                            "Together they looked again at the photo, then again at the rocks, until the safer path made sense.",
                            "Looking again helped them choose the safer path.",
                            tags={"photo", "repetition"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    photo: str
    move: str
    child_name: str
    child_gender: str
    guide_name: str
    guide_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid, hz in HAZARDS.items():
            for pid in PHOTO_CLUES:
                if hazard_at_risk(hz):
                    combos.append((sid, hid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "photo" and "volcano" and uses repetition.',
        f"Tell a happy-ending climbing story where {f['child'].id} follows a photo clue near a volcano and a guide repeats the safety rule.",
        f'Write a family adventure about a descendant and an old photo, with a repeated clue and a safe ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide = f["child"], f["guide"]
    setting, hazard, move = f["setting"], f["hazard"], f["move"]
    photo = f["photo"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {guide.id}, who climbed toward {setting.name} together. The child is a descendant following an old family clue."),
        ("What did the old photo show?",
         f"It showed a repeated clue that pointed toward the trail: {setting.repeated_phrase}. That clue helped them keep going in the right direction."),
        ("Why did the guide tell them to slow down?",
         f"The guide saw hot steam and sharp edges near the {hazard.label}. Repeating the safety rule kept the child away from the risky spot."),
        ("How did they solve the problem?",
         f"They used the safer move: {move.qa_text} That let them keep the adventure without getting too close to danger."),
        ("How did the story end?",
         f"It ended happily at the lookout, where they found a small treasure and took a new photo. The family clue led to a safe and joyful ending."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["setting"].tags) | set(f["photo"].tags) | set(f["hazard"].tags) | set(f["move"].tags)
    out: list[tuple[str, str]] = []
    if "photo" in tags:
        out.append(("What is a photo?",
                     "A photo is a picture made with a camera. It can help you remember a place, a face, or a clue."))
    if "volcano" in tags:
        out.append(("What is a volcano?",
                     "A volcano is a mountain that can have hot rock, steam, or lava inside it. People stay careful around it."))
    if "repetition" in tags:
        out.append(("What does repetition mean?",
                     "Repetition means saying or doing something again and again. In stories, repetition can make a clue easy to remember."))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ridge", "steam", "old_photo", "repeat", "Mina", "girl", "Grandma", "woman"),
    StoryParams("trail", "rocks", "map_photo", "look_again", "Eli", "boy", "Grandpa", "man"),
]


ASP_RULES = r"""
hazard(H) :- hot(H), risky(H).
safe_move(M) :- move(M), sense(M, S), sense_min(Min), S >= Min.
valid_story(S, H, P, M) :- setting(S), hazard(H), photo(P), move(M), hazard(H), safe_move(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hz.hot:
            lines.append(asp.fact("hot", hid))
        if hz.risky:
            lines.append(asp.fact("risky", hid))
    for pid in PHOTO_CLUES:
        lines.append(asp.fact("photo", pid))
    for mid, mv in GUIDE_MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, mv.sense))
    lines.append(asp.fact("sense_min", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((a, b, c, d) for a, b, c in valid_combos() for d in GUIDE_MOVES):
        print("OK: ASP validity available.")
    else:
        rc = 1
        print("MISMATCH in ASP validity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: photo, descendant, volcano, repetition, happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--photo", choices=PHOTO_CLUES)
    ap.add_argument("--move", choices=GUIDE_MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "child"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-gender", choices=["woman", "man", "person"])
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
    if args.move and args.move not in GUIDE_MOVES:
        raise StoryError("Unknown move.")
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    photo = args.photo or rng.choice(list(PHOTO_CLUES))
    move = args.move or rng.choice(list(GUIDE_MOVES))
    child_name = args.child_name or rng.choice(["Mina", "Eli", "Aria", "Noah", "Luna"])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    guide_name = args.guide_name or rng.choice(["Grandma", "Grandpa", "Auntie", "Uncle"])
    guide_gender = args.guide_gender or rng.choice(["woman", "man"])
    return StoryParams(setting, hazard, photo, move, child_name, child_gender, guide_name, guide_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], PHOTO_CLUES[params.photo], GUIDE_MOVES[params.move],
                 params.child_name, params.child_gender, params.guide_name, params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

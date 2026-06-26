#!/usr/bin/env python3
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
    hidden: bool = False
    carried_by: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Suspect:
    id: str
    name: str
    type: str
    habit: str
    funny_tell: str


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    clue: str
    owner: str


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


SETTINGS = {
    "library": Setting(place="the library", mood="quiet", clues=["dust", "footprints", "whisper"]),
    "museum": Setting(place="the museum", mood="curious", clues=["glove", "smudge", "map"]),
    "kitchen": Setting(place="the kitchen", mood="busy", clues=["crumb", "spoon", "laugh"]),
    "garden": Setting(place="the garden", mood="moonlit", clues=["petal", "ladder", "lantern"]),
}

SUSPECTS = [
    Suspect("cat", "Milo the cat", "cat", "stole snacks", "one whisker always looked guilty"),
    Suspect("parrot", "Polly the parrot", "bird", "hid shiny things", "repeated clues in a squeaky voice"),
    Suspect("mouse", "Nip the mouse", "mouse", "borrowed buttons", "had tiny muddy shoes"),
    Suspect("robot", "Rusty the robot", "robot", "sorted everything", "left little gear prints"),
]

OBJECTS = [
    MysteryObject("key", "key", "a brass key", "it opens a secret drawer", "museum"),
    MysteryObject("badge", "badge", "a star-shaped badge", "it belongs to the night guard", "library"),
    MysteryObject("cookie", "cookie", "a sugar cookie", "it leaves crumbs everywhere", "kitchen"),
    MysteryObject("lantern", "lantern", "a small lantern", "it glows by itself", "garden"),
]

HERO_NAMES = ["Mina", "Theo", "Luca", "Ivy", "Nora", "Ben", "Maya", "Owen"]
TRAITS = ["curious", "brave", "silly", "careful", "cheerful", "sharp-eyed"]


@dataclass
class StoryParams:
    place: str
    suspect: str
    object: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous mystery story world about a snatch and a conclusion.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--suspect", choices=[s.id for s in SUSPECTS])
    ap.add_argument("--object", choices=[o.id for o in OBJECTS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def _settings() -> list[tuple[str, str, str]]:
    return [(p, s.id, o.id) for p in SETTINGS for s in SUSPECTS for o in OBJECTS if s.id != "robot" or p != "kitchen"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = _settings()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.suspect:
        combos = [c for c in combos if c[1] == args.suspect]
    if args.object:
        combos = [c for c in combos if c[2] == args.object]
    if not combos:
        raise StoryError("No valid mystery fits those choices.")
    place, suspect_id, object_id = rng.choice(combos)
    obj = next(o for o in OBJECTS if o.id == object_id)
    suspect = next(s for s in SUSPECTS if s.id == suspect_id)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, suspect=suspect_id, object=object_id, name=name, gender=gender, trait=trait)


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    suspect = next(s for s in SUSPECTS if s.id == params.suspect)
    obj_cfg = next(o for o in OBJECTS if o.id == params.object)
    obj = world.add(Entity(id=obj_cfg.id, label=obj_cfg.label, phrase=obj_cfg.phrase, owner=obj_cfg.owner, hidden=True))
    culprit = world.add(Entity(id=suspect.id, kind="character", type=suspect.type, label=suspect.name))
    world.facts.update(hero=hero, suspect=culprit, obj=obj, obj_cfg=obj_cfg, suspect_cfg=suspect)
    hero.memes["curiosity"] = 1
    culprit.meters["suspicion"] = 1
    return world


def tell(world: World) -> None:
    h: Entity = world.facts["hero"]
    s: Entity = world.facts["suspect"]
    o: Entity = world.facts["obj"]
    scfg: Suspect = world.facts["suspect_cfg"]
    ocfg: MysteryObject = world.facts["obj_cfg"]
    place = world.setting.place

    world.say(f"{h.id} was a {world.facts['hero'].type} with a {world.facts['hero'].memes.get('curiosity', 0):.0f} curious spark, and {place} was very quiet.")
    world.say(f"Then {ocfg.phrase} went missing from {place}, and everyone made a very serious face that still looked a little silly.")
    world.para()
    world.say(f"{h.id} looked for clues in {place} and found {', '.join(world.setting.clues[:2])}.")
    world.say(f"Near the clue trail, {s.label} was acting odd: {scfg.funny_tell}, and {s.pronoun().capitalize()} kept circling the room as if the floor were hot.")
    world.say(f"{h.id} guessed the missing thing had been snatched, not lost, because {ocfg.clue}.")
    world.para()
    world.say(f"At last, {h.id} followed the tiny signs to a hidden nook and found the {o.label} tucked behind a stack of books.")
    world.say(f"{s.label} had not stolen it for keeps; {s.pronoun().capitalize()} had snatched it only to use it for a joke and forgot to put it back.")
    world.say(f"{h.id} laughed, {s.label} looked bashful, and the mystery ended with the {o.label} back where it belonged and everyone smiling at the very odd little caper.")


def conclude_world(world: World) -> None:
    obj = world.facts["obj"]
    hero: Entity = world.facts["hero"]
    obj.hidden = False
    obj.found_by = hero.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short humorous mystery story for a child where a {f["obj_cfg"].label} is snatched and later the truth is revealed.',
        f"Tell a funny detective story set in {world.setting.place} where {f['hero'].id} notices clues and concludes who moved the object.",
        f'Write a child-friendly mystery with a playful twist that uses the words "snatch" and "conclude".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    suspect: Entity = f["suspect"]
    obj_cfg: MysteryObject = f["obj_cfg"]
    return [
        QAItem(
            question=f"What happened to {obj_cfg.phrase} in {world.setting.place}?",
            answer=f"{obj_cfg.phrase} was snatched from {world.setting.place}, so everyone had to look for clues.",
        ),
        QAItem(
            question=f"How did {hero.id} conclude what happened?",
            answer=f"{hero.id} looked at the clues, noticed {suspect.label} acting strangely, and concluded the object had been moved for a joke.",
        ),
        QAItem(
            question=f"What made the mystery funny?",
            answer=f"The funny part was that {suspect.label} had a guilty-looking habit but had only snatched the object to play a joke, not to keep it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does it mean to conclude something?",
            answer="To conclude means to figure out an answer after thinking about the facts and clues.",
        ),
        QAItem(
            question="Why can a mystery be funny?",
            answer="A mystery can be funny when the surprising answer is harmless or silly instead of scary.",
        ),
    ]


ASP_RULES = r"""
place(P) :- setting(P).
mystery_object(O) :- object(O).
suspect(S) :- character(S).
snatched(O) :- missing(O).
conclude(H,O) :- found(H,O), clue_trail(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for s in SUSPECTS:
        lines.append(asp.fact("character", s.id))
    for o in OBJECTS:
        lines.append(asp.fact("object", o.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show place/1."))
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP rules load.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    conclude_world(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.hidden:
                bits.append("hidden=True")
            if e.found_by:
                bits.append(f"found_by={e.found_by}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            print(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    if qa:
        print()
        for title, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(title + ":")
            for i, item in enumerate(items, 1):
                if isinstance(item, QAItem):
                    print(f"Q{i}: {item.question}")
                    print(f"A{i}: {item.answer}")
                else:
                    print(f"{i}. {item}")


CURATED = [
    StoryParams(place="library", suspect="cat", object="badge", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="museum", suspect="parrot", object="key", name="Theo", gender="boy", trait="sharp-eyed"),
    StoryParams(place="kitchen", suspect="mouse", object="cookie", name="Ivy", gender="girl", trait="cheerful"),
    StoryParams(place="garden", suspect="robot", object="lantern", name="Ben", gender="boy", trait="careful"),
]


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return CURATED
    out = []
    for i in range(args.n):
        p = resolve_params(args, random.Random((args.seed or 0) + i))
        p.seed = (args.seed or 0) + i
        out.append(p)
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(asp_verify())
    if args.show_asp:
        print(asp_program("#show conclude/2."))
        return
    if args.asp:
        print(asp_program("#show conclude/2."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in (CURATED if args.all else resolve_all(args, rng))]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### {p.name} at {p.place} ({p.suspect}, {p.object})")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

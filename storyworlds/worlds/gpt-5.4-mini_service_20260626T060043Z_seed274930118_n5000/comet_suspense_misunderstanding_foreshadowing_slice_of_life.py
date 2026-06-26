#!/usr/bin/env python3
"""
storyworlds/worlds/comet_suspense_misunderstanding_foreshadowing_slice_of_life.py
==================================================================================

A small slice-of-life story world about waiting for a comet, noticing tiny clues,
and clearing up a misunderstanding before the sky show begins.

The premise is intentionally simple:
- a child and a caregiver plan to watch a comet
- a small misunderstanding creates a gentle suspense beat
- foreshadowing appears in the sky, the notebook, or the preparations
- the ending resolves with a calm shared moment and a visible change in state
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    indoor: bool = False
    sky_view: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    label: str
    foreshadow: str
    suspense: str
    misunderstanding: str
    resolution: str
    visible: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "thing"
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    event: str
    object: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


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


SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, sky_view=True, affords={"watch"}),
    "porch": Setting(place="the porch", indoor=False, sky_view=True, affords={"watch"}),
    "window": Setting(place="the window seat", indoor=True, sky_view=True, affords={"watch"}),
    "hill": Setting(place="the little hill", indoor=False, sky_view=True, affords={"watch"}),
}

EVENTS = {
    "comet": Event(
        id="comet",
        label="comet",
        foreshadow="A thin bright line had already appeared on the sky chart the night before.",
        suspense="The comet would not be easy to see until the sky got dark enough.",
        misunderstanding="The child thought the long glowing tail meant the comet was being chased.",
        resolution="The caregiver explained that the tail was just light and dust shining in the dark.",
        visible="Then the comet slid across the sky like a tiny silver brushstroke.",
        tags={"comet", "sky", "night"},
    )
}

OBJECTS = {
    "blanket": ObjectCfg(id="blanket", label="blanket", phrase="a soft blue blanket", type="blanket"),
    "binoculars": ObjectCfg(id="binoculars", label="binoculars", phrase="small binoculars", type="binoculars", plural=True),
    "snack": ObjectCfg(id="snack", label="snack bag", phrase="a snack bag with crackers", type="bag"),
    "chart": ObjectCfg(id="chart", label="sky chart", phrase="a sky chart with circles and arrows", type="chart"),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Zoe", "Ella", "Ava"],
    "boy": ["Leo", "Noah", "Finn", "Eli", "Sam", "Theo"],
}
TRAITS = ["curious", "quiet", "bright-eyed", "patient", "restless", "careful"]
CAREGIVERS = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life comet storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    event = args.event or "comet"
    obj = args.object or rng.choice(list(OBJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)

    if not SETTINGS[place].sky_view:
        raise StoryError("This story needs a place with a clear view of the sky.")
    if event != "comet":
        raise StoryError("Only the comet story is supported in this world.")
    if obj not in {"blanket", "binoculars", "snack", "chart"}:
        raise StoryError("Unknown object choice.")
    return StoryParams(place=place, event=event, object=obj, name=name, gender=gender, caregiver=caregiver, trait=trait)


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _possessive_name(name: str) -> str:
    return f"{name}'" if name.endswith("s") else f"{name}'s"


def tell(setting: Setting, event: Event, object_cfg: ObjectCfg, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver, label=params.caregiver))
    obj = world.add(Entity(id=object_cfg.id, type=object_cfg.type, label=object_cfg.label, phrase=object_cfg.phrase, plural=object_cfg.plural))
    child.memes["waiting"] = 1.0
    child.memes["curiosity"] = 1.0
    caregiver.memes["calm"] = 1.0
    obj.owner = child.id

    world.say(f"{params.name} was a {params.trait} {params.gender} who loved looking up at the sky.")
    world.say(f"That evening, {params.name} and {params.caregiver} planned to watch the {event.label} from {setting.place}.")
    world.say(event.foreshadow)
    world.say(f"They brought {obj.phrase} and sat down quietly, because {event.suspense.lower()}")

    world.para()
    world.say(f"{params.name} kept staring at the darkening sky.")
    world.say(f"Then {params.name} pointed and whispered, \"Is that the comet running away?\"")
    child.memes["worry"] = 1.0
    world.say(event.misunderstanding)
    world.say(f"For a moment, the waiting felt long and a little suspenseful.")

    world.para()
    world.say(f"{params.caregiver} smiled and patted {params.name} on the shoulder.")
    world.say(f"\"No,\" {params.caregiver} said. \"The tail is just dust and light, and it will look prettier when the sky gets darker.\"")
    child.memes["worry"] = 0.0
    child.memes["relief"] = 1.0
    child.memes["wonder"] = 1.0
    world.say(event.resolution)
    world.say(event.visible)
    world.say(f"{params.name} leaned against the {obj.label} and watched without blinking.")
    world.say(f"By the time the comet passed overhead, the little hill, porch, window seat, or backyard felt very still and very kind.")
    world.say(f"{params.name} smiled up at the sky, and the long bright tail no longer felt scary at all.")

    world.facts.update(
        child=child,
        caregiver=caregiver,
        object=obj,
        event=event,
        setting=setting,
        object_cfg=object_cfg,
        resolved=True,
        misunderstanding=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    event: Event = f["event"]
    obj: Entity = f["object"]
    setting: Setting = f["setting"]
    return [
        f'Write a gentle slice-of-life story about {child.label} waiting to see a {event.label} from {setting.place}.',
        f'Tell a story where {child.label} thinks the {event.label} is chasing something, and {caregiver.label} explains the sky.',
        f'Write a small child-friendly story that includes {obj.phrase} and ends with a calm look at the comet.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    caregiver: Entity = f["caregiver"]
    event: Event = f["event"]
    obj: Entity = f["object"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who watched the {event.label} together at {setting.place}?",
            answer=f"{child.label} and {caregiver.label} watched it together at {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.label} think the {event.label} was doing at first?",
            answer=f"{child.label} thought the {event.label} was running away or being chased because of its long tail.",
        ),
        QAItem(
            question=f"What did {caregiver.label} say about the comet's tail?",
            answer=f"{caregiver.label} explained that the tail was made of dust and light shining in the dark.",
        ),
        QAItem(
            question=f"What did they bring to make the wait more comfortable?",
            answer=f"They brought {obj.phrase} to make the wait feel cozy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comet?",
            answer="A comet is a small icy space object that travels around the sun and can grow a bright tail when it gets close.",
        ),
        QAItem(
            question="Why does a comet have a tail?",
            answer="A comet can have a tail because sunlight warms its ice and dust, which then shines and streams behind it.",
        ),
        QAItem(
            question="Why can waiting for the sky to get dark feel suspenseful?",
            answer="Waiting can feel suspenseful when something exciting is about to happen but has not happened yet.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id}: ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "comet", obj) for place in SETTINGS for obj in OBJECTS]


ASP_RULES = r"""
valid_story(Place, Event, Object) :- setting(Place), event(Event), obj(Object), sky_view(Place), event_ok(Event).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.sky_view:
            lines.append(asp.fact("sky_view", place))
        if setting.indoor:
            lines.append(asp.fact("indoor", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("event_ok", eid))
        lines.append(asp.fact("event_tag", eid, "comet"))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], OBJECTS[params.object], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        import asp
        models = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(models, "valid_story")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for obj in OBJECTS:
                params = StoryParams(
                    place=place,
                    event="comet",
                    object=obj,
                    name="Mia",
                    gender="girl",
                    caregiver="mother",
                    trait="curious",
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

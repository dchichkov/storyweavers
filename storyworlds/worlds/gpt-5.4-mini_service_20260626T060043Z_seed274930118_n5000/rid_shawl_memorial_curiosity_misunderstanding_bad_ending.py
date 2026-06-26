#!/usr/bin/env python3
"""
storyworlds/worlds/rid_shawl_memorial_curiosity_misunderstanding_bad_ending.py
==============================================================================

A small space-adventure storyworld built from the seed words:
rid, shawl, memorial.

Premise:
- Rid is a curious young traveler on a quiet orbital station.
- A memorial drift-garden contains a shawl left for remembrance.
- Curiosity causes Rid to misread a warning plaque.
- The misunderstanding leads to a bad ending: the shawl is lost and the memorial is left dim.

This world intentionally leans into a gentle-but-sad conclusion while still
being state-driven and complete: setup, turn, consequence, ending image.
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the quiet station"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    relic: str
    name: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    curiosity: str
    misunderstanding: str
    consequence: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    used_for: str = ""
    grief: str = ""


@dataclass
class Shawl:
    id: str = "shawl"
    label: str = "shawl"
    phrase: str = "a soft blue shawl"
    region: str = "torso"
    guards: set[str] = field(default_factory=lambda: {"cold", "dust"})
    covers: set[str] = field(default_factory=lambda: {"torso"})
    grief: str = "tugged free by a drift-spark"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    rid = world.entities.get("Rid")
    shawl = world.entities.get("shawl")
    if not rid or not shawl:
        return out
    if rid.memes.get("confused", 0) < THRESHOLD:
        return out
    if rid.memes.get("grabbed", 0) >= THRESHOLD:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shawl.meters["lost"] = 1
    shawl.worn_by = None
    out.append("The shawl slipped away into the station's dark vent-line.")
    return out


def _r_dim_memorial(world: World) -> list[str]:
    memorial = world.entities.get("memorial")
    shawl = world.entities.get("shawl")
    if not memorial or not shawl:
        return []
    if shawl.meters.get("lost", 0) < THRESHOLD:
        return []
    sig = ("dim",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    memorial.meters["brightness"] = 0
    memorial.memes["sorrow"] = memorial.memes.get("sorrow", 0) + 1
    return ["The memorial light grew dim and small."]
    

CAUSAL_RULES = [_r_loss, _r_dim_memorial]


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


def build_world(setting: Setting, activity: Activity, relic: Relic) -> World:
    world = World(setting)
    rid = world.add(Entity(id="Rid", kind="character", type="boy"))
    guide = world.add(Entity(id="Guide", kind="character", type="robot"))
    memorial = world.add(Entity(id="memorial", type="thing", label="memorial", phrase="the memorial light"))
    shawl = world.add(Entity(
        id="shawl",
        type="thing",
        label="shawl",
        phrase="a soft blue shawl",
        owner="memorial",
        caretaker="memorial",
        worn_by="memorial",
    ))

    rid.memes["curiosity"] = 1
    rid.memes["hope"] = 1
    memorial.meters["brightness"] = 1
    memorial.memes["memory"] = 1

    world.say("Rid was a curious little traveler who loved the hush of the station windows.")
    world.say("He liked to count the stars and ask why every glowing thing was there.")
    world.say(f"At the end of the hall stood {setting.place}, and inside it waited the memorial with {shawl.phrase}.")
    world.para()
    world.say(f"One day Rid wanted to {activity.verb}.")
    world.say(f"{activity.curiosity}")
    world.say(f"He saw the warning plaque, but he misunderstood it and thought it meant the path was safe.")
    rid.memes["confused"] = 1
    world.say(f"{guide.id} tried to point at the sign, but Rid kept going because his curiosity pulled harder than his patience.")
    world.say(f"{activity.misunderstanding}")
    propagate(world, narrate=True)
    world.para()
    world.say(f"After the mistake, Rid stood very still in the cold air.")
    world.say(f"{activity.consequence}")
    world.say("The shawl was gone, and the memorial glowed only weakly in the dark.")
    world.say("Rid looked at the dim light and finally understood that some things are meant to be cared for, not chased.")
    world.facts.update(
        rid=rid,
        guide=guide,
        memorial=memorial,
        shawl=shawl,
        setting=setting,
        activity=activity,
        relic=relic,
    )
    return world


SETTINGS = {
    "orbital_hall": Setting(place="the orbital memorial hall", affords={"inspect"}),
    "drift_garden": Setting(place="the drift garden corridor", affords={"inspect"}),
}

ACTIVITIES = {
    "inspect": Activity(
        id="inspect",
        verb="follow the glowing path",
        gerund="following the glowing path",
        rush="dash after the light",
        curiosity="A tiny lamp blinked beside the memorial, and Rid wanted to know what made it wink.",
        misunderstanding="He thought the blinking meant the path invited him to take the shawl and ride the lift more quickly.",
        consequence="When he reached for the shawl, the cloth snagged on a vent grate and slipped away.",
        zone={"torso"},
        tags={"curiosity", "misunderstanding", "space", "memorial"},
    ),
}

RELICS = {
    "shawl": Relic(
        id="shawl",
        label="shawl",
        phrase="a soft blue shawl",
        region="torso",
        used_for="warmth and remembrance",
        grief="it stayed behind as a memorial cloth",
    ),
}

TRAITS = ["curious", "restless", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("orbital_hall", "inspect", "shawl"), ("drift_garden", "inspect", "shawl")]


def explain_rejection(place: str, activity: str, relic: str) -> str:
    return (
        f"(No story: {activity} at {place} does not create the space-adventure misunderstanding "
        f"this world is built for. Try the memorial and shawl together.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("rel_region", rid, rel.region))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Activity, Relic) :- affords(Place, Activity), activity(Activity), relic(Relic), rel_region(Relic, torso).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld: Rid, the shawl, and a memorial misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--relic", choices=RELICS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, relic = rng.choice(sorted(combos))
    name = args.name or "Rid"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, relic=relic, name=name, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space-adventure story for a young child that includes Rid, a shawl, and a memorial.',
        f"Tell a gentle story about {f['rid'].id} being curious at {f['setting'].place} and making a misunderstanding about the memorial shawl.",
        "Write a story where curiosity leads to a bad ending, but the ending still feels complete and clear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rid = f["rid"]
    memorial = f["memorial"]
    shawl = f["shawl"]
    act = f["activity"]
    return [
        QAItem(
            question="Who was the curious traveler in the story?",
            answer=f"The curious traveler was {rid.id}, a little boy who loved to ask questions.",
        ),
        QAItem(
            question="What important thing was at the memorial?",
            answer=f"The memorial held {shawl.phrase}, and that shawl was meant for remembrance.",
        ),
        QAItem(
            question="What caused the trouble in the story?",
            answer=f"Rid's curiosity led to a misunderstanding of the warning sign, and that mistake made the shawl slip away.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended sadly: the shawl was lost, the memorial light grew dim, and Rid learned that careful thinking matters.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a memorial for?",
            answer="A memorial is a place or object that helps people remember someone or something important.",
        ),
        QAItem(
            question="What does a shawl do?",
            answer="A shawl is a soft piece of cloth people wear around their shoulders to stay warm or to look nice.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn what something is and how it works.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a sign, word, or action means the wrong thing.",
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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(SETTINGS[params.place], ACTIVITIES[params.activity], RELICS[params.relic])
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
    StoryParams(place="orbital_hall", activity="inspect", relic="shawl", name="Rid", trait="curious"),
    StoryParams(place="drift_garden", activity="inspect", relic="shawl", name="Rid", trait="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.activity} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

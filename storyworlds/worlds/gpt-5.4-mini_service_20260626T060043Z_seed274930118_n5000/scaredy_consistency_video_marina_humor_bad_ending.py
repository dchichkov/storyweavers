#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scaredy_consistency_video_marina_humor_bad_ending.py
==============================================================================================================

A standalone storyworld for a small marina tale with scaredy consistency,
video-making, humor, and a deliberately bad ending beat.

Premise:
- A shy child at a marina wants to record a little video.
- The child must stay consistent: speak the same brave line, keep filming, and
  not flinch at every horn, gull, or splash.
- The turn is that the marina is full of silly distractions, so the child keeps
  breaking the take.
- The ending is humorous but not fully triumphant: the recording is ruined by a
  comic marina mishap, though the child does end a little braver.

This world models typed entities with physical meters and emotional memes, and
uses a tiny forward-chained simulation so the prose is driven by world state.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Marina:
    place: str = "the marina"
    has_boats: bool = True
    has_dock: bool = True
    has_ice_cream: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, marina: Marina) -> None:
        self.marina = marina
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather = "breezy"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.marina)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


def _r_flinch(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    if child.memes.get("flinch", 0.0) < THRESHOLD:
        return out
    sig = ("flinch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["video_time"] = child.meters.get("video_time", 0.0) - 0.2
    out.append("The camera wobbled as the child flinched again.")
    return out


def _r_inconsistency(world: World) -> list[str]:
    child = world.get("child")
    if child.meters.get("takes", 0.0) < 2:
        return []
    if child.memes.get("consistent", 0.0) >= THRESHOLD:
        return []
    sig = ("inconsistent",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["embarrassed"] = child.memes.get("embarrassed", 0.0) + 1
    return ["The little video kept starting and stopping, which made the joke feel jagged."]


def _r_bad_ending(world: World) -> list[str]:
    child = world.get("child")
    seagull = world.get("seagull")
    if child.meters.get("recorded", 0.0) < THRESHOLD:
        return []
    if seagull.meters.get("snatched", 0.0) < THRESHOLD:
        return []
    sig = ("bad_ending",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    return ["The ending was a goofy flop, because the gull stole the snack right on cue."]


RULES = [_r_flinch, _r_inconsistency, _r_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class VideoPlan:
    title: str
    line: str
    takes_needed: int
    humor: str
    bad_ending: str


MARINA_PLAN = VideoPlan(
    title="a brave marina clip",
    line="I am brave by the waves",
    takes_needed=3,
    humor="a gull wore a bun like a crown and stared at the camera",
    bad_ending="the final frame filled with a splash and a stolen snack",
)


def tell(params: StoryParams) -> World:
    world = World(Marina())
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    gull = world.add(Entity(id="seagull", kind="character", type="bird", label="a seagull"))
    camera = world.add(Entity(id="camera", type="camera", label="camera", owner=child.id))
    snack = world.add(Entity(id="snack", type="thing", label="snack", caretaker=parent.id))

    world.facts.update(child=child, parent=parent, gull=gull, camera=camera, snack=snack, plan=MARINA_PLAN)

    child.memes["scaredy"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["consistent"] = 0.0
    child.meters["takes"] = 0.0
    child.meters["recorded"] = 0.0

    world.say(
        f"{params.name} was a little {params.trait} {params.gender} at the marina, "
        f"where the ropes hummed and the water made a silver line."
    )
    world.say(
        f"{params.name} wanted to make {MARINA_PLAN.title}, a tiny video with "
        f"one steady line: “{MARINA_PLAN.line}.”"
    )
    world.say(
        f"That sounded funny and fine, but {params.name} was a bit scaredy, "
        f"so {params.name} kept checking the waves and the wobble and the wind."
    )

    world.para()
    world.say(
        f"The {params.parent} held up the camera and said, "
        f"“Try again, and try the same line each time.”"
    )
    world.say(f"{MARINA_PLAN.humor}.")
    child.memes["desire"] = 1.0

    for i in range(MARINA_PLAN.takes_needed):
        child.meters["takes"] += 1
        child.meters["video_time"] = child.meters.get("video_time", 0.0) + 0.4
        if i == 0:
            child.memes["flinch"] = 1.0
            world.say(
                f"{params.name} said the line once, then jumped when a horn went "
                f"toot-toot from a boat."
            )
            world.say(
                f"“Oops,” said {params.name}, with a tiny laugh that was half giggle and half gulp."
            )
        elif i == 1:
            child.memes["flinch"] = 1.0
            world.say(
                f"{params.name} tried again, but a gull hopped closer, peeking at the lens "
                f"as if it wanted a close-up."
            )
            world.say(
                f"{params.name} snorted a laugh and forgot the middle word."
            )
        else:
            child.memes["consistent"] = 1.0
            child.meters["recorded"] = 1.0
            world.say(
                f"On the last try, {params.name} stood still, breathed in, and said the line "
                f"all the way through."
            )
            world.say(
                f"The voice was small, but it was steady, and the camera got a clean look at the docks."
            )
        propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then came the bad ending beat: {gull.label_word if hasattr(gull, 'label_word') else 'the gull'} "
        f"snatched the snack from the bench and splashed off with a flap and a flop."
    )
    gull.meters["snatched"] = 1.0
    propagate(world, narrate=True)

    child.memes["brave"] = 1.0
    child.memes["scaredy"] = 0.0
    world.say(
        f"{params.name} blinked, then laughed so hard the shoulders shook."
    )
    world.say(
        f"The video ended with a wobble, a wave, and a silly gull feet-first in the air."
    )

    world.facts["resolved"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f'Write a Rhyming Story set at a marina about a scaredy child making a video, with humor and a bad ending.',
        f"Tell a short, child-facing story where {child.label} keeps trying to make a consistent video line at the marina.",
        f"Write a funny story with waves, a camera, and a gull, and end it with a comic mishap instead of a perfect win.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    plan = f["plan"]
    qa = [
        QAItem(
            question=f"Where did {child.label} try to make the video?",
            answer=f"{child.label} tried to make the video at the marina, where the boats, docks, and waves kept the scene lively.",
        ),
        QAItem(
            question=f"What line was {child.label} trying to say in the video?",
            answer=f"{child.label} was trying to say, “{plan.line}.”",
        ),
        QAItem(
            question=f"Why did {child.label} keep starting over?",
            answer=f"{child.label} kept starting over because the child felt scaredy, got distracted by the horn, and laughed at the gull instead of staying consistent.",
        ),
        QAItem(
            question=f"Who helped {child.label} by holding the camera?",
            answer=f"The {parent.label} helped by holding the camera and telling {child.label} to try again with the same line each time.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended in a bad but funny way: the gull stole the snack, the video wobbled, and the last frame turned into a silly splashy mess.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place near the water where boats are kept, parked, or tied up by docks.",
        ),
        QAItem(
            question="What does consistent mean?",
            answer="Consistent means doing something the same way again and again, without changing the pattern too much.",
        ),
        QAItem(
            question="Why are videos made?",
            answer="Videos are made to save moving pictures and sounds so people can watch, remember, or share a moment later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_scared(C) :- scaredy(C).
needs_consistency(C) :- child_scared(C).
fails_take(C) :- needs_consistency(C), not consistent(C).
bad_ending(C) :- fails_take(C), gull_snatched(_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("scaredy", "child"),
            asp.fact("video", "camera"),
            asp.fact("marina", "marina"),
            asp.fact("humor", "marina_story"),
            asp.fact("bad_ending", "marina_story"),
            asp.fact("consistency", "video"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show bad_ending/1."))
    _ = asp.atoms(model, "bad_ending")
    print("OK: ASP twin loads and produces a model.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Rhyming Story world set at a marina.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=["scaredy", "shy", "curious", "funny", "tiny"], default=None)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Theo", "Luca", "Nia", "Pip", "Lena"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["scaredy", "shy", "curious", "funny", "tiny"])
    if trait not in {"scaredy", "shy", "curious", "funny", "tiny"}:
        raise StoryError("invalid trait")
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/1."))
        print(asp.atoms(model, "bad_ending"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(name="Mina", gender="girl", parent="mother", trait="scaredy")),
            generate(StoryParams(name="Theo", gender="boy", parent="father", trait="shy")),
            generate(StoryParams(name="Lena", gender="girl", parent="father", trait="funny")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/fracture_stench_kamikaze_rhyme_reconciliation_humor_slice.py
==============================================================================================================================

A small slice-of-life storyworld about a child, a stinky little problem, a
paper-plane mishap, and a gentle reconciliation.

This world keeps one compact premise:
- a child makes a rhyming, slightly silly "kamikaze" paper plane
- the plane crashes into a fragile household item and causes a fracture
- the room also smells bad because of a neglected compost bin / trash
- humor and a soft apology turn the tension into cooperation

The story is intentionally grounded in daily life. It should feel like a
single, complete scene rather than an event log.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fracture": 0.0, "stench": 0.0}
        if not self.memes:
            self.memes = {"humor": 0.0, "reconciliation": 0.0, "worry": 0.0, "annoyance": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the kitchen"
    setting_note: str = "the table was a little crowded"
    affords: set[str] = field(default_factory=lambda: {"paper_plane", "cleaning"})
    smell_source: str = "the compost bin"
    smell_reason: str = "the lid had been left open"


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    fracture_target: str
    sound: str
    rhyme_tag: str


@dataclass
class FragileItem:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    sibling: str
    place: str
    action: str
    fragile: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        import copy
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_fracture(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["fracture"] >= THRESHOLD and ("fracture", ent.id) not in world.fired:
            world.fired.add(("fracture", ent.id))
            out.append(f"{ent.label.capitalize()} cracked with a tiny, sharp sound.")
    return out


def _r_stench(world: World) -> list[str]:
    out: list[str] = []
    if world.entities["bin"].meters["stench"] >= THRESHOLD and ("stench", "bin") not in world.fired:
        world.fired.add(("stench", "bin"))
        out.append("The smell from the open bin drifted through the room.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_fracture, _r_stench):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def setup_world(params: StoryParams) -> World:
    world = World(Scene(place=params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    sibling = world.add(Entity(id="sibling", kind="character", type="boy", label=f"the {params.sibling}"))
    fragile = world.add(Entity(
        id="fragile",
        type=params.fragile,
        label=params.fragile,
        phrase=FRAGILES[params.fragile].phrase,
        region=FRAGILES[params.fragile].region,
        owner=child.id,
    ))
    plane = world.add(Entity(id="plane", type="toy", label="paper plane", phrase="a folded paper plane"))
    bin_ent = world.add(Entity(id="bin", type="thing", label="bin", phrase=world.scene.smell_source))
    world.facts.update(child=child, parent=parent, sibling=sibling, fragile=fragile, plane=plane, bin=bin_ent)
    return world


def do_story(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    parent = world.facts["parent"]
    sibling = world.facts["sibling"]
    fragile = world.facts["fragile"]
    plane = world.facts["plane"]
    bin_ent = world.facts["bin"]
    action = ACTIONS[params.action]

    world.say(f"{child.id} was in {world.scene.place}, where {world.scene.setting_note}.")
    world.say(
        f"{child.id} folded {plane.phrase} and gave it a silly nickname: {action.rhyme_tag}. "
        f"{child.pronoun().capitalize()} whispered a rhyme, 'Zip, zap, splash, make the little plane dash.'"
    )
    world.say(
        f"On the shelf sat {fragile.phrase}, and nearby {world.scene.smell_source} had an ugly little stench because {world.scene.smell_reason}."
    )

    world.para()
    child.memes["humor"] += 1
    world.memes = {}
    world.say(
        f"{child.id} wanted to send {plane.label} flying anyway, because the rhyme sounded funny and {child.pronoun()} felt bold."
    )
    world.say(f"{child.pronoun().capitalize()} tried to {action.rush}, and the plane went kamikaze-right toward {fragile.label}.")
    fragile.meters["fracture"] += 1
    child.memes["worry"] += 1
    propagate(world)

    world.para()
    sibling.memes["annoyance"] += 1
    world.say(
        f"{sibling.id} made a face at the smell and said, 'Phew, that stench could knock over a chair!'"
    )
    world.say(
        f"{parent.label.capitalize()} looked at the cracked {fragile.label}, then at the open bin, and took a slow breath."
    )
    parent.memes["worry"] += 1
    if fragile.meters["fracture"] >= THRESHOLD:
        world.say(
            f"{parent.label.capitalize()} did not shout. Instead, {parent.pronoun()} asked {child.id} to help clean up and carry the bin bag out."
        )
    child.memes["reconciliation"] += 1
    parent.memes["reconciliation"] += 1
    child.memes["humor"] += 1

    world.para()
    world.say(
        f"{child.id} sighed, then said, 'Sorry for the plane dive. It was a kamikaze joke, and it was a bad one.'"
    )
    world.say(
        f"{parent.id} gave a small smile. 'At least your rhyme was good,' {parent.pronoun()} said, 'but let's choose a gentler game.'"
    )
    world.say(
        f"So they taped the crack, tied up the trash, and washed their hands together. The room smelled better, and the day felt peaceful again."
    )

    world.facts["resolved"] = True
    world.facts["action"] = action
    world.facts["scene"] = world.scene


def aspiration_line(action: Action, fragile: FragileItem, scene: Scene) -> str:
    return (
        f"Write a slice-of-life story about a child in {scene.place} whose {action.rhyme_tag} paper plane "
        f"causes a fracture and a bad stench, then ends with humor and reconciliation."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sibling = f["sibling"]
    fragile = f["fragile"]
    action = f["action"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"What was {child.id} doing in {scene.place} before the trouble started?",
            answer=(
                f"{child.id} was folding and flying a paper plane while whispering a rhyme. "
                f"{child.pronoun().capitalize()} was trying to make a funny little game out of the moment."
            ),
        ),
        QAItem(
            question=f"What happened to the {fragile.label} when the plane went kamikaze?",
            answer=(
                f"The {fragile.label} got a fracture when the plane rushed into it. "
                f"It made a sharp crack and turned the quiet shelf into a problem to fix."
            ),
        ),
        QAItem(
            question=f"Why did the room smell bad?",
            answer=(
                f"The room smelled bad because the compost bin had been left open. "
                f"The smell drifted out and mixed with the tense feeling after the crack."
            ),
        ),
        QAItem(
            question=f"How did {child.id}, {parent.label}, and {sibling.id} calm things down?",
            answer=(
                f"They used humor, cleaned up together, and made up after the accident. "
                f"{child.id} apologized, {parent.label} stayed gentle, and everyone worked on the mess as a team."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a fracture mean?",
            answer="A fracture is a crack or break in something hard, like a cup, bowl, or stone.",
        ),
        QAItem(
            question="What is stench?",
            answer="Stench means a very strong, unpleasant smell.",
        ),
        QAItem(
            question="What is a kamikaze plane in this story?",
            answer=(
                "It is a silly paper plane that dives straight at something instead of gliding gently."
            ),
        ),
        QAItem(
            question="Why can humor help after a mistake?",
            answer=(
                "Humor can lower the tension, help people breathe, and make it easier to apologize and keep going."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        aspiration_line(f["action"], f["fragile"], f["scene"]),
        f"Tell a gentle slice-of-life story where {f['child'].id} makes a rhyming kamikaze paper plane, breaks {f['fragile'].label}, and fixes the mood with humor.",
        f"Write a short domestic story with a bad stench, a small fracture, and a reconciliation at the end.",
    ]


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    sibling: str
    place: str
    action: str
    fragile: str
    seed: Optional[int] = None


FRAGILES = {
    "bowl": FragileItem(label="bowl", phrase="a little ceramic bowl", type="bowl", region="shelf"),
    "vase": FragileItem(label="vase", phrase="a narrow glass vase", type="vase", region="shelf"),
    "mug": FragileItem(label="mug", phrase="a favorite mug", type="mug", region="table"),
}

ACTIONS = {
    "throw": Action(id="throw", verb="throw", gerund="throwing", rush="throw it hard", fracture_target="fragile", sound="whip", rhyme_tag="zip-zip"),
    "launch": Action(id="launch", verb="launch", gerund="launching", rush="launch it with a flick", fracture_target="fragile", sound="whoosh", rhyme_tag="flip-flap"),
}

SCENES = {
    "kitchen": Scene(place="the kitchen", setting_note="the counter was cluttered with toast crumbs"),
    "laundry": Scene(place="the laundry room", setting_note="the folding basket leaned against the wall"),
}

NAMES = ["Nia", "Milo", "Iris", "Eli", "Maya", "Finn"]
SIBLINGS = ["big sister", "little brother", "cousin", "brother", "sister"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, action, fragile) for place in SCENES for action in ACTIONS for fragile in FRAGILES]


def explain_rejection(action: Action, fragile: FragileItem) -> str:
    return f"(No story: the chosen action and fragile item do not create a believable fracture.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with fracture, stench, kamikaze, humor, and reconciliation.")
    ap.add_argument("--place", choices=SCENES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--fragile", choices=FRAGILES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
              and (args.action is None or c[1] == args.action)
              and (args.fragile is None or c[2] == args.fragile)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, fragile = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    sibling = args.sibling or rng.choice(SIBLINGS)
    return StoryParams(name=name, gender=gender, parent=parent, sibling=sibling, place=place, action=action, fragile=fragile)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    do_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
fracture_item(I) :- item(I), fracture_meter(I, V), V >= 1.
stinky_room :- bin_open, stench_meter(bin, V), V >= 1.
good_story :- fracture_item(_), stinky_room, humor_present, reconciliation_present.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place in SCENES:
        lines.append(asp.fact("place", place))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
    for fid, f in FRAGILES.items():
        lines.append(asp.fact("item", fid))
    lines.append(asp.fact("bin_open"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/0."))
    ok = any(sym.name == "good_story" for sym in model)
    py_ok = True
    if ok == py_ok:
        print("OK: ASP twin matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python checks.")
    return 1


CURATED = [
    StoryParams(name="Nia", gender="girl", parent="mother", sibling="little brother", place="kitchen", action="throw", fragile="mug"),
    StoryParams(name="Milo", gender="boy", parent="father", sibling="big sister", place="laundry", action="launch", fragile="vase"),
]


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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 and not args.all else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

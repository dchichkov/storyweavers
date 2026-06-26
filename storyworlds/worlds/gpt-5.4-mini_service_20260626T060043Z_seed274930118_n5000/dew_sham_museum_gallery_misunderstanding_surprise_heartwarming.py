#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dew_sham_museum_gallery_misunderstanding_surprise_heartwarming.py
===============================================================================================================================

A small, standalone story world about a museum gallery, a misunderstanding,
and a warm surprise. The seed words "dew" and "sham" are woven into the world
as exhibit vocabulary and a fragile display label.

Premise:
- A child visits a museum gallery and loves a delicate exhibit called the Dew
  Window.
- A protective cover called the sham curtain hides repairs before opening.
- The child misunderstands the curtain and worries the beloved exhibit is fake
  or gone.

Turn:
- The curator notices the worry, explains the cover, and reveals that the
  "surprise" is a tiny gift made with the child in mind.

Resolution:
- The child learns the exhibit is safe, not fake.
- The warm reveal softens everyone, and the story ends with a shared smile in
  the gallery light.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "curator"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the museum gallery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Display:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Cover:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.zone = set(self.zone)
        other.facts = dict(self.facts)
        return other


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    exhibit: str
    cover: str
    seed: Optional[int] = None


SETTINGS = {
    "gallery": Setting(place="the museum gallery", affords={"gentle_walk", "quiet_tour"}),
}

ACTIVITIES = {
    "gentle_walk": Activity(
        id="gentle_walk",
        verb="walk close to the display",
        gerund="walking close to the display",
        rush="run toward the glass case",
        mess="stirred",
        soil="all upset",
        zone={"feet"},
        keyword="dew",
        tags={"dew"},
    ),
    "quiet_tour": Activity(
        id="quiet_tour",
        verb="look around the exhibit",
        gerund="looking around the exhibit",
        rush="hurry into the hall",
        mess="ruffled",
        soil="all ruffled",
        zone={"feet"},
        keyword="surprise",
        tags={"surprise"},
    ),
}

DISPLAYS = {
    "dew": Display(
        id="dew",
        label="Dew Window",
        phrase="a tiny glass window that glittered like morning dew",
        region="torso",
        risk="could be mistaken for damage",
        genders={"girl", "boy"},
    ),
    "sham": Display(
        id="sham",
        label="Sham Lantern",
        phrase="a paper lantern wrapped in a sham curtain for repairs",
        region="torso",
        risk="could seem fake or hidden",
        genders={"girl", "boy"},
    ),
}

COVERS = {
    "curtain": Cover(
        id="curtain",
        label="a soft sham curtain",
        covers={"torso"},
        guards={"stirred", "ruffled"},
        prep="lift the sham curtain carefully",
        tail="lifted the sham curtain and smiled",
    ),
    "rope": Cover(
        id="rope",
        label="a velvet rope",
        covers={"feet"},
        guards={"stirred", "ruffled"},
        prep="step behind the velvet rope",
        tail="stepped back behind the velvet rope",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Noa", "Tia", "Ella"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Nico", "Finn", "Sam"]
TRAITS = ["gentle", "curious", "quiet", "sweet", "hopeful"]


def prize_at_risk(activity: Activity, display: Display) -> bool:
    return display.region in activity.zone or activity.keyword in display.label.lower() or activity.keyword in display.id


def select_cover(activity: Activity, display: Display) -> Optional[Cover]:
    for cover in COVERS.values():
        if activity.mess in cover.guards and display.region in cover.covers:
            return cover
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act_id in SETTINGS[place].affords:
            act = ACTIVITIES[act_id]
            for disp_id, disp in DISPLAYS.items():
                if prize_at_risk(act, disp) and select_cover(act, disp):
                    out.append((place, act_id, disp_id))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    for item in world.entities.values():
        if item.worn_by != actor.id or item.protective:
            continue
        if item.caretaker is None:
            continue
        if item.meters.get("dirty", 0) >= THRESHOLD:
            continue
        if item.region in world.zone and not world.covered(actor, item.region):
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label_word} got a little messy.")


def predict_unsettled(world: World, actor: Entity, activity: Activity, display: Display) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return bool(sim.get(display.id).meters.get("dirty", 0) >= THRESHOLD)


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a {next((t for t in child.memes if False), '')}")
    world.say(f"{child.id} loved the museum gallery because every corner held a quiet surprise.")


def setup_story(world: World, child: Entity, parent: Entity, display: Entity, activity: Activity) -> None:
    world.say(
        f"One afternoon, {child.id} and {child.pronoun('possessive')} {parent.label_word} "
        f"visited {world.setting.place}."
    )
    world.say(f"{child.id} stopped at {display.phrase}.")
    world.say(f"{child.id} wanted to {activity.verb}, because {activity.keyword} felt like a little magic.")


def misunderstanding(world: World, child: Entity, parent: Entity, display: Entity, activity: Activity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"When {child.id} saw the sham curtain over the case, {child.pronoun()} thought "
        f"the {display.label_word} might be fake or hiding a problem."
    )
    world.say(
        f"{child.id} asked, 'Is the {display.label_word} all right?' with a small frown."
    )


def reassuring_surprise(world: World, parent: Entity, child: Entity, display: Entity, cover: Cover) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    world.say(
        f"{parent.label_word} knelt beside {child.id} and said the sham curtain was only there "
        f"to keep the display safe while the gallery rested."
    )
    world.say(
        f"Then {parent.pronoun('subject')} {cover.prep}, and behind it was a small card that said "
        f"the Dew Window had been made for children who notice careful, beautiful things."
    )
    world.say(
        f"{child.id}'s eyes went wide. It was a surprise, but a kind one."
    )
    world.say(
        f"{cover.tail}, and {child.id} smiled up at {parent.pronoun('object')} like the room itself had become warmer."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS["gallery"]
    activity = ACTIVITIES["quiet_tour" if params.cover == "curtain" else "gentle_walk"]
    display = DISPLAYS[params.exhibit]
    cover = COVERS[params.cover]

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        memes={"curiosity": 1.0, "worry": 0.0, "surprise": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=params.parent,
        label="caregiver",
        memes={"gentleness": 1.0},
    ))
    disp = world.add(Entity(
        id=display.id,
        type="thing",
        label=display.label,
        phrase=display.phrase,
        caretaker=parent.id,
    ))
    cloth = world.add(Entity(
        id=cover.id,
        type="thing",
        label=cover.label,
        caretaker=parent.id,
        protective=True,
        covers=set(cover.covers),
    ))
    cloth.worn_by = parent.id

    child.memes["love_gallery"] = 1.0

    world.say(f"{child.id} was a {params.trait} little {params.gender} who loved quiet rooms full of pictures.")
    world.say(f"The museum gallery felt cool and bright, and the light on the walls looked almost like dew.")
    world.para()
    setup_story(world, child, parent, disp, activity)
    misunderstanding(world, child, parent, disp, activity)
    world.para()
    reassuring_surprise(world, parent, child, disp, cover)

    world.facts.update(
        child=child,
        parent=parent,
        display=disp,
        cover=cloth,
        activity=activity,
        setting=setting,
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    disp = f["display"]
    act = f["activity"]
    return [
        f'Write a heartwarming story for a young child about a museum gallery, a misunderstanding, and a surprise, using the word "{act.keyword}".',
        f"Tell a gentle story where {child.id} worries that the {disp.label_word} is a sham, then learns it is safe and loved.",
        f"Write a short, warm story set in a museum gallery that includes dew, a sham curtain, and a kind surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    disp = f["display"]
    qa = [
        QAItem(
            question=f"Where did {child.id} and {parent.label_word} go?",
            answer=f"They went to the museum gallery, where the light felt calm and pretty.",
        ),
        QAItem(
            question=f"What did {child.id} think about the {disp.label_word} when the sham curtain was closed?",
            answer=f"{child.id} thought the {disp.label_word} might be fake or hiding trouble.",
        ),
        QAItem(
            question=f"What made the story turn from worry to a happy surprise?",
            answer=f"{parent.label_word} explained the sham curtain, then showed a kind surprise that made {child.id} smile.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and warm, because the misunderstanding was gently cleared up.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a museum gallery?",
            answer="A museum gallery is a room where people look at art or special objects carefully and quietly.",
        ),
        QAItem(
            question="What does dew look like?",
            answer="Dew looks like tiny shining drops of water, often on leaves or glass in the morning.",
        ),
        QAItem(
            question="What is a sham curtain for in a museum?",
            answer="A sham curtain can hide a display while it is being protected or repaired, so visitors do not touch it by accident.",
        ),
        QAItem(
            question="Why can a surprise be heartwarming?",
            answer="A surprise is heartwarming when it is kind and makes someone feel loved or remembered.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", trait="curious", exhibit="dew", cover="curtain"),
    StoryParams(name="Owen", gender="boy", parent="father", trait="gentle", exhibit="sham", cover="curtain"),
    StoryParams(name="Ivy", gender="girl", parent="mother", trait="hopeful", exhibit="dew", cover="rope"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    exhibit = args.exhibit or rng.choice(list(DISPLAYS))
    cover = args.cover or rng.choice(list(COVERS))
    params = StoryParams(name=name, gender=gender, parent=parent, trait=trait, exhibit=exhibit, cover=cover, seed=args.seed)
    return params


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


ASP_RULES = r"""
% A display is at risk when a tour activity touches its region.
at_risk(A,D) :- activity(A), display(D), displays_on(D,R), touches(A,R).

% A cover is a reasonable fix when it guards the mess kind and covers the region.
fix(C,A,D) :- cover(C), at_risk(A,D), guards(C,M), mess_of(A,M), covers(C,R), displays_on(D,R).

valid_story(A,D,C) :- at_risk(A,D), fix(C,A,D).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("touches", aid, r))
    for did, d in DISPLAYS.items():
        lines.append(asp.fact("display", did))
        lines.append(asp.fact("displays_on", did, d.region))
    for cid, c in COVERS.items():
        lines.append(asp.fact("cover", cid))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", cid, r))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((a, d, c) for a, d, c in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming museum gallery story world with dew, sham, misunderstanding, and surprise.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--exhibit", choices=DISPLAYS)
    ap.add_argument("--cover", choices=COVERS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

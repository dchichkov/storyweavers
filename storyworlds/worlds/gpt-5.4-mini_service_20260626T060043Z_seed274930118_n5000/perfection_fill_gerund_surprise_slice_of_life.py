#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/perfection_fill_gerund_surprise_slice_of_life.py
===============================================================================================================================

A small slice-of-life story world about wanting something to be perfect, filling
it just so, and then being surprised by a gentle twist.

Premise:
- A child is making something ordinary but important: a lunchbox, snack tray, or
  small shared container.
- They want it to look perfect and keep filling it until it feels "just right".
- A surprise interrupts the plan: someone arrives, brings a missing piece, or
  reveals the container was meant for sharing.

The simulation tracks:
- physical meters: fullness, neatness, warmth, mess, and readiness
- emotional memes: pride, worry, delight, surprise, and calm

The prose is meant to read like a TinyStories-style slice-of-life scene with a
clear beginning, a small turn, and a grounded ending image.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["fullness", "neatness", "warmth", "mess", "readiness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["pride", "worry", "delight", "surprise", "calm", "sharing"]:
            self.memes.setdefault(k, 0.0)

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
class ContainerSpec:
    id: str
    label: str
    phrase: str
    capacity: int
    target: str
    needs_warmth: bool = False
    surprise_tag: str = "surprise"


@dataclass
class FillAction:
    id: str
    gerund: str
    verb: str
    item_word: str
    item_phrase: str
    item_type: str
    item_warmth: float = 0.0
    item_mess: float = 0.0
    item_delight: float = 0.0
    requires_warmth: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseSpec:
    id: str
    reveal: str
    cause: str
    gift: str
    mood_shift: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    place: str
    indoor: bool = True
    detail: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    container: str
    action: str
    surprise: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS: dict[str, Setting] = {
    "kitchen": Setting(place="the kitchen", indoor=True, detail="The table was by the window."),
    "backroom": Setting(place="the back room", indoor=True, detail="A small shelf sat near the sink."),
    "porch": Setting(place="the porch", indoor=False, detail="The air felt cool and bright."),
}

CONTAINERS: dict[str, ContainerSpec] = {
    "bento": ContainerSpec(
        id="bento",
        label="bento box",
        phrase="a neat bento box",
        capacity=4,
        target="lunch",
        surprise_tag="sharing",
    ),
    "tray": ContainerSpec(
        id="tray",
        label="snack tray",
        phrase="a bright snack tray",
        capacity=6,
        target="snacks",
        surprise_tag="sharing",
    ),
    "jar": ContainerSpec(
        id="jar",
        label="cookie jar",
        phrase="a round cookie jar",
        capacity=8,
        target="cookies",
        needs_warmth=True,
        surprise_tag="warm",
    ),
}

ACTIONS: dict[str, FillAction] = {
    "sandwich": FillAction(
        id="sandwich",
        gerund="filling it with sandwich pieces",
        verb="fill it with sandwich pieces",
        item_word="sandwich",
        item_phrase="tiny sandwich squares",
        item_type="food",
        item_warmth=0.2,
        item_mess=0.0,
        item_delight=0.3,
        tags={"food"},
    ),
    "berries": FillAction(
        id="berries",
        gerund="filling it with berries",
        verb="fill it with berries",
        item_word="berries",
        item_phrase="little berries",
        item_warmth=0.0,
        item_mess=0.0,
        item_delight=0.4,
        tags={"food"},
    ),
    "cookies": FillAction(
        id="cookies",
        gerund="filling it with cookies",
        verb="fill it with cookies",
        item_word="cookies",
        item_phrase="warm cookies",
        item_warmth=1.0,
        item_mess=0.1,
        item_delight=0.6,
        requires_warmth=True,
        tags={"food", "warm"},
    ),
}

SURPRISES: dict[str, SurpriseSpec] = {
    "grandma": SurpriseSpec(
        id="grandma",
        reveal="Grandma arrived with one more little bowl for the middle.",
        cause="there was room left for something shared",
        gift="a tiny dish of strawberries",
        mood_shift=0.6,
        tags={"sharing"},
    ),
    "note": SurpriseSpec(
        id="note",
        reveal="A note under the lid said the box was meant for two.",
        cause="the lunch was for a helper too",
        gift="half a cheese square",
        mood_shift=0.5,
        tags={"sharing"},
    ),
    "warm_towel": SurpriseSpec(
        id="warm_towel",
        reveal="A warm towel on the counter was hiding the last cookies.",
        cause="the cookies needed to stay cozy",
        gift="the last warm cookie",
        mood_shift=0.7,
        tags={"warm"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Ava", "Zoe", "Mia"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Max", "Theo"]
TRAITS = ["careful", "patient", "cheerful", "quiet", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for container_id in CONTAINERS:
            for action_id, action in ACTIONS.items():
                for surprise_id, surprise in SURPRISES.items():
                    if action.requires_warmth and not CONTAINERS[container_id].needs_warmth:
                        continue
                    if surprise.tags and not (surprise.tags & action.tags):
                        continue
                    if CONTAINERS[container_id].needs_warmth and action.item_warmth < THRESHOLD:
                        continue
                    combos.append((place, action_id, surprise_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about perfection, filling, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("capacity", cid, c.capacity))
        if c.needs_warmth:
            lines.append(asp.fact("needs_warmth", cid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.requires_warmth:
            lines.append(asp.fact("requires_warmth", aid))
        if a.item_warmth >= THRESHOLD:
            lines.append(asp.fact("warm_item", aid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("surprise_tag", sid, t))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P, A, S) :- setting(P), action(A), surprise(S),
    (not requires_warmth(A) ; warm_item(A)),
    (not surprise_tag(S, warm) ; warm_item(A) ; needs_warmth_container(A)).
needs_warmth_container(A) :- action(A), warm_item(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(valid_combos_asp())
    if py == ap:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - ap))
    print("only asp:", sorted(ap - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and args.action:
        c = CONTAINERS[args.container]
        a = ACTIONS[args.action]
        if a.requires_warmth and not c.needs_warmth:
            raise StoryError("That action needs a warm container, and this container is not warm-friendly.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, surprise = rng.choice(sorted(combos))
    container = args.container or rng.choice(sorted(CONTAINERS))
    if (place, action, surprise) not in combos:
        combos = [c for c in combos if c[0] == place and c[1] == action and c[2] == surprise]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    container = args.container or rng.choice([cid for cid in CONTAINERS if (place, action, surprise) in valid_combos()
                                              and True])
    action_obj = ACTIONS[action]
    gender = args.gender or "girl"
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, container=container, action=action, surprise=surprise,
                       name=name, gender=gender, parent=parent, trait=trait)


def _do_fill(world: World, child: Entity, action: FillAction, container: Entity, spec: ContainerSpec) -> None:
    child.memes["pride"] += 0.4
    child.meters["readiness"] += 0.3
    container.meters["fullness"] += 1.0
    container.meters["neatness"] += 0.2 if action.item_mess == 0 else -0.1
    if action.item_warmth:
        container.meters["warmth"] += action.item_warmth
    child.memes["delight"] += action.item_delight
    if container.meters["fullness"] > spec.capacity:
        child.memes["worry"] += 0.3


def _surprise(world: World, child: Entity, surprise: SurpriseSpec, container: Entity, parent: Entity) -> None:
    child.memes["surprise"] += 1.0
    child.memes["worry"] = max(0.0, child.memes["worry"] - surprise.mood_shift)
    child.memes["delight"] += surprise.mood_shift
    child.memes["calm"] += 0.3
    world.say(surprise.reveal)
    world.say(f"It made {child.id} pause, then smile at {parent.pronoun('object')}.")

    if surprise.id == "grandma":
        world.say(f"Now the {container.label} felt more like a little shared table than a box.")
    elif surprise.id == "note":
        world.say(f"The note made the careful filling feel kinder, not less perfect.")
    elif surprise.id == "warm_towel":
        world.say(f"The towel kept the cookies cozy, and the last one seemed extra special.")


def tell(setting: Setting, container: ContainerSpec, action: FillAction, surprise: SurpriseSpec,
         hero_name: str = "Maya", hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    box = world.add(Entity(id="Box", type="thing", label=container.label, phrase=container.phrase, owner=child.id, caretaker=parent.id))

    child.memes["pride"] += 0.5
    child.memes["worry"] += 0.2
    child.meters["readiness"] += 0.1

    world.say(f"{child.id} was a {('little ' + (hero_traits or ['gentle'])[0] + ' ' + hero_type).strip()} who liked things to look just right.")
    world.say(f"At {setting.place}, {child.id} started making {container.phrase} for {container.target}.")
    world.say(f"{child.pronoun().capitalize()} wanted it to be perfect, so {child.pronoun()} kept {action.gerund}.")

    _do_fill(world, child, action, box, container)
    world.say(f"After each careful scoop, the {container.label} looked a little fuller and a little nicer.")

    world.para()
    world.say(setting.detail or f"The room felt quiet and ordinary.")
    world.say(f"{child.id} checked the edges, then {action.verb} one more time to make it look neat.")

    world.facts.update(child=child, parent=parent, box=box, container=container, action=action, surprise=surprise, setting=setting)

    world.para()
    if surprise.id == "grandma":
        _surprise(world, child, surprise, box, parent)
    elif surprise.id == "note":
        _surprise(world, child, surprise, box, parent)
    else:
        _surprise(world, child, surprise, box, parent)

    world.say(f"In the end, {child.id} left the {container.label} full, tidy, and ready to share.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    container = f["container"]
    surprise = f["surprise"]
    return [
        f'Write a short slice-of-life story for a young child about "{child.id}" {action.gerund} and wanting it perfect.',
        f"Tell a gentle story where a child named {child.id} keeps {action.gerund} while filling a {container.label}, then gets a surprise.",
        f'Write a simple story with the feeling of perfection, filling, and surprise, centered on a {container.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    container: ContainerSpec = f["container"]
    action: FillAction = f["action"]
    surprise: SurpriseSpec = f["surprise"]
    return [
        QAItem(
            question=f"What was {child.id} trying to make at {world.setting.place}?",
            answer=f"{child.id} was trying to make {container.phrase} for {container.target}, and {child.pronoun()} wanted it to look perfect.",
        ),
        QAItem(
            question=f"Why did {child.id} keep {action.gerund}?",
            answer=f"{child.id} kept {action.gerund} because {child.pronoun('subject')} wanted the {container.label} to be neat, full, and just right.",
        ),
        QAItem(
            question=f"What surprised {child.id} near the end?",
            answer=f"{surprise.reveal} That surprise changed the feeling from careful work to a happier, shared moment.",
        ),
        QAItem(
            question=f"How did the story end for {container.label}?",
            answer=f"It ended with the {container.label} full, tidy, and ready to share.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    action: FillAction = f["action"]
    container: ContainerSpec = f["container"]
    surprise: SurpriseSpec = f["surprise"]
    out = [
        QAItem(
            question="What does it mean to make something perfect?",
            answer="To make something perfect means to take care with it, check it closely, and try to make it as nice and complete as you can.",
        ),
        QAItem(
            question=f"What is a {container.label} used for?",
            answer=f"A {container.label} is used to hold food or small things neatly so they can be carried or shared.",
        ),
    ]
    if action.requires_warmth or container.needs_warmth:
        out.append(QAItem(
            question="Why do some foods need to stay warm?",
            answer="Some foods need to stay warm because they taste best cozy and soft, and warmth helps keep them pleasant to eat.",
        ))
    if surprise.tags:
        out.append(QAItem(
            question="Why can a surprise feel nice?",
            answer="A surprise can feel nice when it turns an ordinary moment into something happy, helpful, or shared.",
        ))
    return out


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CONTAINERS[params.container], ACTIONS[params.action], SURPRISES[params.surprise],
                 params.name, params.gender, [params.trait, "careful"], params.parent)
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
    StoryParams(place="kitchen", container="bento", action="sandwich", surprise="note",
                name="Maya", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="backroom", container="tray", action="berries", surprise="grandma",
                name="Leo", gender="boy", parent="father", trait="patient"),
    StoryParams(place="kitchen", container="jar", action="cookies", surprise="warm_towel",
                name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.action} in {p.container} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

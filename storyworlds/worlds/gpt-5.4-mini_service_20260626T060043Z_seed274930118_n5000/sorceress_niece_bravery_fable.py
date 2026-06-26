#!/usr/bin/env python3
"""
storyworlds/worlds/sorceress_niece_bravery_fable.py
===================================================

A small fable-like story world about a sorceress, her niece, and a test of
bravery. The world simulates a simple premise-turn-resolution: a timid niece
faces a dark task, the sorceress warns her, the niece acts bravely, and the
result changes how both of them feel.

The story is intentionally classical and child-facing: one trouble, one choice,
one clear ending image.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"sorceress", "niece", "girl", "woman", "aunt"}
        male = {"boy", "man", "uncle", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    name: str
    verb: str
    gerund: str
    risk: str
    danger: str
    obstacle: str
    courage_gain: float = 1.0
    fear_gain: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    uses: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


def thresholded(v: float) -> bool:
    return v >= THRESHOLD


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if ent.kind != "character":
                continue
            if thresholded(ent.memes.get("bravery", 0.0)) and thresholded(ent.memes.get("fear", 0.0)):
                sig = ("brave_over_fear", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    if ent.memes.get("fear", 0.0) > 0:
                        ent.memes["fear"] = max(0.0, ent.memes["fear"] - 1.0)
                    ent.memes["resolve"] = ent.memes.get("resolve", 0.0) + 1.0
                    out.append(f"{ent.id} steadied her heart.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_trial(world: World, niece: Entity, trial: Trial) -> dict:
    sim = World(world.place)
    sim.entities = {
        eid: Entity(**{
            "id": e.id,
            "kind": e.kind,
            "type": e.type,
            "label": e.label,
            "phrase": e.phrase,
            "owner": e.owner,
            "caretaker": e.caretaker,
            "worn_by": e.worn_by,
            "plural": e.plural,
            "meters": dict(e.meters),
            "memes": dict(e.memes),
        })
        for eid, e in world.entities.items()
    }
    sim.fired = set(world.fired)
    sim.facts = dict(world.facts)
    sim.get(niece.id).memes["bravery"] = sim.get(niece.id).memes.get("bravery", 0.0) + trial.courage_gain
    sim.get(niece.id).memes["fear"] = sim.get(niece.id).memes.get("fear", 0.0) + trial.fear_gain
    _propagate(sim, narrate=False)
    return {
        "brave": thresholded(sim.get(niece.id).memes.get("bravery", 0.0)),
        "fear": sim.get(niece.id).memes.get("fear", 0.0),
        "resolve": sim.get(niece.id).memes.get("resolve", 0.0),
    }


def build_trial(world: World, trial: Trial, niece: Entity) -> None:
    niece.memes["fear"] = niece.memes.get("fear", 0.0) + 1.0
    world.say(f"{niece.id} looked at the {trial.obstacle} and felt her knees turn small.")
    world.say(f"She wanted to {trial.verb}, but the {trial.risk} made the path seem wide and dark.")


def warning(world: World, sorceress: Entity, niece: Entity, trial: Trial) -> bool:
    pred = predict_trial(world, niece, trial)
    if pred["brave"]:
        return False
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"If you rush into the {trial.obstacle}, you may come back with a frightened heart," '
        f"{sorceress.pronoun('subject').capitalize()} said. "
        f'"Bravery is not the same as shouting. It is doing the hard thing kindly."'
    )
    return True


def compromise(world: World, sorceress: Entity, niece: Entity, trial: Trial) -> Optional[Charm]:
    if trial.id == "bridge":
        charm = CHARM_REGISTRY["lantern"]
    elif trial.id == "well":
        charm = CHARM_REGISTRY["chalk"]
    else:
        charm = CHARM_REGISTRY["song"]
    if trial.id not in charm.helps:
        return None
    world.add(Entity(
        id=charm.id,
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=niece.id,
        caretaker=sorceress.id,
        plural=charm.plural,
    ))
    world.say(
        f'{sorceress.id} smiled and offered a kinder way: {charm.prep}.'
    )
    return charm


def accept(world: World, sorceress: Entity, niece: Entity, trial: Trial, charm: Charm) -> None:
    niece.memes["bravery"] = niece.memes.get("bravery", 0.0) + trial.courage_gain
    niece.memes["fear"] = max(0.0, niece.memes.get("fear", 0.0) - 1.0)
    niece.memes["joy"] = niece.memes.get("joy", 0.0) + 1.0
    sorceress.memes["pride"] = sorceress.memes.get("pride", 0.0) + 1.0
    _propagate(world, narrate=False)
    world.say(
        f'{niece.id} took the {charm.label}, nodded, and chose the safer path. '
        f"{charm.tail}. "
        f"At last she could {trial.gerund}, and the dark place no longer felt lonely."
    )


def tell(place: Place, trial: Trial, niece_name: str = "Elena") -> World:
    world = World(place)
    sorceress = world.add(Entity(id="AuntStar", kind="character", type="sorceress", label="the sorceress"))
    niece = world.add(Entity(id=niece_name, kind="character", type="niece"))
    world.facts.update(sorceress=sorceress, niece=niece, trial=trial, place=place)

    world.say(f"There was once a sorceress named {sorceress.id} who loved her niece very much.")
    world.say(f"{niece.id} was little, curious, and not yet sure she could be brave.")
    world.say(f"One evening, the sorceress showed her a small hard task: {trial.name}.")
    world.say(f"The lesson was simple: bravery grows when a child faces one hard thing at a time.")

    world.para()
    build_trial(world, trial, niece)
    warning(world, sorceress, niece, trial)

    world.para()
    niece.memes["bravery"] = niece.memes.get("bravery", 0.0) + 1.0
    world.say(f"{niece.id} took a slow breath and held her chin a little higher.")
    charm = compromise(world, sorceress, niece, trial)
    if charm is not None:
        accept(world, sorceress, niece, trial, charm)

    return world


PLACES = {
    "old_tower": Place(name="the old tower", kind="tower", affords={"bridge", "well", "cave"}),
    "moon_garden": Place(name="the moon garden", kind="garden", affords={"bridge", "cave"}),
    "river_path": Place(name="the river path", kind="path", affords={"bridge", "well"}),
}

TRIALS = {
    "bridge": Trial(
        id="bridge",
        name="cross the swaying bridge over the dark stream",
        verb="cross the bridge",
        gerund="crossing the bridge",
        risk="wind",
        danger="water below",
        obstacle="bridge",
        tags={"bridge", "bravery"},
    ),
    "well": Trial(
        id="well",
        name="drop a shining bucket into the deep well to fetch clean water",
        verb="drop the bucket into the well",
        gerund="drawing water from the well",
        risk="echoing dark",
        danger="deep water",
        obstacle="well",
        tags={"well", "bravery"},
    ),
    "cave": Trial(
        id="cave",
        name="walk into the little cave to rescue a lost lamb",
        verb="step into the cave",
        gerund="walking into the cave",
        risk="shadows",
        danger="echoes",
        obstacle="cave",
        tags={"cave", "bravery"},
    ),
}

CHARMS = {
    "lantern": Charm(
        id="lantern",
        label="a lantern",
        phrase="a small lantern with a steady flame",
        helps={"bridge"},
        uses={"light"},
        prep="light a lantern and hold it between them",
        tail="They walked one careful step at a time",
    ),
    "chalk": Charm(
        id="chalk",
        label="a chalk line",
        phrase="a piece of white chalk",
        helps={"well"},
        uses={"marking"},
        prep="draw a chalk line so the bucket would not slip",
        tail="The bucket went down straight and came up shining",
    ),
    "song": Charm(
        id="song",
        label="a soft song",
        phrase="a soft song for frightened feet",
        helps={"cave"},
        uses={"comfort"},
        prep="sing a soft song and keep close together",
        tail="Their voices made the cave feel smaller and kinder",
    ),
}

CHILD_NAMES = ["Elena", "Mira", "Nina", "Tessa", "Luna", "Ivy", "Mabel", "Clara"]
TRAITS = ["careful", "gentle", "curious", "timid", "bright", "earnest"]


@dataclass
class StoryParams:
    place: str
    trial: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p, place in PLACES.items() for t in place.affords for _ in [0] if t in TRIALS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    niece = f["niece"]
    trial = f["trial"]
    return [
        f'Write a short fable about a sorceress and her niece named {niece.id} learning bravery at {world.place.name}.',
        f"Tell a child-sized story where {niece.id} must {trial.verb}, fears the {trial.risk}, and finds a gentle brave way through.",
        f'Write a simple fable using the words "sorceress", "niece", and "bravery" with a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    niece: Entity = f["niece"]
    sorceress: Entity = f["sorceress"]
    trial: Trial = f["trial"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {niece.id}, her sorceress aunt, and the brave thing they faced together.",
        ),
        QAItem(
            question=f"What did {niece.id} want to do in the story?",
            answer=f"{niece.id} wanted to {trial.verb}, even though the {trial.risk} made her nervous.",
        ),
        QAItem(
            question=f"Why did the sorceress speak softly to {niece.id}?",
            answer=f"The sorceress spoke softly because she wanted {niece.id} to be brave without feeling rushed or alone.",
        ),
        QAItem(
            question=f"What changed after {niece.id} chose the safer way?",
            answer=f"{niece.id} felt braver, the fear got smaller, and the path felt kind instead of scary.",
        ),
    ]
    if f.get("charm"):
        charm: Charm = f["charm"]
        qa.append(
            QAItem(
                question=f"How did {charm.label} help {niece.id}?",
                answer=f"{charm.label.capitalize()} helped because it gave {niece.id} a calm way to face the hard task while staying safe.",
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is bravery?",
        answer="Bravery is doing something hard or scary even when your heart feels shaky, because you know it is the right thing to do.",
    ),
    QAItem(
        question="Who is a sorceress?",
        answer="A sorceress is a woman in stories who can work magic, cast spells, or use enchanted things.",
    ),
    QAItem(
        question="What is a niece?",
        answer="A niece is the daughter of your brother or sister, or the child of your sibling.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_tower", trial="bridge", name="Elena", trait="careful"),
    StoryParams(place="river_path", trial="well", name="Mira", trait="timid"),
    StoryParams(place="moon_garden", trial="cave", name="Nina", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about a sorceress, her niece, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.trial:
        combos = [c for c in combos if c[1] == args.trial]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trial = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TRIALS[params.trial], params.name)
    world.facts["charm"] = None
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
place(old_tower).
place(moon_garden).
place(river_path).

trial(bridge).
trial(well).
trial(cave).

affords(old_tower, bridge).
affords(old_tower, well).
affords(old_tower, cave).
affords(moon_garden, bridge).
affords(moon_garden, cave).
affords(river_path, bridge).
affords(river_path, well).

valid(Place, Trial) :- affords(Place, Trial).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("place", pid) for pid in PLACES]
        + [asp.fact("trial", tid) for tid in TRIALS]
        + [asp.fact("affords", p, t) for p, place in PLACES.items() for t in sorted(place.affords)]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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

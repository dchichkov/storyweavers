#!/usr/bin/env python3
"""
storyworlds/worlds/burden_camera_lesson_learned_myth.py
========================================================

A small myth-style storyworld about a young hero, a heavy burden, and a camera.
The tales begin in wonder, move through a test, and end with a lesson learned.
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Trial:
    id: str
    act: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Burden:
    label: str
    phrase: str
    type: str
    weight: float
    lesson: str
    plural: bool = False


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    steadies: bool = False
    prep: str = ""
    tail: str = ""
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        other = World(self.setting)
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = dict(self.facts)
        return other


def _light_burden(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.meters.get("burden", 0) < 1:
            continue
        if hero.meters.get("tired", 0) < 1:
            sig = ("tired", hero.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            hero.meters["tired"] = 1
            out.append(f"The weight made {hero.id} slower and quieter.")
    return out


def _drop_camera(world: World) -> list[str]:
    out = []
    camera = world.entities.get("camera")
    hero = world.entities.get("hero")
    if not camera or not hero:
        return out
    if camera.carried_by != hero.id:
        return out
    if hero.meters.get("careless", 0) < 1:
        return out
    sig = ("drop", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    camera.meters["shaken"] = camera.meters.get("shaken", 0) + 1
    out.append("The camera shook in the hero's hands.")
    return out


CAUSAL_RULES = [
    _light_burden,
    _drop_camera,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                lines.extend(s)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


SETTINGS = {
    "temple_steps": Setting(place="the temple steps", indoor=False, affords={"climb"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"carry"}),
    "shore": Setting(place="the shore", indoor=False, affords={"walk"}),
}

TRIALS = {
    "climb": Trial(
        id="climb",
        act="climb the high steps",
        gerund="climbing the high steps",
        rush="rush up the steps",
        risk="the camera could slip",
        zone={"hands"},
        keyword="steps",
        lesson="move with care when the road is steep",
        tags={"high", "care"},
    ),
    "carry": Trial(
        id="carry",
        act="carry the camera through the orchard",
        gerund="carrying the camera through the orchard",
        rush="hurry between the trees",
        risk="the camera could bump against the burden",
        zone={"hands", "torso"},
        keyword="camera",
        lesson="even a dear thing can be too heavy for one pair of arms",
        tags={"camera", "burden"},
    ),
    "walk": Trial(
        id="walk",
        act="walk by the waves with the camera",
        gerund="walking by the waves with the camera",
        rush="run toward the shining water",
        risk="salt spray could reach the camera",
        zone={"hands"},
        keyword="waves",
        lesson="the sea asks for patience",
        tags={"water"},
    ),
}

BURDENS = {
    "camera_bag": Burden(
        label="camera bag",
        phrase="a leather camera bag",
        type="bag",
        weight=2.0,
        lesson="a good strap can share the load",
    ),
    "camera": Burden(
        label="camera",
        phrase="an old silver camera",
        type="camera",
        weight=1.5,
        lesson="a sacred tool should be held steady",
    ),
    "stone_bundle": Burden(
        label="bundle",
        phrase="a bundle of smooth stones",
        type="stones",
        weight=2.2,
        lesson="not every treasure belongs in one hand",
        plural=True,
    ),
}

AIDS = [
    Aid(
        id="strap",
        label="a woven strap",
        covers={"hands", "torso"},
        steadies=True,
        prep="fasten a woven strap around the camera",
        tail="fastened the woven strap and walked more easily",
    ),
    Aid(
        id="satchel",
        label="a small satchel",
        covers={"hands", "torso"},
        steadies=True,
        prep="place the camera in a small satchel",
        tail="placed the camera in the small satchel and continued",
    ),
]

GIVEN_NAMES = ["Ari", "Mara", "Ivo", "Lina", "Tavi", "Nia"]
TRAITS = ["curious", "brave", "gentle", "earnest", "watchful"]


@dataclass
class StoryParams:
    place: str
    trial: str
    burden: str
    name: str
    trait: str
    seed: Optional[int] = None


def burden_at_risk(trial: Trial, burden: Burden) -> bool:
    return burden.weight >= 1.5 and ("camera" in trial.tags or burden.type == "camera")


def select_aid(trial: Trial, burden: Burden) -> Optional[Aid]:
    for aid in AIDS:
        if "hands" in aid.covers and burden_at_risk(trial, burden):
            return aid
    return None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trial and args.burden:
        trial = TRIALS[args.trial]
        burden = BURDENS[args.burden]
        if not burden_at_risk(trial, burden):
            raise StoryError("No story: this burden does not truly threaten the camera in that trial.")
        if select_aid(trial, burden) is None:
            raise StoryError("No story: there is no fitting aid that can carry the burden safely.")
    choices = [
        (place, trial_id, burden_id)
        for place, setting in SETTINGS.items()
        for trial_id in setting.affords
        for burden_id in BURDENS
        if (args.place is None or args.place == place)
        and (args.trial is None or args.trial == trial_id)
        and (args.burden is None or args.burden == burden_id)
        and burden_at_risk(TRIALS[trial_id], BURDENS[burden_id])
        and select_aid(TRIALS[trial_id], BURDENS[burden_id]) is not None
    ]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, trial_id, burden_id = rng.choice(sorted(choices))
    name = args.name or rng.choice(GIVEN_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial_id, burden=burden_id, name=name, trait=trait)


def _hero_name(world: World) -> str:
    return world.facts["hero"].id


def tell(setting: Setting, trial: Trial, burden: Burden, name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="boy", label=name))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label="the elder"))
    cam = world.add(Entity(id="camera", type="camera", label="camera", phrase=burden.phrase, caretaker=elder.id))
    cam.carried_by = hero.id
    hero.meters["burden"] = burden.weight
    hero.memes["wonder"] = 1
    hero.memes["desire"] = 1
    world.facts.update(hero=hero, elder=elder, camera=cam, trial=trial, burden=burden, setting=setting)
    world.say(f"{hero.id} was a {trait} child who listened for signs in the air.")
    world.say(f"{hero.id} loved the camera because it could catch light like a net catches fish.")
    world.say(f"Yet the camera was also a burden, and the burden made {hero.id}'s arms grow tired.")
    world.para()
    world.say(f"One day at {setting.place}, {hero.id} wanted to {trial.act}.")
    world.say(f"But {trial.risk}.")
    hero.meters["careless"] = 1
    world.say(f"{hero.id} tried to {trial.rush}, and the burden tugged hard.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"The elder saw the strain and spoke like a story from old days.")
    world.say(f'"{trial.lesson.capitalize()}," {elder.pronoun("subject")} said. "Let us share the weight."')
    aid = select_aid(trial, burden)
    if aid:
        hero.meters["careless"] = 0
        hero.meters["steadied"] = 1
        hero.meters["burden"] = 0.5
        cam.carried_by = hero.id
        cam.protective = True
        world.say(f"They chose {aid.label}, and the elder helped {hero.id} {aid.prep}.")
        world.say(f"With the load steadied, {hero.id} could {trial.act} without fear.")
        world.say(f"In the end, {hero.id} {aid.tail}, and the camera stayed safe.")
        world.say(f"{hero.id} learned that a burden is lighter when wisdom carries part of it.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about burden and camera, where {f["hero"].id} learns a lesson.',
        f"Tell a gentle mythic story in which {f['hero'].id} faces a burden with a camera and discovers a wiser way.",
        f"Write a small legendary tale that ends with a clear lesson learned and the camera kept safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    trial = f["trial"]
    burden = f["burden"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"What burden did {hero.id} carry in the story?",
            answer=f"{hero.id} carried {burden.phrase}, and it felt heavy enough to slow {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {trial.act}, but the burden made the plan harder.",
        ),
        QAItem(
            question=f"Who helped {hero.id} learn the lesson?",
            answer=f"The elder helped {hero.id} learn the lesson by sharing the weight and making a safer plan.",
        ),
        QAItem(
            question=f"What was the lesson learned?",
            answer=f"The lesson was that {trial.lesson}, and a hard task can become easier when someone helps.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does a camera do?",
            answer="A camera saves pictures of light, people, and places so they can be remembered later.",
        ),
        QAItem(
            question="What is a burden?",
            answer="A burden is something heavy or difficult to carry, whether it is on the body or in the heart.",
        ),
        QAItem(
            question="Why is sharing a load helpful?",
            answer="Sharing a load can keep one person from becoming too tired and can help keep things safe.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
burden_at_risk(T,B) :- trial(T), burden(B), burden_weight(B,W), W >= 1.5, trial_tag(T,camera).
has_aid(T,B) :- burden_at_risk(T,B), aid(A), aid_covers(A,hands).
valid(T,B) :- burden_at_risk(T,B), has_aid(T,B).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for t in sorted(setting.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("trial_tag", tid, "camera"))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("burden_weight", bid, int(b.weight * 10)))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for c in sorted(a.covers):
            lines.append(asp.fact("aid_covers", a.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trial_id in setting.affords:
            trial = TRIALS[trial_id]
            for burden_id, burden in BURDENS.items():
                if burden_at_risk(trial, burden) and select_aid(trial, burden) is not None:
                    combos.append((place, trial_id, burden_id))
    return combos


def asp_verify() -> int:
    py = set(valid_combos())
    # ASP facts do not encode place in this tiny twin; parity is checked on trial/burden pairs.
    asp_pairs = {(t, b) for _, t, b in asp_valid()}
    py_pairs = {(t, b) for _, t, b in py}
    if asp_pairs == py_pairs:
        print(f"OK: ASP matches Python on {len(py_pairs)} valid burden/trial pairs.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_pairs - py_pairs))
    print("only in Python:", sorted(py_pairs - asp_pairs))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-style story world about burden, camera, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TRIALS[params.trial], BURDENS[params.burden], params.name, params.trait)
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
    StoryParams(place="temple_steps", trial="climb", burden="camera", name="Ari", trait="curious"),
    StoryParams(place="orchard", trial="carry", burden="camera_bag", name="Mara", trait="watchful"),
    StoryParams(place="shore", trial="walk", burden="stone_bundle", name="Ivo", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trial and args.burden:
        if not burden_at_risk(TRIALS[args.trial], BURDENS[args.burden]):
            raise StoryError("No story: this burden does not truly test the camera.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.trial is None or c[1] == args.trial)
        and (args.burden is None or c[2] == args.burden)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, trial, burden = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        trial=trial,
        burden=burden,
        name=args.name or rng.choice(GIVEN_NAMES),
        trait=rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_combos()
        print(f"{len(triples)} valid combinations:\n")
        for p, t, b in triples:
            print(f"  {p:12} {t:10} {b:12}")
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

#!/usr/bin/env python3
"""
storyworlds/worlds/perspective_array_moral_value_myth.py
========================================================

A standalone story world for a small mythic domain about perspective, an array
of viewpoints, and moral value.

Seed tale premise:
- A young listener is given a sacred array of polished sight-stones.
- The stones show different sides of the same trouble.
- At first, the listener wants to judge quickly.
- Then the array reveals the missing view, and the story ends with a wiser act.

The world is intentionally small and constraint-checked:
- One hero, one elder, one trouble, one moral value, one mythic artifact.
- The story is driven by the world state, not by a frozen paragraph template.
- The artifact only helps when it genuinely changes what the hero can perceive.
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
        female = {"girl", "woman", "mother", "sister", "daughter"}
        male = {"boy", "man", "father", "brother", "son"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    label: str
    virtue: str
    lesson: str
    color: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    reveals: str
    array_size: int
    sheen: str
    value: str


@dataclass
class Trouble:
    id: str
    verb: str
    rush: str
    confusion: str
    risk: str
    affects: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def predict_trouble(world: World, hero: Entity, trouble: Trouble, artifact: Artifact) -> dict:
    sim = world.copy()
    _do_trouble(sim, sim.get(hero.id), trouble, narrate=False)
    return {
        "confused": bool(sim.get(hero.id).memes.get("confusion", 0.0) >= THRESHOLD),
        "has_view": bool(sim.get(hero.id).memes.get("broader_view", 0.0) >= THRESHOLD),
    }


def _do_trouble(world: World, hero: Entity, trouble: Trouble, narrate: bool = True) -> None:
    hero.meters[trouble.affects] = hero.meters.get(trouble.affects, 0.0) + 1
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    if narrate:
        world.say(
            f"{hero.pronoun('subject').capitalize()} saw the {trouble.id}, "
            f"and the scene felt tangled."
        )


def _use_artifact(world: World, hero: Entity, artifact: Artifact, value: MoralValue) -> None:
    hero.memes["broader_view"] = hero.memes.get("broader_view", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.pronoun('subject').capitalize()} lifted the {artifact.label}, "
        f"and the {artifact.sheen} surface made the different sides easier to see."
    )
    world.say(
        f"The array showed {artifact.reveals}, and the lesson of {value.label} "
        f"stood at the center like a lamp."
    )


def _speak_wisely(world: World, hero: Entity, elder: Entity, value: MoralValue, trouble: Trouble) -> None:
    hero.memes["clarity"] = hero.memes.get("clarity", 0.0) + 1
    hero.memes["confusion"] = 0.0
    world.say(
        f'"{value.lesson}," {elder.pronoun("subject")} said. '
        f'"When we choose {value.virtue}, we do not rush past the whole truth."'
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} nodded and remembered that the "
        f"{trouble.id} was not one-sided."
    )


def _resolve(world: World, hero: Entity, elder: Entity, value: MoralValue, trouble: Trouble) -> None:
    hero.memes["moral_value"] = hero.memes.get("moral_value", 0.0) + 1
    world.say(
        f"{hero.pronoun('subject').capitalize()} walked back to the others with "
        f"a steadier heart and told the truth of both sides."
    )
    world.say(
        f"Because {hero.pronoun('subject')} chose {value.label}, the quarrel softened, "
        f"and the people could mend what was broken."
    )


def tell(setting: Setting, value: MoralValue, artifact: Artifact, trouble: Trouble,
         hero_name: str = "Mira", hero_type: str = "girl", elder_type: str = "woman") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    relic = world.add(Entity(
        id=artifact.id,
        type="artifact",
        label=artifact.label,
        phrase=artifact.phrase,
        owner=elder.id,
    ))

    world.say(
        f"In {setting.place}, {hero_name} was a small listener who loved old stories and "
        f"noticed how one event could look many ways."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} kept a careful heart, but {hero.pronoun('subject')} "
        f"still liked to decide fast when a problem appeared."
    )
    world.say(
        f"One dawn, {elder.pronoun('subject')} placed {relic.phrase} into {hero_name}'s hands "
        f"and called it a {artifact.label}."
    )
    world.say(
        f"It held {artifact.array_size} little panes, and each pane shone {artifact.sheen}."
    )

    world.para()
    world.say(
        f"That day a {trouble.id} rose in {setting.place}: people saw {trouble.confusion}, "
        f"and the first answer looked simple."
    )
    world.say(
        f"{hero_name} wanted to {trouble.verb}, but that would have been too quick, "
        f"because the scene could still hide the truest side."
    )

    pred = predict_trouble(world, hero, trouble, artifact)
    if not pred["confused"]:
        raise StoryError("The chosen trouble is too small; it does not need the array's wider view.")

    world.say(
        f"{hero_name} nearly chose at once, yet {hero.pronoun('possessive')} hands paused "
        f"on the edge of the shining array."
    )
    _use_artifact(world, hero, artifact, value)
    _speak_wisely(world, hero, elder, value, trouble)

    world.para()
    _resolve(world, hero, elder, value, trouble)
    world.say(
        f"In the end, the {artifact.label} rested quiet again, and {setting.place} felt "
        f"as if the whole sky had turned a little wiser."
    )

    world.facts.update(
        hero=hero,
        elder=elder,
        artifact=relic,
        value=value,
        trouble=trouble,
        setting=setting,
    )
    return world


SETTINGS = {
    "hill": Setting(place="the hill of names", affords={"listening", "judging"}),
    "river": Setting(place="the river shrine", affords={"listening", "judging"}),
    "court": Setting(place="the old stone court", affords={"listening", "judging"}),
}

MORAL_VALUES = {
    "truth": MoralValue(
        id="truth",
        label="truth",
        virtue="truth",
        lesson="Look at all the facts before you speak",
        color="clear",
    ),
    "mercy": MoralValue(
        id="mercy",
        label="mercy",
        virtue="mercy",
        lesson="A soft answer can mend what a hard answer would break",
        color="gold",
    ),
    "justice": MoralValue(
        id="justice",
        label="justice",
        virtue="justice",
        lesson="Fairness means hearing every side before choosing",
        color="silver",
    ),
    "courage": MoralValue(
        id="courage",
        label="courage",
        virtue="courage",
        lesson="Brave hearts do not need to hurry",
        color="red",
    ),
}

ARTIFACTS = {
    "array": Artifact(
        id="array",
        label="perspective array",
        phrase="a tray of seven polished sight-stones",
        reveals="the same trouble from seven different angles",
        array_size=7,
        sheen="like moonlit water",
        value="justice",
    ),
    "mirror_array": Artifact(
        id="mirror_array",
        label="mirror array",
        phrase="a ring of nine silver mirrors",
        reveals="faces, footprints, and the space between them",
        array_size=9,
        sheen="like bright dawn",
        value="truth",
    ),
    "lens_array": Artifact(
        id="lens_array",
        label="lens array",
        phrase="a set of five colored lenses",
        reveals="small details that a rushing eye would miss",
        array_size=5,
        sheen="like rain over glass",
        value="mercy",
    ),
}

TROUBLES = {
    "feud": Trouble(
        id="feud",
        verb="judge the feud",
        rush="walk in and blame one side",
        confusion="two families shouting over one broken bowl",
        risk="the wrong person being blamed",
        affects="strain",
    ),
    "bridge": Trouble(
        id="bridge",
        verb="name the blame",
        rush="point at the first worried face",
        confusion="a bridge snapped after the storm and everyone looked afraid",
        risk="fear turning into a harsh verdict",
        affects="strain",
    ),
    "gift": Trouble(
        id="gift",
        verb="decide the gift",
        rush="choose the prettiest pile",
        confusion="three children each claimed the same festival offering",
        risk="envy making a small wound larger",
        affects="strain",
    ),
}

CURATED = [
    ("hill", "justice", "array", "feud"),
    ("river", "truth", "mirror_array", "bridge"),
    ("court", "mercy", "lens_array", "gift"),
]

GIRL_NAMES = ["Mira", "Nina", "Suri", "Tala", "Asha", "Lina"]
BOY_NAMES = ["Arin", "Kian", "Oren", "Ravi", "Seth", "Taro"]


@dataclass
class StoryParams:
    place: str
    value: str
    artifact: str
    trouble: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about perspective, array, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--value", choices=MORAL_VALUES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    value = args.value or rng.choice(list(MORAL_VALUES))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    if artifact == "array" and value != "justice":
        pass
    if args.artifact and args.value and ARTIFACTS[artifact].value != value:
        raise StoryError("That artifact does not fit that moral value in this mythic world.")
    return StoryParams(place=place, value=value, artifact=artifact, trouble=trouble, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mythic story for a child about perspective and an array, using the word "{f["artifact"].label}".',
        f"Tell a gentle myth where {f['hero'].id} learns {f['value'].label} by looking through {f['artifact'].label}.",
        f"Write a simple story about a trouble at {f['setting'].place} that cannot be judged fairly from only one side.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    value = f["value"]
    artifact = f["artifact"]
    trouble = f["trouble"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} learn to do before judging the {trouble.id}?",
            answer=f"{hero.id} learned to pause and look through the {artifact.label} so {hero.pronoun('subject')} could see more than one side.",
        ),
        QAItem(
            question=f"Why did {elder.label} give {hero.id} the {artifact.label}?",
            answer=f"{elder.label} gave {hero.id} the {artifact.label} because {value.label} mattered, and the problem at {setting.place} needed a fairer view.",
        ),
        QAItem(
            question=f"What changed after {hero.id} used the {artifact.label}?",
            answer=f"{hero.id} became calmer, understood the fuller truth of the {trouble.id}, and spoke in a wiser way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    value = f["value"]
    artifact = f["artifact"]
    return [
        QAItem(
            question="What is a perspective?",
            answer="A perspective is the way something looks from one side or one point of view.",
        ),
        QAItem(
            question="What is an array?",
            answer="An array is a set of things laid out in order, like stones or mirrors arranged together.",
        ),
        QAItem(
            question=f"What does {value.label} mean?",
            answer=f"{value.label.capitalize()} means choosing what is fair and good, even when the answer is not quick or easy.",
        ),
        QAItem(
            question=f"What was special about the {artifact.label}?",
            answer=f"The {artifact.label} held several sight-stones, so it could show the same scene in many ways at once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
perspective(art).
array(art) :- perspective(art).
moral_value(truth).
moral_value(mercy).
moral_value(justice).
moral_value(courage).

fits(array, justice).
fits(mirror_array, truth).
fits(lens_array, mercy).

needs_view(feud).
needs_view(bridge).
needs_view(gift).

wisdom(Place, Value, Artifact, Trouble) :- setting(Place), moral(Value), art(Artifact),
                                           trouble(Trouble), fits(Artifact, Value),
                                           needs_view(Trouble).
#show wisdom/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for vid in MORAL_VALUES:
        lines.append(asp.fact("moral", vid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("art", aid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    models = asp.solve(asp_program("#show wisdom/4."), models=0)
    ok = len(models) > 0
    if ok:
        print("OK: ASP twin produced at least one wisdom model.")
        return 0
    print("MISMATCH: ASP twin produced no model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    value = MORAL_VALUES[params.value]
    artifact = ARTIFACTS[params.artifact]
    trouble = TROUBLES[params.trouble]
    world = tell(setting, value, artifact, trouble, params.name, params.gender)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show wisdom/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for i, (place, value, artifact, trouble) in enumerate(CURATED):
            params = StoryParams(
                place=place,
                value=value,
                artifact=artifact,
                trouble=trouble,
                name=("Mira" if i % 2 == 0 else "Arin"),
                gender=("girl" if i % 2 == 0 else "boy"),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.place} / {p.value} / {p.artifact} / {p.trouble}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

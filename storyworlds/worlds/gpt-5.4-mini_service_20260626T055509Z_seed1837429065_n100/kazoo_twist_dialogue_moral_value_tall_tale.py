#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/kazoo_twist_dialogue_moral_value_tall_tale.py
==============================================================================================================

A standalone story world for a tiny tall-tale domain: a child, a kazoo,
a noisy trouble, a surprising twist, dialogue, and a moral value ending.

Seed tale shape:
- A lanky child adores a kazoo and wants to blow it at the wrong moment.
- A grownup warns that the sound may spoil the moment.
- The child pushes ahead, then the world turns with a tall-tale twist.
- The kazoo becomes the right tool after all, and the story ends with a moral.

World model:
- Physical meters track noise, attention, and disturbance.
- Emotional memes track joy, worry, pride, embarrassment, and trust.
- The story is generated from the simulation, not from a frozen paragraph.

Narrative instruments:
- Twist: the expected problem becomes an unexpected help.
- Dialogue: the grownup and child speak directly.
- Moral value: the ending states the lesson earned by the turn.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held_by: Optional[str] = None
    loved: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def short(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    quietness: float = 0.0
    iconic_detail: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    noise: str
    twist_noise: str
    surprise: str
    risk: str
    keyword: str = "kazoo"


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "ears"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _name(title: str) -> str:
    return title.strip().capitalize()


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "fair": Setting(
        place="the county fair",
        indoor=False,
        affords={"kazoo"},
        quietness=0.2,
        iconic_detail="the ferris wheel creaked like a sleepy giant",
    ),
    "barn": Setting(
        place="the red barn",
        indoor=True,
        affords={"kazoo"},
        quietness=0.5,
        iconic_detail="the hay smelled sweet and the boards wore old boot prints",
    ),
    "porch": Setting(
        place="the front porch",
        indoor=False,
        affords={"kazoo"},
        quietness=0.7,
        iconic_detail="the porch steps looked long as a fishing dock",
    ),
}

ACTIVITIES = {
    "kazoo": Activity(
        id="kazoo",
        verb="blow the kazoo",
        gerund="blowing the kazoo",
        noise="loud buzzing",
        twist_noise="a brave, whistling tune",
        surprise="the tune reached something hidden far away",
        risk="spoil the quiet moment",
        keyword="kazoo",
    )
}

PRIZES = {
    "calf": Prize(
        id="calf",
        label="calf",
        phrase="a shy little calf",
        region="barnyard",
    ),
    "nap": Prize(
        id="nap",
        label="nap",
        phrase="a wagon-load nap time",
        region="quiet",
    ),
    "pie": Prize(
        id="pie",
        label="pie",
        phrase="a cooling cherry pie",
        region="table",
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Ada", "Nell", "June", "Lula"]
BOY_NAMES = ["Bennie", "Otis", "Cal", "Eli", "Hank", "Toby"]
TRAITS = ["lanky", "cheerful", "curious", "bold", "spry", "wiry"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: kazoo, twist, dialogue, moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.activity != "kazoo":
        raise StoryError("This world only models the kazoo story.")

    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize for this world.")

    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _act(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.meters["noise"] += 1
    hero.memes["joy"] += 1
    world.facts["did_act"] = True

    if prize.id == "nap":
        parent.memes["worry"] += 1
        world.say(f"{hero.short} wanted to {activity.verb}, but {parent.short} lifted a hand.")
        world.say(
            f'"Not while the {prize.label} is resting," {parent.pronoun("subject").capitalize()} said. '
            f'"That much {activity.noise} could {activity.risk}."'
        )
    elif prize.id == "pie":
        parent.memes["worry"] += 1
        world.say(f"{hero.short} wanted to {activity.verb}, but {parent.short} glanced at the cooling pie.")
        world.say(
            f'"Easy now," {parent.pronoun("subject").capitalize()} said. '
            f'"That {activity.noise} might make the crust jump right off the plate."'
        )
    else:
        parent.memes["worry"] += 1
        world.say(f"{hero.short} wanted to {activity.verb}, but {parent.short} looked toward the barnyard.")
        world.say(
            f'"Hold your breath a second," {parent.pronoun("subject").capitalize()} said. '
            f'"That {activity.noise} could startle the little calf."'
        )


def _twist(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.meters["noise"] += 1
    world.facts["twist"] = True
    world.say(
        f"{hero.short} blew anyway, and the kazoo sent out {activity.twist_noise}."
    )
    if prize.id == "calf":
        world.say(
            "Well, sir, that tune did not scare the calf at all. It turned the calf's ears toward the sound, "
            "and the little wanderer trotted straight out of the tall grass."
        )
        world.facts["helped_calf"] = True
    elif prize.id == "nap":
        world.say(
            "Well, sir, that buzzing did not wake the nap. It rolled past the porch like a warm breeze, "
            "and the sleepy hens began to march in a tidy row behind the tune."
        )
        world.facts["helped_calf"] = False
    else:
        world.say(
            "Well, sir, that buzzing did not ruin the pie. It shook a ribbon of dust from the rafters, "
            "and a hidden bee hive hummed out exactly where the cherry smoke was drifting."
        )
        world.facts["helped_calf"] = False


def _resolution(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["pride"] += 1
    parent.memes["pride"] += 1
    parent.memes["trust"] += 1
    world.para()

    if prize.id == "calf":
        world.say(
            f'{parent.short} laughed so hard the hat nearly flew off. "Ain\'t that a stitch?" '
            f'{parent.pronoun("subject").capitalize()} said. "Your kazoo found the calf better than a whistle ever could."'
        )
        world.say(
            f'{hero.short} grinned and tucked the kazoo under {hero.pronoun("possessive")} arm. '
            f'Together they led the calf home, and the long-legged child learned that a bold sound can help when it is used kindly.'
        )
        world.facts["moral"] = "A gift becomes mighty when it helps somebody else."
    elif prize.id == "nap":
        world.say(
            f'"I was wrong about the racket," {parent.short} admitted. "That tune did not break the rest; it gave the day a fresh step."'
        )
        world.say(
            f'{hero.short} bowed like a tiny bandleader on a wagon tongue, and the porch settled back to peace. '
            f'The child learned that a lively voice can still mind the room when it listens first.'
        )
        world.facts["moral"] = "Even a loud gift works best when it listens to the moment."
    else:
        world.say(
            f'"Well, butter my biscuit," {parent.short} said. "That kazoo uncovered more than trouble. It showed us a secret we would have missed."'
        )
        world.say(
            f'{hero.short} helped move the bees safely, then carried the pie inside to cool. '
            f'The child learned that courage is not just making noise; it is using your noise to do good.'
        )
        world.facts["moral"] = "Courage means using your gift for a good purpose."

    world.say(f"Moral: {world.facts['moral']}")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"noise": 0.0},
        memes={"joy": 0.0, "pride": 0.0, "worry": 0.0, "trust": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label=_name(parent_type),
        meters={"noise": 0.0},
        memes={"worry": 0.0, "pride": 0.0, "trust": 0.0},
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
    ))

    hero.memes["love_kazoo"] = 1.0
    world.say(
        f"{hero.short} was a {(' '.join(['little'] + (hero_traits or ['lanky']))) } {hero_type} who loved a kazoo more than a barn cat loves a sunny beam."
    )
    world.say(
        f"{hero.short} could make the kazoo buzz like a bumblebee and sing like a gate hinge in a summer storm."
    )
    world.say(
        f"At {setting.place}, the air was full of {setting.iconic_detail}."
    )
    world.say(
        f"{hero.short} carried the {prize.label} close, and {parent.short} knew the day might turn funny."
    )

    world.para()
    _act(world, hero, parent, activity, prize)
    _twist(world, hero, parent, activity, prize)
    _resolution(world, hero, parent, prize, activity)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    return [
        f'Write a tall-tale story for a child about a kazoo that starts as trouble and ends as help.',
        f"Tell a gentle tall tale where {hero.short} wants to {activity.verb}, {parent.short} worries about the {prize.label}, and a twist changes everything.",
        f'Write a story with dialogue and a moral value about a kazoo, a warning, and a surprising helpful turn.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]

    return [
        QAItem(
            question=f"Who wanted to {activity.verb} in the story?",
            answer=f"{hero.short} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.short} worry about the {prize.label}?",
            answer=f"{parent.short} worried because the kazoo's loud buzzing might {activity.risk}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=(
                "The twist was that the kazoo noise that seemed like trouble turned out to help instead."
            ),
        ),
        QAItem(
            question="What was the moral at the end?",
            answer=f"The story said: {world.facts['moral']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kazoo?",
            answer="A kazoo is a small musical instrument that makes a buzzing sound when you hum into it.",
        ),
        QAItem(
            question="Why can a loud sound matter in a quiet place?",
            answer="A loud sound can disturb rest, startle animals, or break a quiet moment, so people often ask for gentler play first.",
        ),
        QAItem(
            question="What does moral value mean in a story?",
            answer="A moral value is the lesson the story leaves behind about how to act kindly, wisely, or bravely.",
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
    lines.append("== (3) World knowledge ==")
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
        if e.phrase:
            bits.append(f'phrase="{e.phrase}"')
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="fair", activity="kazoo", prize="calf", name="Bennie", gender="boy", parent="father", trait="wiry"),
    StoryParams(place="barn", activity="kazoo", prize="nap", name="Mina", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="porch", activity="kazoo", prize="pie", name="Otis", gender="boy", parent="mother", trait="bold"),
]


ASP_RULES = r"""
place(P) :- setting(P).
possible(Place, A, Pr) :- affords(Place, A), activity(A), prize(Pr).

shown_story(Place, A, Pr) :- possible(Place, A, Pr).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show possible/3."))
    return sorted(set(asp.atoms(model, "possible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def resolve_restriction_error(args: argparse.Namespace) -> None:
    if args.activity and args.activity != "kazoo":
        raise StoryError("This world only supports the kazoo activity.")


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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
        print(asp_program("#show possible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show possible/3."))
        triples = sorted(set(asp.atoms(model, "possible")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
                resolve_restriction_error(args)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

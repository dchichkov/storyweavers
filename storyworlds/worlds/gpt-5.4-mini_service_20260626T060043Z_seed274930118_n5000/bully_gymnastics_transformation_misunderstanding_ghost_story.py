#!/usr/bin/env python3
"""
A small ghost-story-style world about a bullied young gymnast, a spooky
misunderstanding, and a gentle transformation.

The seed tale:
- In an old gym at night, a bully scares a child who loves gymnastics.
- A white shape in the dark seems like a ghost.
- The child learns it is only chalk, ribbons, and moonlight.
- The bully misunderstands, then transforms from mean to ashamed and kind.

The world model tracks:
- physical meters: chalk, tremble, brightness, bruised, grace
- emotional memes: fear, pride, kindness, apology, swagger, courage
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    transformation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    activity: str
    hero_name: str
    hero_type: str
    bully_name: str
    bully_type: str
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


def _propagate(world: World) -> None:
    hero = world.get("hero")
    bully = world.get("bully")
    if hero.memes.get("courage", 0) >= THRESHOLD and hero.meters.get("grace", 0) >= THRESHOLD:
        hero.memes["fear"] = 0
    if bully.memes.get("shame", 0) >= THRESHOLD and bully.memes.get("kindness", 0) >= THRESHOLD:
        bully.memes["swagger"] = 0


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["grace"] = hero.meters.get("grace", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    _propagate(world)


def tell(setting: Setting, activity: Activity, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=["little", "spirited"],
        meters={"grace": 0, "tremble": 1, "chalk": 0},
        memes={"fear": 1, "courage": 0},
    ))
    bully = world.add(Entity(
        id="bully",
        kind="character",
        type=params.bully_type,
        label=params.bully_name,
        traits=["loud", "swaggering"],
        meters={"noise": 1},
        memes={"swagger": 1, "kindness": 0},
    ))
    coach = world.add(Entity(
        id="coach",
        kind="character",
        type="adult",
        label="the coach",
        traits=["gentle", "watchful"],
        memes={"patience": 1},
    ))
    moon = world.add(Entity(
        id="moon",
        type="thing",
        label="moonlight",
        meters={"brightness": 1},
    ))
    chalk = world.add(Entity(
        id="chalk",
        type="thing",
        label="chalk dust",
        meters={"white": 1, "float": 1},
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        type="thing",
        label="a ribbon",
        meters={"white": 1, "flutter": 1},
    ))

    world.say(f"On a quiet night, {hero.label} slipped into {setting.place}.")
    world.say(
        f"{hero.label} loved {activity.gerund}, especially when the floor shone "
        f"under {setting.mood} light and the beams looked like they were waiting."
    )
    world.say(
        f"But {bully.label} liked to laugh at small things, and {bully.label} "
        f"snickered whenever {hero.label} warmed up."
    )

    world.para()
    world.say(
        f"Then {hero.label} reached for the chalk, and a pale cloud drifted up "
        f"like a shy little ghost."
    )
    world.say(
        f"{bully.label} pointed at the cloud and called, "
        f'"There is a ghost in the gym!"'
    )
    bully.memes["swagger"] += 1
    hero.memes["fear"] += 1

    world.say(
        f"{hero.label} nearly froze, because the shadow on the wall looked strange "
        f"and the ribbon on the bar fluttered like a white hand."
    )

    world.para()
    world.say(
        f"Then {coach.label} smiled and said, "
        f'"That is no ghost. It is only chalk, a ribbon, and moonlight playing tricks."'
    )
    world.say(
        f"{hero.label} took one deep breath and tried {activity.verb} anyway."
    )
    _do_activity(world, hero, activity)
    hero.meters["chalk"] = hero.meters.get("chalk", 0) + 1
    world.say(
        f"{hero.label} turned, jumped, and landed softly. The fear on {hero.label}'s "
        f"face changed into bright focus."
    )

    world.para()
    bully.memes["shame"] = bully.memes.get("shame", 0) + 1
    bully.memes["kindness"] = bully.memes.get("kindness", 0) + 1
    world.say(
        f"{bully.label} looked again and saw the truth: the 'ghost' was only the "
        f"white trail of chalk from {hero.label}'s hands."
    )
    world.say(
        f"{bully.label}'s loud grin melted into a quiet one. "
        f'"I was wrong," {bully.label} muttered. "You were not haunted. You were brave."'
    )
    world.say(
        f"After that, {bully.label} stopped teasing and offered to hold the mat, "
        f"while {hero.label} tried the roundoff one more time."
    )
    world.say(
        f"By the end, the gym was not spooky at all. It was warm with applause, "
        f"and the only ghost left was a silver cloud of chalk sparkling in the moon."
    )

    world.facts.update(
        hero=hero,
        bully=bully,
        coach=coach,
        moon=moon,
        chalk=chalk,
        ribbon=ribbon,
        activity=activity,
        setting=setting,
        resolved=True,
        misunderstood=True,
    )
    return world


SETTINGS = {
    "old_gym": Setting(
        place="the old gym",
        mood="moonlit",
        affords={"balance_beam", "floor_routine", "vault"},
    ),
    "school_gym": Setting(
        place="the school gym",
        mood="echoing",
        affords={"floor_routine", "bars"},
    ),
}

ACTIVITIES = {
    "balance_beam": Activity(
        id="balance_beam",
        verb="walk across the beam",
        gerund="walking the beam",
        rush="dash to the beam",
        risk="the wobble might make you fall",
        transformation="from trembling to steady",
        tags={"gymnastics", "balance", "beam", "transformation"},
    ),
    "floor_routine": Activity(
        id="floor_routine",
        verb="practice a floor routine",
        gerund="spinning and jumping across the floor",
        rush="run to the center of the mat",
        risk="the landing might be rough",
        transformation="from small steps to a shining turn",
        tags={"gymnastics", "floor", "chalk", "ghost", "misunderstanding"},
    ),
    "vault": Activity(
        id="vault",
        verb="run and vault",
        gerund="vaulting over the horse",
        rush="sprint at the vault",
        risk="the speed might scare a beginner",
        transformation="from scared to soaring",
        tags={"gymnastics", "vault", "transformation"},
    ),
    "bars": Activity(
        id="bars",
        verb="swing on the bars",
        gerund="swinging and flying",
        rush="climb to the bars",
        risk="the swing might slip",
        transformation="from shaky to strong",
        tags={"gymnastics", "bars", "transformation"},
    ),
}

GIRL_NAMES = ["Mina", "Tara", "Lia", "Pia", "Nina", "Eli", "Rosa", "June"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Arlo", "Noah", "Jude", "Evan"]
TRAITS = ["quiet", "brave", "curious", "gentle", "determined", "shy"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            out.append((s, a))
    return sorted(out)


ASP_RULES = r"""
setting(old_gym).
setting(school_gym).
activity(balance_beam).
activity(floor_routine).
activity(vault).
activity(bars).

affords(old_gym,balance_beam).
affords(old_gym,floor_routine).
affords(old_gym,vault).
affords(school_gym,floor_routine).
affords(school_gym,bars).

valid(S,A) :- affords(S,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for sid, s in SETTINGS.items():
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class PromptBundle:
    asks: list[str]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story-style story for a child where {f["hero"].label} does {f["activity"].gerund} in {f["setting"].place}.',
        f"Tell a gentle tale in an old gym where a bully mistakes chalk dust for a ghost, and the gymnast finds courage.",
        f'Write a short story about misunderstanding in a gym, using the words "bully" and "gymnastics".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, bully, coach, activity, setting = f["hero"], f["bully"], f["coach"], f["activity"], f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.label} practice {activity.verb}?",
            answer=f"{hero.label} practiced {activity.verb} in {setting.place}, under moonlit light.",
        ),
        QAItem(
            question=f"Why did {bully.label} think there was a ghost?",
            answer="The bully saw a white chalk cloud and the fluttering ribbon in the dark, and misunderstood them as something spooky.",
        ),
        QAItem(
            question=f"What changed after the coach explained the truth?",
            answer=f"{hero.label} grew more courageous, and {bully.label} stopped teasing and became ashamed and kinder.",
        ),
        QAItem(
            question=f"How was {hero.label} transformed by the end of the story?",
            answer=f"{hero.label} changed from trembling and doubtful into a steady gymnast with bright focus.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is gymnastics?",
            answer="Gymnastics is a sport where people balance, jump, swing, and tumble with a lot of control and practice.",
        ),
        QAItem(
            question="What is chalk used for in gymnastics?",
            answer="Gymnasts use chalk to help their hands grip better and to keep sweat from making the bars slippery.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they do not have the right idea yet.",
        ),
        QAItem(
            question="What is a bully?",
            answer="A bully is a person who is mean on purpose and tries to make someone else feel small or scared.",
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
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="old_gym", activity="floor_routine", hero_name="Mina", hero_type="girl",
                bully_name="Rex", bully_type="boy"),
    StoryParams(setting="school_gym", activity="bars", hero_name="Theo", hero_type="boy",
                bully_name="Max", bully_type="boy"),
    StoryParams(setting="old_gym", activity="balance_beam", hero_name="Lia", hero_type="girl",
                bully_name="Ned", bully_type="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story-style gymnastics world with a bully and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--bully-name")
    ap.add_argument("--bully-type", choices=["girl", "boy"])
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
    choices = valid_combos()
    if args.setting and args.activity and (args.setting, args.activity) not in choices:
        raise StoryError("That activity does not fit that setting.")
    combos = [c for c in choices if (args.setting is None or c[0] == args.setting) and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    setting, activity = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    bully_type = args.bully_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    bully_name = args.bully_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    if bully_name == hero_name:
        bully_name = "Rex"
    return StoryParams(setting=setting, activity=activity, hero_name=hero_name, hero_type=hero_type,
                       bully_name=bully_name, bully_type=bully_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], params)
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for s, a in triples:
            print(f"  {s:10} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.hero_name}: {p.activity} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A folk-tale storyworld about a cherished wok, a small kitchen mishap, and a
teamwork fix with a moral and a light rhyme.

The seed premise:
- A family or village uses a wok for a feast.
- Something goes wrong: the wok slips, tips, or gets blackened.
- One character wants to hide the mistake or rush ahead.
- Others help together, mend the problem, and the story ends with a moral.

The generated prose should feel like a child-facing folk tale:
- concrete, small-scale, and warm
- a little rhythmic or rhyming
- driven by world state rather than a frozen template

This script supports the standard storyworld CLI:
- default run
- -n
- --all
- --seed
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "daughter"}
        male = {"boy", "father", "dad", "man", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they" if self.plural else self.pronoun("subject")

    def them(self) -> str:
        return "them" if self.plural else self.pronoun("object")

    def their(self) -> str:
        return "their" if self.plural else self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    role: str
    action: str
    repair: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "cottage": Setting(place="the old cottage", indoor=True, affords={"porridge", "stew"}),
    "market": Setting(place="the village market", indoor=False, affords={"porridge", "stew"}),
    "hearth": Setting(place="the hearth-room", indoor=True, affords={"porridge", "stew"}),
}

ACTIVITIES = {
    "porridge": Activity(
        id="porridge",
        verb="stir the porridge",
        gerund="stirring porridge",
        rush="rush to the pot",
        mess="spilled",
        soil="spilled and sticky",
        keyword="porridge",
        tags={"food", "warm"},
    ),
    "stew": Activity(
        id="stew",
        verb="stir the stew",
        gerund="stirring stew",
        rush="hurry to the pot",
        mess="smeared",
        soil="smeared and smoky",
        keyword="stew",
        tags={"food", "warm"},
    ),
}

PRIZES = {
    "wok": Prize(
        id="wok",
        label="wok",
        phrase="a shiny black wok",
        region="hands",
    ),
    "lid": Prize(
        id="lid",
        label="lid",
        phrase="a round bronze lid",
        region="hands",
    ),
}

HELPERS = {
    "broom": Helper(
        id="broom",
        label="a broom",
        role="sweeper",
        action="sweep together",
        repair="swept the ashes clean",
    ),
    "cloth": Helper(
        id="cloth",
        label="a warm cloth",
        role="wiper",
        action="wipe together",
        repair="wiped the wok bright again",
    ),
    "spoon": Helper(
        id="spoon",
        label="a long spoon",
        role="stirrer",
        action="stir together",
        repair="stirred until the meal shone",
    ),
}

CHARACTER_NAMES = ["Mina", "Tilo", "Bram", "Suri", "Pip", "Jori", "Nela", "Taro"]
CHARACTER_TRAITS = ["kind", "clever", "patient", "brave", "gentle", "quick"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable if the activity can mess up the prize and a helper can fix it.
at_risk(A, P) :- splashes(A, R), worn_on(P, R).
has_fix(A, P) :- at_risk(A, P), helper(H), fixes(H, A, P).

valid(Place, A, P, H) :- affords(Place, A), at_risk(A, P), has_fix(A, P), fixes(H, A, P).
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
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in ("hands",):
            lines.append(asp.fact("splashes", aid, r))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("fixes", hid, "porridge", "wok"))
        lines.append(asp.fact("fixes", hid, "stew", "wok"))
        lines.append(asp.fact("fixes", hid, "porridge", "lid"))
        lines.append(asp.fact("fixes", hid, "stew", "lid"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "hands"


def select_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    for helper in HELPERS.values():
        if helper.id == "broom" and activity.id == "stew":
            return helper
        if helper.id == "cloth" and activity.id == "porridge":
            return helper
        if helper.id == "spoon":
            return helper
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            activity = ACTIVITIES[act]
            for prize_id, prize in PRIZES.items():
                helper = select_helper(activity, prize)
                if prize_at_risk(activity, prize) and helper is not None:
                    out.append((place, act, prize_id, helper.id))
    return out


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_story(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, helper: Helper) -> None:
    world.say(
        f"Once in {world.setting.place}, {hero.id} was a {hero.trait if hasattr(hero, 'trait') else 'kind'} little {hero.type} "
        f"who loved the old kitchen songs."
    )


def rhyme_line(activity: Activity) -> str:
    if activity.id == "porridge":
        return "Stir slow, stir neat, and keep the meal from your feet."
    return "Stir low, stir wise, and keep the steam from your eyes."


def intro(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} loved {activity.gerund}, and {hero.their()} {parent.type} had given {hero.them()} {prize.phrase}."
    )
    world.say(f"The old wok gleamed like a moon in the firelight.")
    world.say(rhyme_line(activity))


def conflict(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["want"] = 1
    world.para()
    world.say(
        f"One day {hero.id} wanted to {activity.verb}, but the {prize.label} slipped from {hero.their()} hands with a clink and a clatter."
    )
    hero.meters["stress"] = 1
    prize.meters["dirt"] = 1
    world.say(
        f"{parent.id} frowned gently. \"If the wok is dropped and the stew is spilled, the supper will be spoiled,\" {parent.pronoun('subject')} said."
    )
    hero.memes["worry"] = 1
    world.say(f"{hero.id} felt small as a pebble in a rain puddle.")


def teamwork(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity, helper: Helper) -> None:
    world.para()
    world.say(
        f"Then {hero.id} listened, and {hero.id} called for help. {parent.id} came, and {helper.label} was brought near."
    )
    world.say(
        f"Together they {helper.action}, for the old folk say, \"Many hands make light work, and a careful heart keeps the meal from harm.\""
    )
    world.say(
        f"{parent.id} held the handle, {hero.id} wiped the rim, and the helper made the task simple and sweet."
    )
    hero.memes["joy"] = 1
    hero.memes["moral"] = 1
    prize.meters["clean"] = 1
    world.say(f"The wok shone again, and the supper stayed safe.")


def ending(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.para()
    world.say(
        f"That night they ate by the fire, and {hero.id} learned the moral: when trouble comes, do not hide it, but share it."
    )
    world.say(
        f"Hand in hand and side by side, the little home was bright inside."
    )
    world.say(
        f"And so the wok sang softly in the firelight, as good meals often do, when hearts are true and hands work through."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, helper_cfg: Helper,
         hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother",
         trait: str = "kind") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait], meters={}, memes={}))
    hero.trait = trait  # for easy prose
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))
    helper = helper_cfg

    intro(world, hero, parent, prize, activity)
    conflict(world, hero, parent, prize, activity)
    teamwork(world, hero, parent, prize, activity, helper)
    ending(world, hero, parent, prize, activity)

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize,
        "activity": activity,
        "helper": helper,
        "setting": setting,
        "resolved": True,
    }
    return world


# ---------------------------------------------------------------------------
# Content / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for children about a {f["prize"].label}, teamwork, and a kind moral.',
        f"Tell a rhyme-like story where {f['hero'].id} and {f['parent'].id} fix a problem with the {f['prize'].label} together.",
        f"Write a gentle story that includes the word '{f['prize'].label}' and ends with a moral about sharing the work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    helper = f["helper"]

    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb}, but the {prize.label} slipped and caused trouble.",
        ),
        QAItem(
            question=f"Who helped {hero.id} fix the problem?",
            answer=f"{parent.id} helped, and {helper.label} was used so they could work together.",
        ),
        QAItem(
            question=f"What moral did {hero.id} learn in the end?",
            answer="The moral was to tell the truth, ask for help, and share the work with others.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "wok": [
        QAItem(
            question="What is a wok?",
            answer="A wok is a round cooking pan with high sides, often used for stirring and frying food quickly.",
        )
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do a job together.",
        )
    ],
    "moral": [
        QAItem(
            question="What is a moral in a story?",
            answer="A moral is the lesson a story teaches about how to act kindly or wisely.",
        )
    ],
    "rhyme": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'light' and 'bright'.",
        )
    ],
    "folk": [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story passed from person to person, often with a lesson or a bit of magic.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        WORLD_KNOWLEDGE["wok"][0],
        WORLD_KNOWLEDGE["teamwork"][0],
        WORLD_KNOWLEDGE["moral"][0],
        WORLD_KNOWLEDGE["rhyme"][0],
        WORLD_KNOWLEDGE["folk"][0],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", activity="porridge", prize="wok", helper="cloth", name="Mina", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="hearth", activity="stew", prize="lid", helper="broom", name="Bram", gender="boy", parent="father", trait="patient"),
    StoryParams(place="market", activity="porridge", prize="wok", helper="spoon", name="Suri", gender="girl", parent="mother", trait="clever"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a wok, teamwork, a moral, and a folk-tale rhyme.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
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
              and (args.prize is None or c[2] == args.prize)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHARACTER_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(CHARACTER_TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, helper=helper_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        HELPERS[params.helper],
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        trait=params.trait,
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


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize, helper) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.activity} with {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

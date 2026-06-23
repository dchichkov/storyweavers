#!/usr/bin/env python3
"""
storyworlds/worlds/olympian_spam_wise_riverbank_moral_value_heartwarming.py
=============================================================================

A small story world set at a riverbank, built from the seed words
"olympian", "spam", and "wise" in a heartwarming moral-value frame.

Premise:
- A child dreams of being an olympian and loves river play.
- A careless pile of spam tins / wrappers would spoil the riverbank picnic.
- A wise helper notices the harm early and suggests a kinder, cleaner plan.

The world keeps two kinds of state:
- meters: physical quantities such as mess, wetness, fullness, or cleanup
- memes: emotional quantities such as joy, worry, pride, and warmth

The stories are driven by state changes, not a frozen paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RIVER_REGIONS = {"bank", "water", "blanket"}
VALID_GENDER = {"girl", "boy"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    splash_zone: set[str]
    affords: set[str]


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    worry: str
    spread_to: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class WiseHelp:
    id: str
    label: str
    phrase: str
    method: str
    ending: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spam_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["spam"] < THRESHOLD:
            continue
        sig = ("spam_spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for obj in world.entities.values():
            if obj.kind == "thing" and obj.region in world.setting.splash_zone:
                obj.meters["messy"] += 1
                obj.meters["dirty"] += 1
        ent.memes["worry"] += 1
        out.append("__spam__")
    return out


def _r_cleanup_help(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["cleanup"] < THRESHOLD:
            continue
        sig = ("cleanup", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["warmth"] += 1
        ent.memes["pride"] += 1
        out.append("__cleanup__")
    return out


CAUSAL_RULES = [
    Rule("spam_spread", "physical", _r_spam_spread),
    Rule("cleanup_help", "social", _r_cleanup_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def warn_cost(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} noticed {problem.phrase} near the {world.setting.place} and frowned.")
    world.say(f"It could {problem.spread_to} and make the riverbank feel messy.")


def wise_plan(world: World, helper: Entity, hero: Entity, help_cfg: WiseHelp) -> None:
    helper.memes["wise"] += 1
    hero.memes["trust"] += 1
    hero.meters["cleanup"] += 1
    world.say(
        f"{helper.id} smiled a wise smile. \"Let's {help_cfg.method},\" {helper.pronoun()} said."
    )
    world.say(f"{helper.id} handed over {help_cfg.phrase} so {hero.id} could help too.")


def finish(world: World, hero: Entity, helper: Entity, help_cfg: WiseHelp) -> None:
    hero.memes["joy"] += 1
    hero.memes["warmth"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Together they {help_cfg.ending}, and the riverbank looked bright again."
    )
    world.say(
        f"{hero.id} stood a little taller, feeling like an olympian for helping in such a kind way."
    )


def play_setup(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a sunny day at the riverbank, {hero.id} loved to {activity.verb} while {helper.id} watched kindly."
    )
    world.say(
        f"{hero.id} dreamed of being an olympian someday, strong and steady like the rowers in storybooks."
    )


def slip_into_spam(world: World, hero: Entity, problem: Problem) -> None:
    hero.meters["spam"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} reached for {problem.phrase}, thinking it would make the picnic more exciting."
    )


def accept_help(world: World, hero: Entity, helper: Entity, problem: Problem, help_cfg: WiseHelp) -> None:
    helper.meters["cleanup"] += 1
    hero.meters["cleanup"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {helper.id} was wise. {helper.id} pointed to the river and said the trash should not go there."
    )
    world.say(
        f"{hero.id} listened, set down the {problem.label}, and chose {help_cfg.phrase} instead."
    )


def tell(setting: Setting, activity: Activity, problem: Problem, help_cfg: WiseHelp,
         hero_name: str = "Mina", hero_type: str = "girl",
         helper_name: str = "Grandma", helper_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    trash = world.add(Entity(id="trash", kind="thing", type="thing", label=problem.label,
                             phrase=problem.phrase, region="bank"))
    snack = world.add(Entity(id="snack", kind="thing", type="thing", label="lunch basket",
                             phrase="a lunch basket with fruit", region="blanket"))
    world.facts = {
        "hero": hero,
        "helper": helper,
        "problem": problem,
        "help_cfg": help_cfg,
        "activity": activity,
        "setting": setting,
        "trash": trash,
        "snack": snack,
        "resolved": False,
    }

    play_setup(world, hero, helper, activity)
    world.para()
    warn_cost(world, hero, problem)
    slip_into_spam(world, hero, problem)
    accept_help(world, hero, helper, problem, help_cfg)
    wise_plan(world, helper, hero, help_cfg)
    world.para()
    finish(world, hero, helper, help_cfg)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "riverbank": Setting(place="the riverbank", splash_zone={"bank", "blanket"}, affords={"skipping", "picnic", "feeding", "rowing"}),
}

ACTIVITIES = {
    "skipping": Activity(id="skipping", verb="skip stones", gerund="skipping stones", rush="run to the water", mess="wet fingers", zone={"water", "bank"}, keyword="stone", tags={"river", "play"}),
    "picnic": Activity(id="picnic", verb="share snacks", gerund="sharing snacks", rush="spoil the meal", mess="crumbs", zone={"blanket", "bank"}, keyword="picnic", tags={"food", "share"}),
    "feeding": Activity(id="feeding", verb="feed the ducks", gerund="feeding ducks", rush="run to the ducks", mess="crumbs", zone={"water", "bank"}, keyword="duck", tags={"kind", "animals"}),
    "rowing": Activity(id="rowing", verb="practice rowing", gerund="rowing like a champion", rush="grab the oar", mess="splashes", zone={"water", "bank"}, keyword="row", tags={"sport", "water"}),
}

PROBLEMS = {
    "spam": Problem(id="spam", label="spam tins", phrase="a pile of spam tins", worry="litter the water", spread_to="spill toward the river", mess="dirty", tags={"spam", "trash"}),
    "wrappers": Problem(id="wrappers", label="snack wrappers", phrase="a crinkly heap of snack wrappers", worry="blow away", spread_to="blow across the bank", mess="messy", tags={"trash"}),
    "cups": Problem(id="cups", label="paper cups", phrase="some paper cups left from lunch", worry="drift into the reeds", spread_to="float downstream", mess="messy", tags={"cleanup", "trash"}),
    "sticks": Problem(id="sticks", label="twigs and sticks", phrase="a tangle of sticks near the blanket", worry="scratch the picnic spot", spread_to="poke through the blanket", mess="messy", tags={"cleanup"}),
}

HELPS = {
    "basket": WiseHelp(id="basket", label="basket", phrase="a woven basket for collecting the litter", method="sort the trash into the basket", ending="carried the basket to the bin", tags={"cleanup"}),
    "gloves": WiseHelp(id="gloves", label="gloves", phrase="soft gloves for the cleanup", method="pick up the scraps with gloved hands", ending="patted the bank clean", tags={"cleanup"}),
    "tongs": WiseHelp(id="tongs", label="tongs", phrase="little tongs for the muddy pieces", method="lift the trash with little tongs", ending="emptied the last bits into the bin", tags={"cleanup"}),
    "bag": WiseHelp(id="bag", label="bag", phrase="a strong cloth bag", method="gather the litter into the cloth bag", ending="tied the bag and set it by the path", tags={"cleanup"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Maya", "June", "Ivy"]
BOY_NAMES = ["Eli", "Theo", "Finn", "Noah", "Owen", "Kai"]


@dataclass
class StoryParams:
    setting: str = "riverbank"
    activity: str = "skipping"
    problem: str = "spam"
    help: str = "basket"
    hero_name: str = "Mina"
    hero_gender: str = "girl"
    helper_name: str = "Grandma"
    helper_gender: str = "grandmother"
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="riverbank", activity="skipping", problem="spam", help="basket", hero_name="Mina", hero_gender="girl", helper_name="Grandma", helper_gender="grandmother"),
    StoryParams(setting="riverbank", activity="picnic", problem="wrappers", help="gloves", hero_name="Eli", hero_gender="boy", helper_name="Auntie", helper_gender="grandmother"),
    StoryParams(setting="riverbank", activity="feeding", problem="cups", help="tongs", hero_name="Nora", hero_gender="girl", helper_name="Grandpa", helper_gender="grandfather"),
    StoryParams(setting="riverbank", activity="rowing", problem="sticks", help="bag", hero_name="Theo", hero_gender="boy", helper_name="Wise Mom", helper_gender="mother"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for p in PROBLEMS:
                for h in HELPS:
                    combos.append((s, a, p, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming riverbank story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--help", dest="help_item", choices=HELPS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["mother", "father", "grandmother", "grandfather"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.problem is None or c[2] == args.problem)
              and (getattr(args, "help_item", None) is None or c[3] == args.help_item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, problem, help_item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["grandmother", "grandfather", "mother", "father"])
    helper = args.helper or rng.choice(["Grandma", "Grandpa", "Auntie", "Uncle", "Wise Mom", "Wise Dad"])
    return StoryParams(setting=setting, activity=activity, problem=problem, help=help_item,
                       hero_name=hero_name, hero_gender=gender, helper_name=helper,
                       helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming riverbank story that uses the words "olympian", "spam", and "wise".',
        f"Tell a gentle story where {f['hero'].id} wants to be an olympian someday, but a wise helper keeps {f['problem'].phrase} from making the riverbank messy.",
        f"Write a short moral-value story about a child, a riverbank, and a wise choice that turns spam into a cleanup lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, help_cfg, activity = f["hero"], f["helper"], f["problem"], f["help_cfg"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the riverbank before the wise helper spoke?",
            answer=f"{hero.id} wanted to {activity.verb}. It showed that {hero.id} loved the riverbank and hoped to be an olympian someday.",
        ),
        QAItem(
            question=f"Why did {helper.id} stop {hero.id} from leaving {problem.label} by the water?",
            answer=f"{helper.id} knew {problem.phrase} could make the bank dirty and drift toward the river. That would spoil the picnic spot and hurt the clean, kind feeling of the day.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} make the right choice?",
            answer=f"{helper.id} offered {help_cfg.phrase} and showed a wiser way to help. Together they cleaned up first, so {hero.id} could feel proud instead of careless.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The riverbank became neat and bright again, and {hero.id} stood there feeling warm and helpful. The ending proved that wise choices can make a day sweeter for everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wise mean?",
            answer="Wise means making a good choice by thinking ahead about what will help and what might cause harm. A wise person notices trouble early and chooses the kinder path.",
        ),
        QAItem(
            question="What is spam in this story world?",
            answer="Spam is treated as unwanted trash or junk that should not be left near the water. It is something to collect and throw away, not something to spread around.",
        ),
        QAItem(
            question="Why is a riverbank a place to keep clean?",
            answer="A riverbank is close to the water, so loose trash can wash or blow into the river. Keeping it clean helps animals, people, and the whole shoreline stay healthy.",
        ),
        QAItem(
            question="What is an olympian?",
            answer="An olympian is a person who trains very hard for sports and tries to do their very best. In this story, it is a dream of strength, practice, and steady effort.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.help not in HELPS:
        raise StoryError("Unknown help option.")
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PROBLEMS[params.problem], HELPS[params.help], params.hero_name, params.hero_gender, params.helper_name, params.helper_gender)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,A,P,H) :- setting(S), activity(A), problem(P), help(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for h in HELPS:
        lines.append(asp.fact("help", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP combos.")
        if py - cl:
            print(" only in python:", sorted(py - cl))
        if cl - py:
            print(" only in asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"Smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

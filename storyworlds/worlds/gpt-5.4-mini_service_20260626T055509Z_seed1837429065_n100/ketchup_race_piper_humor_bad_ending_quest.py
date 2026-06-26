#!/usr/bin/env python3
"""
ketchup_race_piper_humor_bad_ending_quest.py
=============================================

A tiny bedtime-story world about Piper, a ketchup quest, a silly race, and a
small bad ending that still feels complete.

Premise:
- Piper wants to win a kitchen race by delivering ketchup to the picnic table.
- The world tracks the bottle's physical state and Piper's feelings.
- Humor comes from the comic hurry and a few harmless mishaps.
- The story ends badly: the ketchup splashes, the race is lost, and the picnic
  must continue without the prize.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- lazy clingo import through storyworlds/asp.py for ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- physical meters and emotional memes drive prose
- invalid explicit choices raise StoryError with a clear reason
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
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Challenge:
    id: str
    name: str
    setup: str
    success: str
    fail: str
    risk_word: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    challenge: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"race", "quest"}),
    "hall": Setting(place="the hallway", indoor=True, affords={"race"}),
    "garden_path": Setting(place="the garden path", indoor=False, affords={"race", "quest"}),
}

ACTIVITIES = {
    "race": Activity(
        id="race",
        verb="race to the table",
        gerund="racing to the table",
        rush="dash down the hallway",
        mess="splat",
        soil="splatty",
        zone={"floor"},
        keyword="race",
        tags={"race", "humor"},
    ),
    "quest": Activity(
        id="quest",
        verb="go on a ketchup quest",
        gerund="seeking ketchup",
        rush="hurry through the rooms",
        mess="splat",
        soil="messy",
        zone={"floor", "hands"},
        keyword="quest",
        tags={"quest", "ketchup"},
    ),
}

PRIZES = {
    "ketchup": Prize(
        label="ketchup",
        phrase="a bright red ketchup bottle",
        type="bottle",
        region="hands",
    ),
    "tray": Prize(
        label="tray",
        phrase="a shiny serving tray",
        type="tray",
        region="hands",
        plural=False,
    ),
}

CHALLENGES = {
    "search": Challenge(
        id="search",
        name="find the ketchup",
        setup="look behind the napkins and under the chair",
        success="spot the ketchup at once",
        fail="find only crumbs and a spoon",
        risk_word="hidden",
        tags={"quest"},
    ),
    "balance": Challenge(
        id="balance",
        name="carry the ketchup carefully",
        setup="walk very slowly so the bottle would not wobble",
        success="keep the bottle steady all the way",
        fail="slosh the bottle and make a red trail",
        risk_word="wobble",
        tags={"race", "ketchup"},
    ),
}

HELPERS = {
    "cat": "a sleepy cat",
    "parent": "a patient parent",
    "dog": "a bouncy dog",
}

NAMES = ["Piper", "Milo", "Hazel", "June", "Theo", "Nina", "Luna", "Arlo"]
GENDERS = ["girl", "boy"]
TRAITS = ["cheerful", "curious", "brave", "silly", "gentle"]


def active_combo(place: str, act: str, challenge: str, prize: str) -> bool:
    if place not in SETTINGS:
        return False
    if act not in ACTIVITIES or challenge not in CHALLENGES or prize not in PRIZES:
        return False
    setting = SETTINGS[place]
    activity = ACTIVITIES[act]
    ch = CHALLENGES[challenge]
    pr = PRIZES[prize]
    return activity.id in setting.affords and (prize == "ketchup" or challenge == "balance")


def explain_rejection(place: str, act: str, challenge: str, prize: str) -> str:
    if place not in SETTINGS or act not in ACTIVITIES or challenge not in CHALLENGES or prize not in PRIZES:
        return "(No story: one of the chosen parts does not exist.)"
    return (
        f"(No story: {ACTIVITIES[act].verb} at {SETTINGS[place].place} with the {challenge} "
        f"challenge does not make sense for {PRIZES[prize].label}. Try a kitchen or garden-path story with ketchup.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for challenge in CHALLENGES:
                for prize in PRIZES:
                    if active_combo(place, act, challenge, prize):
                        out.append((place, act, challenge, prize))
    return out


def select_helper(name: str) -> str:
    return name if name in HELPERS else "parent"


def make_world(setting: Setting) -> World:
    return World(setting)


def _do_activity(world: World, actor: Entity, act: Activity, narrate: bool = True) -> None:
    actor.meters[act.mess] = actor.meters.get(act.mess, 0.0) + 1.0
    actor.memes["rush"] = actor.memes.get("rush", 0.0) + 1.0
    world.zone = set(act.zone)
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} started {act.gerund}.")


def _spill_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    bottle = world.get("prize")
    if hero.meters.get("splat", 0.0) >= THRESHOLD and bottle.worn_by == hero.id:
        sig = ("spill",)
        if sig not in world.fired:
            world.fired.add(sig)
            bottle.meters["splat"] = bottle.meters.get("splat", 0.0) + 1.0
            bottle.meters["broken"] = bottle.meters.get("broken", 0.0) + 1.0
            hero.memes["oops"] = hero.memes.get("oops", 0.0) + 1.0
            out.append("The ketchup bottle tipped and splashed.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    msgs = []
    changed = True
    while changed:
        changed = False
        for msg in _spill_rule(world):
            changed = True
            msgs.append(msg)
    if narrate:
        for m in msgs:
            world.say(m)
    return msgs


def introduce(world: World, hero: Entity, helper: Entity, prize: Entity, act: Activity, ch: Challenge) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved bedtime games and big tiny errands."
    )
    world.say(
        f"One evening, {hero.pronoun('subject')} spotted {prize.phrase} and dreamed of a {act.keyword}."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, while {helper.label} smiled from the doorway."
    )
    world.say(
        f"The plan was to {ch.setup}, because {hero.pronoun('possessive')} heart liked a little quest before supper."
    )


def start_race(world: World, hero: Entity, act: Activity, ch: Challenge) -> None:
    hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1.0
    world.say(
        f"{hero.id} counted softly, then {act.rush}, trying to win the race in the quietest, silliest way."
    )
    world.say(
        f"The carpet seemed to watch, and even the spoon looked ready to giggle."
    )


def handle_quest(world: World, hero: Entity, prize: Entity, ch: Challenge) -> None:
    found = ch.id == "search"
    if found:
        world.say(
            f"{hero.id} did {ch.success}, but the bottle was too smooth and the hurry was too fast."
        )
    else:
        world.say(
            f"{hero.id} tried to {ch.name}, but {ch.fail}."
        )
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0


def fail_turn(world: World, hero: Entity, helper: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Then the floor gave a little squeak, {hero.pronoun('possessive')} hands wobbled, and the ketchup splashed like a joke with no punchline."
    )
    propagate(world, narrate=True)
    world.say(
        f"{helper.label} gasped, then laughed kindly, because sometimes a mess can be funny right before it is annoying."
    )


def ending_bad(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1.0
    hero.memes["loss"] = hero.memes.get("loss", 0.0) + 1.0
    world.say(
        f"In the end, {hero.id} lost the race, and the ketchup bottle stayed on its side in a shiny red puddle."
    )
    world.say(
        f"{helper.label} wiped up the spill, but the picnic toast had to wait, and the little quest ended with no ketchup at all."
    )


def tell(setting: Setting, act: Activity, prize_cfg: Prize, challenge: Challenge,
         hero_name: str, hero_type: str, helper_kind: str) -> World:
    world = make_world(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=HELPERS.get(helper_kind, HELPER := "a patient parent")))
    prize = world.add(Entity(
        id="prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id
    ))
    prize.worn_by = hero.id

    world.say(f"{hero_name} was a {random.choice(TRAITS)} little {hero_type} named {hero_name}.")
    introduce(world, hero, helper, prize, act, challenge)
    world.para()
    start_race(world, hero, act, challenge)
    handle_quest(world, hero, prize, challenge)
    fail_turn(world, hero, helper, act, prize)
    world.para()
    ending_bad(world, hero, helper, prize)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        setting=setting,
        activity=act,
        challenge=challenge,
        resolved=False,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    ch = f["challenge"]
    prize = f["prize"]
    return [
        f'Write a bedtime story for a young child about {hero.label}, ketchup, and a silly race that becomes a quest.',
        f"Tell a gentle, humorous story where {hero.label} tries to {act.verb} but the {ch.name} goes wrong.",
        f"Write a short bedtime tale using the words ketchup, race, and quest, and end with a small bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    ch = f["challenge"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little {hero.type} who wanted to {act.verb} with {prize.label}.",
        ),
        QAItem(
            question=f"What was {hero.label} trying to do?",
            answer=f"{hero.label} was trying to {act.verb} as part of a small ketchup quest.",
        ),
        QAItem(
            question=f"Why did the race turn into a mess?",
            answer=f"The race turned into a mess because {hero.label} hurried too fast and the ketchup bottle wobbled and splashed.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: {hero.label} lost the race, the ketchup spilled, and the picnic had to continue without it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ketchup?",
            answer="Ketchup is a thick red sauce that people often put on food like fries or sandwiches.",
        ),
        QAItem(
            question="What is a race?",
            answer="A race is a contest where people try to get somewhere first or finish first.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special errand or search where someone tries to find or do something important.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the chosen setting affords the activity.
valid_story(Place, Activity, Challenge, Prize) :-
    affords(Place, Activity),
    activity(Activity),
    challenge(Challenge),
    prize(Prize),
    valid_pair(Activity, Challenge, Prize).

% The quest is acceptable when ketchup is the prize, or the balance challenge
% is paired with the ketchup bottle.
valid_pair(race, balance, ketchup).
valid_pair(quest, search, ketchup).
valid_pair(quest, balance, ketchup).

% Reasonable pairings are mirrored by the Python gate.
compatible(Place, Activity, Prize) :-
    affords(Place, Activity),
    valid_pair(Activity, _, Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: ketchup, race, and quest with a small bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place and args.activity and args.prize and args.challenge:
        if not active_combo(args.place, args.activity, args.challenge, args.prize):
            raise StoryError(explain_rejection(args.place, args.activity, args.challenge, args.prize))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.challenge is None or c[2] == args.challenge)
        and (args.prize is None or c[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, challenge, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or "Piper"
    helper = args.helper or "parent"
    return StoryParams(place=place, activity=act, prize=prize, challenge=challenge, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        CHALLENGES[params.challenge],
        params.name,
        params.gender,
        params.helper,
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


CURATED = [
    StoryParams(place="kitchen", activity="race", prize="ketchup", challenge="balance", name="Piper", gender="girl", helper="parent"),
    StoryParams(place="garden_path", activity="quest", prize="ketchup", challenge="search", name="Piper", gender="girl", helper="parent"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with story form):\n")
        for place, act, chal, prize in triples:
            print(f"  {place:12} {act:8} {chal:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize}, {p.challenge})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

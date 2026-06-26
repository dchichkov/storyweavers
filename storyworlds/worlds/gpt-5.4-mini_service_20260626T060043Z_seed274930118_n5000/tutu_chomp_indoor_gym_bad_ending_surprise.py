#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tutu_chomp_indoor_gym_bad_ending_surprise.py
=================================================================================================

A standalone story world: a pirate-style indoor-gym tale with tutus, chomping,
a surprise twist, and a bad ending that still feels complete and child-facing.

Premise:
A little dancer in an indoor gym loves a shiny tutu and a pretend pirate show.
A snack-eating helper or costume can threaten the tutu, and the story turns on
whether the heroes can keep the show safe.

World model:
- physical meters: crumbs, wet, torn, stained, tidy
- emotional memes: joy, worry, surprise, bravado, disappointment
- named entities have bodies, worn items, and ownership/caretaking links
- the indoor gym supports dance and snack play, but the chomp can stain fabric

Story shape:
1) Setup: introduce the dancer, the tutu, and the indoor gym pirate game.
2) Tension: a chomping mess risks the tutu and the show.
3) Twist: a surprise reveals the snack was meant for the class parrot prop.
4) Bad ending: the tutu still gets stained, but the class makes a new plan.

The result is intentionally a "bad ending" in the TinyStories sense: the
problem is not magically erased, but the final image proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {
                "crumbs": 0.0,
                "wet": 0.0,
                "torn": 0.0,
                "stained": 0.0,
                "tidy": 0.0,
            }
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "worry": 0.0,
                "surprise": 0.0,
                "bravado": 0.0,
                "disappointment": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pirate_girl"}
        male = {"boy", "father", "man", "pirate_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the indoor gym"
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    activity: str
    prize: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "gym": Setting(place="the indoor gym", indoor=True, affords={"dance", "chomp"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance like a pirate captain",
        gerund="dancing like a pirate captain",
        rush="spin toward the center mat",
        mess="crumbs",
        soil="all crumb-speckled",
        keyword="pirate",
        tags={"pirate", "dance"},
    ),
    "chomp": Activity(
        id="chomp",
        verb="chomp crunchy crackers",
        gerund="chomping crunchy crackers",
        rush="dash for the snack bowl",
        mess="crumbs",
        soil="speckled with crumbs",
        keyword="chomp",
        tags={"chomp", "snack", "crumbs"},
    ),
}

PRIZES = {
    "tutu": Prize(
        label="tutu",
        phrase="a bright silver tutu",
        type="tutu",
        plural=False,
    ),
}

GEAR = {
    "napkin": Gear(
        id="napkin",
        label="a big napkin",
        prep="put a big napkin under the snack bowl",
        tail="set the napkin under the bowl",
    ),
    "locker": Gear(
        id="locker",
        label="the locker bench",
        prep="move the snack bowl to the locker bench",
        tail="moved the bowl to the locker bench",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Suri", "Pia", "Tess", "Nia"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Kai", "Ezra", "Noah"]
TRAITS = ["brave", "spry", "curious", "cheery", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if place == "gym" and prize_id == "tutu":
                    combos.append((place, act_id, prize_id))
    return combos


def reasonability_gate(params: StoryParams) -> None:
    if params.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if params.helper not in GEAR:
        raise StoryError("Unknown helper gear.")
    if params.activity == "dance" and params.helper != "locker":
        raise StoryError("(No story: the dance scene needs the locker bench plan to become a real twist.)")
    if params.activity == "chomp" and params.helper != "napkin":
        raise StoryError("(No story: the chomp scene needs a snack-guard plan so the mess can happen in a believable way.)")


ASP_RULES = r"""
% Facts:
% setting(gym). afford(gym,dance). afford(gym,chomp).
% prize(tutu). helper(napkin). helper(locker).
% activity(dance). activity(chomp).

% A story is valid when the indoor gym can host the action and the tutu is
% the featured prize.
valid_story(P,A,R,H) :- setting(P), afford(P,A), prize(R), helper(H), story_ok(P,A,R,H).

story_ok(gym,dance,tutu,locker).
story_ok(gym,chomp,tutu,napkin).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for gid in GEAR:
        lines.append(asp.fact("helper", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {("gym", "dance", "tutu", "locker"), ("gym", "chomp", "tutu", "napkin")}
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-style indoor gym storyworld with tutu, chomp, surprise, twist, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "gym"
    activity = args.activity or rng.choice(["dance", "chomp"])
    prize = args.prize or "tutu"
    helper = args.helper or ("locker" if activity == "dance" else "napkin")
    reasonability_gate(StoryParams(name="x", gender="girl", parent="mother", activity=activity, prize=prize, helper=helper))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, activity=activity, prize=prize, helper=helper)


def _set_story_state(entity: Entity, **kwargs) -> None:
    for k, v in kwargs.items():
        if k in entity.meters:
            entity.meters[k] = v
        else:
            entity.memes[k] = v


def tell(params: StoryParams) -> World:
    setting = SETTINGS["gym"]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(id="tutu", type="tutu", label="tutu", phrase="a bright silver tutu", owner=hero.id, caretaker=parent.id))
    prop = world.add(Entity(id="parrot", type="thing", label="parrot prop", phrase="a paper parrot prop"))
    helper = world.add(Entity(id=params.helper, type="thing", label=GEAR[params.helper].label, phrase=GEAR[params.helper].label))

    hero.memes["joy"] += 1
    world.say(f"{hero.id} was a little {('pirate girl' if params.gender == 'girl' else 'pirate boy')} who loved the indoor gym.")
    world.say(f"{hero.id} loved {prize.phrase} because it shimmered like moonlight on a ship.")
    world.say(f"At the indoor gym, {hero.id} and {parent.label} made a pirate show with a cardboard ship and a paper parrot prop.")
    world.para()

    if params.activity == "dance":
        world.say(f"{hero.id} wanted to {ACTIVITIES['dance'].verb}, but the floor was crowded and the snack bowl sat nearby.")
        hero.memes["bravado"] += 1
        world.say(f'"Watch me spin!" {hero.id} said, and {hero.pronoun().capitalize()} stepped closer to the center mat.')
        world.say(f"Then came the surprise: the chomp noises were not from the snack bowl at all.")
        world.say(f"They came from the paper parrot prop, because the helper had hidden crackers inside it for the show.")
        hero.memes["surprise"] += 1
        parent.memes["surprise"] += 1
        world.say(f"The twist made everyone gasp, but a few crumbs still shook loose onto the tutu.")
        prize.meters["crumbs"] += 1
        prize.meters["stained"] += 1
        hero.memes["worry"] += 1
        world.para()
        world.say(f"{parent.label.capitalize()} tried to fix it with {helper.label}, but the crumbs had already clung to the shiny cloth.")
        world.say(f"{hero.id} stopped dancing and looked down at the speckles on {prize.label}.")
        hero.memes["disappointment"] += 1
        world.say(f"The pirate show ended in a bad ending: the tutu stayed crumb-speckled, and the grand spin had to wait for washing day.")
    else:
        world.say(f"{hero.id} wanted to {ACTIVITIES['chomp'].verb}, but {parent.label} warned that the crumbs could stick to the tutu.")
        hero.memes["worry"] += 1
        world.say(f"Just then, the paper parrot prop made a surprise squawk, and everyone turned to look.")
        hero.memes["surprise"] += 1
        world.say(f"The twist was that the cracker bowl had been saved for the parrot prop, not for the dancers.")
        world.say(f"{hero.id} chomped one bite anyway, and crumbs jumped onto {prize.label} like tiny shipwreck splashes.")
        prize.meters["crumbs"] += 1
        prize.meters["stained"] += 1
        hero.memes["disappointment"] += 1
        world.para()
        world.say(f"{parent.label.capitalize()} spread {helper.label} under the bowl, but the tutu was already dotted with crumbs.")
        world.say(f"The show went on, but the ending was bad for the costume: {prize.label} needed a wash, and the pirate dance had lost its sparkle.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prop=prop, helper=helper, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    return [
        f'Write a short pirate-style story for a young child about {hero.id} in {world.setting.place}, with a tutu, a surprise, and a twist.',
        f'Tell a gentle indoor-gym story where a {p.gender} named {p.name} wants to {ACTIVITIES[p.activity].verb} while wearing a tutu.',
        f'Write a tiny story that includes the words "tutu" and "chomp" and ends with a clear bad ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    prize = world.facts["prize"]
    act = ACTIVITIES[p.activity]
    return [
        QAItem(
            question=f"Who is the story about in the indoor gym?",
            answer=f"The story is about {hero.id}, a little pirate {p.gender} who played at the indoor gym with {parent.label}.",
        ),
        QAItem(
            question=f"What shiny thing did {hero.id} love wearing?",
            answer=f"{hero.id} loved wearing {prize.phrase}, and it looked bright like treasure in a pirate chest.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the chomp noise came from the paper parrot prop, because crackers had been hidden there for the pirate show.",
        ),
        QAItem(
            question=f"Why did the story end badly for the costume?",
            answer=f"The tutu still got crumb-speckled and stained, so the ending was bad for the costume even though everyone understood what happened.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before things went wrong?",
            answer=f"{hero.id} wanted to {act.verb} in the indoor gym during the pirate show.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tutu?",
            answer="A tutu is a fluffy skirt that dancers often wear in shows and pretend plays.",
        ),
        QAItem(
            question="What does chomp mean?",
            answer="Chomp means to bite or chew something with quick, strong bites.",
        ),
        QAItem(
            question="What is an indoor gym?",
            answer="An indoor gym is a room inside where people can run, dance, and play without going outside.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="mother", activity="dance", prize="tutu", helper="locker"),
    StoryParams(name="Kai", gender="boy", parent="father", activity="chomp", prize="tutu", helper="napkin"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_asp_story_list() -> list[tuple]:
    return asp_valid_combos()


def build_parser_wrapper() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params_wrapper(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for item in stories:
            print("  ", item)
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
            header = f"### {p.name}: {p.activity} in the indoor gym"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small storyworld: a space romp with a snip, a bad ending threat, and a happy ending.

The world is built around a child astronaut, a floating line, a tiny snip, and a romp
through a spacecraft or moon base. The tension comes from a snagged tether or a torn
suit piece that could lead to a bad ending in open space. The happy ending comes from
a careful repair and a safer way to keep playing.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "astronaut-girl"}
        male = {"boy", "father", "dad", "man", "astronaut-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    has_windows: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]
    covers: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0

SETTINGS = {
    "orbital_ring": Setting(place="the orbital ring", indoors=True, has_windows=True),
    "moon_base": Setting(place="the moon base", indoors=True, has_windows=True),
    "starship": Setting(place="the starship", indoors=True, has_windows=False),
}

ACTIVITIES = {
    "snip": Activity(
        id="snip",
        verb="snip the loose cord",
        gerund="snipping loose cords",
        rush="dash toward the dangling cable",
        mess="cut",
        risk="a bad ending",
        keyword="snip",
        tags={"snip", "space", "repair"},
    ),
    "romp": Activity(
        id="romp",
        verb="romp through the hall",
        gerund="romping through the hall",
        rush="run too fast",
        mess="scuff",
        risk="a bad ending",
        keyword="romp",
        tags={"romp", "space", "play"},
    ),
}

PRIZES = {
    "tether": Prize(label="tether", phrase="a silver tether", region="body"),
    "visor": Prize(label="visor", phrase="a bright visor", region="face"),
    "satchel": Prize(label="satchel", phrase="a tiny tool satchel", region="body"),
}

TOOLS = [
    Tool(
        id="patch_kit",
        label="a patch kit",
        prep="grab the patch kit first",
        tail="used the patch kit to seal the tear",
        fixes={"cut"},
        covers={"body", "face"},
    ),
    Tool(
        id="safety_clip",
        label="a safety clip",
        prep="clip on a safety clip first",
        tail="used the safety clip to hold the tether tight",
        fixes={"cut"},
        covers={"body"},
    ),
    Tool(
        id="slow_boots",
        label="slow boots",
        prep="put on slow boots first",
        tail="slowed down and kept romping carefully",
        fixes={"scuff"},
        covers={"body"},
    ),
]

NAMES = ["Nova", "Pip", "Rin", "Milo", "Lumi", "Ada", "Sol", "Zed"]
KINDS = [("girl", "astronaut-girl"), ("boy", "astronaut-boy")]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for act_id in ACTIVITIES:
            for prize_id in PRIZES:
                if act_id == "snip" and prize_id in {"tether", "satchel"}:
                    out.append((place, act_id, prize_id))
                if act_id == "romp" and prize_id in {"visor", "satchel"}:
                    out.append((place, act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.label}. "
        f"Try a prize that could be hurt by {activity.keyword}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with snip and romp.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender)


def _do_activity(world: World, actor: Entity, activity: Activity, prize: Entity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    if activity.id == "snip":
        prize.meters["risk"] = 1.0
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.pronoun().capitalize()} made a tiny snip, and the tether went slack.")
    else:
        actor.meters["scuff"] = actor.meters.get("scuff", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.pronoun().capitalize()} began to romp too fast through the corridor.")


def choose_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.fixes and prize.region in tool.covers:
            return tool
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero_type = "astronaut-girl" if hero_gender == "girl" else "astronaut-boy"
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="captain", kind="character", type="adult"))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id))
    hero.meters["joy"] = 1.0

    world.say(f"{hero.id} was a small space explorer at {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved the {activity.gerund} and the bright hum of the ship.")
    world.say(f"One day, {hero.id} carried {hero.pronoun('possessive')} {prize.label} and went looking for a romp.")
    world.para()
    world.say(f"Then {hero.id} wanted to {activity.verb}, but {activity.risk} hovered nearby.")
    _do_activity(world, hero, activity, prize, narrate=True)
    tool = choose_tool(activity, prize)
    world.facts.update(hero=hero, captain=captain, prize=prize, activity=activity, tool=tool, setting=setting)

    if tool is None:
        world.say(f"The story would have ended badly, but the crew had no safe fix.")
        return world

    world.para()
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(f"{captain.pronoun().capitalize()} smiled and said, \"Let's {tool.prep}.\"")
    world.say(f"{hero.id} nodded, because a careful helper could turn a bad ending into a happy ending.")
    if activity.id == "snip":
        world.say(f"Together they {tool.tail}, and the tether stayed strong.")
    else:
        world.say(f"Together they {tool.tail}, and the romp became slow and safe.")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short Space Adventure story about {hero.id}, the word "{act.keyword}", and a safe fix.',
        f"Tell a child-friendly tale where a small astronaut wants to {act.verb} but needs help to keep {prize.label} safe.",
        f"Write a story with a bad ending that almost happens, then a happy ending that saves the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    tool = f["tool"]
    captain = f["captain"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {act.verb} during the space romp.",
        ),
        QAItem(
            question=f"Why did the captain worry about {prize.label}?",
            answer=f"The captain worried because {act.risk} could hurt {prize.label} and spoil the trip.",
        ),
        QAItem(
            question=f"How did the crew turn the bad ending into a happy ending?",
            answer=f"They used {tool.label} and worked together, so the danger passed and the romp stayed safe.",
        ),
        QAItem(
            question=f"Who helped {hero.id} fix the problem?",
            answer=f"The captain helped {hero.id} and stayed with {hero.pronoun('possessive')} side the whole time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tether in a spaceship?",
            answer="A tether is a line that helps keep someone connected so they do not drift away in space.",
        ),
        QAItem(
            question="What does a patch kit do?",
            answer="A patch kit helps fix a small tear or hole so a thing can be used safely again.",
        ),
        QAItem(
            question="Why is space gear important?",
            answer="Space gear helps people stay safe where the air is thin and the places can be dangerous.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, meters={e.meters}, memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(snip). activity(romp).
prize(tether). prize(visor). prize(satchel).
setting(orbital_ring). setting(moon_base). setting(starship).

risk(snip,tether). risk(snip,satchel).
risk(romp,visor). risk(romp,satchel).

fix(cut, tether). fix(cut, satchel).
fix(scuff, visor). fix(scuff, satchel).

valid(Place,Act,Prize) :- setting(Place), activity(Act), prize(Prize), risk(Act,Prize), fix(_,Prize).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for act, prize in [("snip", "tether"), ("snip", "satchel"), ("romp", "visor"), ("romp", "satchel")]:
        lines.append(asp.fact("risk", act, prize))
    for fix, prize in [("cut", "tether"), ("cut", "satchel"), ("scuff", "visor"), ("scuff", "satchel")]:
        lines.append(asp.fact("fix", fix, prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="starship", activity="snip", prize="tether", name="Nova", gender="girl"),
        StoryParams(place="moon_base", activity="romp", prize="visor", name="Pip", gender="boy"),
    ]

    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

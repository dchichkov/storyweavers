#!/usr/bin/env python3
"""
Standalone storyworld: stink dialogue transformation superhero story.

A small superhero-style domain where a young hero, a helpful mentor, and a
stinky transformation suit turn an embarrassing stink problem into a brave
rescues-at-dusk story. The simulated world tracks physical meter facts
(smells, suit readiness, gadget cleanliness) and emotional meme facts
(courage, embarrassment, relief, pride), then turns those state changes into a
child-facing complete story with dialogue and transformation.
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

# World constants
THRESHOLD = 1.0
STINK_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Mission:
    place: str
    danger: str
    rescue: str
    mess: str
    transformation: str
    keyword: str = "stink"


@dataclass
class StoryParams:
    mission: str
    hero_name: str
    hero_type: str
    mentor_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, mission: Mission) -> None:
        self.mission = mission
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy

        w = World(self.mission)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _entity_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _do_mission(world: World, hero: Entity, narrate: bool = True) -> None:
    mission = world.mission
    _add_meter(hero, "stink", 1.0)
    _add_meme(hero, "bravery", 1.0)
    if narrate:
        world.say(f"{hero.id} rushed to {mission.place} to stop {mission.danger}.")
        world.say(f"The closer {hero.id} got, the stronger the stink became.")


def _stink_alert(world: World, hero: Entity, mentor: Entity) -> None:
    if _entity_meter(hero, "stink") < STINK_LIMIT:
        return
    if "alert" in world.fired:
        return
    world.fired.add("alert")
    _add_meme(hero, "embarrassed", 1.0)
    world.say(f'"Phew," {mentor.id} said, wrinkling {mentor.pronoun("possessive")} nose.')
    world.say(f'"{hero.id}, you smell heroic... but also very stinky."')


def _transform(world: World, hero: Entity, mentor: Entity, suit: Entity) -> None:
    if _entity_meter(hero, "stink") < STINK_LIMIT:
        return
    if "transform" in world.fired:
        return
    world.fired.add("transform")
    suit.worn_by = hero.id
    _add_meme(hero, "confidence", 2.0)
    _add_meme(hero, "embarrassed", -1.0)
    _add_meme(hero, "pride", 1.0)
    world.say(f'{mentor.id} smiled. "Then let the stink become your signal."')
    world.say(f'{mentor.id} handed over {suit.label}.')
    world.say(f'{hero.id} pulled it on, and the suit shimmered with a bright, buzzing glow.')
    world.say(f'{hero.id} transformed into {suit.phrase}.')


def _rescue(world: World, hero: Entity, sidekick: Entity) -> None:
    if "rescue" in world.fired:
        return
    if _entity_meme(hero, "confidence") < THRESHOLD:
        return
    world.fired.add("rescue")
    _add_meme(hero, "heroism", 1.0)
    _add_meme(sidekick, "relief", 1.0)
    world.say(f'"Hold on!" {hero.id} called.')
    world.say(f'With {sidekick.id} cheering, {hero.id} swept through {world.mission.place} and saved the day.')
    world.say(f'The danger was gone, and the city could breathe again.')


def tell(mission: Mission, hero_name: str, hero_type: str, mentor_type: str) -> World:
    w = World(mission)
    hero = w.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"stink": 0.0},
        memes={"bravery": 0.0, "confidence": 0.0, "embarrassed": 0.0, "pride": 0.0, "heroism": 0.0},
    ))
    mentor = w.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        label="Captain Spark",
        meters={},
        memes={"wisdom": 1.0},
    ))
    sidekick = w.add(Entity(
        id="Sidekick",
        kind="character",
        type="boy",
        label="Zip",
        meters={},
        memes={"cheer": 1.0, "relief": 0.0},
    ))
    suit = w.add(Entity(
        id="Suit",
        type="thing",
        label="the Thunder Stink Suit",
        phrase="Thunder Stink Hero",
        owner=hero.id,
    ))

    w.say(f"{hero.id} was a little {hero.type} who wanted to be a superhero.")
    w.say(f"{hero.id} loved helping people, even when the missions got messy.")
    w.say(f"One night, a strange stink drifted through {mission.place}, and everyone panicked.")

    w.para()
    _do_mission(w, hero)
    _stink_alert(w, hero, mentor)
    _transform(w, hero, mentor, suit)

    w.para()
    _rescue(w, hero, sidekick)
    if _entity_meter(hero, "stink") >= STINK_LIMIT:
        w.say(f"At the end, {hero.id} still smelled like the mission, but now it felt like a badge of honor.")
    else:
        w.say(f"At the end, {hero.id} looked clean and brave, ready for the next call for help.")

    w.facts.update(hero=hero, mentor=mentor, sidekick=sidekick, suit=suit, mission=mission)
    return w


MISSIONS = {
    "city": Mission(
        place="the city plaza",
        danger="a runaway stink cloud",
        rescue="trapped children",
        mess="stink",
        transformation="a glowing costume change",
        keyword="stink",
    ),
    "subway": Mission(
        place="the subway tunnel",
        danger="a broken pipe that sprayed awful stink",
        rescue="a lost puppy and a small crowd",
        mess="stink",
        transformation="a superhero costume change",
        keyword="stink",
    ),
    "dock": Mission(
        place="the rainy dock",
        danger="a spoiled crate that spread stink everywhere",
        rescue="a fisherman and his cart",
        mess="stink",
        transformation="a bright transformation",
        keyword="stink",
    ),
}

HERO_NAMES = ["Milo", "Nina", "Tessa", "Ravi", "Luna", "Owen"]
HERO_TYPES = ["boy", "girl"]
MENTOR_TYPES = ["woman", "man"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mission: Mission = f["mission"]  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about {hero.id} and a {mission.keyword}y rescue at {mission.place}.',
        f'Tell a dialogue-heavy story where {hero.id} gets very stinky, hears a mentor, and transforms into a hero.',
        f'Write a gentle superhero story that includes the word "{mission.keyword}" and ends with a transformation and rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    mentor: Entity = f["mentor"]  # type: ignore[assignment]
    suit: Entity = f["suit"]  # type: ignore[assignment]
    mission: Mission = f["mission"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Why did {hero.id} feel embarrassed before the transformation?",
            answer=(
                f"{hero.id} felt embarrassed because the mission made {hero.pronoun('object')} very stinky. "
                f"That stink got strong enough that even {mentor.label} noticed it right away."
            ),
        ),
        QAItem(
            question=f"What did {mentor.label} say to help {hero.id}?",
            answer=(
                f'{mentor.label} said, "Then let the stink become your signal." '
                f"That turned the messy problem into a brave superhero idea."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} transform into after putting on the suit?",
            answer=(
                f"{hero.id} transformed into {suit.phrase}. "
                f"The glowing suit made {hero.id} feel confident enough to face {mission.danger}."
            ),
        ),
        QAItem(
            question=f"What got rescued at {mission.place}?",
            answer=(
                f"{mission.rescue} got rescued when {hero.id} used the new superhero form and rushed in to help."
            ),
        ),
    ]
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a superhero?",
        answer=(
            "A superhero is a character who uses special courage, skills, or powers to help people and fix danger."
        ),
    ),
    QAItem(
        question="What is stink?",
        answer="Stink is a strong, bad smell that can make people wrinkle their noses.",
    ),
    QAItem(
        question="What does transform mean?",
        answer=(
            "Transform means to change into something different, like putting on a special suit and becoming a new hero version of yourself."
        ),
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines += ["", "== (2) Story questions ==", ""]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    lines += ["== (3) World knowledge questions ==", ""]
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {e.type:8} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for name, mission in MISSIONS.items():
        lines.append(asp.fact("mission", name))
        lines.append(asp.fact("place", name, mission.place))
        lines.append(asp.fact("danger", name, mission.danger))
        lines.append(asp.fact("rescue", name, mission.rescue))
        lines.append(asp.fact("mess", name, mission.mess))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_mission/1.
valid_mission(M) :- mission(M), place(M,_), danger(M,_), rescue(M,_), mess(M,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_missions() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_mission/1."))
    return sorted(set(asp.atoms(model, "valid_mission")))


def asp_verify() -> int:
    py = sorted((k,) for k in MISSIONS.keys())
    cl = asp_valid_missions()
    if py == cl:
        print(f"OK: ASP matches Python registry ({len(py)} missions).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", py)
    print("asp:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with stink and transformation.")
    ap.add_argument("--mission", choices=MISSIONS.keys())
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--mentor-type", choices=MENTOR_TYPES)
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
    mission = args.mission or rng.choice(list(MISSIONS.keys()))
    name = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    mentor_type = args.mentor_type or rng.choice(MENTOR_TYPES)
    return StoryParams(mission=mission, hero_name=name, hero_type=hero_type, mentor_type=mentor_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(MISSIONS[params.mission], params.hero_name, params.hero_type, params.mentor_type)
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
    StoryParams(mission="city", hero_name="Milo", hero_type="boy", mentor_type="man"),
    StoryParams(mission="subway", hero_name="Luna", hero_type="girl", mentor_type="woman"),
    StoryParams(mission="dock", hero_name="Tessa", hero_type="girl", mentor_type="man"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_mission/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(json.dumps(asp_valid_missions(), indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

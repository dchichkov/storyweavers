#!/usr/bin/env python3
"""
A tiny myth-style story world about a temple scribe, a clever helper, and the
quest to infer the perfect caption.

Seed tale:
---
In a high stone hall above the olive trees, a young scribe named Mira loved
making captions for the museum tablets. She believed every caption should be
perfect, because the old carvings were said to remember every word.

One afternoon, a laughing monkey spirit dropped a shiny pebble on Mira's desk
and pointed at a picture of a cloud-bride, a turtle boat, and three dancing
stars. Mira tried to infer the right caption alone, but every idea felt too
plain or too grand. The more she worried about perfection, the more tangled
her words became.

Then Mira and her brother Sol worked together. Sol noticed the moonlight in the
picture, and Mira noticed the pebble was actually a tiny mirror. They joked,
thought, and tried again until the caption sounded true and funny at once.
The old tablet glowed, because the perfect caption had been found.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother", "monkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    clue: str
    mess: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    hero_likes: bool = True


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.weather: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.lines = []
        c.facts = dict(self.facts)
        c.weather = self.weather
        return c


def _r_stain(world: World) -> list[str]:
    out = []
    for hero in world.entities.values():
        if hero.kind != "character" or hero.meters.get("trouble", 0) < THRESHOLD:
            continue
        artifact = world.facts["artifact"]
        if artifact.meters.get("clean", 0) < THRESHOLD:
            continue
        sig = ("stain", hero.id, artifact.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        artifact.meters["smudged"] = artifact.meters.get("smudged", 0) + 1
        artifact.meters["clean"] = 0
        out.append(f"The tablet grew smudged from all that worried thinking.")
    return out


def _r_clarity(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    if hero.memes.get("perfection", 0) < THRESHOLD:
        return out
    if helper.memes.get("teamwork", 0) < THRESHOLD:
        return out
    sig = ("clarity",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    out.append("Together, their thoughts cleared like morning mist.")
    return out


CAUSAL_RULES = [_r_stain, _r_clarity]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    for line in produced:
        world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    activity: str
    artifact: str
    name: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "hill_temple": Place(name="the hill temple", affords={"infer", "caption"}),
    "river_archive": Place(name="the river archive", affords={"infer", "caption"}),
    "moon_hall": Place(name="the moon hall", affords={"infer", "caption"}),
}

ACTIVITIES = {
    "infer": Activity(
        id="infer",
        verb="infer the meaning",
        gerund="inferring meanings",
        rush="guess too fast",
        clue="the clue",
        mess="worry",
        weather="clear",
        tags={"infer"},
    ),
    "caption": Activity(
        id="caption",
        verb="write the caption",
        gerund="writing captions",
        rush="scribble a caption too quickly",
        clue="the picture",
        mess="ink",
        weather="clear",
        tags={"caption"},
    ),
}

ARTIFACTS = {
    "tablet": Artifact(
        id="tablet",
        label="stone tablet",
        phrase="an old stone tablet",
        risk="smudged",
        region="desk",
    ),
}

TOOLS = [
    Tool(
        id="mirror_pebble",
        label="the mirror pebble",
        helps={"infer"},
        covers={"doubt"},
        prep="use the mirror pebble to look twice",
        tail="used the mirror pebble and laughed at the tiny silly reflection",
    ),
    Tool(
        id="shared_scroll",
        label="a shared scroll",
        helps={"caption"},
        covers={"ink"},
        prep="spread out a shared scroll and write together",
        tail="spread out the shared scroll and finished the caption side by side",
    ),
]


GIRL_NAMES = ["Mira", "Nina", "Lia", "Sara", "Ari"]
BOY_NAMES = ["Sol", "Tavi", "Noam", "Ivo", "Rafi"]


def can_story(place: Place, act: Activity, art: Artifact) -> bool:
    return act.id in place.affords


def select_tool(activity: Activity) -> Optional[Tool]:
    for t in TOOLS:
        if activity.id in t.helps:
            return t
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: infer, caption, and perfection.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    choices = [(p, a, ar) for p in SETTINGS for a in ACTIVITIES for ar in ARTIFACTS if can_story(SETTINGS[p], ACTIVITIES[a], ARTIFACTS[ar])]
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.activity:
        choices = [c for c in choices if c[1] == args.activity]
    if args.artifact:
        choices = [c for c in choices if c[2] == args.artifact]
    if not choices:
        raise StoryError("(No valid mythic caption story matches the given options.)")
    place, activity, artifact = rng.choice(sorted(choices))
    name = args.name or rng.choice(GIRL_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES)
    if helper_name == name:
        helper_name = rng.choice([n for n in BOY_NAMES if n != helper_name])
    return StoryParams(place=place, activity=activity, artifact=artifact, name=name, helper_name=helper_name)


def predict(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.facts["artifact"].meters["clean"] = 1
    hero2 = sim.get(hero.id)
    hero2.meters["trouble"] = hero2.meters.get("trouble", 0) + 1
    propagate(sim)
    return {"smudged": sim.facts["artifact"].meters.get("smudged", 0) >= THRESHOLD}


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    world.weather = "clear"
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="boy" if params.helper_name in BOY_NAMES else "girl"))
    artifact = world.add(Entity(id="tablet", type="tablet", label="tablet", phrase="a carved tablet"))
    world.facts.update(hero=hero, helper=helper, artifact=artifact, activity=ACTIVITIES[params.activity], place=SETTINGS[params.place])

    tool = select_tool(ACTIVITIES[params.activity])

    world.say(f"In {world.place.name}, {hero.id} loved making captions for the old stories.")
    hero.memes["perfection"] = hero.memes.get("perfection", 0) + 1
    world.say(f"{hero.id} believed every caption should be perfect, because the old tablet remembered every word.")
    world.say(f"One bright day, {helper.id} came close with a grin and a curious clue.")
    world.say(f"{hero.id} wanted to {ACTIVITIES[params.activity].verb}, but the answer hid like a little moon behind a cloud.")
    if predict(world, hero, ACTIVITIES[params.activity])["smudged"]:
        world.say(f"{hero.id} worried that a wrong caption would smudge the tablet with embarrassment.")
    hero.meters["trouble"] = hero.meters.get("trouble", 0) + 1
    propagate(world)
    world.say(f"{hero.id} tried to {ACTIVITIES[params.activity].rush}, and the words tangled up like spaghetti stars.")

    world.say("")
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    if tool:
        world.say(f"Then {helper.id} suggested they {tool.prep}.")
    world.say(f"{helper.id} noticed the shiny pebble in the picture, and {hero.id} noticed how the clouds looked like a smiling goat.")
    hero.memes["perfection"] += 1
    world.say(f"They joked, thought, and tried again together.")

    if tool:
        world.say(f"In the end, they {tool.tail}.")
    hero.memes["perfection"] = 0
    helper.memes["teamwork"] += 1
    artifact.meters["clean"] = 1
    world.say(f"The perfect caption finally sounded true and funny at once, and the tablet glowed as if it had been waiting for their teamwork.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a short mythic story about a child who must "{params.activity}" and find the perfect caption.',
            f"Tell a gentle story about {params.name} and {params.helper_name} using humor and teamwork to infer the right caption.",
            f'Write a myth-style tale that includes the words "infer", "caption", and "perfection".',
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    act: Activity = f["activity"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do with the old tablet?",
            answer=f"{hero.id} was trying to {act.verb} and make the caption feel perfect.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the words got tangled?",
            answer=f"{helper.id} helped by using teamwork and thinking about the clue together.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The caption became true and funny, and the old tablet glowed because the friends solved it together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does infer mean?",
            answer="To infer means to figure something out from clues and hints.",
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that explains or names a picture.",
        ),
        QAItem(
            question="What is perfection?",
            answer="Perfection means trying very hard to make something as good as it can be.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together and help each other do a job.",
        ),
        QAItem(
            question="Why can humor help in a hard job?",
            answer="Humor can make people laugh and feel calmer, so they can think more clearly together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Story questions =="]
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill_temple", activity="caption", artifact="tablet", name="Mira", helper_name="Sol"),
    StoryParams(place="moon_hall", activity="infer", artifact="tablet", name="Nina", helper_name="Rafi"),
]


ASP_RULES = r"""
valid_story(P,A,Ar) :- place(P), activity(A), artifact(Ar), affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in sorted(SETTINGS[p].affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for ar in ARTIFACTS:
        lines.append(asp.fact("artifact", ar))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((p, a, ar) for p in SETTINGS for a in ACTIVITIES for ar in ARTIFACTS if can_story(SETTINGS[p], ACTIVITIES[a], ARTIFACTS[ar]))
    cl = asp_valid()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(set(py) - set(cl)))
    print("clingo-only:", sorted(set(cl) - set(py)))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

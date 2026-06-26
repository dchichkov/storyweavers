#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/glitch_basement_stairs_kindness_comedy.py
===========================================================================================================

A standalone *story world* sketch for a glitchy basement stairs tale with kindness and comedy.

Initial story (used to build a world model):
---
Milo and his older sister Clara were home alone. The basement stairs had a funny
glitch: every third step from the bottom would wobble, then say "BOOP!" in a
cheerful robot voice. Milo loved the boop, but Clara worried he'd trip.

One afternoon Milo decided to bring his toy train down to the basement. He
carried the heavy box step by step. When he reached the boop-step, the box
knocked him off balance. Clara heard the thump and came running.

Instead of scolding, Clara sat on the step beside him and said, "Let's make a
game of it." They took turns carrying things down, and Clara held his hand on
the boop-step. Each time they heard "BOOP!" they giggled. Milo learned that
asking for help was brave, not babyish.

Causal state updates:
---
    glitch activates           -> actor.<surprise> += 1
                                   actor.boop_joy += 1
    near miss with glitch      -> actor.risk += 1
    sibling helps              -> actor.trust += 1
                                   actor.kindness_shared += 1
    carrying heavy thing down  -> actor.burden += 1
    hand-hold on glitch-step   -> actor.safety += 1
                                   sibling.kindness_shared += 1
"""

from __future__ import annotations

import argparse
import copy
import json
import os
 Quest = __import__('random', fromlist=('Random',))
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, Story-cls = sys.modules['results'].StorySample if hasattr(sys.modules['results'], 'StorySample') else type('StorySample', (), {})
__import__('results', fromlist=['StorySample'])
StorySample = getattr(sys.modules['results'], 'StorySample')
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
GLITCH_KINDS = {"boop", "wobble", "sparkle"}

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = "top_of_stairs"
    glitchy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"sister", "mom"}
        male = {"brother", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the basement stairs"
    steps: int = 12
    glitch_step: int = 3
    glitch_type: str = "boop"
    affords: set[str] = field(default_factory=lambda: {"carry", "slide", "hop"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.glitch_count: int = 0
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.glitch_count = self.glitch_count
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_glitch(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.location == "stairs" and actor.meters["steps"] >= world.setting.glitch_step:
            sig = ("glitch", actor.id, world.glitch_count)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.glitch_count += 1
            actor.memes["surprise"] += 1
            actor.memes["boop_joy"] += 0.5
            out.append(f"The step went BOOP! {actor.id} wobbled and giggled.")
    return out


def _r_trip_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["burden"] >= THRESHOLD and actor.memes["surprise"] >= THRESHOLD:
            sig = ("trip_risk", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["risk"] += 1
            out.append(f"That wobble nearly made {actor.id} drop everything.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    actors = list(world.characters())
    for i, a in enumerate(actors):
        for b in actors[i+1:]:
            if a.memes["risk"] >= THRESHOLD and b.memes["kindness_shared"] > 0:
                sig = ("help", a.id, b.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                a.memes["safety"] += 1
                a.memes["trust"] += 1
                out.append(f"{b.id} held {a.id}'s hand tight.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="glitch", tag="physical", apply=_r_glitch),
    Rule(name="trip_risk", tag="physical", apply=_r_trip_risk),
    Rule(name="help", tag="social", apply=_r_help),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def glitch_sound(glitch_type: str) -> str:
    return {"boop": "BOOP!", "wobble": "WOOBBLE!", "sparkle": "SPARKLE!"}.get(glitch_type, "BOOP!")


def sibling_kindness(helper: Entity, hero: Entity) -> str:
    return f"{helper.id} did not scold. Instead, {helper.pronoun()} sat beside {hero.id}."


def introduce_basement(world: World, setting: Setting) -> None:
    world.say(f"The {setting.place} had {setting.steps} creaky, old steps.")
    world.say(f"Every {setting.glitch_step}rd step from the bottom had a silly glitch: {glitch_sound(setting.glitch_type)}.")
    world.say("It was the kind of glitch that made you smile even if you fell.")


def introduce_siblings(world: World, hero: Entity, sibling: Entity) -> None:
    world.say(f"{hero.id} and {hero.pronoun('possessive')} big {sibling.type} {sibling.id} were home alone.")
    world.say(f"{hero.id} was small and brave; {sibling.id} was tall and kind.")


def plan_mission(world: World, hero: Entity, activity: Activity, prize: str) -> None:
    world.say(f"{hero.id} wanted to {activity.verb} with {hero.pronoun('possessive')} {prize}.")
    world.say(f"It was down there, at the bottom of the basement stairs.")


def start_carry(world: World, hero: Entity, item: Entity) -> None:
    item.carried_by = hero.id
    hero.location = "stairs"
    hero.meters["burden"] += 1
    hero.meters["steps"] = 0
    world.say(f"{hero.id} picked up {item.phrase} and started down the stairs.")
    world.say(f"Step one was fine. Step two was fine. Step three...")
    world.say(f"{glitch_sound(world.setting.glitch_type)}! {hero.id} wobbled.")


def glitch_hits(world: World, hero: Entity, item: Entity) -> None:
    hero.meters["steps"] += 3
    hero.memes["surprise"] += 2
    item.location = "stairs"
    propagate(world)
    world.say(f"The box tilted and {hero.id} nearly dropped {item.it()}.")


def rescue(world: World, sibling: Entity, hero: Entity, item: Entity) -> None:
    sibling.memes["kindness_shared"] += 1
    hero.memes["trust"] += 1
    world.say(sibling_kindness(sibling, hero))
    world.say(f'"We can do this together," {sibling.id} said. "Let me hold your hand on the boop-step."')
    hero.memes["safety"] += 1


def teamwork(world: World, hero: Entity, sibling: Entity, activity: Activity) -> None:
    world.say(f"Step by step, hand in hand, they carried {hero.pronoun('possessive')} toy.")
    world.say(f"BOOP! went the glitch. GIGGLE! went {hero.id} and {sibling.id}.")
    world.say(f"{hero.id} learned that asking for help was brave, not babyish.")


SETTINGS = {
    "basement": Setting(place="the basement stairs", steps=12, glitch_step=3, glitch_type="boop"),
    "cellar": Setting(place="the cellar stairs", steps=10, glitch_step=2, glitch_type="wobble"),
    "attic": Setting(place="the attic stairs", steps=8, glitch_step=4, glitch_type="sparkle"),
}

ACTIVITIES = {
    "carry": Activity(
        id="carry",
        verb="carry his toy train",
        gerund="carrying toys",
        rush="run down the stairs",
        mess="drop",
        soil="broken on the floor",
        zone={"stairs"},
        keyword="glitch",
        tags={"glitch", "stairs"},
    ),
}

PRIZES = {
    "train": Prize(
        label="train",
        phrase="a red toy train in a big cardboard box",
        type="toy",
        region="hands",
    ),
    "dolls": Prize(
        label="dolls",
        phrase="two big fluffy dolls with button eyes",
        type="toy",
        region="hands",
        plural=True,
    ),
    "books": Prize(
        label="books",
        phrase="a stack of picture books for story time",
        type="book",
        region="hands",
        plural=True,
    ),
}

SIBLING_TYPES = ["sister", "brother"]
SIBLING_NAMES = {"sister": ["Clara", "Maya", "Sophie"], "brother": ["Leo", "Finn", "Ollie"]}
HERO_NAMES = {"boy": ["Milo", "Sam", "Ben"], "girl": ["Lily", "Zoe", "Ella"]}
TRAITS = ["cheerful", "curious", "stubborn", "spirited", "lively"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_gender: str
    sibling_type: str
    sibling_name: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "glitch": [("What is a glitch?",
                "A glitch is a funny mistake or odd thing that happens, "
                "like a step that says BOOP! when you step on it.")],
    "stairs": [("Why can stairs be tricky?",
                "Stairs can be tricky because they are steep, and if you carry "
                "something big you might not see where you are stepping.")],
    "kindness": [("What does kindness mean?",
                  "Kindness means helping someone who is having a hard time, "
                  "like holding their hand on a tricky step.")],
}
KNOWLEDGE_ORDER = ["glitch", "stairs", "kindness"]


def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short comedy story for a 3-to-5-year-old about a glitchy step '
        f'and a kind sibling.',
        f"Tell a funny story where {world.facts['hero'].id} learns that asking "
        f"for help is brave, not babyish, on the basement stairs.",
        f'Write a simple story that uses the word "BOOP" and ends with a sibling hug.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling = f["hero"], f["sibling"]
    h = hero
    s = sibling
    place = world.setting.place
    glitch_word = glitch_sound(world.setting.glitch_type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is Milo and what happened when he carried his toy down {place}?",
            answer=f"Milo was a little boy who wanted to carry his toy train down {place}. "
                   f"When he stepped on the glitchy step, it said {glitch_word} and he nearly fell."
        ),
        QAItem(
            question=f"How did {s.id} help {h.id} on the stairs?",
            answer=f"{s.id} came running when {h.id} wobbled. Instead of scolding, "
                   f"{s.pronoun()} sat beside {h.id} and offered to hold {h.pronoun('possessive')} hand "
                   f"on the boop-step."
        ),
        QAItem(
            question=f"What did {h.id} learn at the end of the story?",
            answer=f"{h.id} learned that asking for help was brave, not babyish. "
                   f"The glitchy step became a fun game when {s.id} helped."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.location:
            bits.append(f"loc={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name, kind="character", type="child",
        traits=["little", params.trait], location="top_of_stairs",
    ))
    sibling = world.add(Entity(
        id=params.sibling_name, kind="character", type=params.sibling_type,
        traits=["kind", "big"], location="top_of_stairs",
    ))
    prize_cfg = PRIZES[params.prize]
    item = world.add(Entity(
        id="item", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, location="top_of_stairs",
    ))

    introduce_basement(world, setting)
    introduce_siblings(world, hero, sibling)
    world.para()
    plan_mission(world, hero, ACTIVITIES[params.activity], prize_cfg.label)
    world.para()
    start_carry(world, hero, item)
    glitch_hits(world, hero, item)
    world.para()
    rescue(world, sibling, hero, item)
    teamwork(world, hero, sibling, ACTIVITIES[params.activity])

    world.facts.update(hero=hero, sibling=sibling, item=item, prize_cfg=prize_cfg,
                       activity=ACTIVITIES[params.activity], setting=setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIVITIES:
            for prize in PRIZES:
                combos.append((place, act, prize))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Glitchy basement stairs kindness comedy story world.")
    ap.add_argument("--place", choices=list(SETTINGS.keys()))
    ap.add_argument("--activity", choices=list(ACTIVITIES.keys()))
    ap.add_argument("--prize", choices=list(PRIZES.keys()))
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--sibling-type", choices=["sister", "brother"])
    ap.add_argument("--hero-name")
    ap.add_argument("--sibling-name")
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
    combos = valid_combos()
    place, activity, prize_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    sibling_type = args.sibling_type or rng.choice(["sister", "brother"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[hero_gender])
    sibling_name = args.sibling_name or rng.choice(SIBLING_NAMES[sibling_type])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sibling_type=sibling_type,
        sibling_name=sibling_name,
        trait=trait,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        combos = valid_combos()
        for place, activity, prize_id in combos:
            for hero_gender in ["boy", "girl"]:
                for sibling_type in ["sister", "brother"]:
                    params = StoryParams(
                        place=place,
                        activity=activity,
                        prize=prize_id,
                        hero_name=random.choice(HERO_NAMES[hero_gender]),
                        hero_gender=hero_gender,
                        sibling_type=sibling_type,
                        sibling_name=random.choice(SIBLING_NAMES[sibling_type]),
                        trait=random.choice(TRAITS),
                    )
                    samples.append(generate(params))
    else:
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
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### {p.hero_name} and {p.sibling_name}: {p.activity} at {p.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

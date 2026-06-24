#!/usr/bin/env python3
"""
A small Tall Tale storyworld about an ornery croak, a bit of embroidery, and
the choice between a bad ending and a happy ending.

Seed tale:
---
On a windy evening, an ornery old frog in a straw hat lived beside a creek.
He loved to croak so loud the reeds shivered. One day he found a bright spool
of embroidery thread tangled in the cattails. He wanted to stitch a banner for
the county fair, but the thread kept knotting up whenever he got grumpy. A
kind little girl offered to help him, and together they made a funny, shining
banner that made everybody laugh.

Core beat:
- an ornery character wants to use embroidery thread for a proud display
- the character's mood makes the work go wrong
- a helper offers a calmer method
- the ending can either be ruined or turn happy, depending on state
- humor is part of the world, not a garnish

The story is intentionally small and state-driven. State tracks:
- meters: physical progress, thread tangles, finished embroidery, ruined cloth
- memes: ornery mood, delight, embarrassment, humor, pride
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

TARGET_THEME = "ornery croak embroidery happy ending bad ending humor tall tale"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    ending: str
    humor_level: str
    seed: Optional[int] = None


SETTINGS = {
    "creekbank": Setting(place="the creek bank", detail="The reeds leaned like old fence posts in a storm."),
    "fairground": Setting(place="the county fairground", detail="The tents flapped like laundry on a high line."),
    "barnloft": Setting(place="the barn loft", detail="The hay smelled sweet and dusty, and the rafters creaked."),
}

HEROES = {
    "frog": {"type": "frog", "label": "frog", "phrase": "an ornery old frog in a straw hat"},
    "crow": {"type": "bird", "label": "crow", "phrase": "an ornery black crow with a bright red scarf"},
    "goat": {"type": "goat", "label": "goat", "phrase": "an ornery little goat with a crooked bell"},
}

HELPERS = {
    "girl": {"type": "girl", "label": "girl", "phrase": "a kind little girl with a needle case"},
    "boy": {"type": "boy", "label": "boy", "phrase": "a cheerful little boy with a thimble tin"},
    "cat": {"type": "cat", "label": "cat", "phrase": "a patient barn cat with a spool basket"},
}

ENDINGS = {"happy", "bad"}
HUMOR_LEVELS = {"low", "medium", "high"}

THRESHOLD = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _inc(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _mood(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_ornery_spiral(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes.get("ornery", 0.0) < THRESHOLD:
        return []
    sig = ("ornery_spiral",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _inc(hero, "tangle", 1.0)
    _mood(hero, "pride", 1.0)
    return [f"{hero.label.capitalize()} got more stubborn than a fence post in January."]


def _rule_tangle_work(world: World) -> list[str]:
    hero = world.get("hero")
    thread = world.get("thread")
    if hero.memes.get("ornery", 0.0) < THRESHOLD:
        return []
    if hero.meters.get("croak", 0.0) < THRESHOLD:
        return []
    sig = ("tangle_work",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    _inc(thread, "tangle", 1.0)
    _inc(thread, "waste", 1.0)
    return ["Every grumpy croak twisted the embroidery thread into a bigger knot."]


def _rule_helper_calm(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.memes.get("kind", 0.0) < THRESHOLD:
        return []
    if hero.memes.get("humor", 0.0) < THRESHOLD:
        return []
    sig = ("helper_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["ornery"] = max(0.0, hero.memes.get("ornery", 0.0) - 1.0)
    _mood(hero, "delight", 1.0)
    return [f"{helper.label.capitalize()} kept a straight face and handed over the needle as gentle as a moonbeam."]


def _rule_finish_banner(world: World) -> list[str]:
    hero = world.get("hero")
    thread = world.get("thread")
    banner = world.get("banner")
    helper = world.get("helper")
    if hero.meters.get("stitch", 0.0) < 2.0:
        return []
    if thread.meters.get("tangle", 0.0) >= 2.0 and hero.memes.get("ornery", 0.0) >= THRESHOLD:
        return []
    sig = ("finish_banner",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    banner.meters["done"] = 1.0
    _mood(hero, "pride", 1.0)
    _mood(helper, "joy", 1.0)
    return ["Together they finished the banner, and it shone like a sunrise caught in string."]


def _rule_bad_ending(world: World) -> list[str]:
    hero = world.get("hero")
    banner = world.get("banner")
    if banner.meters.get("done", 0.0) >= THRESHOLD:
        return []
    if hero.meters.get("stitch", 0.0) < 1.0:
        return []
    sig = ("bad_ending",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    banner.meters["ruined"] = 1.0
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1.0
    return ["The banner came out crooked and muddy, fit for a goat parade in a thunderstorm."]


CAUSAL_RULES = [_rule_ornery_spiral, _rule_tangle_work, _rule_helper_calm, _rule_finish_banner, _rule_bad_ending]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def predict_outcome(world: World, steps: int = 1) -> dict[str, bool]:
    sim = world.copy()
    for _ in range(steps):
        propagate(sim, narrate=False)
    banner = sim.get("banner")
    return {
        "done": banner.meters.get("done", 0.0) >= THRESHOLD,
        "ruined": banner.meters.get("ruined", 0.0) >= THRESHOLD,
    }


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_data = HEROES[params.hero]
    helper_data = HELPERS[params.helper]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_data["type"],
        label=hero_data["label"],
        phrase=hero_data["phrase"],
        meters={"croak": 0.0, "stitch": 0.0, "tangle": 0.0},
        memes={"ornery": 1.0, "humor": 1.0, "pride": 0.0, "delight": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_data["type"],
        label=helper_data["label"],
        phrase=helper_data["phrase"],
        meters={"stitch": 0.0},
        memes={"kind": 1.0, "joy": 0.0},
    ))
    thread = world.add(Entity(
        id="thread",
        kind="thing",
        type="thread",
        label="embroidery thread",
        phrase="a bright spool of embroidery thread",
        meters={"tangle": 0.0, "waste": 0.0},
    ))
    banner = world.add(Entity(
        id="banner",
        kind="thing",
        type="banner",
        label="banner",
        phrase="a county fair banner",
        meters={"done": 0.0, "ruined": 0.0},
    ))

    world.facts.update(
        setting=setting,
        hero=hero,
        helper=helper,
        thread=thread,
        banner=banner,
        ending=params.ending,
        humor_level=params.humor_level,
    )

    world.say(f"{hero_data['phrase'].capitalize()} lived beside {setting.place}.")
    world.say(f"{setting.detail}")
    world.say(f"He loved to croak so loud the whole marsh shook like a washing tub in a windstorm.")
    world.para()
    world.say(f"One day he found {thread.phrase} tangled in the cattails and decided it would make a fine banner for the fair.")
    world.say("That was a tall order, because the frog was as ornery as a boot on a mule.")
    if params.humor_level in {"medium", "high"}:
        world.say("He gave one mean croak at the thread, as if a spool could be scared into cooperation.")
    _mood(hero, "ornery", 1.0)
    _inc(hero, "croak", 1.0)
    _inc(hero, "stitch", 1.0)
    propagate(world, narrate=True)

    world.para()
    outcome = predict_outcome(world, steps=1)
    world.say(f"{helper_data['phrase'].capitalize()} came along with a needle case and a calm grin.")
    if outcome["ruined"] and params.ending == "bad":
        world.say("But the frog kept huffing and puffing, and the thread fought back like a cat in a rain barrel.")
    else:
        world.say("She said a crooked stitch could still hold a happy dream if the hands behind it stayed steady.")

    _mood(helper, "kind", 1.0)
    _mood(hero, "humor", 1.0)
    if params.ending == "happy":
        hero.meters["croak"] += 1.0
        hero.meters["stitch"] += 2.0
        helper.meters["stitch"] += 1.0
        _mood(hero, "ornery", -0.5)
    else:
        hero.meters["croak"] += 1.0
        hero.meters["stitch"] += 0.5
        _mood(hero, "ornery", 0.5)

    propagate(world, narrate=True)

    world.para()
    banner = world.get("banner")
    if banner.meters.get("done", 0.0) >= THRESHOLD and params.ending == "happy":
        world.say("In the end the banner hung straight, bright as a penny in sunlight, and the frog laughed so hard he croaked a jig.")
        world.say("Everybody at the fair cheered, because even an ornery old frog can make something beautiful when he lets a friend help.")
    else:
        world.say("In the end the banner hung crooked and muddy, and the frog's great croak turned into a grumble that could sour a peach pie.")
        world.say("Still, the tall tale says the crowed-up little mess made everybody laugh, which is a poor ending for the banner but a fine joke for the town.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    return [
        f'Write a tall tale for a small child about an ornery {hero.label} who loves to croak and finds embroidery thread.',
        f"Tell a funny story where {hero.phrase} meets {helper.phrase} and the two decide whether the embroidery ends happily or badly.",
        f'Write a humorous story that includes the words "ornery", "croak", and "embroidery" and ends with a clear final image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    banner: Entity = f["banner"]  # type: ignore[assignment]
    ending = f["ending"]
    qa = [
        QAItem(
            question=f"Who was the ornery character in the story?",
            answer=f"The ornery character was {hero.phrase}. He kept trying to croak his way through the embroidery work.",
        ),
        QAItem(
            question=f"What did the hero want to make with the embroidery thread?",
            answer="He wanted to make a banner for the fair. The banner was supposed to look proud and shiny, not twisted and muddy.",
        ),
        QAItem(
            question=f"Who helped with the thread and stitching?",
            answer=f"{helper.phrase.capitalize()} helped with the stitching. She stayed calm, which made the crooked work easier to fix.",
        ),
    ]
    if ending == "happy" and banner.meters.get("done", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended happily. The banner was finished, it hung straight, and the frog laughed instead of grumbling.",
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended badly for the banner. The cloth came out crooked and muddy, and the frog was left grumbling.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is embroidery?",
            answer="Embroidery is making pictures or decorations with needle and thread on cloth.",
        ),
        QAItem(
            question="What does it mean to croak?",
            answer="A croak is a rough frog sound. Frogs croak when they call out near water or in the grass.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny story that stretches things bigger than life, but it still has a clear lesson or joke.",
        ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="creekbank", hero="frog", helper="girl", ending="happy", humor_level="high"),
    StoryParams(place="fairground", hero="crow", helper="boy", ending="happy", humor_level="medium"),
    StoryParams(place="barnloft", hero="goat", helper="cat", ending="bad", humor_level="low"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about ornery croaks and embroidery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--humor-level", choices=HUMOR_LEVELS, dest="humor_level")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    ending = args.ending or rng.choice(list(ENDINGS))
    humor_level = args.humor_level or rng.choice(list(HUMOR_LEVELS))
    if ending not in ENDINGS:
        raise StoryError("Invalid ending.")
    return StoryParams(place=place, hero=hero, helper=helper, ending=ending, humor_level=humor_level)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


ASP_RULES = r"""
hero(ornery).
topic(ornery).
topic(croak).
topic(embroidery).

happy_if(done).
bad_if(ruined).

% This tiny twin mirrors the Python reasonableness:
% if the helper is kind and the ending is happy, the banner is done.
done :- kind_helper, happy_request.
ruined :- ornery, croak, not kind_helper.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("ornery"),
        asp.fact("croak"),
        asp.fact("embroidery"),
        asp.fact("humor"),
        asp.fact("tall_tale"),
        asp.fact("happy_ending"),
        asp.fact("bad_ending"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show done/0.\n#show ruined/0.")
    model = __import__("storyworlds.asp", fromlist=["one_model"]).one_model(program)
    done = any(sym.name == "done" for sym in model)
    ruined = any(sym.name == "ruined" for sym in model)
    if done or ruined:
        print("OK: ASP twin is syntactically alive.")
        return 0
    print("MISMATCH: ASP twin produced no outcome atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show done/0.\n#show ruined/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

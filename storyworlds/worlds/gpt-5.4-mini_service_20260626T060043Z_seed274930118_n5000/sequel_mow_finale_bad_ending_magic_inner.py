#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sequel_mow_finale_bad_ending_magic_inner.py
===============================================================================================================

A small fairy-tale storyworld about a child, a magical lawn, and a bad ending.
The world is built from a seed that asked for sequel, mow, and finale, with
Magic and Inner Monologue as the narrative instruments.

Premise:
- A child wants to mow a spellbound meadow.
- The meadow is not ordinary: it keeps tiny fairy paths and moonlit flowers.
- The child hears a warning, but the wish to finish the job is strong.

Turn:
- Magic responds to the mower and the child's choice.
- Inner monologue carries the fear, hope, and stubbornness.

Resolution:
- This world intentionally allows a bad ending.
- The mowing goes through, the magic is broken, and the story ends with a
  changed, quieter place instead of a happy compromise.

The script still follows the Storyweavers contract:
- self-contained stdlib script
- StoryParams + registries + build_parser + resolve_params + generate + emit + main
- eager results import; lazy ASP import in helpers
- Python reasonableness gate plus inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    magical: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "princess"}
        male = {"boy", "father", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.magical and item.location == region for item in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _key(e: Entity) -> str:
    return e.label or e.type


def _mow(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host the mowing scene.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["determination"] = actor.memes.get("determination", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} bent over the grass and began to {activity.verb}.")


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("cut", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != actor.id:
                continue
            if item.magical:
                continue
            if item.location not in world.zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ruined"] = item.meters.get("ruined", 0.0) + 1
            out.append(f"The sharp work touched {_key(item)}, and it came to grief.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    meadow = world.entities.get("meadow")
    if not meadow or meadow.meters.get("blessed", 0.0) < THRESHOLD:
        return out
    mower = world.entities.get("mower")
    if not mower:
        return out
    if mower.meters.get("used", 0.0) < THRESHOLD:
        return out
    sig = ("magic_break",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    meadow.meters["blessed"] = 0.0
    meadow.meters["bare"] = meadow.meters.get("bare", 0.0) + 1
    out.append("The old blessing broke, and the meadow went silent.")
    return out


CAUSAL_RULES = [_r_soil, _r_magic]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _mow(sim, sim.get(hero.id), activity, narrate=False)
    sim.get(hero.id).meters["cut"] = sim.get(hero.id).meters.get("cut", 0.0) + 1
    propagate(sim, narrate=False)
    meadow = sim.get("meadow")
    return {
        "magic_broken": meadow.meters.get("blessed", 0.0) < THRESHOLD,
        "bare": meadow.meters.get("bare", 0.0) >= THRESHOLD,
    }


def setup_line(world: World, hero: Entity, caretaker: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"Once in the bright edge of a fairy meadow, {hero.id} listened to the wind and "
        f"watched the grass sway like a green wave."
    )
    world.say(
        f"{hero.id} loved to {activity.gerund}, though {hero.pronoun('possessive')} "
        f"{caretaker.label} warned that the place was more than ordinary."
    )
    world.say(
        f"At the center of the tale stood {prize.phrase}, which the child treasured as if it were a small crown."
    )


def inner_monologue(world: World, hero: Entity, text: str) -> None:
    world.say(f'Inside {hero.pronoun("possessive")} heart, {hero.id} thought, "{text}"')


def warning_line(world: World, caretaker: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    pred = predict(world, hero, activity)
    if pred["magic_broken"]:
        world.say(
            f'"If you {activity.verb}, you may break the blessing," {caretaker.id} said. '
            f'"Then {prize.label} will not stay the same."'
        )


def bad_choice(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    inner_monologue(world, hero, "I only want to finish this one little job.")
    world.say(
        f"Still, {hero.id} took the mower with both hands and stepped into the shining grass."
    )
    _mow(world, hero, activity)
    hero.meters["cut"] = hero.meters.get("cut", 0.0) + 1
    hero.meters["used"] = hero.meters.get("used", 0.0) + 1
    propagate(world, narrate=True)


def finale_bad_ending(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    meadow = world.get("meadow")
    world.para()
    if meadow.meters.get("bare", 0.0) >= THRESHOLD:
        hero.memes["sadness"] = hero.memes.get("sadness", 0.0) + 1
        world.say(
            f"When the finale came, the meadow was no longer bright and thick."
        )
        world.say(
            f"The fairy paths were gone, the flowers drooped, and {prize.label} lost its little spell."
        )
        world.say(
            f"{hero.id} stood very still, hearing only the hiss of the last cut in the grass."
        )
        inner_monologue(world, hero, "I wanted a tidy field, but I made a lonely one.")
    else:
        world.say(
            "When the finale came, the meadow still shimmered, though the air felt uneasy."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lina", hero_type: str = "girl",
         caretaker_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, label="mother"))
    prize = world.add(Entity(
        id="meadow",
        type="meadow",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=caretaker.id,
    ))
    mower = world.add(Entity(id="mower", type="mower", label="gold mower", magical=False))
    meadow = world.get("meadow")
    meadow.meters["blessed"] = 1.0
    meadow.meters["bare"] = 0.0
    mower.meters["used"] = 0.0

    setup_line(world, hero, caretaker, prize, activity)
    world.para()
    warning_line(world, caretaker, hero, prize, activity)
    bad_choice(world, hero, activity)
    finale_bad_ending(world, hero, prize, activity)

    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        prize=prize,
        activity=activity,
        setting=setting,
        meadow=meadow,
    )
    return world


SETTINGS = {
    "fairy_meadow": Setting(place="the fairy meadow", indoor=False, affords={"mow"}),
}

ACTIVITIES = {
    "mow": Activity(
        id="mow",
        verb="mow the meadow",
        gerund="mowing the meadow",
        rush="rush over the grass",
        mess="cut",
        soil="short and ruined",
        zone={"ground"},
        keyword="mow",
        tags={"mow", "magic"},
    ),
}

PRIZES = {
    "meadow": Prize(
        label="the fairy meadow",
        phrase="a fairy meadow with moonlit grass",
        type="meadow",
        region="ground",
    ),
}

TOOLS = {
    "mower": Tool(
        id="mower",
        label="gold mower",
        guards={"cut"},
        covers={"ground"},
        prep="take the gold mower",
        tail="finished the mowing",
    )
}

NAMES = ["Lina", "Nora", "Pip", "Elsa", "Mira", "Tessa", "Ivy", "Rose"]
CAREGIVERS = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    caretaker: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("fairy_meadow", "mow", "meadow")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale bad-ending storyworld with magic and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--caretaker", choices=CAREGIVERS)
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
    if args.place and args.activity and args.prize:
        if (args.place, args.activity, args.prize) not in valid_combos():
            raise StoryError("No valid fairy-tale mowing story matches those explicit choices.")
    return StoryParams(
        place=args.place or "fairy_meadow",
        activity=args.activity or "mow",
        prize=args.prize or "meadow",
        name=args.name or rng.choice(NAMES),
        caretaker=args.caretaker or rng.choice(CAREGIVERS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short fairy tale with the words "sequel", "mow", and "finale".',
        f"Tell a magical story where {hero.id} tries to mow a blessed meadow and the ending goes badly.",
        "Write a gentle but sad fairy tale with inner monologue and a broken spell.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    caretaker = f["caretaker"]
    activity = f["activity"]
    meadow = f["meadow"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the meadow?",
            answer=f"{hero.id} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {caretaker.id} worry about the mowing?",
            answer="Because the meadow was magical, and cutting it could break the blessing.",
        ),
        QAItem(
            question="What happened at the finale?",
            answer="The meadow was cut down, the spell broke, and the ending was sad.",
        ),
        QAItem(
            question=f"How did {hero.id} feel inside?",
            answer="The child felt stubborn at first, and then sad when the meadow went quiet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a meadow?",
            answer="A meadow is a grassy field where flowers can grow and small animals can hide.",
        ),
        QAItem(
            question="What does magic mean in a fairy tale?",
            answer="Magic is a special power that can make unusual things happen, like spells or enchanted places.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's mind, like the thoughts they do not say out loud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,R) :- place(P), activity(A), prize(R),
                      valid_combo(P,A,R).
valid_combo(fairy_meadow,mow,meadow).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    lines.append(asp.fact("valid_combo", "fairy_meadow", "mow", "meadow"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    clingo_set = set(asp.atoms(model, "valid_combo"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combo).")
        return 0
    print("MISMATCH between clingo and python:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.caretaker)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


CURATED = [StoryParams(place="fairy_meadow", activity="mow", prize="meadow", name="Lina", caretaker="mother")]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combo(s):")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/muffle_baloney_happy_ending_cautionary_animal_story.py
===============================================================================================================

A small animal storyworld about noisy wishes, careful warnings, and a happy
ending that comes from a sensible fix.

Seed tale used to shape the world:
---
A young animal wanted to make a big noisy show in the evening. A grown-up
warned that the noise would wake the little nestlings and called the excuse
"baloney" when the youngster said it was fine. The child felt hurt at first,
but then found a way to muffle the sound so everyone could enjoy the show.

This world keeps that premise, but generates a few close, constraint-checked
variants with different animals, places, noisy toys, and sensible muffling gear.
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
ANIMAL_KINDS = {"fox", "rabbit", "bear", "hedgehog", "otter", "mouse", "panda", "cat", "dog"}
NOISE_KINDS = {"bell", "drum", "horn", "toy trumpet"}
PLACES = {"meadow", "barn", "backyard", "porch", "tree hollow"}
MUFFLERS = {"felt wrap", "soft scarf", "quilt cover", "wool sock"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    quiets: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("noise", "worry", "joy", "hurt", "defiance", "care"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
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
class Noise:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    quiets: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _noise_rise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.type != "nestlings":
                continue
            sig = ("wake", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["woken"] += 1
            out.append("The little nestlings stirred awake.")
    return out


def _worry_rise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for other in world.characters():
            if other.kind != "character" or other.id == actor.id:
                continue
            if other.type not in {"mother", "father", "aunt", "uncle"}:
                continue
            sig = ("worry", other.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            other.meters["worry"] += 1
            out.append(f"{other.label} worried about the noise.")
    return out


CAUSAL_RULES = [_noise_rise, _worry_rise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_fix(noise: Noise, gear: Gear) -> bool:
    return noise.id in gear.quiets


def select_gear(noise: Noise) -> Optional[Gear]:
    for gear in GEAR:
        if can_fix(noise, gear):
            return gear
    return None


def predict_problem(world: World, actor: Entity, noise: Noise) -> bool:
    sim = copy_world(world)
    do_noise(sim, sim.get(actor.id), noise, narrate=False)
    return any(e.meters["worry"] >= THRESHOLD for e in sim.characters() if e.type in {"mother", "father", "aunt", "uncle"})


def copy_world(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.facts = copy.deepcopy(world.facts)
    clone.paragraphs = [[]]
    return clone


def do_noise(world: World, actor: Entity, noise: Noise, narrate: bool = True) -> None:
    if noise.id not in world.setting.affords:
        return
    world.zone = set(noise.zone)
    actor.meters["noise"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "small")
    world.say(f"{hero.id} was a young {trait} {hero.type} who loved making the world feel like a game.")


def loves_noise(world: World, hero: Entity, noise: Noise) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved the {noise.gerund}, because it made the evening feel exciting.")


def gift(world: World, helper: Entity, hero: Entity, noise: Noise) -> None:
    world.say(f"One day, {helper.label} gave {hero.id} a {noise.label} for the little show.")


def wants(world: World, hero: Entity, noise: Noise) -> None:
    hero.meters["noise"] += 1
    world.say(f"{hero.id} wanted to {noise.verb}, but the sound would travel far.")


def warn(world: World, grownup: Entity, hero: Entity, noise: Noise, nestlings: Entity) -> None:
    if not predict_problem(world, hero, noise):
        return
    grownup.meters["care"] += 1
    world.say(
        f'"That sounds like baloney," {grownup.label} said. '
        f'"If you do that here, you may wake the {nestlings.label}."'
    )


def argue(world: World, hero: Entity, noise: Noise) -> None:
    hero.meters["defiance"] += 1
    world.say(f"{hero.id} frowned and muttered that it would be fine.")
    world.say(f"{hero.pronoun().capitalize()} tried to {noise.rush},")


def steady_hand(world: World, grownup: Entity, hero: Entity, noise: Noise) -> None:
    hero.meters["hurt"] += 1
    world.say(
        f"but {grownup.label} gently held up a hand and said, "
        f'"Let\'s not call that baloney too quickly. Let\'s find a softer way."'
    )


def compromise(world: World, grownup: Entity, hero: Entity, noise: Noise, nestlings: Entity) -> Optional[Gear]:
    gear = select_gear(noise)
    if gear is None:
        return None
    if predict_problem(world, hero, noise):
        world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=grownup.id,
            protective=True,
            covers=set(gear.covers),
            quiets=set(gear.quiets),
        )).worn_by = hero.id
        # recheck silently
        if predict_problem(world, hero, noise):
            del world.entities[gear.id]
            return None
    world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=grownup.id,
        protective=True,
        covers=set(gear.covers),
        quiets=set(gear.quiets),
    )).worn_by = hero.id
    world.say(f"{grownup.label} found {gear.label} and smiled.")
    world.say(f'"How about we {gear.prep} and still {noise.verb}?"')
    return gear


def happy_ending(world: World, hero: Entity, grownup: Entity, noise: Noise, gear: Gear, nestlings: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["defiance"] = 0
    world.say(
        f"{hero.id}'s face brightened, and {hero.pronoun()} nodded. "
        f"{hero.pronoun().capitalize()} hugged {grownup.pronoun('object')}, and the two of them got ready."
    )
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {noise.gerund}, but the sound stayed soft, "
        f"{nestlings.label} stayed asleep, and the evening ended in happy laughter."
    )


def tell(setting: Setting, noise: Noise, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "curious"]))
    grownup = world.add(Entity(id="Grownup", kind="character", type=parent_type, label="the grown-up"))
    nestlings = world.add(Entity(id="Nestlings", kind="thing", type="nestlings", label="nestlings", plural=True))
    hero.meters["noise"] = 0.0
    nestlings.meters["woken"] = 0.0

    introduce(world, hero)
    loves_noise(world, hero, noise)
    gift(world, grownup, hero, noise)

    world.para()
    wants(world, hero, noise)
    warn(world, grownup, hero, noise, nestlings)
    argue(world, hero, noise)
    steady_hand(world, grownup, hero, noise)

    world.para()
    gear = compromise(world, grownup, hero, noise, nestlings)
    if gear:
        happy_ending(world, hero, grownup, noise, gear, nestlings)

    world.facts.update(hero=hero, grownup=grownup, nestlings=nestlings, noise=noise, gear=gear, setting=setting)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"bell", "horn"}),
    "barn": Setting(place="the barn", indoor=True, affords={"drum", "bell"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"drum", "toy trumpet"}),
    "porch": Setting(place="the porch", indoor=False, affords={"bell", "toy trumpet"}),
    "tree hollow": Setting(place="the tree hollow", indoor=True, affords={"horn"}),
}

NOISES = {
    "bell": Noise(
        id="bell",
        label="a bright little bell",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="ring it as loud as possible",
        danger="its clanging could wake the nestlings",
        zone={"ears"},
        keyword="bell",
        tags={"sound", "quiet"},
    ),
    "drum": Noise(
        id="drum",
        label="a hand drum",
        verb="beat the drum",
        gerund="beating the drum",
        rush="bang it hard",
        danger="its thump could shake the nest",
        zone={"ears"},
        keyword="drum",
        tags={"sound", "quiet"},
    ),
    "horn": Noise(
        id="horn",
        label="a tiny horn",
        verb="toot the horn",
        gerund="tooting the horn",
        rush="toot it in a big blast",
        danger="its blast could echo everywhere",
        zone={"ears"},
        keyword="horn",
        tags={"sound", "quiet"},
    ),
    "toy trumpet": Noise(
        id="toy trumpet",
        label="a toy trumpet",
        verb="play the toy trumpet",
        gerund="playing the toy trumpet",
        rush="blare it out",
        danger="its brassy noise could wake everyone",
        zone={"ears"},
        keyword="trumpet",
        tags={"sound", "quiet"},
    ),
}

GEAR = [
    Gear(id="felt_wrap", label="a felt wrap", covers={"ears"}, quiets={"bell", "horn"}, prep="wrap the bell in a felt wrap", tail="wrapped the bell in the felt wrap"),
    Gear(id="soft_scarf", label="a soft scarf", covers={"ears"}, quiets={"bell", "drum"}, prep="hold the drum under a soft scarf", tail="tucked the drum under the soft scarf"),
    Gear(id="quilt_cover", label="a quilt cover", covers={"ears"}, quiets={"horn", "toy trumpet"}, prep="cover the horn with a quilt cover", tail="covered the horn with the quilt cover"),
    Gear(id="wool_sock", label="a wool sock", covers={"ears"}, quiets={"bell", "toy trumpet"}, prep="slide the toy trumpet into a wool sock", tail="slid the toy trumpet into the wool sock"),
]

HERO_NAMES = ["Pip", "Milo", "Tessa", "Nori", "Bram", "Juno", "Clover", "Pogo", "Fern", "Ollie"]
TRAITS = ["small", "brave", "bouncy", "curious", "cheery", "spry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for noise_id in setting.affords:
            if select_gear(NOISES[noise_id]) is not None:
                combos.append((place, noise_id))
    return combos


@dataclass
class StoryParams:
    place: str
    noise: str
    name: str
    animal: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, grownup, noise = f["hero"], f["grownup"], f["noise"]
    return [
        f'Write a short animal story for a young child that includes the word "baloney" and the phrase "{noise.keyword}".',
        f"Tell a cautionary story where a {hero.type} named {hero.id} wants to {noise.verb}, but {grownup.label} worries about the nestlings.",
        f"Write a happy-ending animal tale about making a loud game quieter with a muffle so the little ones can sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grownup, noise, nestlings = f["hero"], f["grownup"], f["noise"], f["nestlings"]
    gear = f.get("gear")
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Who wanted to make the noise at {place}?",
            answer=f"It was {hero.id}, a young {hero.type} who loved the {noise.gerund}.",
        ),
        QAItem(
            question=f"Why did the grown-up call the idea baloney?",
            answer=f"Because the noise would travel through {place} and could wake the {nestlings.label}. The grown-up did not think it was a safe plan.",
        ),
        QAItem(
            question=f"What did {hero.id} do after hearing the warning?",
            answer=f"{hero.id} stopped arguing, listened, and helped make the noise soft instead of loud.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"It muffled the noise so {hero.id} could {noise.verb} without waking the {nestlings.label}.",
        ))
    qa.append(QAItem(
        question=f"What was the happy ending?",
        answer=f"{hero.id} got to enjoy the show, the {nestlings.label} stayed asleep, and everyone ended up smiling together.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does muffle mean?",
            answer="To muffle something means to make it quieter or softer so it does not sound so loud.",
        ),
        QAItem(
            question="What is baloney?",
            answer="Baloney can mean silly nonsense, the kind of claim that does not really make sense.",
        ),
        QAItem(
            question="Why should little animals sleep when they are sleepy?",
            answer="Little animals need sleep so their bodies and brains can rest and grow strong.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
            bits.append(f"quiets={sorted(e.quiets)}")
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", noise="bell", name="Pip", animal="fox", parent="mother", trait="curious"),
    StoryParams(place="barn", noise="drum", name="Milo", animal="rabbit", parent="father", trait="bouncy"),
    StoryParams(place="porch", noise="toy trumpet", name="Tessa", animal="otter", parent="aunt", trait="cheery"),
]


def explain_rejection(noise: Noise) -> str:
    return f"(No story: nothing in the gear catalog can muffle {noise.label} here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("(No story: unknown place.)")
    if args.noise and args.noise not in NOISES:
        raise StoryError("(No story: unknown noise.)")

    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and args.noise is None or c[1] == args.noise]
    if not combos:
        if args.noise:
            raise StoryError(explain_rejection(NOISES[args.noise]))
        raise StoryError("(No valid animal story matches the given options.)")

    place, noise = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMAL_KINDS))
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, noise=noise, name=name, animal=animal, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], NOISES[params.noise], params.name, params.animal, params.parent)
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
prize_at_risk(N, P) :- noise(N), nestlings(P), talks_to_ears(N).
protects(G, N, P) :- gear(G), prize_at_risk(N, P), quiets(G, N), covers(G, ears).
has_fix(N, P) :- protects(_, N, P).
valid(Place, N) :- affords(Place, N), has_fix(N, nestlings).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for n in sorted(s.affords):
            lines.append(asp.fact("affords", pid, n))
    for nid, n in NOISES.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("talks_to_ears", nid))
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
        for q in sorted(g.quiets):
            lines.append(asp.fact("quiets", g.id, q))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    lines.append(asp.fact("nestlings", "nestlings"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with baloney, muffle, and a happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--animal", choices=sorted(ANIMAL_KINDS))
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, noise in combos:
            print(f"  {place:10} {noise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

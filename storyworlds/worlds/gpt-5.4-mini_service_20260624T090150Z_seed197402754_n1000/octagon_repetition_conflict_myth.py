#!/usr/bin/env python3
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    sacred: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Rite:
    id: str
    verb: str
    gerund: str
    echo: str
    tension: str
    resolve: str
    keyword: str = "repetition"
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    shape: str
    meaning: str
    protected: bool = False


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    role: str
    helps: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    rite: str
    relic: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "hill": Setting(place="the moonlit hill", affords={"chant"}),
    "temple": Setting(place="the old temple", affords={"chant"}),
    "grove": Setting(place="the quiet grove", affords={"chant"}),
}

RITES = {
    "chant": Rite(
        id="chant",
        verb="sing the old chant",
        gerund="singing the old chant",
        echo="the chant grew louder with every repeat",
        tension="the voices began to push against each other",
        resolve="the voices took turns instead of crowding together",
        tags={"myth", "repetition", "conflict", "octagon"},
    )
}

RELICS = {
    "stone": Relic(
        id="stone",
        label="octagon stone",
        phrase="a carved octagon stone",
        shape="octagon",
        meaning="a sign of balance",
    ),
    "seal": Relic(
        id="seal",
        label="octagon seal",
        phrase="an octagon seal of pale gold",
        shape="octagon",
        meaning="a sign of peace",
    ),
}

TOKENS = {
    "drum": Token(
        id="drum",
        label="drum",
        phrase="a small drum",
        role="kept the rhythm",
        helps="it could call people to take turns",
    ),
    "lantern": Token(
        id="lantern",
        label="lantern",
        phrase="a bright lantern",
        role="marked each speaker",
        helps="its light showed who would speak next",
    ),
}

NAMES = ["Mira", "Nilo", "Tala", "Ivo", "Sera", "Kian"]
HELPERS = ["drum", "lantern"]


def reasonableness_ok(rite: Rite, relic: Relic) -> bool:
    return rite.id == "chant" and relic.shape == "octagon"


def select_token(rite: Rite, relic: Relic) -> Optional[Token]:
    return TOKENS["drum"] if relic.id == "stone" else TOKENS["lantern"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for rite in RITES:
            for relic in RELICS:
                if reasonableness_ok(RITES[rite], RELICS[relic]):
                    out.append((place, rite, relic))
    return out


def intro(world: World, hero: Entity, relic: Entity, helper: Entity, rite: Rite) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} stood before the {relic.label} and listened "
        f"to the oldest stories. The {relic.label} was an octagon, and that shape felt "
        f"steady like a promise."
    )
    world.say(
        f"{hero.id} loved {rite.gerund}, because every repetition made the hall feel fuller and warmer."
    )
    world.say(
        f"{helper.label.capitalize()} was there too, ready to help when the words needed order."
    )


def build_tension(world: World, hero: Entity, rival: Entity, relic: Entity, rite: Rite) -> None:
    hero.memes["devotion"] = hero.memes.get("devotion", 0) + 1
    rival.memes["pride"] = rival.memes.get("pride", 0) + 1
    world.say(
        f"One day, {hero.id} began {rite.verb} again and again. The repetition made the stones hum."
    )
    world.say(
        f"But {rival.id} wanted the first word for {rival.pronoun('possessive')} own voice, and that started a conflict."
    )
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    rival.memes["conflict"] = rival.memes.get("conflict", 0) + 1
    relic.meters["echo"] = relic.meters.get("echo", 0) + 1
    world.say(f"{rite.echo.capitalize()}, and soon {rite.tension}.")


def foresee(world: World, rite: Rite, relic: Entity) -> bool:
    sim = world.copy()
    sim.get("Hero").meters["chant"] = 1
    sim.get("Relic").meters["echo"] = sim.get("Relic").meters.get("echo", 0) + 1
    return sim.get("Relic").meters.get("echo", 0) >= 1 and rite.id == "chant" and relic.shape == "octagon"


def resolve(world: World, hero: Entity, rival: Entity, relic: Entity, helper: Entity, rite: Rite) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0) + 1
    rival.memes["peace"] = rival.memes.get("peace", 0) + 1
    hero.memes["conflict"] = 0
    rival.memes["conflict"] = 0
    world.say(
        f"{hero.id} lifted the {helper.label}, and its help was simple: it kept the turns clear."
    )
    world.say(
        f"Then {hero.id} and {rival.id} shared the chant. They took turns, so the repetition became gentle instead of crowded."
    )
    world.say(
        f"At last, the {relic.label} shone quietly. The octagon looked like a little shelter for both voices."
    )
    world.say(
        f"{rite.resolve.capitalize()}, and the hill remembered them kindly."
    )


def tell(setting: Setting, rite: Rite, relic_cfg: Relic, hero_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type="child", label=hero_name))
    rival = world.add(Entity(id="Rival", kind="character", type="character", label="the elder"))
    helper_cfg = select_token(rite, relic_cfg)
    helper = world.add(Entity(id="Helper", kind="thing", type="token", label=helper_cfg.label, phrase=helper_cfg.phrase))
    relic = world.add(Entity(id="Relic", kind="thing", type="relic", label=relic_cfg.label, phrase=relic_cfg.phrase))

    intro(world, hero, relic, helper, rite)
    world.para()
    build_tension(world, hero, rival, relic, rite)
    world.para()
    resolve(world, hero, rival, relic, helper, rite)

    world.facts.update(hero=hero, rival=rival, helper=helper, relic=relic, rite=rite, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child about an {f["relic"].label} and the danger of too much repetition.',
        f"Tell a gentle story where {f['hero'].label} and the elder fall into conflict during a sacred chant, then find a calmer way to speak.",
        f'Write a simple mythic story that uses the word "octagon" and ends with repetition becoming peaceful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, rival, helper, relic, rite = f["hero"], f["rival"], f["helper"], f["relic"], f["rite"]
    return [
        QAItem(
            question=f"What shape was the sacred stone in the story?",
            answer=f"It was an octagon stone, so its many sides made it feel balanced and strong.",
        ),
        QAItem(
            question=f"Why did the conflict begin during the chant?",
            answer=f"The conflict began because {hero.label} kept repeating the chant, while {rival.label} wanted the first word and felt crowded out.",
        ),
        QAItem(
            question=f"How did {hero.label} and {rival.label} fix the problem?",
            answer=f"They used the {helper.label} to keep turns clear, and then the repetition became calm instead of noisy.",
        ),
        QAItem(
            question=f"What changed at the end of the myth?",
            answer=f"At the end, the two voices shared the chant, the conflict disappeared, and the octagon relic shone quietly.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an octagon?",
            answer="An octagon is a shape with eight sides.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a struggle or disagreement between people or forces.",
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
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        parts.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(parts)


ASP_RULES = r"""
shape(octagon).
rite(chant).

valid(Place, Rite, Relic) :- setting(Place), rite(Rite), relic(Relic),
                             place_affords(Place, Rite),
                             relic_shape(Relic, octagon).

conflict(Rite) :- repetition(Rite), not turn_taking(Rite).
resolution(Rite) :- turn_taking(Rite), repetition(Rite).

#show valid/3.
#show conflict/1.
#show resolution/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for rid in RITES:
        lines.append(asp.fact("rite", rid))
        lines.append(asp.fact("repetition", rid))
        lines.append(asp.fact("turn_taking", rid))
    for relid, rel in RELICS.items():
        lines.append(asp.fact("relic", relid))
        lines.append(asp.fact("relic_shape", relid, rel.shape))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - ac))
    print("only asp:", sorted(ac - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny myth of octagon and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--relic", choices=RELICS)
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
              and (args.rite is None or c[1] == args.rite)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rite, relic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, rite=rite, relic=relic, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITES[params.rite], RELICS[params.relic], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="hill", rite="chant", relic="stone", name="Mira"),
    StoryParams(place="temple", rite="chant", relic="seal", name="Tala"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

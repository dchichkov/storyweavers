#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boomsie_goop_dialogue_myth.py
=============================================================

A tiny mythic dialogue storyworld about a childlike trickster, a sticky goop,
and a careful turn toward a clean ending.

The world is built to satisfy the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven narrative
- three QA sets
- a Python reasonableness gate plus inline ASP twin
- CLI support for --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

Seed words: boomsie, goop
Features: dialogue
Style: myth
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    ancient: str
    echo: str


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    sacred: bool = True
    sticky: bool = False


@dataclass
class Goop:
    id: str
    label: str
    phrase: str
    pour: str
    stickiness: int
    messy: bool = True


@dataclass
class Response:
    id: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    setting: str
    relic: str
    goop: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "shrine": Setting("shrine", "the hill shrine", "old stones", "their soft echo"),
    "grove": Setting("grove", "the moon grove", "silver roots", "their hollow echo"),
    "cave": Setting("cave", "the cave hall", "black walls", "their deep echo"),
}

RELICS = {
    "idol": Relic("idol", "stone idol", "the stone idol"),
    "drum": Relic("drum", "bronze drum", "the bronze drum"),
    "lamp": Relic("lamp", "sun lamp", "the sun lamp"),
}

GOOPS = {
    "honey-goop": Goop("honey-goop", "honey goop", "a jar of honey goop", "pour", 3),
    "swamp-goop": Goop("swamp-goop", "swamp goop", "a bowl of swamp goop", "slosh", 2),
    "moon-goop": Goop("moon-goop", "moon goop", "a silver bowl of moon goop", "drip", 2),
}

RESPONSES = {
    "wipe": Response("wipe", 3, 3, "wiped the goop away with clean cloths", "tried to wipe it away, but the goop had already set like glue", "wiped the goop away with clean cloths"),
    "scrape": Response("scrape", 4, 4, "scraped the goop loose with a wooden blade and washed the stone after", "scraped at it, but the goop stayed clung fast", "scraped the goop loose with a wooden blade and washed the stone after"),
    "salt-rinse": Response("salt-rinse", 2, 2, "mixed salt water and rinsed the relic until the stickiness faded", "rinsed and rinsed, but the goop only grew tackier", "mixed salt water and rinsed the relic until the stickiness faded"),
}

NAMES = ["Ari", "Mina", "Toma", "Lio", "Sera", "Niko", "Iva", "Zee"]
TRAITS = ["curious", "careful", "brave", "gentle"]


def is_reasonable(goop: Goop, relic: Relic) -> bool:
    return goop.messy and relic.sacred


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for gid, g in GOOPS.items():
            for rid, r in RELICS.items():
                if is_reasonable(g, r):
                    out.append((sid, gid, rid))
    return out


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(sensible_responses(), key=lambda r: r.sense)


def damage_level(goop: Goop) -> int:
    return goop.stickiness


def can_save(resp: Response, goop: Goop) -> bool:
    return resp.power >= damage_level(goop)


def tell(world: World, setting: Setting, relic: Relic, goop: Goop, response: Response,
         hero: str, hero_gender: str, helper: str, helper_gender: str,
         elder: str, elder_gender: str) -> World:
    h = world.add(Entity(hero, "character", hero_gender, role="hero", traits=["bold"]))
    k = world.add(Entity(helper, "character", helper_gender, role="helper", traits=["wise"]))
    e = world.add(Entity(elder, "character", elder_gender, role="elder", traits=["calm"]))
    r = world.add(Entity("relic", "thing", "thing", label=relic.label, attrs={"sacred": True}))
    g = world.add(Entity("goop", "thing", "thing", label=goop.label, attrs={"sticky": True}))
    world.facts.update(setting=setting, relic=relic, goop=goop, response=response,
                       hero=h, helper=k, elder=e, sacred=r, slick=g)

    h.memes["wonder"] += 1
    k.memes["watchful"] += 1
    e.memes["peace"] += 1

    world.say(
        f"In {setting.place}, under {setting.ancient}, {h.id} and {k.id} came to hear the old echo."
    )
    world.say(
        f'"Listen," said {k.id}, "for {setting.echo} speaks when the shrine is quiet."'
    )
    world.say(
        f'But {h.id} held up {goop.phrase} and grinned. "Boomsie," {h.id} whispered, '
        f'"if the relic drinks this, it will wake!"'
    )
    world.para()

    # prediction
    sim = world.copy()
    sim.get("goop").meters["on_relic"] += 1
    sim.get("relic").meters["sticky"] += float(goop.stickiness)
    danger = sim.get("relic").meters["sticky"] >= THRESHOLD
    world.facts["predicted_sticky"] = danger

    if danger:
        k.memes["warning"] += 1
        world.say(
            f'"Do not," said {k.id}. "That goop will cling to {relic.label} and make it hard to sing cleanly."'
        )
    world.say(
        f'"But boomsie loves a wonder," {h.id} said, and tipped the bowl anyway.'
    )

    relic_ent = world.get("relic")
    goop_ent = world.get("goop")
    relic_ent.meters["sticky"] += float(goop.stickiness)
    goop_ent.meters["spilled"] += 1
    h.memes["defiance"] += 1
    if relic_ent.meters["sticky"] >= THRESHOLD:
        world.say(
            f'The {goop.label} ran over the {relic.label} and made it shine with a slow, heavy gloss.'
        )

    world.para()
    if can_save(response, goop):
        world.say(
            f'{elder.id} came forward and {response.text}.'
        )
        relic_ent.meters["sticky"] = 0.0
        world.say(
            f'The old stone breathed easy again, and the echo in the hall grew clear.'
        )
        h.memes["relief"] += 1
        k.memes["relief"] += 1
        world.say(
            f'"Boomsie was a foolish song," said {h.id}, smiling shyly. "Now I will choose cleaner magic."'
        )
        world.say(
            f'"And I will help," said {k.id}. "Myth is brighter when hands are careful."'
        )
        world.para()
        world.say(
            f'That night, {h.id} left the shrine with {goop.label} in a sealed jar and the {relic.label} singing free.'
        )
        outcome = "clean"
    else:
        world.say(
            f'{elder.id} came forward and {response.fail}.'
        )
        relic_ent.meters["sticky"] += 1
        world.say(
            f'The blessing faded into a dull smear, and the hall felt sad and heavy.'
        )
        world.say(
            f'At last {h.id} and {k.id} cleaned what they could and promised to keep the sacred things from sticky tricks.'
        )
        outcome = "stuck"

    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child that includes the words "boomsie" and "{f["goop"].label}".',
        f'Tell a dialogue-heavy myth where {f["hero"].id} wants to use {f["goop"].label} on a sacred object, but a friend warns them.',
        f'Write a gentle myth with speaking characters, a messy magical mistake, and a clean ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, k, e = f["hero"], f["helper"], f["elder"]
    r, g = f["relic"], f["goop"]
    qa = [
        QAItem(
            question="Who are the main characters in the story?",
            answer=f"The story is about {h.id}, {k.id}, and {e.id}. They meet beside the {r.label} and argue gently about the {g.label}.",
        ),
        QAItem(
            question="Why did the helper warn about the goop?",
            answer=f"{k.id} warned because the {g.label} would cling to the {r.label} and make it hard to keep the shrine clean. The warning matched what the world model predicted before the spill."
        ),
    ]
    if f["outcome"] == "clean":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the {r.label} clean again and the {g.label} sealed away. {h.id} learned to choose cleaner magic after the elder fixed the mess."
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the {r.label} still marked by sticky {g.label}. {h.id} and {k.id} had to clean carefully and promise to be wiser next time."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sticky goop do?",
            answer="Sticky goop clings to surfaces and makes them hard to clean. If it dries on a sacred object, someone usually has to wash or scrape it off."
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story about important things, strange wonders, and lessons people remember. Myths often sound grand even when the characters speak simply."
        ),
        QAItem(
            question="Why is dialogue useful in a story?",
            answer="Dialogue lets characters speak directly so their choices and feelings are easy to hear. It can make a story feel alive and clear."
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S, G, R) :- setting(S), goop(G), relic(R), messy(G), sacred(R).
outcome(clean) :- chosen_response(R), response(R), power(R, P), chosen_goop(G), goop(G), stickiness(G, D), P >= D.
outcome(stuck) :- chosen_response(R), response(R), power(R, P), chosen_goop(G), goop(G), stickiness(G, D), P < D.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GOOPS.items():
        lines.append(asp.fact("goop", gid))
        lines.append(asp.fact("stickiness", gid, g.stickiness))
        if g.messy:
            lines.append(asp.fact("messy", gid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if r.sacred:
            lines.append(asp.fact("sacred", rid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("power", rid, r.power))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_goop", params.goop),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def valid_response_set() -> list[str]:
    return [r.id for r in sensible_responses()]


def outcome_of(params: StoryParams) -> str:
    return "clean" if can_save(RESPONSES[params.response], GOOPS[params.goop]) else "stuck"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    cases = [StoryParams(s, g, r, "Ari", "girl", "Mina", "girl", "Sera", "woman") for s, g, r in valid_combos()]
    cases.append(resolve_params(argparse.Namespace(setting=None, relic=None, goop=None, response=None, hero=None, helper=None, elder=None), random.Random(7)))
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, relic=None, goop=None, response=None, hero=None, helper=None, elder=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke-generated story builds successfully.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic dialogue storyworld about boomsie and goop.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--goop", choices=GOOPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("The chosen response is too weak for this mythic goop story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.relic is None or c[2] == args.relic)
              and (args.goop is None or c[1] == args.goop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, goop, relic = rng.choice(sorted(combos))
    response = args.response or rng.choice(valid_response_set())
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in NAMES if n != hero])
    elder = args.elder or rng.choice([n for n in NAMES if n not in {hero, helper}])
    return StoryParams(setting, relic, goop, response, hero, hero_gender, helper, helper_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        World(),
        SETTINGS[params.setting],
        RELICS[params.relic],
        GOOPS[params.goop],
        RESPONSES[params.response],
        params.hero, params.hero_gender, params.helper, params.helper_gender, params.elder, params.elder_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in world_knowledge_qa(world)]],
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


def _default_args() -> argparse.Namespace:
    return argparse.Namespace(setting=None, relic=None, goop=None, response=None,
                              hero=None, helper=None, elder=None, gender=None,
                              helper_gender=None, elder_gender=None)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show good_combo/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("shrine", "idol", "honey-goop", "wipe", "Ari", "girl", "Mina", "girl", "Sera", "woman"),
            StoryParams("grove", "drum", "moon-goop", "scrape", "Lio", "boy", "Zee", "boy", "Iva", "woman"),
            StoryParams("cave", "lamp", "swamp-goop", "salt-rinse", "Toma", "boy", "Niko", "boy", "Mina", "woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/accommodate_auditorium_provoke_humor_surprise_inner_monologue.py
===============================================================================================================================

A small standalone storyworld for a tall-tale stage adventure in an auditorium.

Premise:
- A little stage helper wants to accommodate a giant visitor in an auditorium.
- A comic remark might provoke trouble, but the world favors a clever, gentle turn.
- Humor, Surprise, and Inner Monologue are first-class narrative instruments.

The story engine models:
- physical meters: noise, crowd, space, laughter, blush, hush, worry, relief
- emotional memes: confidence, patience, delight, alarm, pride, affection

The ending image proves what changed: the auditorium is arranged, the crowd is laughing,
and the would-be trouble turns into a cheerful surprise.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") else "it"


@dataclass
class CastMember:
    id: str
    type: str
    label: str
    voice: str
    trait: str
    age: int = 0
    plural: bool = False


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    size: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    cast: str
    helper: str
    prop: str
    surprise: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _up(m: dict[str, float], key: str, amount: float = 1.0) -> None:
    m[key] += amount


def _rule_echo(world: World) -> list[str]:
    out: list[str] = []
    hall = world.get("auditorium")
    performer = world.get("performer")
    if performer.meters["voice"] >= THRESHOLD and hall.meters["empty"] < THRESHOLD:
        sig = ("echo",)
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["noise"] += 1
            out.append("The old auditorium answered with a grand echo.")
    return out


def _rule_laugh(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    helper = world.get("helper")
    hall = world.get("auditorium")
    if performer.memes["delight"] >= THRESHOLD and hall.meters["noise"] >= THRESHOLD:
        sig = ("laugh",)
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["laughter"] += 1
            helper.memes["pride"] += 1
            out.append("Even the rafters seemed to giggle.")
    return out


def _rule_relieved(world: World) -> list[str]:
    out: list[str] = []
    guest = world.get("guest")
    if guest.meters["settled"] >= THRESHOLD:
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            guest.memes["affection"] += 1
            out.append("The giant guest smiled like a lantern in a barn window.")
    return out


RULES = [_rule_echo, _rule_laugh, _rule_relieved]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_surprise(world: World, prop: Thing) -> bool:
    sim = world.copy()
    guest = sim.get("guest")
    if prop.id == "bench":
        guest.meters["settled"] += 1
    return bool(sim.get("auditorium").meters["laughter"] >= THRESHOLD or guest.meters["settled"] >= THRESHOLD)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cast in CAST:
        for helper in HELPERS:
            for prop in PROPS:
                if cast.id != helper.id and prop.id in {"bench", "curtain", "hat"}:
                    combos.append((cast.id, helper.id, prop.id))
    return combos


def explain_rejection(cast: CastMember, helper: CastMember, prop: Thing) -> str:
    return (
        f"(No story: this setup cannot reasonably accommodate {cast.label} with {prop.label} "
        f"and {helper.label}. Pick one of the valid stage props.)"
    )


def reasonableness_gate(params: StoryParams) -> None:
    if (params.cast, params.helper, params.prop) not in {tuple(x) for x in valid_combos()}:
        raise StoryError("(No valid combination matches the given options.)")


def tell(cast: CastMember, helper: CastMember, prop: Thing, surprise: Thing) -> World:
    world = World()
    performer = world.add(Entity(id="performer", kind="character", type=cast.type, label=cast.label, role="performer"))
    helper_e = world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, role="helper"))
    guest = world.add(Entity(id="guest", kind="character", type="giant", label="the giant guest", role="guest"))
    auditorium = world.add(Entity(id="auditorium", type="room", label="the auditorium"))
    bench = world.add(Entity(id="bench", type="thing", label="a long bench"))
    curtain = world.add(Entity(id="curtain", type="thing", label="the red curtain"))
    hat = world.add(Entity(id="hat", type="thing", label="a hat as wide as a wagon wheel"))

    world.facts.update(cast=cast, helper=helper, prop=prop, surprise=surprise)

    auditorium.meters["empty"] += 1
    guest.meters["settled"] += 0
    performer.memes["confidence"] += 1
    helper_e.memes["patience"] += 1
    guest.memes["worry"] += 1
    bench.meters["space"] += 1
    curtain.meters["hush"] += 1
    hat.meters["size"] += 1

    world.say(
        f"On a windy afternoon, {performer.label} and {helper_e.label} tiptoed into {auditorium.label} "
        f"with a plan as big as a hay wagon. They meant to accommodate {guest.label}, who was coming to "
        f"hear a song and a joke."
    )
    world.say(
        f"{performer.label} looked at {prop.phrase} and thought, almost laughing aloud, "
        f"'{prop.purpose.capitalize()} ought to fit, if the old hall has any manners.'"
    )
    world.para()
    world.say(
        f"But then {helper_e.label} gave a tiny warning. '{surprise.phrase.capitalize()} might provoke trouble "
        f"if we act too quick,' {helper_e.pronoun()} said, though {helper_e.pronoun('possessive')} eyes were smiling."
    )
    world.say(
        f"Inside {performer.label}'s head, a quick inner monologue ran like a squirrel on a fence: "
        f"'If I blurt the wrong joke, that giant will frown. If I make room first, maybe the whole room will grin.'"
    )
    world.say(
        f"That thought had barely landed when {guest.label} arrived, ducking under the doorway with "
        f"{surprise.phrase} tucked under one arm."
    )
    guest.meters["crowd"] += 1
    if prop.id == "bench":
        guest.meters["settled"] += 1
        auditorium.meters["space"] += 1
        world.say(
            f"{performer.label} slid the long bench toward the center aisle, and it looked so small beside "
            f"{guest.label} that even the dust wanted to laugh."
        )
    elif prop.id == "curtain":
        auditorium.meters["space"] += 1
        guest.memes["worry"] -= 1
        world.say(
            f"{helper_e.label} pulled back the curtain and made a wide, friendly lane. The curtain fluttered "
            f"like a flag greeting a giant."
        )
    else:
        auditorium.meters["space"] += 1
        world.say(
            f"{performer.label} lifted the giant hat onto a chair so it would not block the aisle, and the chair "
            f"wobbled like a baby colt."
        )

    if predict_surprise(world, prop):
        world.say(
            f"Then came the surprise: {surprise.label} was not a problem at all, but the very thing the giant had "
            f"brought to help the show."
        )
        performer.memes["delight"] += 1
        helper_e.memes["delight"] += 1
        guest.meters["settled"] += 1
        guest.meters["voice"] += 1
        world.para()
        world.say(
            f"{guest.label} unfurled {surprise.phrase}, and the whole auditorium filled with a comic shimmer. "
            f"The giant bowed, the children snickered, and the rafters behaved like they had just heard a goose tell a joke."
        )
        propagate(world, narrate=True)
        world.say(
            f"At the end, the auditorium had been made roomy enough to accommodate everybody, and the laughter rolled "
            f"out the doors like warm biscuit steam."
        )
    else:
        world.say(
            f"The plan still worked, but only because {performer.label} chose kindness over bravado and arranged the hall "
            f"before saying anything that might provoke a fuss."
        )
        performer.memes["confidence"] += 1
        guest.meters["settled"] += 1
        propagate(world, narrate=True)
        world.say(
            f"By the time the first laugh bounced off the balcony, the giant was smiling, the helper was beaming, "
            f"and the auditorium itself seemed to stand a little taller."
        )

    world.facts.update(
        performer=performer,
        helper_e=helper_e,
        guest=guest,
        auditorium=auditorium,
        bench=bench,
        curtain=curtain,
        hat=hat,
    )
    return world


CAST = [
    CastMember(id="Nell", type="girl", label="Nell", voice="bright", trait="curious"),
    CastMember(id="Bo", type="boy", label="Bo", voice="booming", trait="cheerful"),
    CastMember(id="June", type="girl", label="June", voice="quick", trait="lively"),
]

HELPERS = [
    CastMember(id="AuntMoss", type="woman", label="Aunt Moss", voice="soft", trait="patient"),
    CastMember(id="UnclePike", type="man", label="Uncle Pike", voice="warm", trait="wise"),
    CastMember(id="Mina", type="girl", label="Mina", voice="gentle", trait="playful"),
]

PROPS = [
    Thing(id="bench", label="bench", phrase="a long bench", size="wide", purpose="Settle the giant on a bench", tags={"bench"}),
    Thing(id="curtain", label="curtain", phrase="the red curtain", size="long", purpose="Open the curtain like a doorway", tags={"curtain"}),
    Thing(id="hat", label="hat", phrase="a hat as wide as a wagon wheel", size="wide", purpose="Move the giant hat out of the aisle", tags={"hat"}),
]

SURPRISES = [
    Thing(id="goose", label="a feathered goose", phrase="a feathered goose in a tiny vest", size="small", purpose="Provide a comic surprise", tags={"goose", "humor"}),
    Thing(id="banjo", label="a banjo", phrase="a banjo with a bright blue ribbon", size="small", purpose="Bring a noisy surprise", tags={"banjo", "music"}),
    Thing(id="cookies", label="a tray of cookies", phrase="a tray of star-shaped cookies", size="small", purpose="Sweeten the surprise", tags={"cookies"}),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cast, helper, prop, surprise = f["cast"], f["helper"], f["prop"], f["surprise"]
    return [
        f'Write a tall-tale story for a young child that includes the words "accommodate", "auditorium", and "provoke".',
        f"Tell a funny story where {cast.label} and {helper.label} must accommodate a giant in an auditorium without provoking trouble.",
        f"Write a short, lively story with an inner monologue, a surprise, and a joke that ends with laughter in the auditorium.",
        f"Make a child-friendly tall tale in which {prop.label} helps the characters make room for {surprise.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    performer: Entity = f["performer"]
    helper_e: Entity = f["helper_e"]
    guest: Entity = f["guest"]
    auditorium: Entity = f["auditorium"]
    surprise: Thing = f["surprise"]
    prop: Thing = f["prop"]
    return [
        QAItem(
            question=f"Why did {performer.label} and {helper_e.label} go into the auditorium?",
            answer=(
                f"They went there to accommodate the giant guest and make the room ready for the show. "
                f"That way nobody had to squeeze into a bad spot, and the evening could start with a smile."
            ),
        ),
        QAItem(
            question=f"What did {performer.label} worry about before saying the joke?",
            answer=(
                f"{performer.label} worried that a careless joke might provoke trouble. "
                f"Inside {performer.pronoun('possessive')} head, {performer.pronoun()} decided that making room first was wiser than trying to sound clever."
            ),
        ),
        QAItem(
            question=f"What changed when {surprise.label} turned out to be part of the show?",
            answer=(
                f"The surprise stopped feeling scary and became funny instead. "
                f"After that, the auditorium filled with laughter and the giant could settle in without fuss."
            ),
        ),
        QAItem(
            question=f"How did {prop.label} help the tall-tale ending?",
            answer=(
                f"{prop.phrase.capitalize()} gave the characters a simple way to make space. "
                f"Once the room was arranged, the giant had room, the crowd had room, and the joke had room to land."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a large room built for a crowd to listen, watch, and laugh together.",
        ),
        QAItem(
            question="What does accommodate mean?",
            answer="To accommodate something means to make room for it or help it fit comfortably.",
        ),
        QAItem(
            question="What does provoke mean?",
            answer="To provoke means to stir up a strong reaction, sometimes a laugh and sometimes trouble.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is a sudden change the reader did not expect, and it can make the story feel lively.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thinking on the page, as if the reader can hear the thoughts inside the head.",
        ),
        QAItem(
            question="Why do tall tales sound funny?",
            answer="Tall tales sound funny because they stretch things big and far, but still keep a playful heart.",
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


ASP_RULES = r"""
accommodates(P, G) :- performer(P), guest(G), makes_room(P, G).
provokes(P, G) :- performer(P), guest(G), risky_joke(P), not makes_room(P, G).
happy_end :- accommodates(_, _), surprise_good, laughter.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CAST:
        lines.append(asp.fact("cast", c.id))
        lines.append(asp.fact("type_of", c.id, c.type))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("type_of", h.id, h.type))
    for p in PROPS:
        lines.append(asp.fact("prop", p.id))
        lines.append(asp.fact("size", p.id, p.size))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s.id))
    lines.append(asp.fact("auditorium", "auditorium"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show accommodates/2.\n#show provokes/2."))
    return sorted(set(asp.atoms(model, "accommodates")))


def asp_verify() -> int:
    import asp
    program = asp_program("#show accommodates/2.")
    _ = asp.one_model(program)
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    sample = generate(resolve_params(argparse.Namespace(cast=None, helper=None, prop=None, surprise=None, seed=None), random.Random(777)))
    if ok and sample.story:
        print(f"OK: ASP/Python parity holds ({len(py)} combos).")
        print("OK: generate() smoke test produced a story.")
        return 0
    print("MISMATCH or smoke-test failure.")
    if cl != py:
        print("Python only:", sorted(py - cl))
        print("ASP only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale auditorium storyworld.")
    ap.add_argument("--cast", choices=[c.id for c in CAST])
    ap.add_argument("--helper", choices=[h.id for h in HELPERS])
    ap.add_argument("--prop", choices=[p.id for p in PROPS])
    ap.add_argument("--surprise", choices=[s.id for s in SURPRISES])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    filtered = [
        c for c in combos
        if (args.cast is None or c[0] == args.cast)
        and (args.helper is None or c[1] == args.helper)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    cast, helper, prop = rng.choice(sorted(filtered))
    surprise = args.surprise or rng.choice([s.id for s in SURPRISES])
    return StoryParams(cast=cast, helper=helper, prop=prop, surprise=surprise)


def generate(params: StoryParams) -> StorySample:
    cast = next((c for c in CAST if c.id == params.cast), None)
    helper = next((h for h in HELPERS if h.id == params.helper), None)
    prop = next((p for p in PROPS if p.id == params.prop), None)
    surprise = next((s for s in SURPRISES if s.id == params.surprise), None)
    if not all([cast, helper, prop, surprise]):
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(cast, helper, prop, surprise)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            if e.role:
                bits.append(f"role={e.role}")
            print(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(cast="Nell", helper="AuntMoss", prop="bench", surprise="goose"),
    StoryParams(cast="Bo", helper="UnclePike", prop="curtain", surprise="banjo"),
    StoryParams(cast="June", helper="Mina", prop="hat", surprise="cookies"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CAST:
        for h in HELPERS:
            for p in PROPS:
                if c.id != h.id and p.id in {x.id for x in PROPS}:
                    combos.append((c.id, h.id, p.id))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show accommodates/2.\n#show provokes/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show accommodates/2.\n#show provokes/2."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

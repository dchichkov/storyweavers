#!/usr/bin/env python3
"""
A small mythic storyworld about a dude, a grammatic charm, bravery, and humor.

The world premise:
A young dude wants to prove bravery by climbing a steep hill to ring a sky-bell,
but the climb only works if he carries a grammatic charm that keeps the old
riddle-steps in order. Humor helps him stay calm; bravery helps him keep going.
The ending shows that the hill is climbed, the charm is used correctly, and the
dude returns with a story worth telling.

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager results import
- lazy asp import in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python vs ASP parity and exercises generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dude", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    fixs: set[str]
    needed_for: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _raise_bravery(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + amount


def _raise_humor(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0.0) + amount


def _raise_confidence(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + amount


def _do_challenge(world: World, hero: Entity, challenge: Challenge, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} does not afford {challenge.id}.")
    hero.meters[challenge.id] = hero.meters.get(challenge.id, 0.0) + 1.0
    _raise_bravery(world, hero, 1.0)
    if narrate:
        world.say(f"{hero.id} climbed farther, and his bravery grew.")


def predict_outcome(world: World, hero: Entity, challenge: Challenge, charm: Optional[Charm]) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    _do_challenge(sim, h, challenge, narrate=False)
    grammar_ok = True
    if charm is None:
        grammar_ok = False
    else:
        grammar_ok = challenge.id in charm.needed_for
    return {
        "brave": h.memes.get("bravery", 0.0) >= THRESHOLD,
        "grammar_ok": grammar_ok,
        "resolved": grammar_ok and h.meters.get(challenge.id, 0.0) >= THRESHOLD,
    }


def setup_story(world: World, hero: Entity, challenge: Challenge, charm: Charm) -> None:
    world.say(
        f"{hero.id} was a little dude with a big wish to prove himself."
    )
    world.say(
        f"He loved old myths, and he loved humor even more, because a laugh could make a hard road feel lighter."
    )
    world.say(
        f"One day, he found a {charm.label} with a {charm.phrase}, and the charm promised to keep the steps grammatic."
    )
    world.say(
        f"Beyond the village stood {world.setting.place}, where the sky-bell waited above the {challenge.verb} path."
    )


def tension_story(world: World, hero: Entity, challenge: Challenge, charm: Charm) -> None:
    world.para()
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to {challenge.verb}, but the path was known for breaking careless travelers into tangled mistakes."
    )
    world.say(
        f"The old gatekeeper warned that the climb had to stay grammatic, or the hill would answer with confusion."
    )
    world.say(
        f"{hero.id} tried to laugh off the fear, but his knees still felt wobbly at the thought of the steep stones."
    )
    _raise_humor(world, hero, 1.0)
    if predict_outcome(world, hero, challenge, charm)["grammar_ok"]:
        world.say(
            f"Still, the charm sat warm in his palm, and that gave him enough courage to begin."
        )


def resolution_story(world: World, hero: Entity, challenge: Challenge, charm: Charm) -> None:
    world.para()
    if not predict_outcome(world, hero, challenge, charm)["grammar_ok"]:
        raise StoryError("the charm does not fit this challenge's grammar.")
    _do_challenge(world, hero, challenge, narrate=False)
    _raise_confidence(world, hero, 1.0)
    world.say(
        f"{hero.id} took the charm, counted the steps, and climbed with slow brave feet."
    )
    world.say(
        f"Whenever the stones tried to trip him, he remembered the grammatic pattern and the silly joke he had made earlier."
    )
    world.say(
        f"At the top, he rang the sky-bell, and its bright sound rolled across the valley like a blessing."
    )
    world.say(
        f"When he came home, the village called him brave, and the dude laughed because the best hero stories always had room for humor."
    )


def build_world(setting: Setting, challenge: Challenge, charm: Charm, name: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters={},
        memes={"bravery": 0.0, "humor": 1.0, "confidence": 0.0},
    ))
    world.add(Entity(
        id=charm.id,
        kind="thing",
        type="charm",
        label=charm.label,
        phrase=charm.phrase,
        owner=hero.id,
    ))
    setup_story(world, hero, challenge, charm)
    tension_story(world, hero, challenge, charm)
    resolution_story(world, hero, challenge, charm)
    world.facts.update(hero=hero, challenge=challenge, charm=charm, setting=setting)
    return world


SETTINGS = {
    "skyhill": Setting(place="the skyhill", affords={"bellclimb"}),
    "ruinstairs": Setting(place="the ancient ruin stairs", affords={"bellclimb"}),
    "moonroad": Setting(place="the moonroad ridge", affords={"bellclimb"}),
}

CHALLENGES = {
    "bellclimb": Challenge(
        id="bellclimb",
        verb="climb to the sky-bell",
        gerund="climbing to the sky-bell",
        risk="slipping and losing the way",
        zone="stone steps",
        keyword="bell",
        tags={"bravery", "myth"},
    ),
}

CHARMS = {
    "grammatic_charm": Charm(
        id="grammatic_charm",
        label="grammatic charm",
        phrase="tiny runes that ordered every step",
        fixs={"confusion"},
        needed_for={"bellclimb"},
    ),
}

NAMES = ["Dude", "Milo", "Ravi", "Theo", "Bram", "Niko"]
GENDERS = ["dude"]
TRAITS = ["brave", "funny", "earnest", "bold"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    charm: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for challenge in setting.affords:
            for charm_id, charm in CHARMS.items():
                if challenge in charm.needed_for:
                    combos.append((place, challenge, charm_id))
    return combos


def explain_rejection(challenge: Challenge, charm: Charm) -> str:
    return f"(No story: the {charm.label} does not really help with {challenge.verb}; the myth needs a grammatic fit.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: a dude, a grammatic charm, bravery, and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.challenge and args.charm:
        ch = CHALLENGES[args.challenge]
        cm = CHARMS[args.charm]
        if args.challenge not in cm.needed_for:
            raise StoryError(explain_rejection(ch, cm))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, charm = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or "dude"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, charm=charm, name=name, gender=gender, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth about a dude and a grammatic charm who need bravery and humor to finish a climb.',
        f"Tell a child-friendly myth where {f['hero'].id} uses a grammatic charm to {f['challenge'].verb}.",
        f"Write a story about {f['hero'].id}, bravery, humor, and a sky-bell on {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, challenge, charm, setting = f["hero"], f["challenge"], f["charm"], f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little dude who wants to be brave."
        ),
        QAItem(
            question=f"What did {hero.id} carry to help with the climb?",
            answer=f"{hero.id} carried the {charm.label}, which kept the climb grammatic."
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"He wanted to {challenge.verb} and ring the sky-bell at the top."
        ),
        QAItem(
            question=f"How did humor help {hero.id}?",
            answer=f"Humor helped him stay calm and keep going when the path felt scary."
        ),
        QAItem(
            question=f"How did bravery change by the end?",
            answer=f"His bravery grew because he kept climbing until he reached the sky-bell."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling and choice of keeping on when something is scary."
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is what makes people laugh and feel lighter."
        ),
        QAItem(
            question="What does grammatic mean in this story?",
            answer="Here, grammatic means arranged in the right order, so the climb works properly."
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old-style story about big actions, special places, and lessons people remember."
        ),
    ]


ASP_RULES = r"""
#show valid/3.

valid(P,C,H) :- place(P), challenge(C), charm(H), affords(P,C), helps(H,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for hid, h in CHARMS.items():
        lines.append(asp.fact("charm", hid))
        for c in sorted(h.needed_for):
            lines.append(asp.fact("helps", hid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(SETTINGS[params.place], CHALLENGES[params.challenge], CHARMS[params.charm], params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id} ({e.type}) meters={meters} memes={memes}")
    return "\n".join(lines)


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
    StoryParams(place="skyhill", challenge="bellclimb", charm="grammatic_charm", name="Dude", gender="dude", trait="brave"),
    StoryParams(place="ruinstairs", challenge="bellclimb", charm="grammatic_charm", name="Milo", gender="dude", trait="funny"),
    StoryParams(place="moonroad", challenge="bellclimb", charm="grammatic_charm", name="Bram", gender="dude", trait="earnest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

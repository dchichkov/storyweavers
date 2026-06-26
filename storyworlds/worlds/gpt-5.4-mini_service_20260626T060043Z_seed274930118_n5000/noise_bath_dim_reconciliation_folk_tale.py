#!/usr/bin/env python3
"""
storyworlds/worlds/noise_bath_dim_reconciliation_folk_tale.py
==============================================================

A small folk-tale storyworld about noise in a bath-dim place and a reconciliation
that mends a strained friendship.

The core premise:
- A young helper makes too much noise in a dim bath-house.
- A careful elder warns them because the noise wakes animals and upsets the quiet.
- The helper learns a gentler way to act, apologizes, and the two reconcile.

This world is intentionally narrow: it favors a few strong, child-facing
problem/fix pairs over many weak variants.
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "quiet": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "hurt": 0.0, "trust": 0.0, "peace": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elder_woman"}
        male = {"boy", "father", "man", "elder_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bath-dim house"
    noun: str = "bath-dim house"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    noisy_thing: str
    noise_kind: str
    consequence: str
    quiet_way: str
    keyword: str = "noise"
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_noise_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("noise", 0.0) < THRESHOLD:
            continue
        sig = ("noise_spread", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.characters():
            if other.id == actor.id:
                continue
            other.memes["worry"] += 1
            other.memes["hurt"] += 1
        out.append("The noise drifted through the dim rooms and made the others wince.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("apology", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.characters():
            if other.id == actor.id:
                continue
            if other.memes.get("hurt", 0.0) >= THRESHOLD:
                other.memes["hurt"] = 0.0
                other.memes["peace"] += 1
                other.memes["trust"] += 1
        actor.memes["peace"] += 1
        actor.memes["trust"] += 1
        out.append("The apology settled softly, like rain on a roof, and the room grew gentle again.")
    return out


def propagate(world: World) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_noise_spread, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    for s in out:
        world.say(s)
    return out


def predict_consequence(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["noise"] += 1
    propagate(sim)
    hurt = sum(e.memes.get("hurt", 0.0) for e in sim.characters())
    peace = sum(e.memes.get("peace", 0.0) for e in sim.characters())
    return {"hurt": hurt, "peace": peace}


def select_comfort(action: Action) -> Optional[Comfort]:
    for c in COMFORTS:
        if action.noise_kind in c.helps:
            return c
    return None


def introduction(world: World, hero: Entity, elder: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "bright")
    world.say(
        f"In a small village, there lived a young {trait} {hero.type} named {hero.id}. "
        f"Near the bath-dim house lived {elder.id}, who kept the place calm and kind."
    )


def setup_love(world: World, hero: Entity, action: Action) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved to {action.verb}, because {action.gerund} made the day feel lively and bold."
    )


def arrive(world: World, hero: Entity, elder: Entity, action: Action) -> None:
    world.say(
        f"One evening, {hero.id} came to {world.setting.place}, where the lanterns glowed bath-dim and the air was still."
    )
    world.say(
        f"{hero.id} wanted to {action.verb} at once."
    )


def warning(world: World, elder: Entity, hero: Entity, action: Action) -> bool:
    pred = predict_consequence(world, hero, action)
    if pred["hurt"] < THRESHOLD:
        return False
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f'"If you make that {action.noisy_thing}, child," {elder.id} said, '
        f'"the village will hear it, and the quiet folk will be troubled."'
    )
    return True


def defy(world: World, hero: Entity, action: Action) -> None:
    hero.meters["noise"] += 1
    hero.memes["worry"] += 0.5
    world.say(
        f"{hero.id} did not mean harm, but the wish to play was loud in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{hero.id} tried to {action.verb}, and the {action.noisy_thing} went clatter-clap through the bath-dim room."
    )
    propagate(world)


def apology(world: World, hero: Entity, elder: Entity, action: Action, comfort: Comfort) -> None:
    hero.memes["apology"] += 1
    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head and said, "
        f'"I am sorry for the noise. I can use a gentler way."'
    )
    world.say(
        f"{elder.id} listened, and together they chose {comfort.phrase}, so {hero.id} could still {action.verb} without troubling the house."
    )
    propagate(world)


def ending(world: World, hero: Entity, elder: Entity, action: Action, comfort: Comfort) -> None:
    hero.meters["noise"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["peace"] += 1
    world.say(
        f"Before long, {hero.id} was {action.gerund}, and the only sound was a soft, happy one."
    )
    world.say(
        f"{elder.id} smiled at the bath-dim light, because the room was calm again and the two of them had made peace."
    )


def tell(setting: Setting, action: Action, comfort: Comfort, hero_name: str, hero_type: str,
         elder_name: str, elder_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, traits=["young", "lively", "stubborn"]
    ))
    elder = world.add(Entity(
        id=elder_name, kind="character", type=elder_type, traits=["old", "wise", "gentle"]
    ))
    world.facts.update(hero=hero, elder=elder, action=action, comfort=comfort)

    introduction(world, hero, elder)
    world.para()
    setup_love(world, hero, action)
    world.para()
    arrive(world, hero, elder, action)
    warning(world, elder, hero, action)
    defy(world, hero, action)
    world.para()
    apology(world, hero, elder, action, comfort)
    ending(world, hero, elder, action, comfort)

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "village_house": Setting(place="the bath-dim house", noun="bath-dim house", affords={"drum", "pan", "sing"}),
    "river_lantern_room": Setting(place="the lantern room by the river", noun="lantern room", affords={"bell", "drum", "sing"}),
}

ACTIONS = {
    "drum": Action(
        id="drum",
        verb="beat a drum",
        gerund="beating the drum",
        noisy_thing="drum",
        noise_kind="noise",
        consequence="the walls trembled",
        quiet_way="tap a small drum softly",
        tags={"noise"},
    ),
    "bell": Action(
        id="bell",
        verb="ring a bell",
        gerund="ringing the bell",
        noisy_thing="bell",
        noise_kind="noise",
        consequence="the animals woke and peeped out",
        quiet_way="shake a little hand bell softly",
        tags={"noise"},
    ),
    "pan": Action(
        id="pan",
        verb="tap a pan",
        gerund="tapping the pan",
        noisy_thing="pan",
        noise_kind="noise",
        consequence="the soup spoon jumped in its bowl",
        quiet_way="tap the pan with a cloth-wrapped spoon",
        tags={"noise"},
    ),
    "sing": Action(
        id="sing",
        verb="sing a folk song",
        gerund="singing a folk song",
        noisy_thing="song",
        noise_kind="noise",
        consequence="the dim room filled with bright echoes",
        quiet_way="sing a lullaby",
        tags={"noise"},
    ),
}

COMFORTS = [
    Comfort(id="soft_cloth", label="soft cloth", phrase="a soft cloth wrapped around the drumsticks", helps={"noise"}),
    Comfort(id="hush_song", label="hush song", phrase="a hush song in a low voice", helps={"noise"}),
    Comfort(id="felt_mallet", label="felt mallet", phrase="felt mallets that made the drum speak gently", helps={"noise"}),
]

HEROES = {
    "girl": ["Mira", "Nia", "Tessa", "Lina"],
    "boy": ["Eli", "Milo", "Jun", "Pavel"],
}
ELDERS = {
    "woman": ["Grandmother Reed", "Aunt Sava", "Old Maren"],
    "man": ["Grandfather Moss", "Uncle Bran", "Old Tovin"],
}


@dataclass
class StoryParams:
    place: str
    action: str
    comfort: str
    hero_name: str
    hero_type: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            action = ACTIONS[act_id]
            for comfort in COMFORTS:
                if action.noise_kind in comfort.helps:
                    combos.append((place, act_id, comfort.id))
    return combos


def explain_rejection(action: Action, comfort: Comfort) -> str:
    return (
        f"(No story: {action.verb} does not pair with {comfort.label} in a convincing reconciliation. "
        f"The fix must soften the same noise problem, or the tale would feel forced.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about noise, a bath-dim place, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--comfort", choices=[c.id for c in COMFORTS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--elder-name")
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
    if args.action and args.comfort:
        action = ACTIONS[args.action]
        comfort = next(c for c in COMFORTS if c.id == args.comfort)
        if action.noise_kind not in comfort.helps:
            raise StoryError(explain_rejection(action, comfort))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero_name = args.name or rng.choice(HEROES[gender])
    elder_name = args.elder_name or rng.choice(ELDERS[elder_gender])
    return StoryParams(place, action, comfort, hero_name, gender, elder_name, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        next(c for c in COMFORTS if c.id == params.comfort),
        params.hero_name,
        params.hero_type,
        params.elder_name,
        params.elder_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    action = f["action"]
    return [
        f'Write a short folk tale for a child that includes the word "noise" and the phrase "bath-dim".',
        f"Tell a gentle village story where {f['hero'].id} wants to {action.verb} in {world.setting.place}, but learns a quieter way.",
        f"Write a reconciliation story about a loud mistake, an apology, and a calm ending in a dim house.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    action = f["action"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Why did {hero.id} get into trouble at {world.setting.place}?",
            answer=f"{hero.id} got into trouble because {hero.pronoun('subject')} made too much noise by {action.verb}. That was hard in the bath-dim house because the others were trying to keep things calm.",
        ),
        QAItem(
            question=f"What did {elder.id} ask {hero.id} to do instead?",
            answer=f"{elder.id} asked {hero.id} to choose a gentler way, using {comfort.phrase}. That way, {hero.id} could still enjoy the play without waking up the whole place.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {elder.id}?",
            answer=f"They apologized and made peace. In the end, {hero.id} was still {action.gerund}, but softly, and {elder.id} was smiling again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does noise do in a quiet place?",
            answer="Noise can carry far in a quiet place, which is why it can bother people or animals who are resting.",
        ),
        QAItem(
            question="What is an apology?",
            answer="An apology is when someone says they are sorry for hurting or troubling another person.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset with each other become friendly again.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
noise_spreads(A) :- actor(A), noisy(A).
hurt(B) :- noise_spreads(A), actor(B), B != A.
needs_reconcile(A,B) :- apology(A), hurt(B), actor(A), actor(B), A != B.
peace(A) :- apology(A), actor(A).
valid_story(P, A, C) :- setting(P), action(A), comfort(C), compatible(A,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("noisy", aid))
    for cid, c in ((c.id, c) for c in COMFORTS):
        lines.append(asp.fact("comfort", cid))
        for h in c.helps:
            lines.append(asp.fact("compatible", next(k for k, v in ACTIONS.items() if v.noise_kind in c.helps), cid))
    for who in ("hero", "elder"):
        lines.append(asp.fact("actor", who))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams("village_house", "drum", "soft_cloth", "Mira", "girl", "Grandmother Reed", "woman"),
    StoryParams("river_lantern_room", "bell", "hush_song", "Eli", "boy", "Grandfather Moss", "man"),
    StoryParams("village_house", "sing", "hush_song", "Lina", "girl", "Old Maren", "woman"),
]


def world_knowledge_only() -> bool:
    return True


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        i = 0
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reconciliation?",
            answer="A reconciliation is when people who were upset with each other become friendly again.",
        ),
        QAItem(
            question="Why is a bath-dim room peaceful?",
            answer="A bath-dim room is peaceful because the light is low and the place is meant for resting and washing, not for rough noise.",
        ),
        QAItem(
            question="Why should a child use a quieter way in a folk tale?",
            answer="In folk tales, a quieter way often helps the child respect others, solve the problem, and keep the village harmony."
        ),
    ]


if __name__ == "__main__":
    main()

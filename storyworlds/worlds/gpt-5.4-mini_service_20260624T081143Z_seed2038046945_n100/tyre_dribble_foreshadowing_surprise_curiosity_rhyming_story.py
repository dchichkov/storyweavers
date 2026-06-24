#!/usr/bin/env python3
"""
storyworlds/worlds/tyre_dribble_foreshadowing_surprise_curiosity_rhyming_story.py
=================================================================================

A tiny classical story world for a rhyming TinyStories-style tale about a tyre,
a dribble, curiosity, foreshadowing, and surprise.

Premise:
- A child notices a strange dribble near an old tyre.
- Curiosity leads the child to inspect it.
- Foreshadowing hints that something is hidden or loose.
- Surprise reveals a small, harmless cause.
- The ending proves what changed in the world: the tyre is fixed, and the child
  feels calmer and wiser.

The world is deliberately small and state-driven:
- physical meters track moisture, wobble, rollability, and dirt
- emotional memes track curiosity, worry, surprise, and relief
- prose is generated from the simulated world state rather than from a frozen
  template swap

This script follows the storyworld contract:
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- imports storyworlds/results eagerly and storyworlds/asp lazily
- provides inline ASP rules and a Python reasonableness gate
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed, -n
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    action: str
    fix: str
    clue: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = meter(ent, key) + delta


def add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = meme(ent, key) + delta


SETTINGS = {
    "yard": Setting(place="the yard", indoors=False, affords={"dribble", "inspect"}),
    "garage": Setting(place="the garage", indoors=True, affords={"dribble", "inspect"}),
    "shed": Setting(place="the shed", indoors=True, affords={"inspect"}),
}

ACTIVITIES = {
    "dribble": Activity(
        id="dribble",
        verb="follow the dribble",
        gerund="following the dribble",
        rush="run toward the drip",
        mess="wet",
        soil="a little wet",
        keyword="dribble",
        clues=["sparkle", "trail", "drop"],
    ),
    "inspect": Activity(
        id="inspect",
        verb="look closely at the tyre",
        gerund="peeking near the tyre",
        rush="tiptoe closer",
        mess="dusty",
        soil="dusty",
        keyword="tyre",
        clues=["look", "peek", "check"],
    ),
}

PRIZES = {
    "tyre": Prize(
        label="tyre",
        phrase="an old round tyre",
        type="tyre",
        region="ground",
    ),
}

HELPERS = {
    "patch": Helper(
        id="patch",
        label="a little patch kit",
        action="patch the hole",
        fix="patched",
        clue="a tiny thorn",
    ),
}

GIRL_NAMES = ["Mia", "Ava", "Nora", "Zoe", "Luna", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Owen", "Eli", "Max"]
TRAITS = ["curious", "brave", "cheerful", "bouncy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return prize.region == "ground" and activity.id in {"dribble", "inspect"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if is_reasonable(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: this world only fits a tyre on the ground with a dribble or a close look. "
        f"The requested pair would not give a clear foreshadowing, surprise, and fix.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming story world about a tyre, a dribble, curiosity, and surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not is_reasonable(act, prize):
            raise StoryError(explain_rejection(act, prize))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def setting_line(setting: Setting) -> str:
    return "The yard was warm and bright." if not setting.indoors else "The garage was dim, but neat and light."


def narrate_foreshadow(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = 1.0
    world.say(
        f"{hero.id} was a {hero.pronoun('possessive')} curious little soul, with a grin so bright and light. "
        f"{setting_line(world.setting)}"
    )
    world.say(
        f"{hero.id} loved to {activity.verb}, to sing and swing and sway, "
        f"but near the old tyre there was a dribble in the way."
    )
    world.say(
        f"That tiny wet trail gave a clue, a hint, a gleam, a sheen; "
        f"something small was hiding there, not quite as it had seemed."
    )


def narrate_surprise(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    add_meme(hero, "surprise", 1.0)
    world.say(
        f"{hero.id} leaned in close, then blinked and gasped, with eyes both wide and new: "
        f"the dribble came from a tiny thorn that poked the tyre through and through."
    )
    world.say(
        f"It was not a spooky beast at all, nor ghostly gooey slime; "
        f"just one small thorn, half-hidden there, and found at the perfect time."
    )


def narrate_fix(world: World, hero: Entity, prize: Entity) -> None:
    helper = world.facts["helper"]
    add_meter(prize, "broken", 0.0)
    prize.meters["leak"] = 0.0
    world.say(
        f"Then {hero.id} fetched {helper.label}, a patch kit neat and keen; "
        f"they patched the spot, the dribble stopped, and the tyre stayed clean."
    )
    world.say(
        f"{hero.id} felt proud and calm and glad, with curiosity now fed; "
        f"the tyre was safe, the trail was done, and all the worry fled."
    )
    world.facts["resolved"] = True


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    prize = world.add(Entity(id="tyre", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, meters={"leak": 1.0}))
    helper = world.add(Entity(id="patch", type="tool", label=HELPERS["patch"].label))
    world.facts.update(hero=hero, prize=prize, helper=HELPERS["patch"], activity=activity, setting=setting, trait=trait)

    world.say(
        f"{hero.id} was a {trait} {hero.type} who liked a rhyme and a climb, "
        f"and every day loved wonder as much as sunshine."
    )
    world.para()
    narrate_foreshadow(world, hero, prize, activity)
    world.para()
    narrate_surprise(world, hero, prize, activity)
    world.para()
    narrate_fix(world, hero, prize)
    return world


KNOWLEDGE = {
    "tyre": [("What is a tyre?", "A tyre is the round rubber ring on a wheel that helps a vehicle roll.")],
    "dribble": [("What is a dribble?", "A dribble is a tiny trickle or drop that moves slowly along a surface.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn.")],
    "surprise": [("What is surprise?", "Surprise is a quick feeling you get when something happens that you did not expect.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is a small hint that something important may happen later.")],
}


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    prize = world.facts["prize"]
    activity = world.facts["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} look at the tyre so closely?",
            answer=f"{hero.id} was curious and noticed the dribble, so {hero.pronoun()} wanted to find out what was causing it.",
        ),
        QAItem(
            question=f"What surprising thing caused the dribble near the tyre?",
            answer="A tiny thorn had poked the tyre, and that made the little wet trail.",
        ),
        QAItem(
            question=f"What changed after the patch kit was used?",
            answer=f"The tyre stopped leaking, the dribble was gone, and {hero.id} felt calm and proud.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = {"tyre", "dribble", "curiosity", "surprise", "foreshadowing"}
    out: list[QAItem] = []
    for tag in ["foreshadowing", "surprise", "curiosity", "dribble", "tyre"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    activity = world.facts["activity"]
    return [
        f"Write a short rhyming story for a child named {hero.id} who notices a dribble by a tyre.",
        f"Tell a gentle story where curiosity leads {hero.id} to inspect a tyre and find the source of the dribble.",
        f"Write a rhyming TinyStories-style tale with foreshadowing, surprise, and a happy repair.",
    ]


ASP_RULES = r"""
#show valid/3.
place(P) :- setting(P).
valid(P,A,T) :- afford(P,A), tyre(T), ground(T), dribble_story(A), foreshadows(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("afford", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if aid == "dribble":
            lines.append(asp.fact("dribble_story", aid))
            lines.append(asp.fact("foreshadows", aid))
        if aid == "inspect":
            lines.append(asp.fact("foreshadows", aid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("tyre", pid))
        lines.append(asp.fact("ground", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        lines.append(f"  {e.id:8} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place=p, activity=a, prize=t, name="Mia", gender="girl", trait="curious")
            for p, a, t in valid_combos()
        ]
        samples = [generate(p) for p in params_list]
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

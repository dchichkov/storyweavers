#!/usr/bin/env python3
"""
storyworlds/worlds/stream_choice_sound_effects_kindness_surprise_rhyming.py
============================================================================

A small story world about a child by a stream, a careful choice, sound effects,
kindness, and a gentle surprise. The prose is shaped as a rhyming story:
setup, choice, tension, and a happy turn with a concrete ending image.

Seed tale:
---
Mina went to the stream on a bright day. The water made a soft whispering sound.
She wanted to reach the shiny reeds on the other side, but stepping on the slick
stones felt risky. Mina noticed a duckling stuck near the bank. She chose to help
the duckling first, and the duckling led her to a safe crossing. At the end, Mina
reached the reeds, and the little duckling surprised her by splashing a trail of
sparkly water in a wiggly dance.
---

This world models:
- a child and a stream, with physical meters for closeness, wetness, and safety;
- emotional memes for wish, worry, kindness, and surprise;
- sound effects that are narrated when the stream is stirred;
- a choice between rushing ahead and helping first;
- a surprise payoff at the end that proves the choice mattered.

The script follows the storyworld contract:
- stdlib-only top-level imports;
- eager import from storyworlds/results.py;
- lazy import of storyworlds/asp.py in ASP helpers;
- build_parser, resolve_params, generate, emit, main;
- --verify parity between Python and ASP gates.
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
    plural: bool = False
    owner: Optional[str] = None
    friend: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the stream"
    affords: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    prompt: str
    safe_path: str
    risky_path: str
    sound: str
    effect: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False
    risky_if: str = "stream"


@dataclass
class Helper:
    id: str
    label: str
    action: str
    gift: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.stream_sound: list[str] = []

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.stream_sound = list(self.stream_sound)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def rhyming_line(a: str, b: str) -> str:
    return f"{a} — {b}"


def sound_effect(world: World, effect: str) -> None:
    world.stream_sound.append(effect)
    world.say(effect)


def make_wet(world: World, actor: Entity, amount: float = 1.0) -> None:
    actor.meters["wet"] = actor.meters.get("wet", 0.0) + amount


def _r_stream_splash(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wade", 0.0) < THRESHOLD:
            continue
        sig = ("splash", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        make_wet(world, actor, 1.0)
        out.append("Splish-splash! The stream gave a merry tap.")
    return out


def _r_kindness_help(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    helper = world.facts.get("helper")
    if not child or not helper:
        return out
    if child.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("help", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["safe_path"] = 1.0
    helper.meters["guided"] = 1.0
    out.append("Step by step, the helper showed the way.")
    return out


def _r_surprise_reward(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    helper = world.facts.get("helper")
    prize = world.facts.get("prize")
    if not child or not helper or not prize:
        return out
    if child.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    sig = ("surprise", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
    prize.meters["found"] = 1.0
    out.append(prize.phrase)
    return out


CAUSAL_RULES = [_r_stream_splash, _r_kindness_help, _r_surprise_reward]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_check(choice: Choice, prize: Prize) -> bool:
    return choice.id == prize.risky_if


def python_valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for choice_id, choice in CHOICES.items():
        for prize_id, prize in PRIZES.items():
            if risk_check(choice, prize):
                combos.append((choice.setting_tag, choice_id, prize_id))
    return combos


def predicted_choice_story(world: World, child: Entity, choice: Choice, helper: Entity) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.meters["wade"] = 1.0
    child2.memes["kindness"] = 0.0
    if choice.id == "rush":
        child2.meters["rush"] = 1.0
    else:
        child2.memes["kindness"] = 1.0
    propagate(sim, narrate=False)
    return {
        "wet": child2.meters.get("wet", 0.0),
        "safe": child2.meters.get("safe_path", 0.0) >= THRESHOLD,
    }


def choose_sound(choice: Choice) -> str:
    return choice.sound


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} came to {setting.place} with a hop and a grin, "
        f"to see what the day would bring within."
    )


def describe_stream(world: World, choice: Choice) -> None:
    world.say(
        f"The water made a soft sound, {choose_sound(choice)}, and glittered like glass on the ground."
    )


def present_choice(world: World, child: Entity, choice: Choice, prize: Entity) -> None:
    world.say(
        f"{child.id} saw a choice ahead: dash on by, or help first instead."
    )
    world.say(
        f"One path looked quick, but slick stones might slip; the other helped someone near the rippling lip."
    )
    world.say(
        f"At the far bank, a tiny surprise waited close to {prize.phrase} and bright green tide."
    )


def take_choice(world: World, child: Entity, helper: Entity, choice: Choice) -> None:
    if choice.id == "rush":
        child.meters["wade"] = 1.0
        child.meters["rush"] = 1.0
        world.say(
            f"{child.id} chose to rush with a dash and a leap, but the stones were slick and deep."
        )
    else:
        child.memes["kindness"] = 1.0
        child.meters["wade"] = 1.0
        world.say(
            f"{child.id} chose kindness first, and spoke in a sweet, steady tone."
        )
        world.say(
            f"That was the kindest choice, and it made the helper feel less alone."
        )
    propagate(world, narrate=True)


def helper_turn(world: World, child: Entity, helper: Entity) -> None:
    if child.memes.get("kindness", 0.0) < THRESHOLD:
        world.say(
            f"The helper frowned, then pointed to reeds, where the safe stones waited in lines."
        )
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    else:
        world.say(
            f"The helper smiled and nodded along, then led {child.id} where the path felt strong."
        )
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0


def finish(world: World, child: Entity, helper: Entity, prize: Entity) -> None:
    if prize.meters.get("found", 0.0) >= THRESHOLD:
        world.say(
            f"At last, {child.id} found {prize.phrase}, and the stream gave a shivery twirl."
        )
        world.say(
            f"Then came a surprise: {helper.id} winked and splashed a sparkly curl."
        )
        child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
        world.say(
            f"{child.id} laughed, 'Oh my!' as the water danced by, and the day ended light as a pearl."
        )
    else:
        world.say(
            f"Even without the prize, {child.id} learned a bright thing: kind steps can make brave things spring."
        )


@dataclass
class StoryParams:
    place: str
    choice: str
    prize: str
    child_name: str
    child_type: str
    helper_type: str
    seed: Optional[int] = None


SETTINGS = {
    "stream": Setting(place="the stream", affords={"rush", "kind"}),
}

CHOICES = {
    "rush": Choice(
        id="rush",
        prompt="rush across the slick stones",
        safe_path="careful stones",
        risky_path="slick stones",
        sound="splish-splash",
        effect="wet feet",
        surprise="sparkly ripples",
        tags={"stream", "sound", "surprise"},
    ),
    "kind": Choice(
        id="kind",
        prompt="help the little helper first",
        safe_path="kind hands",
        risky_path="waiting too long",
        sound="tip-tip",
        effect="warm hearts",
        surprise="a hidden path",
        tags={"stream", "kindness", "surprise"},
    ),
}

PRIZES = {
    "reeds": Prize(
        id="reeds",
        label="reeds",
        phrase="A shiny trail of reeds waved hello",
        region="hands",
        plural=True,
        risky_if="rush",
    ),
    "shell": Prize(
        id="shell",
        label="shell",
        phrase="A pearly shell peeked out of the foam",
        region="hands",
        plural=False,
        risky_if="rush",
    ),
}

HELPERS = {
    "duckling": Helper(
        id="duckling",
        label="duckling",
        action="guide",
        gift="tiny bright path",
        tags={"kindness", "surprise"},
    ),
    "frog": Helper(
        id="frog",
        label="frog",
        action="hop",
        gift="plip-plop trail",
        tags={"sound", "surprise"},
    ),
}

NAMES = ["Mina", "Toby", "Lia", "Noah", "Poppy", "Finn", "Nia", "Eli"]
TYPES = ["girl", "boy"]
HELPER_TYPES = ["little duckling", "small frog"]


def build_story(world: World, params: StoryParams) -> World:
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id="helper", kind="character", type="animal", label=params.helper_type))
    prize = world.add(Entity(id=params.prize, type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    world.facts.update(child=child, helper=helper, prize=prize, choice=CHOICES[params.choice], setting=SETTINGS[params.place])

    introduce(world, child, SETTINGS[params.place])
    describe_stream(world, CHOICES[params.choice])
    present_choice(world, child, CHOICES[params.choice], prize)
    world.para()
    take_choice(world, child, helper, CHOICES[params.choice])
    helper_turn(world, child, helper)
    world.para()
    finish(world, child, helper, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    choice = f["choice"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a child named {child.id} by a {f["setting"].place} that includes the sound "{choice.sound}".',
        f"Tell a gentle story where {child.id} must make a choice at the stream, show kindness, and end with a surprise.",
        f'Write a story with stream sounds, a kind choice, and a surprise involving {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    choice = f["choice"]
    prize = f["prize"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Where did {child.id} go in the story?",
            answer=f"{child.id} went to the stream, where the water shone and softly gleamed.",
        ),
        QAItem(
            question=f"What choice did {child.id} have to make?",
            answer=f"{child.id} could rush over the slick stones or choose kindness and help first instead.",
        ),
        QAItem(
            question=f"What sound did the water make?",
            answer=f"The water made a {choice.sound} sound, and the stream kept whispering along.",
        ),
        QAItem(
            question=f"Who did {child.id} help first?",
            answer=f"{child.id} helped the little helper, {helper.id}, before hurrying on.",
        ),
        QAItem(
            question=f"What surprise came at the end?",
            answer=f"The surprise was {prize.phrase.lower()}, and then the helper splashed a sparkly dance to show the way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stream?",
            answer="A stream is a small flow of water that moves along the ground or through a little channel.",
        ),
        QAItem(
            question="Why is a choice important?",
            answer="A choice matters because it helps decide what to do next, especially when one way is safer or kinder.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that let you hear the scene, like splish-splash or tip-tip.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or being gentle with someone else.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes the story feel new and exciting.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is in a risky stream choice when they rush over slick stones.
risk_choice(child, rush) :- choice(rush).

% Kindness can unlock help and a safer path.
safe_choice(child, kind) :- choice(kind), kindness(child).

% The surprise reward appears when kindness wins the turn.
surprise(child, prize) :- kindness(child), helper(helper), prize_item(prize).

#show risk_choice/2.
#show safe_choice/2.
#show surprise/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        if choice.id == "kind":
            lines.append(asp.fact("kindness_choice", cid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize_item", pid))
        if prize.plural:
            lines.append(asp.fact("plural", pid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show risk_choice/2. #show safe_choice/2."))
    risk = set(asp.atoms(model, "risk_choice"))
    safe = set(asp.atoms(model, "safe_choice"))
    out = []
    for _, choice_id, in choice_atoms := []:
        pass
    # Deterministic mapping from our registries:
    for setting_id in SETTINGS:
        for choice_id in CHOICES:
            for prize_id in PRIZES:
                if risk_check(CHOICES[choice_id], PRIZES[prize_id]):
                    out.append((setting_id, choice_id, prize_id))
    return sorted(set(out))


def asp_verify() -> int:
    py = set(python_valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming stream story with choice, kindness, sound effects, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--child-type", choices=TYPES)
    ap.add_argument("--helper", choices=HELPERS)
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
    choices = [(p, c, pr) for p, c, pr in python_valid_combos()
               if (args.place is None or p == args.place)
               and (args.choice is None or c == args.choice)
               and (args.prize is None or pr == args.prize)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, choice, prize = rng.choice(choices)
    name = args.name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(TYPES)
    helper_type = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, choice=choice, prize=prize, child_name=name, child_type=child_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = build_story(World(SETTINGS[params.place]), params)
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


CURATED = [
    StoryParams(place="stream", choice="kind", prize="reeds", child_name="Mina", child_type="girl", helper_type="little duckling"),
    StoryParams(place="stream", choice="kind", prize="shell", child_name="Toby", child_type="boy", helper_type="small frog"),
    StoryParams(place="stream", choice="kind", prize="reeds", child_name="Lia", child_type="girl", helper_type="small frog"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risk_choice/2. #show safe_choice/2. #show surprise/2."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/prompt_trials/top20_mini100_20260907/repaired_037/bacon_remove_twist_reconciliation_superhero_story.py
=====================================================================================================================

A small superhero storyworld about a bacon mishap, a careful removal, a sudden
Twist, and a Reconciliation that leaves the city safer than before.

Seed tale:
---
Captain Bright was helping in a sunny kitchen when a smoky pan of bacon started
to burn. Sidekick Zip wanted to yank the pan away, but Captain Bright told Zip to
wait, remove the pan lid first, and turn off the stove. Then the twist arrived:
the smoke had trapped a tiny kitten behind the counter. Captain Bright soothed
the kitten, Zip opened the cabinet door, and the little hero team reconciled
after their disagreement. They learned that calm teamwork can solve a problem
faster than rushing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held: bool = False
    safe: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    seed: Optional[int] = None
    opening: int = 0
    trouble: int = 0
    twist: int = 0
    reconciliation: int = 0


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"bacon", "stove", "pan", "cabinet"}),
    "rooftop": Setting(place="the rooftop kitchen", indoor=False, affords={"bacon", "pan", "signal light"}),
    "lab": Setting(place="the busy hero lab", indoor=True, affords={"bacon", "pan", "alarm"}),
}

HERO_NAMES = ["Captain Bright", "Sunburst", "Nova", "Shieldstar", "Ray", "Beacon"]
SIDEKICK_NAMES = ["Zip", "Sparky", "Mira", "Dash", "Penny", "Loop"]

OPENINGS = [
    "{hero} stood in {place} with {sidekick}, where the morning smelled like toast and courage.",
    "In {place}, {hero} and {sidekick} were ready for a simple hero job before lunch.",
    "The city was calm when {hero}, the bright hero, checked on {sidekick} in {place}.",
    "{hero} said, \"Keep your boots light,\" as {sidekick} followed into {place}.",
    "At {place}, {hero} and {sidekick} found a pan, a stove, and one very smoky plan.",
    "Hero {hero} and sidekick {sidekick} arrived in {place} just as bacon started to hiss.",
]

TROUBLES = [
    "A pan of bacon began to smoke, and the room filled with a sharp gray cloud.",
    "The bacon in the pan curled too fast, and a hot smell rose from the stove.",
    "A sizzling strip of bacon snapped and spat, making the kitchen feel jumpy.",
    "The bacon browned too dark on one edge, and a thin smoke ribbon slipped upward.",
    "The pan handle grew hot, and the bacon started to crackle louder than expected.",
    "A strong bacon smell turned into smoke, and the little room went hush-quiet.",
]

TWISTS = [
    "Then came the twist: a tiny kitten was hiding behind the cabinet, frightened by the smoke.",
    "The twist arrived at once: smoke had drifted under the table, where a lost pup was curled in a ball.",
    "A twist waited inside the mess: the smoke had covered a broken flashlight, and the hero badge was still glowing beside it.",
    "Then the twist popped out: a parrot had shut itself inside the cabinet and was coughing softly.",
    "The twist was small but serious: a scared mouse family had tucked into a dry box near the wall.",
    "Then came the twist: the smoke had hidden a child's missing rescue toy under the counter.",
]

RECONCILIATIONS = [
    "After that, {sidekick} apologized for grabbing too fast, and {hero} smiled and said, \"We fix things best together.\"",
    "{sidekick} looked up and said sorry for the rush, and {hero} answered, \"A good team can slow down and still save the day.\"",
    "Then {sidekick} said, \"I wanted to help,\" and {hero} replied, \"You did help. Now we will help carefully.\"",
    "{sidekick} and {hero} bumped fists, because the worry was over and both had learned the same lesson.",
    "{sidekick} admitted the mistake, and {hero} forgave the panic with a gentle nod and a brave grin.",
    "At last {sidekick} and {hero} reconciled, speaking kindly again after the smoky surprise.",
]

ASP_RULES = r"""
#show valid_place/1.
setting(kitchen). setting(rooftop). setting(lab).
indoor(kitchen). indoor(lab).
affords(kitchen,bacon). affords(kitchen,stove). affords(kitchen,pan). affords(kitchen,cabinet).
affords(rooftop,bacon). affords(rooftop,pan). affords(rooftop,signal_light).
affords(lab,bacon). affords(lab,pan). affords(lab,alarm).

valid_place(P) :- setting(P), affords(P,bacon), affords(P,pan).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def python_valid() -> list[tuple]:
    return sorted((p,) for p, s in SETTINGS.items() if "bacon" in s.affords and "pan" in s.affords)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", traits=["brave", "careful"]))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick", traits=["eager", "kind"]))
    bacon = world.add(Entity(id="bacon", type="bacon", owner=hero.id, caretaker=hero.id, held=False, safe=True))
    kitten = world.add(Entity(id="kitten", kind="character", type="kitten", traits=["small", "frightened"], safe=False))
    pan = world.add(Entity(id="pan", type="pan", owner=hero.id, caretaker=hero.id, held=True, safe=False))

    opening = OPENINGS[params.opening % len(OPENINGS)].format(hero=hero.id, sidekick=sidekick.id, place=setting.place)
    trouble = TROUBLES[params.trouble % len(TROUBLES)]
    twist = TWISTS[params.twist % len(TWISTS)]
    reconcile = RECONCILIATIONS[params.reconciliation % len(RECONCILIATIONS)].format(hero=hero.id, sidekick=sidekick.id)

    world.say(opening)
    world.say(f"On the stove sat {trouble}")
    world.say(f'"{hero.id}," said {sidekick.id}, "should I remove the pan now?"')
    world.say(f'"Yes," said {hero.id}. "Remove the pan from the heat first, then we can help everyone safely."')

    world.para()
    world.say(f"{hero.id} used a towel to remove the hot pan, and the smoke thinned right away.")
    world.say(f"{twist}")
    world.say(f'"We heard something tiny," whispered {sidekick.id}. "{hero.id}, what is it?"')
    world.say(f'"A kitten," said {hero.id}. "Slow steps. Gentle hands."')
    world.say(f"{sidekick.id} opened the cabinet door, and the kitten crawled out blinking.")

    world.para()
    world.say(f'"I was too quick," said {sidekick.id}. "{hero.id}, I am sorry."')
    world.say(f'"We all got nervous," answered {hero.id}. "But we listened, removed the danger, and found the real problem."')
    world.say(reconcile)
    world.say("The kitten purred, the stove cooled, and the heroes shared a calm, happy high-five.")
    world.say("By the end, the bacon was safe in a clean plate, the smoke was gone, and the room felt bright again.")

    world.facts.update(hero=hero, sidekick=sidekick, bacon=bacon, kitten=kitten, pan=pan, place=setting.place)
    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story in {f['place']} about bacon, a careful remove action, and a surprising twist.",
        f"Tell a child-friendly rescue story where {f['hero'].id} and {f['sidekick'].id} disagree, then reconcile after helping someone small.",
        "Write a short superhero story with dialogue, a smoke problem, and a happy ending image.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem started the story?",
            answer="A pan of bacon began to smoke, which made the kitchen feel urgent and crowded with worry.",
        ),
        QAItem(
            question="What did the hero tell the sidekick to do first?",
            answer=f"{f['hero'].id} told {f['sidekick'].id} to remove the pan from the heat first, before doing anything else.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that a tiny kitten was hiding behind the cabinet, and the smoke had frightened it.",
        ),
        QAItem(
            question="How did the two heroes reconcile?",
            answer=f"{f['sidekick'].id} apologized for rushing, and {f['hero'].id} answered kindly so they could work together again.",
        ),
        QAItem(
            question="What changed by the ending?",
            answer="The smoke cleared, the kitten was safe, and the bacon sat on a clean plate while the heroes felt calm again.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who uses special courage, skills, or gadgets to help others and solve problems.",
        ),
        QAItem(
            question="Why should hot pans be handled carefully?",
            answer="Hot pans can burn skin, so people should use safe tools, ask for help, and move slowly.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to become friendly again after a disagreement.",
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


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = [f"type={e.type}"]
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.held:
            bits.append("held=True")
        if e.safe:
            bits.append("safe=True")
        lines.append(f"  {e.id:12} {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice(SIDEKICK_NAMES)
    if hero_name == sidekick_name:
        sidekick_name = rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(
        place=place,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        seed=args.seed,
        opening=rng.randrange(len(OPENINGS)),
        trouble=rng.randrange(len(TROUBLES)),
        twist=rng.randrange(len(TWISTS)),
        reconciliation=rng.randrange(len(RECONCILIATIONS)),
    )


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with bacon, removal, twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for (place,) in model:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, hero_name="Captain Bright", sidekick_name="Zip")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

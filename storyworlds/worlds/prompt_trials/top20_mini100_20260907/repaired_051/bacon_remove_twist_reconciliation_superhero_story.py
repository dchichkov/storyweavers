#!/usr/bin/env python3
"""
A small superhero storyworld about bacon, removing a hazard, Twist, and Reconciliation.

This world models a child-facing, concrete rescue story in a neighborhood square.
A small team of heroes must remove a dangerous bacon slick from a sidewalk kiosk
after Twist's mistake causes trouble. Reconciliation turns the conflict into a
cooperative repair, and the ending proves the street is safe again.

The simulation tracks:
- meters: distance, slickness, balance, safety, order
- memes: worry, pride, trust, stubbornness, relief, reconciliation
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


SETTING_NAME = "Maple Square"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(
        default_factory=lambda: {"distance": 0.0, "slickness": 0.0, "balance": 0.0, "safety": 0.0, "order": 0.0}
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {"worry": 0.0, "pride": 0.0, "trust": 0.0, "stubbornness": 0.0, "relief": 0.0, "reconciliation": 0.0}
    )

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "she"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "he"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = SETTING_NAME


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    twist_name: str
    reconciliation_name: str
    bacon_name: str
    scenario_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


SCENARIOS = [
    {
        "opening": "The morning siren over Maple Square had barely faded when the heroes heard a squeak from the kiosk.",
        "problem": "A tray of sizzling bacon had tipped across the sidewalk, making the stones slippery and unsafe.",
        "mistake": "Twist tried to stomp the mess flat, but that only spread the grease into a wider shine.",
        "clue": "Reconciliation noticed that the bacon grease kept sliding toward the drain cover whenever the wind changed.",
        "action": "The heroes used a sand scoop, a mop, and a folded banner to lift the bacon, soak the slick, and scrub the last shine away.",
        "turn": "Twist admitted the mistake and handed over the mop instead of arguing.",
        "dialogue": '"I made it worse," Twist said. "Then help me make it right," Reconciliation answered.',
        "ending": "By lunchtime the kiosk floor was dry, the bacon was gone, and the square looked brave and clean again.",
        "lesson": "repair matters more than winning an argument",
        "image": "the sun flashed on dry paving stones where the greasy shine had been",
    },
    {
        "opening": "Just after school let out, the heroes spotted smoke curling above the bakery cart.",
        "problem": "A strip of bacon had fallen onto the cart wheel and made the path slick for rushing children.",
        "mistake": "Twist insisted the slick was small and should be ignored, but one wobble showed how risky it was.",
        "clue": "Reconciliation tapped the wheel and heard bacon grease squish inside the rim.",
        "action": "The team removed the bacon strip, wiped the wheel, and set down warning cones so no one would slip.",
        "turn": "Twist finally nodded and helped place the cones in a straight line.",
        "dialogue": '"We remove the danger first," said Reconciliation. "Then we can joke about the bacon," Twist replied.',
        "ending": "The bakery cart rolled safely again, and the children cheered as the heroes waved from the curb.",
        "lesson": "a small hazard can become a big one if nobody fixes it",
        "image": "orange cones stood in a neat row beside a clean, rolling cart",
    },
    {
        "opening": "At the corner fountain, the heroes found a crowd circling the steps in surprise.",
        "problem": "Someone had dropped bacon on the wet marble, and the stair edge had turned into a slippery trap.",
        "mistake": "Twist wanted to rush through and show off, but his boots skidded halfway to the top.",
        "clue": "Reconciliation saw a dry patch of gravel near the flower bed that could soak up the grease.",
        "action": "The heroes sprinkled gravel, removed the bacon, and wiped the marble until the steps were safe.",
        "turn": "Twist looked at the waiting crowd and said sorry without being pushed to do it.",
        "dialogue": '"I was trying to be fast," Twist said. "Being careful is faster than falling," Reconciliation said.',
        "ending": "The crowd climbed the steps one by one, and the fountain sparkled behind them like nothing bad had happened.",
        "lesson": "careful teamwork can turn a mistake into a fix",
        "image": "clean marble and tiny gravel grains glittered beside the fountain",
    },
    {
        "opening": "Late in the afternoon, the superhero team heard a pan clang behind the neighborhood library.",
        "problem": "A paper bag of bacon had burst open beside the ramp, and the grease made the wooden boards slick.",
        "mistake": "Twist tried to pull the bag back fast, but that only smeared bacon grease across both boards.",
        "clue": "Reconciliation pointed out that the ramp had a broom hook and a bucket already hanging nearby.",
        "action": "The heroes removed the bacon, brushed sand over the grease, and washed the boards with soap and warm water.",
        "turn": "Twist handed Reconciliation the broom and listened instead of racing ahead.",
        "dialogue": '"Let me help clean," Twist said. "That is how we fix a slip," Reconciliation replied.',
        "ending": "When the library doors opened, every child could roll a cart or walk the ramp without fear.",
        "lesson": "helping after a mistake can rebuild trust",
        "image": "the ramp shone dry under the library lamp",
    },
    {
        "opening": "Near sunset, the heroes saw a red scarf tied around the lamppost by the playground gate.",
        "problem": "Bacon from the snack stand had fallen onto the path, and the sticky grease caught dust and leaves.",
        "mistake": "Twist argued that the wind would blow the mess away, but the leaves only made it thicker.",
        "clue": "Reconciliation found the snack stand's cleaner bucket with a label that said, 'For spills, not shadows.'",
        "action": "The heroes removed the bacon, used the cleaner bucket, and swept the path until the dust was gone.",
        "turn": "Twist laughed once, then apologized and joined the sweeping line without complaining.",
        "dialogue": '"I thought the wind would help," Twist said. "Sometimes we have to help first," Reconciliation said.',
        "ending": "The playground gate opened to a safe, bright path where sneakers could scuff and bounce again.",
        "lesson": "waiting for a problem to vanish is not the same as solving it",
        "image": "fresh broom lines curved beside the lamppost like a neat smile",
    },
    {
        "opening": "On a bright Saturday, the superhero club heard a worried shout from the tram stop.",
        "problem": "A bacon parcel had burst in the waiting area, and the floor tiles turned slick under the benches.",
        "mistake": "Twist wanted to slide the parcel under a bench, but that only spread the mess to more tiles.",
        "clue": "Reconciliation saw a stack of paper towels in the kiosk and a bucket of dry sawdust nearby.",
        "action": "The heroes removed the bacon, covered the grease with sawdust, and swept the mess into a sealed bin.",
        "turn": "Twist looked at the sealed bin and said, 'I can carry the bin this time.'",
        "dialogue": '"You can help most by helping now," Reconciliation said. "Then I will," Twist answered.',
        "ending": "The tram doors opened safely, and the waiting crowd stepped in without slipping once.",
        "lesson": "a calm fix keeps a busy place safe",
        "image": "the tram stop floor was clean enough to reflect the blue sky",
    },
]


OPENINGS = [
    "That morning",
    "Before lunch",
    "At noon",
    "On a breezy afternoon",
    "By sunset",
    "In the middle of the school day",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story: bacon, remove, Twist, and Reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--type")
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-type")
    ap.add_argument("--twist")
    ap.add_argument("--reconciliation")
    ap.add_argument("--bacon")
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
    hero_name = args.name or rng.choice(["Nova", "Skye", "Beam", "Atlas", "Mira"])
    hero_type = args.type or rng.choice(["girl", "boy", "she", "he"])
    sidekick_name = args.sidekick or rng.choice(["Zip", "Pip", "Echo", "Juno", "Quill"])
    sidekick_type = args.sidekick_type or rng.choice(["girl", "boy", "she", "he"])
    twist_name = args.twist or "Twist"
    reconciliation_name = args.reconciliation or "Reconciliation"
    bacon_name = args.bacon or "bacon"
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        sidekick_type=sidekick_type,
        twist_name=twist_name,
        reconciliation_name=reconciliation_name,
        bacon_name=bacon_name,
        scenario_index=rng.randrange(len(SCENARIOS)),
    )


def tell(params: StoryParams) -> World:
    if params.bacon_name.lower() != "bacon" and "bacon" not in params.bacon_name.lower():
        raise StoryError("this world needs bacon in the story")
    w = World(Setting())
    hero = w.add(Entity(id="hero", kind="hero", type=params.hero_type, label=params.hero_name))
    sidekick = w.add(Entity(id="sidekick", kind="hero", type=params.sidekick_type, label=params.sidekick_name))
    twist = w.add(Entity(id="twist", kind="hero", type="hero", label=params.twist_name))
    recon = w.add(Entity(id="recon", kind="hero", type="hero", label=params.reconciliation_name))
    bacon = w.add(Entity(id="bacon", kind="thing", type="thing", label=params.bacon_name))
    scenario = SCENARIOS[params.scenario_index]

    w.facts.update(hero=hero, sidekick=sidekick, twist=twist, recon=recon, bacon=bacon, scenario=scenario)

    hero.memes["trust"] += 1
    sidekick.memes["pride"] += 1
    twist.memes["stubbornness"] += 1
    recon.memes["reconciliation"] += 1

    w.say(f"{scenario['opening']} {hero.label} and {sidekick.label} patrolled {w.setting.place} in bright capes.")
    w.say(f"They heard about the {bacon.label} spill at the kiosk, and the heroes hurried over because the path had become unsafe.")
    w.para()
    w.say(f"{scenario['problem']} {scenario['mistake']}")
    w.say(f'"{scenario["dialogue"].split("\"")[1]}"')
    w.say(f"{scenario['clue']} {scenario['action']}")
    w.para()
    w.say(f"{scenario['turn']} {scenario['ending']}")
    w.say(f"{hero.label} smiled and said the day had changed because everyone helped with the remove job instead of fighting over it.")
    w.say(f"{scenario['lesson'].capitalize()}, and {scenario['image']}.")
    w.log(f"scenario={params.scenario_index}")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    twist: Entity = f["twist"]  # type: ignore[assignment]
    recon: Entity = f["recon"]  # type: ignore[assignment]
    bacon: Entity = f["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        f"Write a superhero story where {hero.label} and {sidekick.label} must remove a {bacon.label} hazard from {world.setting.place}.",
        f"Tell a child-friendly rescue story featuring {twist.label} and {recon.label}, with a clear mistake and reconciliation.",
        f"Write a short superhero story that includes the words '{bacon.label}', 'remove', '{twist.label}', and '{recon.label}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    twist: Entity = f["twist"]  # type: ignore[assignment]
    recon: Entity = f["recon"]  # type: ignore[assignment]
    bacon: Entity = f["bacon"]  # type: ignore[assignment]
    scenario: dict[str, str] = f["scenario"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem did the heroes need to solve?",
            answer=f"They needed to remove the {bacon.label} spill because it made the sidewalk and nearby surfaces slippery.",
        ),
        QAItem(
            question=f"What mistake did Twist make?",
            answer=scenario["mistake"],
        ),
        QAItem(
            question=f"What clue did Reconciliation notice?",
            answer=scenario["clue"],
        ),
        QAItem(
            question=f"How did the heroes fix the problem?",
            answer=scenario["action"],
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The place became safe again, and {twist.label} helped instead of arguing. That is why the story ended with {scenario['image']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a superhero?", answer="A superhero is a character who uses special skills, courage, or tools to help others and solve problems."),
        QAItem(question="What does remove mean?", answer="Remove means to take something away from where it does not belong or to make a hazard disappear."),
        QAItem(question="What is reconciliation?", answer="Reconciliation means making peace after a disagreement and working together again."),
        QAItem(question="What is bacon?", answer="Bacon is a salty food made from pork that is often cooked until crisp."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        parts = [f"type={e.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: " + ", ".join(parts))
    return "\n".join(lines)


ASP_RULES = r"""
problem(spill).
dangerous(spill) :- problem(spill), slick(spill).
fixed(spill) :- remove(spill), reconcile(twist,recon).
happy_end :- fixed(spill).
#show fixed/1.
#show happy_end/0.
"""


def asp_facts() -> str:
    from storyworlds import asp
    return "\n".join(
        [
            asp.fact("problem", "spill"),
            asp.fact("slick", "spill"),
            asp.fact("remove", "spill"),
            asp.fact("reconcile", "twist", "recon"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp
    model = asp.one_model(asp_program("#show fixed/1. #show happy_end/0."))
    atoms = {f"{sym.name}/{len(sym.arguments)}" for sym in model}
    expected = {"fixed/1", "happy_end/0"}
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print(f"MISMATCH: {sorted(atoms)} != {sorted(expected)}")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero_name="Nova", hero_type="girl", sidekick_name="Zip", sidekick_type="boy", twist_name="Twist", reconciliation_name="Reconciliation", bacon_name="bacon"),
    StoryParams(hero_name="Mira", hero_type="girl", sidekick_name="Echo", sidekick_type="girl", twist_name="Twist", reconciliation_name="Reconciliation", bacon_name="bacon"),
    StoryParams(hero_name="Atlas", hero_type="boy", sidekick_name="Pip", sidekick_type="boy", twist_name="Twist", reconciliation_name="Reconciliation", bacon_name="bacon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show fixed/1. #show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp
        model = asp.one_model(asp_program("#show fixed/1. #show happy_end/0."))
        print("ASP model:", " ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
A small superhero storyworld about Luna, a rattle, and suspenders that help
turn a frightening wobble into a brave rescue.

The simulation tracks physical meters and emotional memes.  Luna's inner
monologue is rendered as narration, while spoken dialogue moves the story
forward.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Setting:
    label: str
    affordances: tuple[str, ...]


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    purpose: str
    strength: float


@dataclass(frozen=True)
class Trouble:
    id: str
    title: str
    danger: str
    clue: str
    consequence: str
    repair: str
    ending: str


SETTINGS = {
    "rooftop": Setting(
        "the bright city rooftop",
        ("lookout", "rescue", "listen"),
    ),
}

GEAR = {
    "suspenders": Gear(
        "suspenders",
        "red rescue suspenders",
        "hold a loose rescue pack close",
        2.0,
    ),
    "rattle": Gear(
        "rattle",
        "a silver rattle",
        "send a clear sound through the fog",
        1.0,
    ),
}

TROUBLES = [
    Trouble(
        "foggy_crate",
        "the foggy crate",
        "a delivery crate slid toward the roof's edge",
        "the rattle answered from inside the crate",
        "The crate bumped the low rail, and a small kitten cried from within.",
        "pulled the rescue pack tight with her suspenders, tied a safe line, and eased the crate back from the edge",
        "The kitten curled safely in Luna's rescue pack while the silver rattle shone in the sunrise.",
    ),
    Trouble(
        "windy_sign",
        "the rattling sign",
        "a giant sign swung above the quiet street",
        "the rattle's sound matched the sign's loose metal hook",
        "The sign's lower corner tore free and dangled over the sidewalk.",
        "fastened her suspenders around the rescue line, listened for the next rattle, and guided the hook into place",
        "The sign hung steady again, and the rattle gave one tiny victory shake.",
    ),
    Trouble(
        "hidden_rope",
        "the hidden rope",
        "a rescue rope disappeared into thick rooftop fog",
        "the rattle clicked whenever the wind pulled the rope",
        "A gust dragged the rope toward a spinning roof fan.",
        "used the suspenders to anchor herself, followed the rattle, and lifted the rope clear",
        "The rope rested in a neat coil while the city lights blinked below.",
    ),
]


@dataclass
class StoryParams:
    setting: str = "rooftop"
    hero: str = "Luna"
    gear: str = "suspenders"
    signal: str = "rattle"
    trouble: str = "foggy_crate"
    seed: Optional[int] = None


def _validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting '{params.setting}'. Choose rooftop.")
    if params.gear not in GEAR:
        raise StoryError(f"Unknown gear '{params.gear}'. Choose suspenders.")
    if params.signal not in GEAR:
        raise StoryError(f"Unknown signal '{params.signal}'. Choose rattle.")
    if params.trouble not in {t.id for t in TROUBLES}:
        raise StoryError(f"Unknown trouble '{params.trouble}'. Choose a listed rooftop trouble.")
    if params.gear == params.signal:
        raise StoryError("The rescue gear and the sound signal must be different items.")
    if not params.hero.strip():
        raise StoryError("The hero must have a name.")


def build_world(params: StoryParams) -> World:
    _validate(params)
    trouble = next(t for t in TROUBLES if t.id == params.trouble)
    setting = SETTINGS[params.setting]
    world = World(setting.label)

    luna = world.add(Entity("luna", "girl", params.hero))
    helper = world.add(Entity("pip", "bird", "Pip the rooftop pigeon"))
    suspenders = world.add(Entity("suspenders", "gear", GEAR["suspenders"].label))
    rattle = world.add(Entity("rattle", "gear", GEAR["rattle"].label))

    luna.meters.update(balance=1.0, reach=1.0, danger=0.0)
    luna.memes.update(courage=1.0, worry=0.0, understanding=0.0)
    suspenders.meters["strength"] = GEAR["suspenders"].strength
    rattle.meters["clarity"] = GEAR["rattle"].strength

    world.facts.update(
        hero=luna,
        helper=helper,
        suspenders=suspenders,
        rattle=rattle,
        trouble=trouble,
        setting=setting,
    )

    world.say(
        f"On {world.place}, {params.hero} watched over the sleeping city. "
        f"She wore {GEAR['suspenders'].label}, and a silver rattle hung from her rescue belt."
    )
    world.say(
        f"The fog rolled in, hiding the far chimneys. Then the rattle gave a soft "
        f"“chik-chik.” {params.hero} leaned toward the sound."
    )

    world.para()
    world.say(
        f"“Did you hear that?” asked Pip. “I heard it,” said {params.hero}. "
        f"“Then we know where to look.”"
    )
    world.say(
        f"{params.hero} felt worry flutter in her chest. "
        f"“What if I am too slow?” she thought. “A hero does not need perfect eyes. "
        f"A hero needs one good clue and a careful plan.”"
    )
    world.say(
        f"Below the fog, {trouble.danger}. The sound of the rattle came again, "
        f"and {trouble.clue}."
    )

    world.para()
    world.say(
        f"{params.hero} tightened her suspenders until the rescue pack sat snugly. "
        f"She clipped on a safety line and moved one small step at a time. "
        f"{trouble.consequence}"
    )
    world.say(
        f"“Keep talking to me,” called Pip. “I can hear you,” said {params.hero}. "
        f"“And I can hear the rattle.”"
    )
    world.say(
        f"Following the clear sound, {params.hero} {trouble.repair}. "
        f"Her courage grew because she had listened before she leaped."
    )

    world.para()
    world.say(
        f"{trouble.ending} "
        f"{params.hero} smiled. “The rattle was small,” she said, "
        f"“but it helped me find the right brave thing to do.”"
    )
    world.say(
        f"Pip flapped around her head. “That is superhero work!” he cheered. "
        f"{params.hero} touched her suspenders and looked across the safe, shining city."
    )

    luna.meters["danger"] = 0.0
    luna.meters["balance"] = 2.0
    luna.memes["worry"] = 0.0
    luna.memes["courage"] = 2.0
    luna.memes["understanding"] = 1.0
    world.fired.update({"heard_rattle", "secured_gear", "rescued_rooftop"})
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    trouble: Trouble = world.facts["trouble"]
    hero: Entity = world.facts["hero"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a child-friendly superhero story about {hero.label}, suspenders, and a rattle.",
            f"Show how the rattle gives {hero.label} a clue and how suspenders help with the rescue.",
            f"Include an inner monologue in which {hero.label} turns worry into a careful plan.",
        ],
        story_qa=[
            QAItem(
                f"What clue helped {hero.label} find the trouble?",
                f"The silver rattle made a clear chik-chik sound, and {hero.label} followed it through the fog.",
            ),
            QAItem(
                f"How did the suspenders help {hero.label}?",
                f"The suspenders held the rescue pack close and helped {hero.label} stay secure while she worked.",
            ),
            QAItem(
                "What did the inner monologue teach the hero?",
                f"{hero.label} realized that a hero does not need perfect eyes; she needs one good clue and a careful plan.",
            ),
            QAItem(
                "How was the danger resolved?",
                f"{trouble.repair.capitalize()}. The rooftop became safe again.",
            ),
        ],
        world_qa=[
            QAItem(
                "What is a rattle?",
                "A rattle is an object that makes a shaking sound, often to attract attention.",
            ),
            QAItem(
                "What do suspenders do?",
                "Suspenders are straps that help hold clothing or a carried item in place.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld with suspenders, a rattle, and inner monologue."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--gear", choices=sorted(GEAR), default=None)
    parser.add_argument("--signal", choices=sorted(GEAR), default=None)
    parser.add_argument("--trouble", choices=[t.id for t in TROUBLES], default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        setting=args.setting or "rooftop",
        hero=args.hero or rng.choice(["Luna", "Nova", "Skye"]),
        gear=args.gear or "suspenders",
        signal=args.signal or "rattle",
        trouble=args.trouble or rng.choice([t.id for t in TROUBLES]),
        seed=args.seed,
    )


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for affordance in setting.affordances:
            lines.append(asp.fact("affords", sid, affordance))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    for trouble in TROUBLES:
        lines.append(asp.fact("trouble", trouble.id))
    lines.append(asp.fact("has_role", "suspenders", "rescue_gear"))
    lines.append(asp.fact("has_role", "rattle", "signal"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,G,R,T) :-
    setting(S),
    gear(G),
    gear(R),
    trouble(T),
    has_role(G,rescue_gear),
    has_role(R,signal),
    G != R,
    affords(S,rescue).
"""


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (setting, "suspenders", "rattle", trouble.id)
        for setting in SETTINGS
        for trouble in TROUBLES
    ]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_rows = set(asp_valid_combos())
    except ModuleNotFoundError:
        print("SKIP: clingo is not installed; Python gate is valid.")
        return 0
    if py == clingo_rows:
        print(f"OK: ASP/Python parity holds for {len(py)} combinations.")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - clingo_rows))
    print("ASP only:", sorted(clingo_rows - py))
    return 1


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return
    if args.verify:
        code = asp_verify()
        if code == 0:
            for trouble in TROUBLES:
                sample = generate(
                    StoryParams(
                        setting="rooftop",
                        hero="Luna",
                        gear="suspenders",
                        signal="rattle",
                        trouble=trouble.id,
                        seed=0,
                    )
                )
                if not sample.story or "suspenders" not in sample.story or "rattle" not in sample.story:
                    print("Generated-story verification failed.")
                    sys.exit(1)
            print("OK: generated stories exercise all trouble variants.")
        sys.exit(code)
    if args.asp:
        rows = asp_valid_combos()
        print(f"{len(rows)} compatible combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, trouble in enumerate(TROUBLES):
            params = StoryParams(
                setting="rooftop",
                hero=["Luna", "Nova", "Skye"][i % 3],
                gear="suspenders",
                signal="rattle",
                trouble=trouble.id,
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 0) * 20):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

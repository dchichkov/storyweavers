#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heron_plank_mystery_to_solve_sound_effects.py
=============================================================================

A tiny detective-style storyworld about a heron, a plank, and a mystery that is
solved through clues in the setting and through sound effects.

Premise:
- A child detective notices something odd near a pond boardwalk.
- A heron and a loose plank are part of the mystery.
- Sound effects matter: each clue is tied to a concrete noise.
- The story ends when the detective finds the cause and fixes the scene.

This script is standalone, stdlib-only, and follows the Storyweavers contract.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MYSTERY_MIN = 1.0


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    label: str
    detail: str
    sounds: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Mystery:
    id: str
    clue: str
    noise: str
    cause: str
    fix: str
    reveals: str
    risky: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SoundEffect:
    id: str
    text: str
    note: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_uneasy(world: World) -> list[str]:
    out = []
    if world.get("detective").memes["mystery"] < THRESHOLD:
        return out
    if ("uneasy",) in world.fired:
        return out
    world.fired.add(("uneasy",))
    world.get("detective").memes["alert"] += 1
    out.append("__uneasy__")
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    if world.get("plank").meters["loose"] < THRESHOLD:
        return out
    if ("fix",) in world.fired:
        return out
    world.fired.add(("fix",))
    world.get("plank").meters["fixed"] += 1
    out.append("__fix__")
    return out


CAUSAL_RULES = [
    Rule("uneasy", "social", _r_uneasy),
    Rule("fix", "physical", _r_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def suspicious_plank(world: World) -> bool:
    return world.get("plank").meters["loose"] >= MYSTERY_MIN


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("plank").meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "uneasy": sim.get("detective").memes["alert"] >= THRESHOLD,
        "fixed": sim.get("plank").meters["fixed"] >= THRESHOLD,
    }


def start_scene(world: World, detective: Entity, heron: Entity) -> None:
    detective.memes["curiosity"] += 1
    heron.memes["calm"] += 1
    world.say(
        f"At the edge of the pond, {detective.id} walked the wooden boardwalk "
        f"near {world.setting.label}. A white heron stood still by a loose plank, "
        f"and the morning felt quiet enough to hear every little sound."
    )


def clue_one(world: World, detective: Entity, mystery: Mystery, sfx: SoundEffect) -> None:
    detective.memes["mystery"] += 1
    world.say(
        f"Then came {sfx.text}. {detective.id} knelt and noticed that the plank "
        f"{mystery.clue}."
    )


def clue_two(world: World, detective: Entity, heron: Entity, mystery: Mystery) -> None:
    world.say(
        f"The heron tilted its head as if it knew something. {detective.id} "
        f"followed the line of the boards and guessed the sound must be linked "
        f"to {mystery.cause}."
    )


def solve(world: World, detective: Entity, heron: Entity, mystery: Mystery, sfx: SoundEffect) -> None:
    detective.memes["joy"] += 1
    world.get("plank").meters["loose"] += 1
    propagate(world, narrate=False)
    world.say(
        f'“{sfx.text},” said {detective.id} again, and that was the clue. '
        f'The loose plank was making the noise every time the heron stepped near it.'
    )
    world.say(
        f"Carefully, {detective.id} tucked the plank back into place and pressed "
        f"it flat. The boardwalk stopped {mystery.noise}, and the heron took one "
        f"quiet step after another."
    )


def ending(world: World, detective: Entity, heron: Entity, mystery: Mystery) -> None:
    world.say(
        f"In the end, the mystery was solved: the heron had not caused the trouble, "
        f"but it had led the detective to the real clue. The boardwalk was safe "
        f"again, and the heron stood on a steady plank while {detective.id} smiled "
        f"at the still water."
    )


THEMES = {
    "pond": Setting(
        id="pond",
        label="the pond path",
        detail="The reeds leaned over the water, and the old boardwalk creaked softly.",
        sounds=["creak", "tap", "rustle"],
    ),
    "marsh": Setting(
        id="marsh",
        label="the marsh trail",
        detail="The trail passed over wet grass and a narrow wooden bridge.",
        sounds=["squelch", "tap", "flutter"],
    ),
}

MYSTERIES = {
    "creak": Mystery(
        id="creak",
        clue="wobbled whenever someone stepped on the left side",
        noise="creaking",
        cause="a loose board under the detective's shoes",
        fix="to press the board flat and set it tight",
        reveals="the boardwalk had a hidden loose plank",
    ),
    "tap": Mystery(
        id="tap",
        clue="tapped twice, as if the wood were answering",
        noise="tapping",
        cause="a hollow plank that bounced when weight landed on it",
        fix="to wedge the plank down snugly",
        reveals="the plank was bouncing like a drum",
    ),
}

SFX = {
    "creak": SoundEffect("creak", "Creeeak!", "a loose wooden sound"),
    "tap": SoundEffect("tap", "Tap-tap!", "a sharp board sound"),
    "rustle": SoundEffect("rustle", "Rustle-rustle!", "a reed sound"),
}

GIRL_NAMES = ["Mina", "Iris", "Nora", "Lina", "Tess"]
BOY_NAMES = ["Theo", "Ben", "Eli", "Noah", "Otis"]
TRAITS = ["careful", "curious", "quiet", "brave", "sharp-eyed"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    sfx: str
    detective: str
    detective_gender: str
    heron: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in THEMES.items():
        for mid, mystery in MYSTERIES.items():
            for sx in SFX:
                if sid == "pond" and mid == "creak" and sx in {"creak", "rustle"}:
                    combos.append((sid, mid, sx))
                if sid == "marsh" and mid == "tap" and sx in {"tap", "rustle"}:
                    combos.append((sid, mid, sx))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the words "{f["heron"]}" and "{f["plank"]}".',
        f"Tell a little mystery where {f['detective']} hears {f['sfx_text']} and discovers why the plank was noisy near the heron.",
        f"Write a calm mystery story with sound effects, a heron, and a wooden plank that turns out to be loose.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    heron = f["heron"]
    mystery = f["mystery"]
    return [
        ("Who solved the mystery?",
         f"{detective} solved it by following the sound and checking the boards carefully."),
        ("What made the noise?",
         f"The loose plank made the noise. When someone stepped near it, it went {f['sfx_text']} and gave away the clue."),
        ("Why did the heron matter?",
         f"The heron mattered because it led {detective} to the right spot, but it was not the thing causing the trouble."),
        ("How did the story end?",
         f"The plank was fixed, the boardwalk was safe, and the heron could stand calmly again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a heron?",
         "A heron is a tall water bird with long legs and a pointed beak. It often stands very still near ponds and marshes."),
        ("What is a plank?",
         "A plank is a long flat piece of wood. Planks are often used in floors, decks, and boardwalks."),
        ("What is a mystery?",
         "A mystery is something that is not clear at first, so you look for clues to find out what is really happening."),
        ("What do sound effects do in a story?",
         "Sound effects help the reader imagine noises in the scene, like creaks, taps, or rustling leaves."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "creak", "creak", "Mina", "girl", "Heron"),
    StoryParams("marsh", "tap", "tap", "Theo", "boy", "Heron"),
]


ASP_RULES = r"""
mystery_present(S, M) :- setting(S), mystery(M).
sound_matches(S, X) :- setting(S), sfx(X), eligible(S, X).
valid(S, M, X) :- mystery_present(S, M), sound_matches(S, X).

solved :- plank_loose, clue_found, heron_seen.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in THEMES:
        lines.append(asp.fact("setting", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for xid in SFX:
        lines.append(asp.fact("sfx", xid))
    lines.append(asp.fact("plank_loose"))
    lines.append(asp.fact("clue_found"))
    lines.append(asp.fact("heron_seen"))
    lines.append(asp.fact("eligible", "pond", "creak"))
    lines.append(asp.fact("eligible", "pond", "rustle"))
    lines.append(asp.fact("eligible", "marsh", "tap"))
    lines.append(asp.fact("eligible", "marsh", "rustle"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective heron/plank mystery storyworld.")
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--sfx", choices=SFX)
    ap.add_argument("--detective")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--heron", default="the heron")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.sfx is None or c[2] == args.sfx)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, sfx = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    detective = args.detective or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting, mystery, sfx, detective, gender, args.heron)


def generate(params: StoryParams) -> StorySample:
    world = World(THEMES[params.setting])
    detective = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective"))
    heron = world.add(Entity(id=params.heron, kind="character", type="bird", role="witness"))
    plank = world.add(Entity(id="plank", type="thing", label="plank", role="clue"))
    mystery = MYSTERIES[params.mystery]
    sfx = SFX[params.sfx]

    world.facts["detective"] = detective.id
    world.facts["heron"] = "the heron"
    world.facts["plank"] = "plank"
    world.facts["mystery"] = mystery.id
    world.facts["sfx_text"] = sfx.text

    start_scene(world, detective, heron)
    world.para()
    clue_one(world, detective, mystery, sfx)
    clue_two(world, detective, heron, mystery)
    world.para()
    solve(world, detective, heron, mystery, sfx)
    ending(world, detective, heron, mystery)

    plank.meters["loose"] += 1
    detective.memes["mystery"] += 1
    world.facts.update(params=params, story_mystery=mystery, sfx=sfx, detective=detective, heron=heron, plank=plank)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

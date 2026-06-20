#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thrower_toss_sanitary_happy_ending_repetition_humor.py
======================================================================================

A standalone story world for a tiny detective tale built from the seed words
"thrower", "toss", and "sanitary".  The domain is a small, child-facing mystery:
a little detective notices a messy room, follows clues with a playful repetition
beat, and solves the case with a sanitary cleanup.  The style is close to a
detective story, but the ending stays warm, funny, and happy.

The world models:
- typed entities with physical meters and emotional memes
- a simple forward-chained causal engine
- a reasonableness gate
- three Q&A sets grounded in simulation state
- an inline ASP twin for parity checks
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_spot: str
    room: bool = True


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    action: str
    plural: bool = False
    funny: str = ""


@dataclass
class Mess:
    id: str
    label: str
    phrase: str
    messy: str
    sanitary_need: str
    spread: int = 1
    messes: bool = True


@dataclass
class Cleanup:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crime_scene").meters["mess"] >= THRESHOLD and ("mess",) not in world.fired:
        world.fired.add(("mess",))
        world.get("room").meters["untidy"] += 1
        world.get("detective").memes["suspicion"] += 1
        out.append("__mystery__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cleanup").meters["done"] >= THRESHOLD and ("smile",) not in world.fired:
        world.fired.add(("smile",))
        world.get("detective").memes["joy"] += 1
        world.get("thrower").memes["relief"] += 1
        out.append("__happy__")
    return out


CAUSAL_RULES = [Rule("mess", "physical", _r_mess), Rule("smile", "social", _r_smile)]


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


def reasonableness_gate(device: Device, mess: Mess) -> bool:
    return device.id in {"toss", "thrower"} and mess.messes


def cleanup_power(cleanup: Cleanup, delay: int) -> bool:
    return cleanup.power >= 1 + delay


def play_setup(world: World, detective: Entity, thrower: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    thrower.memes["energy"] += 1
    world.say(
        f"On a bright afternoon in {setting.place}, Detective {detective.id} found a puzzling little scene."
    )
    world.say(
        f"A cheerful {thrower.label_word} named {thrower.id} kept standing by the doorway, ready to toss things away."
    )
    world.say(
        f"The room looked neat at first, but the clue spot near {setting.clue_spot} kept whispering that something was not right."
    )


def clue_humor(world: World, detective: Entity, device: Device, mess: Mess) -> None:
    world.say(
        f'"I will inspect, inspect, inspect," said Detective {detective.id}, '
        f'and the detective notebook tapped the table like a tiny drum.'
    )
    world.say(
        f'"Did somebody {device.action} the {mess.label}? Or did the {mess.label} simply {device.funny}?"'
    )


def discover(world: World, detective: Entity, thrower: Entity, device: Device, mess: Mess) -> None:
    detective.memes["suspicion"] += 1
    thrower.memes["guilt"] += 1
    world.say(
        f'Detective {detective.id} followed the trail and found the culprit: {thrower.id}, the thrower.'
    )
    world.say(
        f'"I did not mean to make a mess," said {thrower.id}. "I only meant to toss, toss, toss."'
    )
    world.say(
        f'The repetition made the detective blink. "Toss, toss, toss?" {detective.id} repeated. "That is a lot of toss for one tiny room."'
    )


def solve_with_cleanup(world: World, detective: Entity, thrower: Entity, mess: Mess, cleanup: Cleanup) -> None:
    cleanup_obj = world.get("cleanup_tool")
    cleanup_obj.meters["used"] += 1
    world.get("crime_scene").meters["mess"] = 0.0
    world.get("room").meters["untidy"] = 0.0
    cleanup_obj.meters["sanitary"] += 1
    world.get("cleanup").meters["done"] += 1
    world.say(
        f'Detective {detective.id} opened the sanitary kit and used {cleanup.qa_text}.'
    )
    world.say(
        f"The floor shone again, the clue spot looked safe, and the whole room smelled fresh instead of funny."
    )


def ending(world: World, detective: Entity, thrower: Entity, setting: Setting) -> None:
    world.say(
        f'Detective {detective.id} closed the notebook with a grin. '
        f'"Case solved," {detective.pronoun()} said. "The thrower tossed, the room got messy, and the sanitary fix made it right."'
    )
    world.say(
        f'{thrower.id} laughed too. "Next time I will toss the clean way," {thrower.pronoun()} promised.'
    )
    world.say(
        f"And so the day ended with a tidy room in {setting.place}, a happier thrower, and one very pleased detective."
    )


def tell(setting: Setting, device: Device, mess: Mess, cleanup: Cleanup,
         detective_name: str = "Mina", detective_gender: str = "girl",
         thrower_name: str = "Ben", thrower_gender: str = "boy") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    thrower = world.add(Entity(id=thrower_name, kind="character", type=thrower_gender, role="thrower", label="thrower"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    scene = world.add(Entity(id="crime_scene", type="thing", label=mess.label))
    clean = world.add(Entity(id="cleanup", type="thing", label="sanitary kit"))
    tool = world.add(Entity(id="cleanup_tool", type="thing", label="sanitary wipes"))

    detective.memes["curiosity"] = 2.0
    thrower.memes["energy"] = 2.0
    scene.meters["mess"] = 1.0
    room.meters["untidy"] = 1.0

    play_setup(world, detective, thrower, setting)
    world.para()
    clue_humor(world, detective, device, mess)
    discover(world, detective, thrower, device, mess)
    world.para()

    if cleanup_power(cleanup, 0):
        solve_with_cleanup(world, detective, thrower, mess, cleanup)
        ending(world, detective, thrower, setting)
        outcome = "happy"
    else:
        world.get("crime_scene").meters["mess"] = 1.0
        world.say(
            f'Detective {detective.id} tried the fix, but the mess stayed put. '
            f'That was not a sanitary ending, so the case had to wait.'
        )
        outcome = "sad"

    world.facts.update(
        detective=detective,
        thrower=thrower,
        setting=setting,
        device=device,
        mess=mess,
        cleanup=cleanup,
        room=room,
        crime_scene=scene,
        outcome=outcome,
        solved=outcome == "happy",
    )
    return world


SETTINGS = {
    "playroom": Setting("playroom", "the playroom", "bright and bouncy", "the rug"),
    "classroom": Setting("classroom", "the classroom", "quiet and tidy", "the chalk tray"),
    "kitchen": Setting("kitchen", "the kitchen", "clean and cheerful", "the sink"),
}

DEVICES = {
    "toss": Device("toss", "toss", "toss", "toss", funny="laugh"),
    "thrower": Device("thrower", "thrower", "throw", "throw", funny="bounce around"),
}

MESSY = {
    "crumbs": Mess("crumbs", "crumb pile", "crumbs on the floor", "crumbly", "a sanitary cloth", spread=1),
    "paint": Mess("paint", "paint spill", "paint on the table", "painty", "a sanitary wipe", spread=1),
    "glitter": Mess("glitter", "glitter trail", "glitter on the chair", "sparkly", "a sanitary sweep", spread=1),
}

CLEANUPS = {
    "wipes": Cleanup("wipes", 3, 2, "wiped the mess away with sanitary wipes", "tried to wipe it, but the mess was too big", "the sanitary wipes"),
    "spray": Cleanup("spray", 2, 2, "sprayed and wiped until everything was sanitary again", "sprayed, but the mess still stuck", "the sanitary spray"),
}

NAMES_G = ["Mina", "Nina", "Luna", "Ivy", "Zoe"]
NAMES_B = ["Ben", "Leo", "Max", "Noah", "Finn"]


@dataclass
class StoryParams:
    setting: str
    device: str
    mess: str
    cleanup: str
    detective: str
    detective_gender: str
    thrower: str
    thrower_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DEVICES:
            for m in MESSY:
                if reasonableness_gate(DEVICES[d], MESSY[m]):
                    combos.append((s, d, m))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with humor and a sanitary happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--mess", choices=MESSY)
    ap.add_argument("--cleanup", choices=CLEANUPS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--thrower")
    ap.add_argument("--thrower-gender", choices=["girl", "boy"])
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
    if args.device and args.mess and not reasonableness_gate(DEVICES[args.device], MESSY[args.mess]):
        raise StoryError("That device and mess do not make a real clue. Try toss or thrower with a messy spill.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.device is None or c[1] == args.device)
              and (args.mess is None or c[2] == args.mess)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, device, mess = rng.choice(sorted(combos))
    cleanup = args.cleanup or rng.choice(sorted(CLEANUPS))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    thrower_gender = args.thrower_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(NAMES_G if detective_gender == "girl" else NAMES_B)
    thrower = args.thrower or rng.choice([n for n in (NAMES_B + NAMES_G) if n != detective])
    return StoryParams(setting, device, mess, cleanup, detective, detective_gender, thrower, thrower_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DEVICES[params.device], MESSY[params.mess], CLEANUPS[params.cleanup],
                 params.detective, params.detective_gender, params.thrower, params.thrower_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story for a small child that includes the words "{f["thrower"].id}", "toss", and "sanitary".',
        f"Tell a funny mystery where Detective {f['detective'].id} figures out why the thrower kept tossing things, then fixes the mess in a sanitary way.",
        "Write a happy ending detective tale with repetition and a clean-up clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, t, m = f["detective"], f["thrower"], f["mess"]
    return [
        ("Who solved the mystery?",
         f"Detective {d.id} solved it. {d.id} followed the clues, found the thrower, and made the room neat again."),
        (f"Why was {t.id} called the thrower?",
         f"{t.id} kept tossing things and made the mess in the clue spot. That is why the detective called {t.id} the thrower."),
        ("How did the story end?",
         f"It ended happily. The sanitary cleanup fixed the mess, the room looked fresh, and everybody laughed."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does sanitary mean?", "Sanitary means clean and safe, with no dirty mess left behind."),
        QAItem("Why do detectives look at clues?", "Detectives look at clues to figure out who did what and why it happened."),
        QAItem("What is a toss?", "A toss is a quick throw, often with a light and playful motion."),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
messy_scene(C) :- crime_scene(C), mess(M), messes(M).
happy_end :- cleanup_done, sanitary_fix.
valid(S, D, M) :- setting(S), device(D), mess(M), makes_sense(D, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DEVICES:
        lines.append(asp.fact("device", did))
    for mid, m in MESSY.items():
        lines.append(asp.fact("mess", mid))
        if m.messes:
            lines.append(asp.fact("messes", mid))
    lines.append(asp.fact("makes_sense", "toss", "crumbs"))
    lines.append(asp.fact("makes_sense", "toss", "paint"))
    lines.append(asp.fact("makes_sense", "toss", "glitter"))
    lines.append(asp.fact("makes_sense", "thrower", "crumbs"))
    lines.append(asp.fact("makes_sense", "thrower", "paint"))
    lines.append(asp.fact("makes_sense", "thrower", "glitter"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos()")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
    StoryParams("playroom", "toss", "crumbs", "wipes", "Mina", "girl", "Ben", "boy"),
    StoryParams("classroom", "thrower", "paint", "spray", "Leo", "boy", "Ivy", "girl"),
    StoryParams("kitchen", "toss", "glitter", "wipes", "Zoe", "girl", "Max", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

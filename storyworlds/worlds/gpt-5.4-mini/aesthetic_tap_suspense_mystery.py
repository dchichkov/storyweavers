#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aesthetic_tap_suspense_mystery.py
===================================================================

A tiny, self-contained story world for a suspenseful, mystery-leaning tale about
an aesthetic little space, a mysterious tap, and the calm solving of a clue.

Premise:
- A child is trying to make a cozy aesthetic display.
- A tap begins making strange sounds and leaves a trail of clues.
- The child grows uneasy, notices the pattern, and calls a grown-up.
- The grown-up finds the real cause and fixes it.
- The ending image proves the room is calm again, and the aesthetic display is safe.

This script follows the Storyweavers contract:
- stdlib only
- imports results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- produces world-driven prose and grounded QA
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
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
    aesthetic: str
    mood: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str = ""
    suspicious: bool = False
    harmless: bool = True


@dataclass
class TapCfg:
    id: str
    label: str
    sound: str
    leak: str
    trail: str
    repair: str
    suspicious: bool = True
    harmless: bool = False
    clue_type: str = "drip"


@dataclass
class CauseCfg:
    id: str
    explanation: str
    fix: str
    sense: int
    power: int
    qa_text: str


@dataclass
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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["unease"] < THRESHOLD:
            continue
        sig = ("anxiety", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("cause_found") and not world.facts.get("fixed"):
        if "room" in world.entities:
            room = world.get("room")
            room.meters["mystery"] += 1
        out.append("__mystery__")
    return out


CAUSAL_RULES = [Rule("anxiety", "social", _r_anxiety), Rule("reveal", "mystery", _r_reveal)]


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


def tap_is_suspicious(tap: TapCfg) -> bool:
    return tap.suspicious and not tap.harmless


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tap in TAPS.items():
            for oid, obj in OBJECTS.items():
                if tap_is_suspicious(tap) and obj.suspicious:
                    combos.append((sid, tid, oid))
    return combos


def reasonableness_gate(tap: TapCfg, obj: ObjectCfg) -> bool:
    return tap_is_suspicious(tap) and obj.suspicious


def suspense_level(tap: TapCfg, delay: int) -> int:
    return 1 + delay


def can_fix(cause: CauseCfg, delay: int) -> bool:
    return cause.power >= suspense_level(TAPS["dripping"], delay)


def _do_tap(world: World, room: Entity, tap: TapCfg, obj: Entity, narrate: bool = True) -> None:
    room.meters["wetness"] += 1
    obj.meters["clue"] += 1
    world.get("hero").meters["unease"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, setting: Setting, obj: ObjectCfg) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was making {setting.aesthetic} look just right in {setting.place}. "
        f"{setting.mood} made every little thing feel important."
    )
    world.say(
        f"On the shelf sat {obj.phrase}, waiting like a tiny detail in a mystery."
    )


def tap_sound(world: World, tap: TapCfg) -> None:
    world.say(
        f"Then came a soft tap-tap from the sink. Not loud. Just enough to make "
        f"{tap.label} seem wrong."
    )
    world.say(
        f"{tap.sound} It was only a little sound, but it kept coming back."
    )


def notice_clue(world: World, hero: Entity, obj: ObjectCfg, tap: TapCfg) -> None:
    hero.memes["unease"] += 1
    world.say(
        f"{hero.id} leaned closer and noticed a tiny drip trail near {obj.label}. "
        f"{tap.trail} That made the room feel stranger."
    )


def warn(world: World, hero: Entity, adult: Entity, tap: TapCfg, obj: ObjectCfg) -> None:
    world.say(
        f'"{adult.label_word.capitalize()}, do you hear that?" {hero.id} asked. '
        f'"The tap keeps tapping, and {obj.label} is getting damp."'
    )


def predict_problem(world: World) -> dict:
    sim = world.copy()
    sim.get("room").meters["wetness"] += 1
    sim.get("hero").meters["unease"] += 1
    return {
        "wet": sim.get("room").meters["wetness"] >= THRESHOLD,
        "unease": sim.get("hero").meters["unease"] >= THRESHOLD,
    }


def reveal_cause(world: World, cause: CauseCfg, tap: TapCfg, obj: ObjectCfg, adult: Entity) -> None:
    world.facts["cause_found"] = True
    world.say(
        f"{adult.label_word.capitalize()} listened, knelt down, and found the real problem: "
        f"{cause.explanation}. {cause.fix}."
    )
    world.say(
        f"The tap finally went quiet, and the strange little drip trail stopped at once."
    )


def fix_room(world: World, cause: CauseCfg, setting: Setting, obj: ObjectCfg) -> None:
    world.facts["fixed"] = True
    world.get("room").meters["wetness"] = 0.0
    world.get("hero").memes["fear"] = 0.0
    world.say(
        f"After that, the room looked calm again: {setting.aesthetic}, {obj.phrase}, "
        f"and no more mystery water on the floor."
    )
    world.say(
        f"{cause.qa_text} The little tap no longer spoiled the careful display."
    )


def tell(setting: Setting, tap: TapCfg, obj: ObjectCfg, cause: CauseCfg,
         hero_name: str = "Mina", hero_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "woman",
         delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the grown-up"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    clue = world.add(Entity(id="clue", type="thing", label=obj.label, attrs={"kind": obj.kind}))

    introduce(world, hero, setting, obj)
    world.para()
    tap_sound(world, tap)
    notice_clue(world, hero, obj, tap)
    warn(world, hero, adult, tap, obj)
    world.para()
    pred = predict_problem(world)
    world.facts["pred"] = pred
    if tap_is_suspicious(tap):
        _do_tap(world, room, tap, clue)
    reveal_cause(world, cause, tap, obj, adult)
    if can_fix(cause, delay):
        fix_room(world, cause, setting, obj)
    else:
        world.say(
            "The grown-up worked fast, but the leak had already made too much trouble."
        )
        world.get("room").meters["wetness"] += 1
        world.say(
            f"Still, they dried everything carefully, and {setting.aesthetic} was saved "
            f"from the worst of it."
        )
    world.facts.update(
        hero=hero, adult=adult, room=room, clue=clue, setting=setting, tap=tap,
        obj_cfg=obj, cause=cause, delay=delay, resolved=True
    )
    return world


SETTINGS = {
    "apartment": Setting("apartment", "the small apartment", "a soft aesthetic corner", "The lights were low and cozy"),
    "bathroom": Setting("bathroom", "the bathroom", "a neat aesthetic shelf", "Everything smelled clean and still"),
    "studio": Setting("studio", "the studio", "an artsy aesthetic table", "The whole place felt quiet and careful"),
}

TAPS = {
    "dripping": TapCfg("dripping", "tap", "tap... tap... tap...", "a tiny leak", "a damp trail", "replace the washer"),
    "knocking": TapCfg("knocking", "tap", "tap-tap from the pipe", "a hidden rattle", "a wet ring", "tighten the valve"),
    "soft": TapCfg("soft", "tap", "tap from the sink", "a slow drip", "a shiny line", "close the handle"),
}

OBJECTS = {
    "frame": ObjectCfg("frame", "picture frame", "a framed photo", "thing", clue="photo", suspicious=True),
    "note": ObjectCfg("note", "paper note", "a handwritten note", "thing", clue="ink", suspicious=True),
    "plant": ObjectCfg("plant", "little plant", "a little plant on a stand", "thing", clue="soil", suspicious=True),
    "lamp": ObjectCfg("lamp", "lamp", "a small lamp with a glass base", "thing", clue="glass", suspicious=True),
}

CAUSES = {
    "washer": CauseCfg("washer", "a worn washer inside the tap had gone old", "The grown-up replaced it with a fresh one", 3, 3, "The drip stopped, and the little mystery was solved."),
    "valve": CauseCfg("valve", "a loose valve was letting water whisper through", "They tightened it until the tap held steady", 2, 2, "The sink stayed dry after that."),
    "handle": CauseCfg("handle", "the handle had not been closed all the way", "They turned it until the tap clicked shut", 2, 2, "The tap became still and silent."),
}

GIRL_NAMES = ["Mina", "Lina", "Sana", "Ivy", "Nora", "Luna"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Owen", "Milo"]


@dataclass
class StoryParams:
    setting: str
    tap: str
    obj: str
    cause: str
    hero: str
    hero_gender: str
    adult: str
    adult_gender: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful, mystery-leaning story for a child that includes the word "aesthetic" and the word "tap".',
        f"Tell a gentle mystery about {f['hero'].id} noticing a strange tap in {f['setting'].place} and finding the real cause.",
        f"Write a short story with quiet suspense where a careful child spots a clue near {f['obj_cfg'].label} and calls a grown-up.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, adult = f["hero"], f["adult"]
    setting, tap, obj, cause = f["setting"], f["tap"], f["obj_cfg"], f["cause"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {adult.label_word}. {hero.id} was trying to keep a little {setting.aesthetic} neat and beautiful."),
        ("Why did the room feel suspenseful?",
         f"Because the tap kept making a strange tap sound, and there was a tiny drip trail near {obj.label}. That made {hero.id} feel like something important was hiding in plain sight."),
        ("What did the grown-up find?",
         f"{adult.label_word.capitalize()} found that {cause.explanation}. {cause.fix}."),
        ("How did the story end?",
         f"It ended calmly, with the tap quiet and the aesthetic display safe again. The mystery was solved, so the room felt peaceful instead of uneasy."),
    ]
    if f.get("resolved"):
        qa.append((
            "What changed after the fix?",
            f"The wetness went away and the mystery stopped. {setting.aesthetic} still looked lovely, but now nothing was dripping near {obj.label}."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a tap?",
         "A tap is a water fixture that can turn water on and off. If it drips when it should be still, something may need fixing."),
        ("What does aesthetic mean?",
         "Aesthetic means something looks pleasing and thoughtfully arranged. People use it when they want a room or display to feel especially nice."),
        ("Why can a drip be a clue in a mystery?",
         "A drip can show where water is coming from. That helps someone follow the evidence and find the cause."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("apartment", "dripping", "frame", "washer", "Mina", "girl", "Mom", "woman", 0),
    StoryParams("bathroom", "knocking", "plant", "valve", "Eli", "boy", "Dad", "man", 0),
    StoryParams("studio", "soft", "lamp", "handle", "Nora", "girl", "Mom", "woman", 1),
]


def explain_rejection(tap: TapCfg, obj: ObjectCfg) -> str:
    if not reasonableness_gate(tap, obj):
        return "(No story: this tap/object pair is too ordinary for suspense. Pick a suspicious object and a suspicious tap.)"
    return "(No story: invalid combination.)"


def valid_story(params: StoryParams) -> bool:
    return reasonableness_gate(TAPS[params.tap], OBJECTS[params.obj])


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for tid, t in TAPS.items():
        lines.append(asp.fact("tap", tid))
        if t.suspicious:
            lines.append(asp.fact("suspicious_tap", tid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.suspicious:
            lines.append(asp.fact("suspicious_obj", oid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("sense", cid, c.sense))
        lines.append(asp.fact("power", cid, c.power))
    lines.append(asp.fact("sense_min", SUSPENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, O) :- setting(S), tap(T), object(O), suspicious_tap(T), suspicious_obj(O).
mystery(T) :- suspicious_tap(T).
solved(C) :- cause(C), sense(C, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, tap=None, obj=None, cause=None, hero=None, hero_gender=None, adult=None, adult_gender=None, delay=None), random.Random(7)))
        assert sample.story
        print("OK: default generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: generation smoke test failed: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small suspenseful mystery storyworld about a tap and an aesthetic room.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tap", choices=TAPS)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    combos = valid_combos()
    if args.setting and args.tap and args.obj and not valid_story(StoryParams(args.setting, args.tap, args.obj, "Mina", "girl", "Mom", "woman")):
        raise StoryError(explain_rejection(TAPS[args.tap], OBJECTS[args.obj]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tap, obj = rng.choice(sorted(combos))
    cause = args.cause or rng.choice(sorted(CAUSES))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    adult = args.adult or ("Mom" if adult_gender == "woman" else "Dad")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, tap, obj, cause, hero, gender, adult, adult_gender, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TAPS[params.tap], OBJECTS[params.obj], CAUSES[params.cause],
                 params.hero, params.hero_gender, params.adult, params.adult_gender, params.delay)
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
        print(asp_program("", "#show valid/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, t, o in combos:
            print(f"  {s:10} {t:10} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

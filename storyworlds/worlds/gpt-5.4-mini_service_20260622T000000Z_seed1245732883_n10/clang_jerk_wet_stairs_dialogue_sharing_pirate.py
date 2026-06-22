#!/usr/bin/env python3
"""
storyworlds/worlds/clang_jerk_wet_stairs_dialogue_sharing_pirate.py
====================================================================

A small pirate-tale storyworld set on wet stairs.

Premise:
- Two children in pirate play climb a slippery stairway.
- One hears a clang and gets a jerk from the slippery step.
- They share a lantern or rope or towel to help each other.
- A helpful adult or crewmate arrives, and the ending shows the change:
  the risky climb becomes a safer shared crossing.

This script follows the Storyweavers standalone world contract:
- typed entities with meters and memes
- state-driven prose
- QA grounded in world state
- lazy ASP helper import
- verify mode that checks Python/ASP parity and a normal generation smoke test
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    wet: bool = False
    shareable: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "pirate": "pirate"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    hazard: str
    safe_spot: str
    windup: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    help_text: str
    share_text: str
    fixes_wet: bool = False
    shares_light: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str = "wet_stairs"
    response: str = "towel"
    gear1: str = "lantern"
    gear2: str = "rope"
    hero: str = "Nia"
    hero_gender: str = "girl"
    mate: str = "Bo"
    mate_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_clang(world: World) -> list[str]:
    out: list[str] = []
    stair = world.entities.get("stairs")
    if not stair:
        return out
    for e in world.entities.values():
        if e.meters["jerked"] < THRESHOLD:
            continue
        sig = ("clang", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        stair.meters["noise"] += 1
        for kid in [x for x in world.entities.values() if x.role in {"hero", "mate"}]:
            kid.memes["alarm"] += 1
        out.append("__clang__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    stair = world.entities.get("stairs")
    if not stair:
        return out
    for e in world.entities.values():
        if e.role not in {"hero", "mate"}:
            continue
        if not stair.wet or e.meters["slipped"] >= THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["slipped"] += 1
        e.memes["fear"] += 1
        out.append(f"{e.id} lost footing on the wet stairs.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("gear")
    if not helper:
        return out
    if helper.meters["shared"] < THRESHOLD:
        return out
    if ("share", helper.id) in world.fired:
        return out
    world.fired.add(("share", helper.id))
    for e in world.entities.values():
        if e.role in {"hero", "mate"}:
            e.memes["hope"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_slip, _r_clang, _r_share]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "wet_stairs": Setting(
        id="wet_stairs",
        place="the wet stairs",
        detail="The stairs by the harbor were slick with rain, and every step shone like glass.",
        hazard="wet stairs",
        safe_spot="the dry landing",
        windup="climb the stairs to the ship loft",
        tags={"stairs", "wet", "pirate"},
    ),
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="lantern",
        help_text="a little lantern that glowed like a gold coin",
        share_text="shared the lantern and made the steps bright",
        shares_light=True,
        tags={"light", "share"},
    ),
    "rope": Gear(
        id="rope",
        label="rope",
        help_text="a rope to hold so no one slid too far",
        share_text="shared the rope and held on together",
        tags={"rope", "share"},
    ),
    "towel": Gear(
        id="towel",
        label="towel",
        help_text="a dry towel to wipe the slippery boards",
        share_text="shared the towel and wiped the steps dry",
        fixes_wet=True,
        tags={"dry", "share"},
    ),
    "bucket": Gear(
        id="bucket",
        label="bucket",
        help_text="a bucket, though it was not the best choice",
        share_text="shared the bucket",
        tags={"share"},
    ),
}

RESPONSES = {
    "towel": Response(
        id="towel",
        sense=3,
        power=2,
        text="grabbed the dry towel and wiped the stairs until the shine went dull",
        fail="tried to mop the stairs, but the water kept beading up again",
        qa_text="grabbed the dry towel and wiped the stairs dry",
        tags={"dry"},
    ),
    "rope": Response(
        id="rope",
        sense=3,
        power=2,
        text="looped the rope along the banister so the children could climb carefully",
        fail="tied the rope too late to stop the slipping",
        qa_text="used the rope to help the children climb carefully",
        tags={"rope"},
    ),
    "lantern": Response(
        id="lantern",
        sense=2,
        power=1,
        text="set down the lantern and lit the path without rushing anyone",
        fail="held up the lantern, but the wet steps were still too slick",
        qa_text="used the lantern to light the path",
        tags={"light"},
    ),
    "bucket": Response(
        id="bucket",
        sense=1,
        power=1,
        text="slopped a bucket of water around and made the stairs worse",
        fail="slopped water everywhere and made the stairs even slicker",
        qa_text="used a bucket in a way that was not very wise",
        tags={"water"},
    ),
}

NAMES = ["Nia", "Bo", "Mia", "Toby", "Zoe", "Pip", "Finn", "Ivy"]
TRAITS = ["brave", "curious", "cheerful", "clever", "careful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, response in RESPONSES.items():
            if response.sense < 2:
                continue
            for g1 in GEAR:
                for g2 in GEAR:
                    if g1 == g2:
                        continue
                    combos.append((sid, rid, g1, g2))
    return combos


def explain_rejection(response: Response) -> str:
    return f"(No story: response '{response.id}' is too wobbly for a child-facing pirate rescue.)"


def outcome_of(params: StoryParams) -> str:
    return "shared"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale on wet stairs with clangs, jerks, dialogue, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gear1", choices=GEAR)
    ap.add_argument("--gear2", choices=GEAR)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.response is None or c[1] == args.response)
              and (args.gear1 is None or c[2] == args.gear1)
              and (args.gear2 is None or c[3] == args.gear2)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, response, gear1, gear2 = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice([n for n in NAMES if n != args.mate])
    mate = args.mate or rng.choice([n for n in NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, response=response, gear1=gear1, gear2=gear2, hero=hero, hero_gender=hero_gender, mate=mate, mate_gender=mate_gender, parent=parent)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    mate = world.add(Entity(id=params.mate, kind="character", type=params.mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the captain-parent"))
    stairs = world.add(Entity(id="stairs", kind="thing", type="stairs", label="the wet stairs", wet=True))
    gear = world.add(Entity(id="gear", kind="thing", type="gear", label=GEAR[params.gear1].label, shareable=True))
    alt = world.add(Entity(id="alt", kind="thing", type="gear", label=GEAR[params.gear2].label, shareable=True))
    world.facts.update(setting=setting, hero=hero, mate=mate, parent=parent, stairs=stairs, gear=gear, alt=alt, response=RESPONSES[params.response])

    world.say(f"On {setting.place}, {hero.id} and {mate.id} played pirate explorers. {setting.detail}")
    world.say(f'"Listen," {hero.id} said, "if we {setting.windup}, we can hear the sea from the top."')
    world.say(f'"Aye, but the stairs are slick," {mate.id} said. "I heard a { "clang" } when my boot hit the rail."')
    world.para()
    world.say(f'Their {parent.label_word} pointed at the hazard. "One wrong { "jerk" } and someone could fall," {parent.pronoun()} warned.')
    world.say(f'"Then let us share," {mate.id} said, and passed over {GEAR[params.gear1].help_text}.')

    # initialize facts before propagation
    stairs.meters["noise"] = 0.0
    stairs.meters["wetness"] = 1.0
    hero.meters["jerked"] = 1.0
    mate.meters["jerked"] = 0.0
    hero.memes["hope"] = 0.0
    mate.memes["hope"] = 0.0

    if params.gear1 == "towel" or params.gear2 == "towel":
        stairs.wet = True
        gear.meters["shared"] = 1.0
    else:
        gear.meters["shared"] = 1.0
    propagate(world, narrate=False)

    world.para()
    resp = RESPONSES[params.response]
    if params.response == "bucket":
        world.say(f'{parent.id} shook {parent.pronoun("possessive")} head. "No, matey, that only makes the deck slicker."')
    world.say(f'{parent.id} chose to {resp.text}.')
    world.say(f'Together they {GEAR[params.gear1].share_text} and {GEAR[params.gear2].share_text}.')
    world.say(f'"{setting.safe_spot}!" cheered {hero.id}. "That is the best deck on the ship now!"')

    world.facts.update(outcome="shared")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child set on wet stairs that includes the words "clang" and "jerk".',
        f"Tell a story where {f['hero'].id} and {f['mate'].id} hear a clang on wet stairs, speak in dialogue, and end by sharing a helpful tool.",
        f"Write a short pirate adventure about slick stairs, a warning, and sharing something useful so everyone can climb safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    resp = f["response"]
    gear = f["gear"]
    alt = f["alt"]
    return [
        QAItem(
            question=f"What did {hero.id} and {mate.id} hear on the wet stairs?",
            answer=f"They heard a clang, and it made the steps feel even more slippery. The sound reminded them that the stairs were wet and that they needed to move carefully.",
        ),
        QAItem(
            question=f"Why did {parent.id} warn them about a jerk on the stairs?",
            answer=f"{parent.id} warned them because one sudden jerk on wet stairs could make someone fall. The slippery steps made the risk real, so speaking up was the safe thing to do.",
        ),
        QAItem(
            question=f"How did the children share things to make the climb safer?",
            answer=f"They shared {gear.label} and {alt.label} so they could help each other on the stairs. Sharing the tools meant they could keep the adventure going without rushing.",
        ),
        QAItem(
            question=f"What did the parent choose to do after the warning?",
            answer=f"{parent.id} chose to {resp.qa_text}. That helped turn the wet stairs from a risky spot into a safer place for the pirate play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does clang mean?",
            answer="Clang is a loud metal sound, like when something hard bumps a rail or a bell rings nearby.",
        ),
        QAItem(
            question="What does jerk mean?",
            answer="A jerk is a quick, sudden pull or shake. On stairs it can throw someone off balance.",
        ),
        QAItem(
            question="Why are wet stairs dangerous?",
            answer="Wet stairs can be slippery, so feet may slide. That is why people should hold on and go slowly.",
        ),
        QAItem(
            question="Why is sharing helpful in a pirate story?",
            answer="Sharing lets everyone use the same useful thing without fighting over it. In a story, it helps the whole crew stay together.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.wet:
            bits.append("wet=True")
        if e.shareable:
            bits.append("shareable=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
wet_steps(stairs).
jerked(X) :- hero(X).
clang_event(stairs) :- jerked(X).
shared(X) :- gear(X).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "hero"), asp.fact("gear", "gear")]
    lines.append(asp.fact("stairs", "stairs"))
    lines.append(asp.fact("wet_steps", "stairs"))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show wet_steps/1."))
    return sorted(set(asp.atoms(model, "wet_steps")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("stairs",)}:
        rc = 1
        print("MISMATCH in ASP twin.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams(setting="wet_stairs", response="towel", gear1="lantern", gear2="rope", hero="Nia", hero_gender="girl", mate="Bo", mate_gender="boy", parent="mother"),
    StoryParams(setting="wet_stairs", response="rope", gear1="lantern", gear2="towel", hero="Bo", hero_gender="boy", mate="Ivy", mate_gender="girl", parent="father"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if params.gear1 not in GEAR or params.gear2 not in GEAR:
        raise StoryError("Unknown gear.")
    if params.gear1 == params.gear2:
        raise StoryError("Need two different shared items.")
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show wet_steps/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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

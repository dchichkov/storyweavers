#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trough_orca_dialogue_ghost_story.py
====================================================================

A standalone storyworld for a tiny ghost-story domain built from the seed words
"trough" and "orca", with dialogue as a narrative instrument.

This world is intentionally small and classical: a child hears a spooky sound by
an old trough at dusk, worries a ghost is there, speaks with a grown-up, and
discovers the thing in the trough is not a monster after all. The ending image
proves the change in state: fear drops, curiosity rises, and the child leaves
with a calmer understanding of the dark.

The story quality goal is a gentle ghost story, not a horror story. Spooky
beats are allowed, but the resolution must be safe and child-facing.
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    weather: str
    details: str
    dark: str


@dataclass
class SpookyThing:
    id: str
    label: str
    sound: str
    seen_as: str
    harmless_truth: str
    truth_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    trough = world.entities.get("trough")
    orca = world.entities.get("orca")
    if not trough or not orca:
        return out
    if trough.meters["water"] < THRESHOLD:
        return out
    if child.memes["fear"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    out.append("__spook__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["fear"] < THRESHOLD or child.memes["comfort"] < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["brave"] += 1
    out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("settle", "social", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_truth(world: World) -> dict:
    sim = world.copy()
    reveal(sim, narrate=False)
    child = sim.get("child")
    return {"fear": child.memes["fear"], "brave": child.memes["brave"]}


def peek_spooky(world: World) -> str:
    setting = world.setting
    return f"The {setting.dark} sat beside the old trough, and the wind kept making little sounds."


def tell_ghost(world: World, child: Entity, adult: Entity, spooky: SpookyThing, comfort: Comfort) -> None:
    world.say(
        f"At {world.setting.place}, {child.id} stopped at an old trough and listened. "
        f"{peek_spooky(world)}"
    )
    world.say(
        f'"Did you hear that?" {child.id} whispered. "It sounds like an orca under the water."'
    )
    world.say(
        f'"An orca?" {adult.id} said. "That sounds very grand for a trough."'
    )
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f'"I know," {child.id} said, "but it keeps saying {spooky.sound}."'
    )
    world.say(
        f'"Let us look together," {adult.id} said, and {adult.pronoun()} held up {comfort.phrase}.'
    )


def reveal(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    adult = world.get("adult")
    trough = world.get("trough")
    orca = world.get("orca")
    lantern = world.get("lantern")
    trough.meters["water"] = 1.0
    trough.meters["moonlight"] = 1.0
    orca.meters["toy"] = 1.0
    child.memes["comfort"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["brave"] += 1
    child.memes["relief"] += 1
    if narrate:
        world.say(
            f'{adult.id} shone the {lantern.label} over the trough. '
            f'The "orca" was only {orca.label} bobbing in the water, and the sound was just the trough tapping in the wind.'
        )
        world.say(
            f'"Oh," {child.id} said, and the scared look on {child.pronoun("possessive")} face softened. '
            f'"It is only a little one."'
        )
        world.say(
            f'"Exactly," {adult.id} said. "{spooky_truth(spooky=world.facts["spooky"]) }"'
        )


def spooky_truth(spooky: SpookyThing) -> str:
    return spooky.harmless_truth


def finish(world: World, child: Entity, adult: Entity, comfort: Comfort) -> None:
    world.say(
        f"{child.id} leaned closer, not frightened now. {child.pronoun().capitalize()} touched the dry rim of the trough and smiled at the moon."
    )
    world.say(
        f'"We can hear ghosts in the dark and still be brave," {adult.id} said.'
    )
    world.say(
        f'{child.id} nodded, holding {comfort.phrase} tight. The trough stayed still, the moon kept shining, and the night felt quiet instead of haunted.'
    )


def scenario(world: World, child: Entity, adult: Entity, spooky: SpookyThing, comfort: Comfort) -> None:
    tell_ghost(world, child, adult, spooky, comfort)
    world.para()
    world.say(
        f'"Maybe the orca is a ghost," {child.id} whispered.'
    )
    world.say(
        f'"Or maybe it is waiting for us to be brave enough to look," {adult.id} answered.'
    )
    world.say(
        f'That made {child.id} swallow hard, but {child.memes["curiosity"]} was stronger than the shiver.'
    )
    world.para()
    reveal(world)
    finish(world, child, adult, comfort)


SETTINGS = {
    "garden": Setting("garden", "the garden", "moonlit", "clear", "a stone path and wet herbs", "hedge shadow"),
    "yard": Setting("yard", "the yard", "quiet", "misty", "a fence and a sleepy tree", "long fence shadow"),
    "shore": Setting("shore", "the shore", "salt-sweet", "foggy", "damp sand and a cold breeze", "fog"),
}

SPOOKY_THINGS = {
    "orca": SpookyThing("orca", "a little orca figurine", "tap-tap", "a ghost orca", "The orca was only a little figurine bobbing in the trough.", "looked closer at the little figurine", tags={"orca", "ghost", "water"}),
    "owl": SpookyThing("owl", "a round owl charm", "hoo-hoo", "a ghost owl", "The owl was only a charm bumping softly against the trough.", "lifted the charm from the trough", tags={"owl", "ghost"}),
    "boat": SpookyThing("boat", "a tiny toy boat", "click-clack", "a ghost boat", "The boat was only a toy nudging the sides of the trough.", "lifted the toy boat out of the water", tags={"boat", "ghost", "water"}),
}

COMFORTS = {
    "lantern": Comfort("lantern", "a small lantern", "a small lantern", "glowed warm and steady", tags={"lantern", "light"}),
    "blanket": Comfort("blanket", "a thick blanket", "a thick blanket", "felt warm and safe", tags={"blanket"}),
    "candle": Comfort("candle", "a covered candle lantern", "a covered candle lantern", "glimmered behind its glass", tags={"candle", "light"}),
}


@dataclass
class StoryParams:
    setting: str
    spooky: str
    comfort: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, sp, c) for s in SETTINGS for sp in SPOOKY_THINGS for c in COMFORTS]


def explain_rejection(_: str, __: str, ___: str) -> str:
    return "(No story: this little ghost tale only uses the built-in haunted-trough combinations.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about a trough, an orca, and brave dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spooky", choices=SPOOKY_THINGS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father", "grandmother", "grandfather"])
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
    choice = rng.choice(combos)
    setting = args.setting or choice[0]
    spooky = args.spooky or choice[1]
    comfort = args.comfort or choice[2]
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(["Mia", "Lena", "Nora", "Finn", "Theo", "Eli"])
    adult_gender = args.adult_gender or rng.choice(["mother", "father", "grandmother", "grandfather"])
    adult = args.adult or rng.choice(["Mom", "Dad", "Grandma", "Grandpa"])
    return StoryParams(setting, spooky, comfort, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="child", label=params.child))
    adult = world.add(Entity("adult", kind="character", type=params.adult_gender, role="adult", label=params.adult))
    trough = world.add(Entity("trough", label="the trough"))
    orca = world.add(Entity("orca", label=SPOOKY_THINGS[params.spooky].label))
    lantern = world.add(Entity("lantern", label=COMFORTS[params.comfort].label))
    world.facts["spooky"] = SPOOKY_THINGS[params.spooky]
    world.facts["comfort"] = COMFORTS[params.comfort]

    scenario(world, child, adult, SPOOKY_THINGS[params.spooky], COMFORTS[params.comfort])

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
        f'Write a gentle ghost story for a young child that includes the words "trough" and "orca" and uses dialogue to build suspense.',
        f"Tell a spooky-but-safe story where {f['spooky'].seen_as} seems to be in an old trough, but an adult helps a child look more closely.",
        f"Write a child-facing ghost story with a dark opening, spoken lines, and a calm ending at the trough.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.get("child")
    adult = world.get("adult")
    spooky = world.facts["spooky"]
    comfort = world.facts["comfort"]
    return [
        ("What made the child feel scared at first?",
         f"The child heard the trough making strange sounds and thought it might be {spooky.seen_as}. That spooky guess made the dark feel bigger than it really was."),
        ("What did the adult say to help?",
         f'The adult said, "Let us look together," and shone a light over the trough. That gave the child a calmer way to face the dark instead of running away from it.'),
        ("What was the thing in the trough really?",
         f"It was only {spooky.label}, and the strange sound was just the trough tapping in the wind. Once that was clear, the scary idea stopped being scary."),
        ("How did the child feel at the end?",
         f"The child felt relieved and braver, and held {comfort.phrase} close. The trough, the moonlight, and the quiet night all stayed the same, but the fear was gone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    spooky = world.facts["spooky"]
    comfort = world.facts["comfort"]
    return [
        ("What is a trough?",
         "A trough is a long container for water. It can be made of stone, wood, or metal, and animals or people may use it for water."),
        ("What is an orca?",
         "An orca is a big black-and-white whale that lives in the ocean. It is also called a killer whale."),
        ("Why can the dark sound spooky?",
         "When you cannot see well, normal sounds can seem mysterious or scary. A creak or tap can feel like a ghost story until you look closely."),
        ("Why do lamps help in a ghost story?",
         "A lamp or lantern gives steady light, which makes shadows easier to understand. Light can turn a spooky guess into a plain, safe answer."),
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
spooky(X) :- trough_water(X), fear(X).
settled(X) :- comfort(X), fear(X), not too_scared(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SPOOKY_THINGS:
        lines.append(asp.fact("spooky_thing", sid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    combos = set(valid_combos())
    c = set(asp_valid_combos())
    if c != combos:
        print("MISMATCH in valid combos")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, spooky=None, comfort=None, child=None, child_gender=None, adult=None, adult_gender=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity with {len(c)} combos and smoke test passed.")
    return 0


CURATED = [
    StoryParams("garden", "orca", "lantern", "Mia", "girl", "Grandma", "grandmother"),
    StoryParams("yard", "boat", "blanket", "Finn", "boy", "Dad", "father"),
    StoryParams("shore", "orca", "candle", "Lena", "girl", "Mom", "mother"),
]


def resolve_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spooky and args.comfort:
        return StoryParams(args.setting, args.spooky, args.comfort,
                           args.child or "Mia", args.child_gender or "girl",
                           args.adult or "Grandma", args.adult_gender or "grandmother")
    return resolve_params(args, rng)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_choice(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

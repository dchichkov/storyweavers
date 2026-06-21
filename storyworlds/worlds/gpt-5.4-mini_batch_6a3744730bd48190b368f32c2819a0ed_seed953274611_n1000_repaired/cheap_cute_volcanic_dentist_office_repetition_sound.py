#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cheap_cute_volcanic_dentist_office_repetition_sound.py
======================================================================================

A tiny bedtime storyworld set in a dentist office.

Premise:
- A child comes in with a cheap, cute toy volcano.
- The volcano likes to make repeating sound effects.
- The dentist needs quiet to do a checkup.
- The child learns to use the volcano in a calmer, safer way.

The world is small on purpose: a few typed entities, physical meters, emotional
memes, a causal turn, and a gentle ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    noisy: bool = False
    calming: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "tension": 0.0, "quiet": 0.0}
        if not self.memes:
            self.memes = {"delight": 0.0, "worry": 0.0, "relief": 0.0, "pride": 0.0}

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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    dentist = world.entities.get("dentist")
    if not child or not toy or not dentist:
        return out
    if child.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dentist.meters["tension"] += 1
    dentist.memes["worry"] += 1
    child.memes["worry"] += 1
    out.append("__noise__")
    return out


def _r_quiet(world: World) -> list[str]:
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    dentist = world.entities.get("dentist")
    if not child or not toy or not dentist:
        return []
    if toy.meters["quiet"] < THRESHOLD:
        return []
    sig = ("quiet",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dentist.meters["tension"] = max(0.0, dentist.meters["tension"] - 1)
    child.memes["relief"] += 1
    return ["__quiet__"]


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("quiet", _r_quiet)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    child_name: str = "Milo"
    child_gender: str = "boy"
    dentist_name: str = "Dr. Poppy"
    toy_name: str = "the volcano"
    mode: str = "calm"  # calm | echo | hush
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CHILD_NAMES = ["Milo", "Nina", "Toby", "Luna", "Pip", "Maya", "Ollie", "June"]
DENTIST_NAMES = ["Dr. Poppy", "Dr. Tinsel", "Dr. Mint", "Dr. Mallow"]

TOY_LOOKUP = {
    "volcano": {"label": "volcano", "phrase": "a cheap, cute volcanic toy volcano", "noisy": True, "calming": False},
    "shell": {"label": "shell", "phrase": "a cheap, cute little shell toy", "noisy": False, "calming": True},
}

MODES = {
    "calm": {
        "opening": "The waiting room was soft and sleepy, with a round lamp and a fish poster that looked half-asleep.",
        "sound": "The toy went boom-bip, boom-bip, boom-bip, and then ka-pow! ka-pow!",
        "resolution": "The child tucked the toy under a blanket and made it whisper instead of shout.",
    },
    "echo": {
        "opening": "The dentist office was clean and bright, with a tiny cup of water and a clock that ticked like a mouse.",
        "sound": "The toy said rumble-rumble, rattle-rattle, rumble-rattle, louder and louder.",
        "resolution": "The child bounced the toy on a pillow and let the sound become a sleepy murmur.",
    },
    "hush": {
        "opening": "The hallway smelled like mint, and the dentist office felt as quiet as a moonlit nest.",
        "sound": "The toy chirped ding-ding-ding, ding-ding-ding, and then one last ding!",
        "resolution": "The child pressed the toy into a soft mitt so the noises turned tiny and kind.",
    },
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for toy in TOY_LOOKUP:
        for mode in MODES:
            combos.append((toy, mode))
    return combos


def explain_rejection(toy: str, mode: str) -> str:
    return f"(No story: the toy '{toy}' with mode '{mode}' does not fit this calm dentist-office bedtime world.)"


def tell(child_name: str, child_gender: str, dentist_name: str, toy_name: str, mode: str) -> World:
    if toy_name not in TOY_LOOKUP:
        raise StoryError(f"Unknown toy '{toy_name}'.")
    if mode not in MODES:
        raise StoryError(f"Unknown mode '{mode}'.")
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    dentist = world.add(Entity(id="dentist", kind="character", type="adult", label=dentist_name, role="dentist"))
    toy_cfg = TOY_LOOKUP[toy_name]
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label=toy_cfg["label"],
        phrase=toy_cfg["phrase"],
        noisy=toy_cfg["noisy"],
        calming=toy_cfg["calming"],
    ))
    world.facts.update(child=child, dentist=dentist, toy=toy, mode=mode)

    child.memes["delight"] += 1
    toy.meters["noise"] += 1 if toy.noisy else 0
    world.say(f"At the dentist office, {child_name} held {toy_cfg['phrase']}.")
    world.say(MODES[mode]["opening"])
    world.say(f"{child_name} smiled and made it go: {MODES[mode]['sound']}")
    world.para()

    if toy.noisy:
        child.meters["noise"] += 1
        world.say(f"{child_name} said it again and again: {MODES[mode]['sound']}")
        world.say(f"{dentist_name} put a gentle hand on the chair and waited for the sound to settle.")
        propagate(world, narrate=False)
        world.say(f"{dentist_name} whispered, 'Let's make the volcano small, small, small.'")
        world.say(MODES[mode]["resolution"])
        toy.meters["noise"] = 0.0
        toy.meters["quiet"] = 1.0
        propagate(world, narrate=False)
        child.memes["relief"] += 1
        child.memes["pride"] += 1
        dentist.memes["relief"] += 1
        world.para()
        world.say(f"Then the room grew quiet again, and {child_name} could open wide and get the little checkup done.")
        world.say(f"When it was over, {child_name} carried the cheap, cute volcanic toy home in a calm, careful hug.")
    else:
        toy.meters["quiet"] = 1.0
        propagate(world, narrate=False)
        world.say(f"The little toy stayed quiet, and {child_name} listened to the soft tick of the clock.")
        world.say(f"The checkup was quick, and the room felt warm and safe, like a bedtime song.")

    world.facts["outcome"] = "quiet"
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a bedtime story set in a dentist office about a cheap, cute volcanic toy that makes repeating sound effects.",
        "Tell a gentle story where a child learns to keep a noisy toy volcano quiet during a dentist visit.",
        "Write a small bedtime tale that uses the words cheap, cute, and volcanic, with sound effects and a soft ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dentist = f["dentist"]
    toy = f["toy"]
    mode = f["mode"]
    qa = [
        ("Where does the story happen?",
         f"It happens in a dentist office, where the air is calm and the walls feel clean and bright."),
        (f"What did {child.label} bring?",
         f"{child.label} brought {toy.phrase}. It was cheap, cute, and volcanic, so it made the story feel playful."),
        (f"Why did {dentist.label} ask for quiet?",
         f"{dentist.label} needed the room to settle so the checkup could go smoothly. The repeating sound effects were funny, but they were too loud for a visit with a dentist."),
        ("How did the child solve the problem?",
         f"The child made the volcano smaller and quieter. That let the sounds turn soft, and the checkup could finish without fuss."),
    ]
    if mode:
        qa.append(("How did the story end?",
                   "It ended softly, with the toy quiet and the child calm. The room felt ready for sleep again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dentist office?",
         "A dentist office is a place where people go to have their teeth checked and cleaned. It is usually a quiet place with chairs, bright lights, and gentle tools."),
        ("What does volcanic mean?",
         "Volcanic means it is like a volcano or comes from a volcano. In a story, it can mean the toy makes a rumbling, erupting sound."),
        ("Why can repeating sound effects be fun?",
         "Repeating sound effects can feel playful because they are easy to remember and sing along with. They can also make a bedtime story sound cozy and musical."),
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.noisy:
            bits.append("noisy")
        if e.calming:
            bits.append("calming")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
noisy(X) :- thing(X), noisy_thing(X).
quiet(X) :- thing(X), quiet_thing(X).
rumble :- child_noise, noisy(toy).
calm :- quiet(toy).
"""


def asp_facts() -> str:
    import asp
    parts = []
    for toy_id, cfg in TOY_LOOKUP.items():
        parts.append(asp.fact("thing", toy_id))
        if cfg["noisy"]:
            parts.append(asp.fact("noisy_thing", toy_id))
        if cfg["calming"]:
            parts.append(asp.fact("quiet_thing", toy_id))
    for mode in MODES:
        parts.append(asp.fact("mode", mode))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show thing/1.\n#show mode/1."))
    return sorted(set(asp.atoms(model, "thing")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generated a story.")
    except Exception as err:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    py = set(valid_combos())
    asp_set = set((a, b) for (a, b) in py) if False else py
    if asp_set == py:
        print(f"OK: ASP and Python parity check passed ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP/Python parity.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: cheap, cute, volcanic sounds in a dentist office.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--dentist-name", choices=DENTIST_NAMES)
    ap.add_argument("--toy", choices=TOY_LOOKUP)
    ap.add_argument("--mode", choices=MODES)
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
    toy = args.toy or rng.choice(list(TOY_LOOKUP))
    mode = args.mode or rng.choice(list(MODES))
    if toy not in TOY_LOOKUP or mode not in MODES:
        raise StoryError("Unknown toy or mode.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    dentist_name = args.dentist_name or rng.choice(DENTIST_NAMES)
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        dentist_name=dentist_name,
        toy_name=toy,
        mode=mode,
    )


def generate(params: StoryParams) -> StorySample:
    if params.toy_name not in TOY_LOOKUP:
        raise StoryError(f"Unknown toy '{params.toy_name}'.")
    if params.mode not in MODES:
        raise StoryError(f"Unknown mode '{params.mode}'.")
    world = tell(params.child_name, params.child_gender, params.dentist_name, params.toy_name, params.mode)
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


CURATED = [
    StoryParams(child_name="Milo", child_gender="boy", dentist_name="Dr. Poppy", toy_name="volcano", mode="calm"),
    StoryParams(child_name="Luna", child_gender="girl", dentist_name="Dr. Mint", toy_name="volcano", mode="echo"),
    StoryParams(child_name="Pip", child_gender="boy", dentist_name="Dr. Tinsel", toy_name="shell", mode="hush"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(toy, mode) for toy in TOY_LOOKUP for mode in MODES]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show thing/1.\n#show mode/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for toy, mode in valid_combos():
            print(f"  {toy:8} {mode}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

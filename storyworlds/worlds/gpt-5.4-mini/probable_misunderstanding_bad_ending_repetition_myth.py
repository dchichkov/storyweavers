#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/probable_misunderstanding_bad_ending_repetition_myth.py
======================================================================================

A standalone story world sketch for a small mythic domain: a village listens for
omens, repeats a ritual three times, and then mistakes a harmless sign for a
probable warning. The misunderstanding grows into a bad ending, but the story is
still child-facing, concrete, and driven by world state.

The domain is intentionally tiny:
- a child or helper notices an omen,
- another character misreads it,
- a repeated ritual makes the misunderstanding feel more certain,
- the wrong decision leads to loss,
- the ending image proves the change.

The seed word "probable" is used in the world model and may appear in dialogue or
generated questions, but the core story stays authored and state-driven.
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

POSITIONS = {"village", "hill", "river", "shrine", "gate"}
OMENS = {"wind", "owl", "drum", "cloud"}
MISREADINGS = {"storm", "raiders", "curse", "earthquake"}
RITUALS = {"bell", "prayer", "signal_fire", "drum"}
LOSSES = {"harvest", "bridge", "boat", "roof"}


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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Sign:
    id: str
    label: str
    omen_word: str
    sound: str
    likely: str
    true_meaning: str
    tags: set[str] = field(default_factory=set)

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
class Ritual:
    id: str
    label: str
    repeat: int
    line: str
    tags: set[str] = field(default_factory=set)

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
class Loss:
    id: str
    label: str
    visible: str
    ruined: str
    tags: set[str] = field(default_factory=set)

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
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("elder").memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    elder = world.get("elder")
    if elder.memes["certainty"] < 2:
        return out
    if world.get("village").meters["alarm"] >= THRESHOLD:
        sig = ("repeat",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("gate").meters["locked"] += 1
            out.append("__repeat__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    if world.get("gate").meters["locked"] < THRESHOLD:
        return out
    sig = ("loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("loss").meters["ruined"] += 1
    world.get("village").meters["sad"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("repeat", "social", _r_repeat),
    Rule("loss", "physical", _r_loss),
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


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    return {
        "alarm": sim.get("village").meters["alarm"],
        "locked": sim.get("gate").meters["locked"],
    }


def wise_enough(sign: Sign, ritual: Ritual) -> bool:
    return sign.likely == ritual.label and ritual.repeat >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in POSITIONS:
        for sign in SIGNS:
            for ritual in RITUALS_MAP:
                for loss in LOSSES_MAP:
                    if SIGNS[sign].likely == RITUALS_MAP[ritual].label:
                        combos.append((place, sign, ritual, loss))
    return combos


def _do_misunderstanding(world: World, sign: Sign) -> None:
    world.get("child").memes["worry"] += 1
    world.get("elder").memes["certainty"] += 1
    world.get("village").meters["alarm"] += 1
    world.say(
        f"At the {world.get('village').label_word}, {world.get('child').id} heard "
        f"{sign.sound} and saw {sign.omen_word}."
    )
    world.say(
        f'"That is probably {sign.likely}," said {world.get("elder").id}, and the '
        f"words felt heavy as stones."
    )


def _do_repetition(world: World, ritual: Ritual) -> None:
    elder = world.get("elder")
    for _ in range(ritual.repeat):
        elder.memes["certainty"] += 1
    world.say(
        f"So the people repeated the {ritual.label} {ritual.repeat} times: "
        f"{ritual.line}"
    )
    world.say("Again they repeated it. Again they repeated it. Again they repeated it.")


def _do_bad_choice(world: World) -> None:
    world.get("gate").meters["locked"] += 1
    world.say(
        "Then they shut the gate and would not open it, because they feared the dark."
    )


def _do_loss(world: World, loss: Loss) -> None:
    world.get("loss").meters["ruined"] += 1
    world.say(
        f"By morning, the {loss.label} was gone: {loss.visible} had turned into "
        f"{loss.ruined}."
    )
    world.say(
        "The village stood quiet, and the same fear that had made them hurry now "
        "made them too late."
    )


def _do_end(world: World, loss: Loss) -> None:
    world.say(
        f"Only the {loss.label} and the locked gate remained, and the people kept "
        f"their voices low whenever the wind moved."
    )


def tell(place: str, sign: Sign, ritual: Ritual, loss: Loss,
         child_name: str = "Mira", child_type: str = "girl",
         elder_name: str = "Eren", elder_type: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="seer"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, role="elder"))
    village = world.add(Entity(id="village", type=place, label=place, role="setting"))
    gate = world.add(Entity(id="gate", type="thing", label="the gate"))
    loss_ent = world.add(Entity(id="loss", type="thing", label=loss.label))
    world.facts.update(sign=sign, ritual=ritual, loss=loss, child=child, elder=elder, village=village)

    world.say(
        f"In a small mythic village, {child.id} listened to the {sign.label} "
        f"while the people watched the sky."
    )
    world.say(
        f"The sign was {sign.true_meaning}, but no one remembered that at first."
    )

    world.para()
    _do_misunderstanding(world, sign)
    _do_repetition(world, ritual)

    if wise_enough(sign, ritual):
        _do_bad_choice(world)
        propagate(world, narrate=False)
        world.para()
        _do_loss(world, loss)
        _do_end(world, loss)
        outcome = "bad"
    else:
        world.say("Instead they looked again and understood the sign before the gate was shut.")
        outcome = "good"

    world.facts.update(outcome=outcome, child=child, elder=elder, gate=gate, loss_ent=loss_ent)
    return world


@dataclass
@dataclass
class StoryParams:
    place: str
    sign: str
    ritual: str
    loss: str
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


POSITIONS = ["village", "hill", "river", "shrine", "gate"]

SIGNS = {
    "wind": Sign("wind", "whistling wind", "wind", "a long whistle", "change", "a messenger, not an enemy", {"wind"}),
    "owl": Sign("owl", "owl call", "owl", "a soft hoot", "night", "a watcher in the trees", {"owl"}),
    "drum": Sign("drum", "drumbeat", "drum", "a distant boom", "approaching people", "a festival, not a raid", {"drum"}),
    "cloud": Sign("cloud", "dark cloud", "cloud", "a low grumble", "rain", "water-laden sky, not a curse", {"cloud"}),
}

RITUALS_MAP = {
    "bell": Ritual("bell", "bell-ringing", 3, "the bell must ring three times", {"bell"}),
    "prayer": Ritual("prayer", "prayer-circling", 3, "the prayer must be spoken three times", {"prayer"}),
    "signal_fire": Ritual("signal_fire", "signal fire", 2, "the fire must be lit two times", {"signal_fire"}),
    "drum": Ritual("drum", "drumming", 3, "the drum must sound three times", {"drum"}),
}

LOSSES_MAP = {
    "harvest": Loss("harvest", "harvest", "the grain in the field", "scattered seed", {"harvest"}),
    "bridge": Loss("bridge", "bridge", "the planks over the river", "broken boards", {"bridge"}),
    "boat": Loss("boat", "boat", "the boat at the bank", "splintered wood", {"boat"}),
    "roof": Loss("roof", "roof", "the roof over the shrine", "fallen shingles", {"roof"}),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in POSITIONS:
        for sign_id, sign in SIGNS.items():
            for ritual_id, ritual in RITUALS_MAP.items():
                for loss_id in LOSSES_MAP:
                    if ritual.repeat >= 2 and sign.likely in ritual.line:
                        combos.append((place, sign_id, ritual_id, loss_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic misunderstanding with repetition and a bad ending.")
    ap.add_argument("--place", choices=POSITIONS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--ritual", choices=RITUALS_MAP)
    ap.add_argument("--loss", choices=LOSSES_MAP)
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
              if (args.place is None or c[0] == args.place)
              and (args.sign is None or c[1] == args.sign)
              and (args.ritual is None or c[2] == args.ritual)
              and (args.loss is None or c[3] == args.loss)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sign, ritual, loss = rng.choice(sorted(combos))
    return StoryParams(place, sign, ritual, loss)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child where the word "probable" matters and a sign is misread.',
        f"Tell a small legend where {f['sign'].label} seems to mean disaster, but the people are only partly right.",
        f"Write a story with repetition and a bad ending in which a village says something is probable and acts too fast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sign: Sign = f["sign"]
    ritual: Ritual = f["ritual"]
    loss: Loss = f["loss"]
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    qa = [
        QAItem(
            question="What did the village misunderstand?",
            answer=f"They misunderstood the {sign.label}. It was really {sign.true_meaning}, but they treated it like a warning of {sign.likely}."
        ),
        QAItem(
            question="Why did they repeat the ritual?",
            answer=f"They repeated {ritual.label} because {elder.id} thought it was probably the right way to keep everyone safe. The repetition made the fear feel stronger, not wiser."
        ),
        QAItem(
            question=f"What happened to {loss.label} at the end?",
            answer=f"The {loss.label} was ruined. The ending shows that their rushed choice could not be taken back once the gate stayed shut."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sign: Sign = f["sign"]
    ritual: Ritual = f["ritual"]
    loss: Loss = f["loss"]
    out = [
        QAItem(
            question="What does probable mean?",
            answer="Probable means something is likely to happen, but it is still not certain."
        ),
        QAItem(
            question=f"Why are repeated rituals important in myths?",
            answer="In myths, repetition can make an action feel powerful or serious. It also helps people remember the rule or warning."
        ),
        QAItem(
            question=f"What should people do before locking a gate because of a warning?",
            answer="They should look again and make sure they understood the sign correctly. A hasty lock can create a problem instead of solving one."
        ),
    ]
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "wind", "bell", "harvest"),
    StoryParams("hill", "owl", "prayer", "roof"),
    StoryParams("river", "drum", "signal_fire", "boat"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not produce the mythic misunderstanding we need.)"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SIGNS.values():
        lines.append(asp.fact("sign", s.id))
        lines.append(asp.fact("likely", s.id, s.likely))
    for r in RITUALS_MAP.values():
        lines.append(asp.fact("ritual", r.id))
        lines.append(asp.fact("repeat", r.id, r.repeat))
    for l in LOSSES_MAP.values():
        lines.append(asp.fact("loss", l.id))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,R,L) :- sign(S), ritual(R), loss(L), likely(S, X), repeat(R, N), N >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, sign=None, ritual=None, loss=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, SIGNS[params.sign], RITUALS_MAP[params.ritual], LOSSES_MAP[params.loss])
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
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

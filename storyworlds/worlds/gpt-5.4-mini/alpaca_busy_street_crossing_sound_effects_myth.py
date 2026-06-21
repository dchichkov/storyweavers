#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alpaca_busy_street_crossing_sound_effects_myth.py
=================================================================================

A standalone story world for a tiny mythic crossing tale: an alpaca, a busy
street crossing, and sound effects that matter. A child and a grown-up want to
cross a noisy street; the alpaca's bells and the city's sounds create tension;
then a wise helper uses a signal, a safe pause, and a small charm of patience to
cross at the right time.

The world is built as a small simulation with typed entities, physical meters,
emotional memes, a Python reasonableness gate, and an inline ASP twin.
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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Crossing:
    id: str
    label: str
    sound: str
    crosswalk: str
    signal: str
    busy: bool = True
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
class Guide:
    id: str
    label: str
    sound: str
    action: str
    calm: str
    power: int
    sense: int
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
class Charm:
    id: str
    label: str
    phrase: str
    gives_patience: bool = True
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    if "road" not in world.entities:
        return out
    road = world.get("road")
    if road.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["startle"] += 1
    out.append("__noise__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if "guide" not in world.entities:
        return out
    guide = world.get("guide")
    if guide.memes["calm"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "road" in world.entities:
        world.get("road").meters["rush"] = 0.0
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("noise", "physical", _r_noise), Rule("calm", "social", _r_calm)]


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


def road_is_too_busy(crossing: Crossing) -> bool:
    return crossing.busy


def safe_guide_available(guide: Guide) -> bool:
    return guide.sense >= SENSE_MIN


def would_wait_for_signal(crossing: Crossing, guide: Guide) -> bool:
    return crossing.busy and safe_guide_available(guide)


def _step_toward_crossing(world: World, child: Entity, alpaca: Entity, crossing: Crossing) -> None:
    child.memes["wonder"] += 1
    alpaca.memes["restless"] += 1
    world.say(
        f"At the busy street crossing, {child.id} stood beside the alpaca while "
        f"cars flashed by. The crossing stones were bright, but the road roared."
    )
    world.say(f'"{crossing.sound}!" said the city, and the alpaca flicked its ears.')


def tempt(world: World, child: Entity, alpaca: Entity) -> None:
    world.say(
        f"The alpaca leaned toward the curb and made a soft little sound, "
        f'"hmm-maa." {child.id} wanted to step out at once.'
    )
    child.memes["desire"] += 1


def warn(world: World, guide: Entity, child: Entity, crossing: Crossing) -> None:
    guide.memes["calm"] += 1
    guide.meters["attention"] += 1
    world.say(
        f'{guide.id} lifted a hand and listened to the street. '
        f'"{crossing.sound}," {guide.pronoun()} said. '
        f'"We wait for the signal, because a busy road is not a game."'
    )


def rush(world: World, child: Entity, alpaca: Entity, crossing: Crossing) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} laughed and almost ran forward. "
        f'The crossing answered with a sharper sound -- {crossing.sound}! -- '
        f'and the alpaca stamped once, clop-clop.'
    )
    world.get("road").meters["noise"] += 1
    propagate(world, narrate=False)


def signal_change(world: World, crossing: Crossing) -> None:
    road = world.get("road")
    road.meters["noise"] += 0.5
    world.say(
        f"Then the little signal changed. The red wait faded, the white walk "
        f"glimmered, and even the horn-song of the road seemed to pause."
    )
    crossing.busy = False


def cross_safely(world: World, child: Entity, alpaca: Entity, guide: Entity, crossing: Crossing) -> None:
    child.memes["joy"] += 1
    alpaca.memes["calm"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"{guide.id} smiled. {child.id} took the alpaca by its rope, and together "
        f"they crossed on the green light. Clip-clop, step, step -- and the cars "
        f"waited like patient giants."
    )
    world.say(
        f"On the far side, the alpaca shook its bells in a tiny victory song, "
        f"and the crossing stayed behind them, loud but harmless."
    )


def tell(crossing: Crossing, guide: Guide, alpaca_name: str = "Pip", child_name: str = "Mira") -> World:
    world = World()
    road = world.add(Entity(id="road", type="thing", label="the road"))
    child = world.add(Entity(id=child_name, kind="character", type="girl", role="child"))
    alpaca = world.add(Entity(id=alpaca_name, kind="character", type="thing", role="companion"))
    helper = world.add(Entity(id=guide.id, kind="character", type="mother", role="guide", label=guide.label))
    world.facts["crossing"] = crossing
    world.facts["guide_cfg"] = guide
    world.facts["alpaca_name"] = alpaca_name
    world.facts["child_name"] = child_name
    child.memes["trust"] = 4
    alpaca.memes["curiosity"] = 3

    world.say(
        f"Long ago, at {crossing.label}, {child.id} met an alpaca with bright eyes "
        f"and a bell on its collar. The crossing was busy, and every engine made "
        f"its own little thunder."
    )
    world.say(f'The city went "{crossing.sound}" all around them.')

    world.para()
    _step_toward_crossing(world, child, alpaca, crossing)
    tempt(world, child, alpaca)
    warn(world, helper, child, crossing)

    if would_wait_for_signal(crossing, guide):
        signal_change(world, crossing)
        world.para()
        cross_safely(world, child, alpaca, helper, crossing)
        outcome = "safe"
    else:
        rush(world, child, alpaca, crossing)
        world.say(
            "For a heartbeat the street felt too fast, and the child remembered "
            "to stop. They stayed on the curb until the noise loosened its grip."
        )
        world.para()
        signal_change(world, crossing)
        cross_safely(world, child, alpaca, helper, crossing)
        outcome = "delayed"

    world.facts.update(child=child, alpaca=alpaca, guide=helper, road=road, outcome=outcome)
    return world


CROSSINGS = {
    "mythic_crossing": Crossing(
        id="mythic_crossing",
        label="the busy street crossing",
        sound="whoosh-honk, whoosh-honk",
        crosswalk="the striped crosswalk",
        signal="the signal",
        busy=True,
        tags={"crossing", "busy", "sound"},
    ),
    "market_crossing": Crossing(
        id="market_crossing",
        label="the market crossing",
        sound="beep-beep, vroom-vroom",
        crosswalk="the painted crosswalk",
        signal="the crossing light",
        busy=True,
        tags={"crossing", "busy", "sound"},
    ),
}

GUIDES = {
    "wise_mom": Guide(
        id="Mother",
        label="the mother",
        sound="listen first",
        action="wait",
        calm="a calm hand",
        power=3,
        sense=3,
        tags={"guide", "calm"},
    ),
    "aunt": Guide(
        id="Aunt",
        label="the aunt",
        sound="hear the road",
        action="pause",
        calm="a patient smile",
        power=2,
        sense=2,
        tags={"guide", "calm"},
    ),
}

ALPACA_NAMES = ["Pip", "Mochi", "Luna", "Taco", "Zuri"]
CHILD_NAMES = ["Mira", "Nina", "Theo", "Aria", "Jules"]


@dataclass
@dataclass
class StoryParams:
    crossing: str
    guide: str
    alpaca_name: str
    child_name: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(c, g) for c in CROSSINGS for g in GUIDES if road_is_too_busy(CROSSINGS[c]) and safe_guide_available(GUIDES[g])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic alpaca crossing story world.")
    ap.add_argument("--crossing", choices=CROSSINGS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--alpaca-name", choices=ALPACA_NAMES)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
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
    if not combos:
        raise StoryError("No valid crossing stories are available.")
    if args.crossing and args.guide:
        if (args.crossing, args.guide) not in combos:
            raise StoryError("That guide does not fit this crossing well enough.")
    c, g = rng.choice(sorted(combos))
    return StoryParams(
        crossing=args.crossing or c,
        guide=args.guide or g,
        alpaca_name=args.alpaca_name or rng.choice(ALPACA_NAMES),
        child_name=args.child_name or rng.choice(CHILD_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child about an alpaca at {f["crossing"].label} with sound effects.',
        f'Tell a story where {f["child_name"]} and an alpaca must wait for the signal at a busy crossing, and the sounds matter.',
        "Write a gentle myth about patience, a noisy road, and a safe crossing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    alpaca = f["alpaca"]
    guide = f["guide"]
    crossing = f["crossing"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, {alpaca.id} the alpaca, and {guide.id}, who helped at {crossing.label}. The busy street crossing and its sounds are part of the lesson.",
        ),
        QAItem(
            question="Why did they wait before crossing?",
            answer=f"They waited because {crossing.label} was busy and noisy. {guide.id} listened to the road and chose the safe time instead of rushing.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They crossed safely on the green light, and the alpaca's bells made a tiny victory sound. The crossing stayed loud, but the danger was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should you look and listen before crossing a busy street?",
            answer="Because cars and bikes can move very fast, and sound can warn you that something is coming. Looking and listening helps you wait for a safe moment.",
        ),
        QAItem(
            question="What is a crosswalk?",
            answer="A crosswalk is a marked place where people cross a street more safely. Drivers can see it and know to slow down or stop.",
        ),
        QAItem(
            question="What sounds can a busy street make?",
            answer="A busy street can make honks, engine hums, tire whooshes, and little bell sounds from people or animals. Those sounds help a story feel alive.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(CROSSINGS[params.crossing], GUIDES[params.guide], params.alpaca_name, params.child_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen crossing and guide do not make a safe, sensible myth.)"


ASP_RULES = r"""
busy(C) :- crossing(C).
safe(G) :- guide(G), sense(G, S), sense_min(M), S >= M.
valid(C, G) :- busy(C), safe(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CROSSINGS:
        lines.append(asp.fact("crossing", cid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("sense", gid, g.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(crossing=None, guide=None, alpaca_name=None, child_name=None), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible crossing stories:")
        for c, g in asp_valid_combos():
            print(f"  {c:15} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for c, g in valid_combos():
            p = StoryParams(c, g, random.choice(ALPACA_NAMES), random.choice(CHILD_NAMES), seed=base_seed)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.alpaca_name} at {p.crossing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

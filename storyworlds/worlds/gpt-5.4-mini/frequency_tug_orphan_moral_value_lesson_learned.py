#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/frequency_tug_orphan_moral_value_lesson_learned.py
====================================================================================

A standalone story world for a tall-tale-like little domain:

- a child hears a strange frequency in the wind,
- a tugging sound leads them to an orphaned bell, kite, or wagon charm,
- the moral value of patience and kindness matters,
- a lesson learned ends with a rhyme.

The world is deliberately small and state-driven. Physical meters and emotional
memes both change during the story, and the prose is rendered from that state.
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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Tone:
    id: str
    place: str
    opening: str
    moral_value: str
    rhyme: str
    lesson_phrase: str
    ending_image: str

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
class MysteryThing:
    id: str
    label: str
    phrase: str
    kind: str
    can_be_found: bool = True
    can_be_heard: bool = False
    can_be_tugged: bool = False
    can_be_repaired: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["startled"] < THRESHOLD:
            continue
        sig = ("fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    return produced


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tone in TONES:
        for thing_id, thing in THINGS.items():
            for resp_id, resp in RESPONSES.items():
                if thing.can_be_heard and thing.can_be_tugged and resp.sense >= SENSE_MIN:
                    combos.append((tone, thing_id, resp_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def reasonableness_gate(thing: MysteryThing) -> bool:
    return thing.can_be_heard and thing.can_be_tugged and thing.can_be_found


def predict(world: World, thing_id: str) -> dict:
    sim = world.copy()
    thing = sim.get(thing_id)
    thing.meters["tugged"] += 1
    thing.meters["found"] += 1
    child = sim.get("child")
    child.memes["wonder"] += 1
    return {
        "tugged": thing.meters["tugged"] >= THRESHOLD,
        "repair_need": thing.meters["broken"] >= THRESHOLD,
    }


def setup(world: World, tone: Tone, child: Entity, elder: Entity, thing: MysteryThing) -> None:
    child.memes["joy"] += 1
    elder.memes["care"] += 1
    world.say(f"{tone.opening} {child.id} and {elder.id} crossed the dusty yard where {tone.place}.")
    world.say(f"They heard a thin old frequency in the wind, a hum that seemed to call their names.")
    world.say(f"Then came a soft tug from the gatepost, and there sat {thing.phrase}.")


def warn(world: World, elder: Entity, child: Entity, thing: MysteryThing, tone: Tone) -> None:
    pred = predict(world, thing.id)
    elder.memes["moral_value"] += 1
    world.facts["predicted_tugged"] = pred["tugged"]
    world.say(
        f'{elder.id} narrowed {elder.pronoun("possessive")} eyes. '
        f'"A tug on a lonely thing ought to be gentle," {elder.id} said. '
        f'"That little orphan {thing.label} might be waiting for its rightful home."'
    )


def defy(world: World, child: Entity, thing: MysteryThing) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} grinned and said, "I only mean to tug it once and see what it knows."'
    )


def tug_thing(world: World, child: Entity, thing: MysteryThing, response: Response) -> None:
    child.meters["tugged"] += 1
    child.meters["found"] += 1
    thing_ent = world.get(thing.id)
    thing_ent.meters["tugged"] += 1
    thing_ent.meters["found"] += 1
    if thing.can_be_repaired:
        thing_ent.meters["broken"] += 1
    world.say(
        f"{response.text.format(target=thing.label)}"
    )


def repair(world: World, elder: Entity, thing: MysteryThing) -> None:
    if thing.can_be_repaired:
        world.get(thing.id).meters["repaired"] = 1
        elder.memes["pride"] += 1
        world.say(
            f"{elder.id} smiled wide as a barn door and showed {world.get('child').id} "
            f"how to mend the little broken bit with twine and a careful knot."
        )
    else:
        world.say(
            f"{elder.id} tucked the orphan {thing.label} into a pocket of safe keeping "
            f"until the right owner could be found."
        )


def lesson(world: World, child: Entity, elder: Entity, thing: MysteryThing, tone: Tone) -> None:
    child.memes["moral_value"] += 1
    child.memes["lesson_learned"] += 1
    elder.memes["lesson_learned"] += 1
    world.say(
        f'For a spell they stood together, and {elder.id} said, "{tone.lesson_phrase}." '
        f'"Kind hands and patient hearts keep the world in tune."'
    )
    world.say(
        f'{child.id} nodded, feeling the truth of it, and repeated the rhyme: '
        f'"If a thing is small and all alone, ask first before you tug it home."'
    )
    world.say(
        f"In that tall-tale yard, the {tone.rhyme} went round like a bell and "
        f"the orphan thing was treated right at last."
    )


def ending(world: World, child: Entity, elder: Entity, tone: Tone, thing: MysteryThing) -> None:
    world.say(
        f"{tone.ending_image}, and {child.id} walked away lighter in {child.pronoun('possessive')} heart."
    )


def tell(tone: Tone, thing: MysteryThing, response: Response, child_name: str = "Milo",
         child_gender: str = "boy", elder_name: str = "Gran", elder_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    world.add(Entity(id=thing.id, type=thing.kind, label=thing.label))
    setup(world, tone, child, elder, thing)
    world.para()
    warn(world, elder, child, thing, tone)
    defy(world, child, thing)
    world.para()
    tug_thing(world, child, thing, response)
    repair(world, elder, thing)
    lesson(world, child, elder, thing, tone)
    ending(world, child, elder, tone, thing)
    world.facts.update(child=child, elder=elder, thing=thing, tone=tone, response=response,
                       outcome="learned", promised=True)
    return world


TONES = {
    "tall_tale": "the grass leaned like a green sea and the fence posts stood like old sentries",
}


MYSTERY = {
    "orphan_bell": MysteryThing(
        "orphan_bell",
        "orphan bell",
        "an orphan bell with a cracked tongue",
        "thing",
        can_be_found=True,
        can_be_heard=True,
        can_be_tugged=True,
        can_be_repaired=True,
        tags={"orphan", "tug", "frequency"},
    ),
    "orphan_kite": MysteryThing(
        "orphan_kite",
        "orphan kite",
        "an orphan kite snagged on the apple tree",
        "thing",
        can_be_found=True,
        can_be_heard=True,
        can_be_tugged=True,
        can_be_repaired=False,
        tags={"orphan", "tug", "frequency"},
    ),
    "orphan_wagon": MysteryThing(
        "orphan_wagon",
        "orphan wagon",
        "an orphan wagon with a squeaky wheel",
        "thing",
        can_be_found=True,
        can_be_heard=True,
        can_be_tugged=True,
        can_be_repaired=True,
        tags={"orphan", "tug", "frequency"},
    ),
}

THINGS = MYSTERY

RESPONSES = {
    "gentle_pull": Response(
        "gentle_pull", 3, 2,
        "carefully tugged {target} just enough to listen, and a soft chime answered back",
        "yanked at {target} too hard, but only made it wobble in the dust",
        tags={"tug"},
    ),
    "repair_twine": Response(
        "repair_twine", 3, 3,
        "lifted {target}, set it straight, and fixed the wobbly part with twine",
        "tried to fix {target}, but the piece was too far gone for that day",
        tags={"orphan", "moral"},
    ),
    "ask_first": Response(
        "ask_first", 2, 2,
        "called out for the owner, then lifted {target} only after getting a nod",
        "called out, but nobody came, so {target} still waited alone",
        tags={"moral"},
    ),
    "water_bucket": Response(
        "water_bucket", 1, 1,
        "splashed water on {target}",
        "splashed water on {target}",
        tags={"bad"},
    ),
}



@dataclass
class StoryParams:
    tone: str
    thing: str
    response: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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

CURATED = [
    ("tall_tale", "orphan_bell", "gentle_pull"),
    ("tall_tale", "orphan_wagon", "repair_twine"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about frequency, tug, and orphan.")
    ap.add_argument("--tone", choices=TONES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["man", "woman"])
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
    if args.thing and not reasonableness_gate(THINGS[args.thing]):
        raise StoryError("That orphan thing cannot be meaningfully tugged in this world.")
    combos = [
        c for c in valid_combos()
        if (args.tone is None or c[0] == args.tone)
        and (args.thing is None or c[1] == args.thing)
        and (args.response is None or c[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    tone, thing, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    elder_gender = args.elder_gender or rng.choice(["man", "woman"])
    child = args.child or rng.choice(["Milo", "Nia", "Jo", "Bea"])
    elder = args.elder or rng.choice(["Gran", "Uncle Ray", "Aunt June", "Old Pike"])
    return StoryParams(tone, thing, response, child, child_gender, elder, elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the words "frequency", "tug", and "orphan".',
        f"Tell a story where {f['child'].id} hears a strange frequency, follows a tugging sound, and learns how to treat an orphaned thing with care.",
        f'Write a moral story with a rhyme at the end about asking first before you tug a lonely thing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    thing = f["thing"]
    tone = f["tone"]
    return [
        QAItem(
            question="What strange thing did the child hear?",
            answer=f"{child.id} heard a thin frequency in the wind, like a note that wanted to be found. It tugged at the child's attention and led them toward the yard.",
        ),
        QAItem(
            question="Why did the elder warn the child?",
            answer=f"{elder.id} warned {child.id} because the thing looked orphaned and alone. That meant it should be handled gently and checked for its rightful home before anyone tugged it.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{child.id} learned that kindness matters more than hurry. The lesson was to ask first, use gentle hands, and help an orphaned thing instead of grabbing it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a rhyme, a calm repair, and a kinder choice. The orphan thing was treated right, and {child.id} walked away wiser.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frequency?",
            answer="A frequency is how often a sound or wave repeats. In stories, it can be a hum, a pitch, or a steady ringing note.",
        ),
        QAItem(
            question="What does tug mean?",
            answer="To tug means to pull with a quick, small motion. A gentle tug can move something, but a hard tug can damage it.",
        ),
        QAItem(
            question="What does orphan mean?",
            answer="An orphan is someone or something without the home or family that should care for it. In a story, an orphaned thing is lonely and needs careful help.",
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


ASP_RULES = r"""
valid(Tone, Thing, Resp) :- tone(Tone), thing(Thing), response(Resp), tuggable(Thing), hearing(Thing), response_sense(Resp, S), sense_min(M), S >= M.
outcome(learned) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in TONES:
        lines.append(asp.fact("tone", t))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if thing.can_be_heard:
            lines.append(asp.fact("hearing", tid))
        if thing.can_be_tugged:
            lines.append(asp.fact("tuggable", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("response_sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            tone=None, thing=None, response=None, child=None, child_gender=None,
            elder=None, elder_gender=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(TONES[params.tone], THINGS[params.thing], RESPONSES[params.response],
                 params.child, params.child_gender, params.elder, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(t, th, r, "Milo", "boy", "Gran", "woman")) for t, th, r in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

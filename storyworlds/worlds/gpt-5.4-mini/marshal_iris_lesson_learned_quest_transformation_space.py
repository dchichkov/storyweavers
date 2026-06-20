#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marshal_iris_lesson_learned_quest_transformation_space.py
==========================================================================================

A standalone story world for a small space-adventure tale: a young marshal and
Iris take a quest to repair a drifting beacon, learn a lesson about careful
space travel, and end with a transformation that changes how they explore.

The domain is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate for valid story combinations
- a Python/ASP twin for parity checking
- story-grounded and world-knowledge Q&A sets

The seed words are used as story elements:
- marshal
- iris

The narrative instruments are:
- Quest
- Lesson Learned
- Transformation

Style: space adventure.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str
    sky: str
    afford: set[str] = field(default_factory=set)

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
class Quest:
    id: str
    goal: str
    method: str
    risk: str
    ending: str
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
class Artifact:
    id: str
    label: str
    fragile: bool = False
    dangerous: bool = False
    gives_light: bool = False
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
    qa_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ship").meters["drift"] += 1
        out.append("__drift__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ship").meters["drift"] < THRESHOLD:
        return out
    sig = ("fear", "ship")
    if sig not in world.fired:
        world.fired.add(sig)
        for eid in ("marshal", "iris"):
            world.get(eid).memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("wobble", "physical", _r_wobble), Rule("fear", "social", _r_fear)]


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


def predict(world: World, artifact_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(artifact_id), narrate=False)
    return {"drift": sim.get("ship").meters["drift"]}


def _do_action(world: World, artifact: Entity, narrate: bool = True) -> None:
    artifact.meters["wobble"] += 1
    propagate(world, narrate=narrate)


def hazard_ok(q: Quest, art: Artifact) -> bool:
    return q.id == "repair" and art.dangerous


def response_ok(r: Response) -> bool:
    return r.sense >= SENSE_MIN


def severity(delay: int) -> int:
    return 1 + delay


def contained(r: Response, delay: int) -> bool:
    return r.power >= severity(delay)


def tell(setting: Setting, quest: Quest, artifact: Artifact, response: Response,
         marshal_name: str = "Marshal", iris_name: str = "Iris",
         marshal_type: str = "boy", iris_type: str = "girl",
         delay: int = 0, seed: Optional[int] = None) -> World:
    w = World()
    marshal = w.add(Entity("marshal", "character", marshal_type, role="leader"))
    iris = w.add(Entity("iris", "character", iris_type, role="navigator"))
    ship = w.add(Entity("ship", "thing", "ship"))
    beacon = w.add(Entity("beacon", "thing", artifact.label))
    w.facts.update(setting=setting, quest=quest, artifact=artifact, response=response,
                   marshal_name=marshal_name, iris_name=iris_name, delay=delay)
    marshal.memes["bravery"] = 4.0
    iris.memes["care"] = 5.0

    w.say(
        f"On a bright day above the {setting.place}, {marshal_name} and {iris_name} "
        f"floated through space in their little ship. {marshal_name} called himself a marshal, "
        f"and {iris_name} kept the map steady while stars glittered outside the windows."
    )
    w.say(
        f"They had a quest: {quest.goal}. {quest.method} sounded exciting, but the drifting beacon "
        f"near the rim of the station looked risky."
    )
    w.para()
    w.say(
        f"{iris_name} peered ahead and frowned. \"If we bump the beacon, it could wobble the ship,\" "
        f"{iris_name} said. {marshal_name} wanted to rush in anyway."
    )
    if quest.id == "repair":
        _do_action(w, beacon)
        w.say(
            f"{marshal_name} reached out too fast, and the beacon began to shake. The whole ship gave a small lurch."
        )
        w.say(
            f'"{iris_name}!" {marshal_name} cried. "The ship is drifting!"'
        )
        if contained(response, delay):
            w.para()
            beacon.meters["wobble"] = 0.0
            w.get("ship").meters["drift"] = 0.0
            w.say(
                f"Then {iris_name} stayed calm. In one smooth motion {iris_name} {response.text.replace('{artifact}', artifact.label)}."
            )
            w.say(
                f"The wobble stopped, and the ship settled like a feather. After that, {marshal_name} listened first and reached second."
            )
            w.para()
            marshal.memes["lesson"] += 1
            iris.memes["lesson"] += 1
            w.say(
                f"Their lesson learned was simple: in space, the careful choice is the brave choice."
            )
            w.say(
                f"The next day, they returned with {quest.ending}, and the little ship looked different too."
            )
            w.say(
                f"A new guidance light clicked on at the front of the craft, and {marshal_name} and {iris_name} flew on as a steadier team."
            )
        else:
            w.para()
            beacon.meters["wobble"] = 0.0
            w.get("ship").meters["drift"] = 1.0
            w.say(
                f"Then {iris_name} tried to stop it with {response.fail.replace('{artifact}', artifact.label)}, but the drift had already grown too large."
            )
            w.say(
                f"Still, they did the smart thing: they called for help, backed away from the rim, and watched the station crew secure the beacon."
            )
            w.say(
                f"Their lesson learned was the same: rushing in space can turn a small wobble into a bigger problem."
            )
            w.say(
                f"By the end, the ship was safe again, but the lesson stayed bright in their minds like a warning star."
            )
    w.facts.update(outcome="contained" if contained(response, delay) else "burned",
                   ignored=False, rescued=contained(response, delay))
    return w


SETTINGS = {
    "orbital_station": Setting("orbital station", "the orbital station", "bright", {"repair"}),
    "moon_dock": Setting("moon dock", "the moon dock", "silver", {"repair"}),
    "deep_space": Setting("deep_space", "deep space", "dark", {"repair"}),
}

QUESTS = {
    "repair": Quest(
        "repair",
        "repair the drifting beacon",
        "reach out quickly",
        "the beacon could wobble the ship",
        "a glowing guidance light",
        {"repair", "beacon"},
    ),
}

ARTIFACTS = {
    "beacon": Artifact("beacon", "drifting beacon", fragile=True, dangerous=True, tags={"beacon"}),
}

RESPONSES = {
    "seal": Response(
        "seal", 3, 2,
        "sealed the hatch and steadied the control panel",
        "sealed the hatch, but the drift kept tugging the ship",
        "sealed the hatch and steadied the control panel",
        {"help", "repair"},
    ),
    "guide": Response(
        "guide", 3, 3,
        "guided the ship to the beacon and locked it in place",
        "guided the ship too late, and the beacon kept wobbling",
        "guided the ship to the beacon and locked it in place",
        {"help", "repair"},
    ),
    "brace": Response(
        "brace", 2, 1,
        "braced her feet and held the rail while the beacon settled",
        "braced her feet, but the ship had already drifted too far",
        "braced her feet and held the rail while the beacon settled",
        {"help", "repair"},
    ),
}

MARSHAL_NAMES = ["Marshal", "Jory", "Nia", "Nova", "Milo", "Tess"]
IRIS_NAMES = ["Iris", "Aria", "Lumi", "Zed", "Orin", "Pia"]
TRAITS = ["bold", "careful", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for qid in QUESTS:
            for aid in ARTIFACTS:
                if hazard_ok(QUESTS[qid], ARTIFACTS[aid]):
                    out.append((sid, qid, aid))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    artifact: str
    response: str
    marshal_name: str
    iris_name: str
    marshal_type: str
    iris_type: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure story that includes the words "{f["marshal_name"].lower()}" and "{f["iris_name"].lower()}" and ends with a lesson learned.',
        f"Tell a quest story about {f['marshal_name']} and {f['iris_name']} fixing a drifting beacon without losing the ship.",
        f"Write a child-friendly transformation story where a small crew learns to travel more carefully in space.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    outcome = f.get("outcome")
    ans = [
        ("Who are the story about?",
         f"The story is about {f['marshal_name']} and {f['iris_name']}, two tiny space travelers on a quest."),
        ("What was their quest?",
         f"They were trying to {QUESTS[f['quest'].id].goal}."),
        ("What lesson did they learn?",
         "They learned that careful choices are the brave choices in space."),
    ]
    if outcome == "contained":
        ans.append((
            "How did Iris help?",
            f"Iris stayed calm and used the right help to steady the ship. That stopped the wobble before it could grow bigger."
        ))
    return ans


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a marshal?", "A marshal is a person who keeps order or leads a group, like a careful space helper."),
        ("What is an iris?", "Iris is a flower name and also a name people can have. In stories it can be the name of a brave traveler."),
        ("What is a beacon?", "A beacon is a bright light or signal that helps travelers find their way."),
        ("Why are stars useful to space travelers?", "Stars can help travelers know where they are and make the dark sky feel less lonely."),
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
    return "\n".join(lines)


CURATED = [
    StoryParams("orbital_station", "repair", "beacon", "seal", "Marshal", "Iris", "boy", "girl", 0),
    StoryParams("moon_dock", "repair", "beacon", "guide", "Milo", "Iris", "boy", "girl", 1),
    StoryParams("deep_space", "repair", "beacon", "brace", "Nova", "Iris", "girl", "girl", 0),
]

ASP_RULES = r"""
valid(S,Q,A) :- setting(S), quest(Q), artifact(A), hazard_ok(Q,A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, artifact=None, response=None, marshal_name=None, iris_name=None, marshal_type=None, iris_type=None, delay=None, seed=None), random.Random(1)))
        assert sample.story
        print("OK: smoke test generate() produced story text.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with marshal and iris.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--marshal-name")
    ap.add_argument("--iris-name")
    ap.add_argument("--marshal-type", choices=["boy", "girl"])
    ap.add_argument("--iris-type", choices=["boy", "girl"])
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
    if args.response and not response_ok(RESPONSES[args.response]):
        raise StoryError("Chosen response is too weak for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.artifact is None or c[2] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, artifact = rng.choice(combos)
    response = args.response or rng.choice(sorted(RESPONSES))
    marshal_name = args.marshal_name or rng.choice(MARSHAL_NAMES)
    iris_name = args.iris_name or rng.choice([n for n in IRIS_NAMES if n != marshal_name])
    marshal_type = args.marshal_type or rng.choice(["boy", "girl"])
    iris_type = args.iris_type or rng.choice(["boy", "girl"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, quest, artifact, response, marshal_name, iris_name, marshal_type, iris_type, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], ARTIFACTS[params.artifact],
                 RESPONSES[params.response], params.marshal_name, params.iris_name,
                 params.marshal_type, params.iris_type, params.delay, params.seed)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

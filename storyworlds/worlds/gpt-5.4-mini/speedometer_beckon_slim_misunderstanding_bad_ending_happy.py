#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/speedometer_beckon_slim_misunderstanding_bad_ending_happy.py
=============================================================================================

A standalone story world for a small slice-of-life misunderstanding tale:
someone notices a slim car on the road, misreads a beckon, and the speedometer
matters in the turn from bad ending to happy ending.

The world is intentionally tiny and concrete:
- a driver and a passerby
- one car with a speedometer
- one road-side situation where a beckon can be misread
- one misunderstanding path that can become dangerous
- one calm correction path that can end warmly

The seed words are folded into the model:
- speedometer
- beckon
- slim

Features supported in the story space:
- Misunderstanding
- Bad Ending
- Happy Ending

Style:
- Slice of life, child-facing, concrete, state-driven prose.
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
    slim: bool = False
    moving: bool = False
    parked: bool = False

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
class Scene:
    id: str
    place: str
    road: str
    time: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Signal:
    id: str
    label: str
    type: str
    is_beckon: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_alarm(world: World) -> list[str]:
    out = []
    driver = world.entities.get("driver")
    car = world.entities.get("car")
    if not driver or not car:
        return out
    if driver.memes["worry"] >= THRESHOLD and car.meters["rolling"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            driver.memes["fear"] += 1
            out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_scene(scene: Scene) -> bool:
    return True


def speed_risk(scene: Scene, car: Entity) -> bool:
    return scene.keyword in {"road", "crosswalk"} and car.moving


def predict_misunderstanding(world: World, scene: Scene) -> dict:
    sim = world.copy()
    _do_drive(sim, narrate=False)
    return {
        "alarm": sim.get("driver").memes["fear"] >= THRESHOLD,
        "speed": sim.get("car").meters["speed"],
    }


def _do_drive(world: World, narrate: bool = True) -> None:
    car = world.get("car")
    driver = world.get("driver")
    passerby = world.get("passerby")
    car.meters["rolling"] += 1
    car.meters["speed"] += 1
    driver.memes["attention"] += 1
    propagate(world, narrate=narrate)


def start(world: World, scene: Scene, driver: Entity, passerby: Entity, car: Entity) -> None:
    world.say(
        f"On a calm afternoon, {driver.id} was driving along {scene.road} while "
        f"{passerby.id} stood near the curb. {car.label_word.capitalize()} had a "
        f"slim, neat shape, and the speedometer sat bright on the dash."
    )
    world.say(
        f"{driver.id} liked quiet errands like this. {passerby.id} was only trying "
        f"to help, but the little road was easy to misunderstand."
    )


def beckon(world: World, passerby: Entity, driver: Entity, car: Entity) -> None:
    passerby.memes["encouragement"] += 1
    world.say(
        f"{passerby.id} gave a small beckon, as if to say, 'Come a little closer, "
        f"I have room for you to stop.'"
    )
    world.say(
        f"But {driver.id} only saw the hand motion and thought, 'They want me to "
        f"keep going.'"
    )


def misunderstanding(world: World, driver: Entity, passerby: Entity, car: Entity) -> None:
    driver.memes["worry"] += 1
    world.say(
        f"{driver.id} frowned and pressed on. The speedometer climbed, and the car "
        f"moved past {passerby.id} before either of them could speak clearly."
    )


def bad_turn(world: World, driver: Entity, passerby: Entity) -> None:
    driver.memes["fear"] += 1
    passerby.memes["shock"] += 1
    world.say(
        f"That was the bad part of the misunderstanding: {driver.id} thought the "
        f"beckon meant go, but it really meant stop and talk."
    )
    world.say(
        f"The car rolled too far, {passerby.id} had to step back, and the moment "
        f"felt awkward and sad."
    )


def calm_fix(world: World, driver: Entity, passerby: Entity, response: Response) -> None:
    driver.memes["calm"] += 1
    passerby.memes["relief"] += 1
    world.say(
        f"Then {passerby.id} waved again, this time bigger and slower. {driver.id} "
        f"finally understood, slowed down, and pulled over."
    )
    world.say(
        f"{driver.id} did what helped most: {response.text}. The speedometer dropped "
        f"back down, and the road felt safe again."
    )


def happy_end(world: World, driver: Entity, passerby: Entity, scene: Scene) -> None:
    driver.memes["joy"] += 1
    passerby.memes["joy"] += 1
    world.say(
        f"{driver.id} and {passerby.id} laughed at the mix-up, then talked for a "
        f"minute by {scene.place}. The slim car stayed parked, the speedometer was "
        f"quiet, and the afternoon went back to being ordinary and kind."
    )


def rescue_fail(world: World, driver: Entity, passerby: Entity) -> None:
    driver.memes["fear"] += 1
    passerby.memes["sad"] += 1
    world.say(
        f"{driver.id} did not slow in time. The car moved past the turn, the little "
        f"beckon was lost, and both people felt the sting of the mistake."
    )
    world.say(
        f"Nothing terrible happened, but the day ended in a bad silence, with no "
        f"chance to fix the misunderstanding right away."
    )


def tell(scene: Scene, signal: Signal, response: Response, *, happy: bool = True,
         driver_name: str = "Ari", passerby_name: str = "Mina",
         driver_gender: str = "boy", passerby_gender: str = "girl") -> World:
    world = World()
    driver = world.add(Entity(id="driver", kind="character", type=driver_gender,
                              label=driver_name, role="driver"))
    passerby = world.add(Entity(id="passerby", kind="character", type=passerby_gender,
                                label=passerby_name, role="passerby"))
    car = world.add(Entity(id="car", kind="thing", type="car", label="the car"))
    car.moving = True
    car.slim = True
    car.meters["speedometer"] = 1.0
    world.facts["scene"] = scene
    world.facts["signal"] = signal
    world.facts["response"] = response
    world.facts["driver"] = driver
    world.facts["passerby"] = passerby
    world.facts["car"] = car

    start(world, scene, driver, passerby, car)
    world.para()
    beckon(world, passerby, driver, car)
    misunderstanding(world, driver, passerby, car)

    if happy:
        world.para()
        calm_fix(world, driver, passerby, response)
        happy_end(world, driver, passerby, scene)
        outcome = "happy"
    else:
        world.para()
        bad_turn(world, driver, passerby)
        rescue_fail(world, driver, passerby)
        outcome = "bad"

    world.facts["outcome"] = outcome
    world.facts["speedometer"] = car.meters["speedometer"]
    return world


SCENES = {
    "crosswalk": Scene("crosswalk", "the corner store", "the crosswalk", "late morning", "clear", "road", {"road"}),
    "parking_lot": Scene("parking_lot", "the grocery lot", "the parking lot", "afternoon", "clear", "road", {"road"}),
    "driveway": Scene("driveway", "the apartment driveway", "the driveway", "evening", "soft", "road", {"road"}),
}

SIGNALS = {
    "beckon": Signal("beckon", "beckon", "hand motion", is_beckon=True, tags={"beckon"}),
}

RESPONSES = {
    "pull_over": Response(
        "pull_over", 3, 3,
        "pulled over gently and opened the window so they could talk",
        "pulled over too late, after the moment had already passed",
        "pulled over and opened the window to talk",
        tags={"calm"}),
    "wave_back": Response(
        "wave_back", 2, 2,
        "slowed down, waved back, and waited for a clearer sign",
        "waved back, but kept rolling right past",
        "slowed down and waved back",
        tags={"calm"}),
    "stop_and_talk": Response(
        "stop_and_talk", 3, 3,
        "stopped beside the curb and spoke kindly with the person there",
        "stopped in the wrong spot, too far away to understand anything",
        "stopped beside the curb and talked kindly",
        tags={"calm"}),
}



@dataclass
class StoryParams:
    scene: str
    signal: str
    response: str
    driver_name: str
    driver_gender: str
    passerby_name: str
    passerby_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    StoryParams("crosswalk", "beckon", "pull_over", "Ari", "boy", "Mina", "girl", seed=11),
    StoryParams("parking_lot", "beckon", "wave_back", "June", "girl", "Owen", "boy", seed=22),
    StoryParams("driveway", "beckon", "stop_and_talk", "Leo", "boy", "Ivy", "girl", seed=33),
]



KNOWLEDGE = {
    "speedometer": [("What is a speedometer?", "A speedometer is a dial in a car that shows how fast the car is moving.")],
    "beckon": [("What does it mean to beckon?", "To beckon is to wave someone closer with your hand.")],
    "slim": [("What does slim mean?", "Slim means thin and neat, not wide or bulky.")],
    "calm": [("Why is it good to slow down before talking?", "Slowing down gives people time to understand each other and stay safe.")],
    "road": [("Why should drivers be careful near people on the road?", "People and cars need room, so careful driving helps everyone stay safe.")],
}
KNOWLEDGE_ORDER = ["speedometer", "beckon", "slim", "calm", "road"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for signal in SIGNALS:
            for response in RESPONSES:
                combos.append((scene, signal, response))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, sig, resp = f["scene"], f["signal"], f["response"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "speedometer", "beckon", and "slim".',
        f"Tell a small misunderstanding story where {f['driver'].label} misreads a {sig.label} from {f['passerby'].label} near {s.place}, then fixes it calmly.",
        f"Write a child-facing story about a slim car, a beckon, and a speedometer, ending with a happy or a bad turn.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    driver: Entity = f["driver"]
    passerby: Entity = f["passerby"]
    response: Response = f["response"]
    scene: Scene = f["scene"]
    qa = [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {driver.label} and {passerby.label}, two people sharing an ordinary road-side moment."
        ),
        QAItem(
            question="What did the passerby do?",
            answer=f"{passerby.label} gave a beckon to try to get {driver.label} to understand and stop near {scene.place}."
        ),
        QAItem(
            question="What happened with the speedometer?",
            answer=f"The speedometer climbed when the car kept moving, and it dropped again when {driver.label} slowed down."
        ),
    ]
    if f["outcome"] == "happy":
        qa.append(QAItem(
            question="How did they fix the misunderstanding?",
            answer=f"{driver.label} slowed down and used a calm response, so the beckon became clear and the car could pull over safely. Then both people laughed because the mistake was small and easy to repair."
        ))
        qa.append(QAItem(
            question="How did the story end?",
            answer="It ended happily. The car stayed slim and parked, the speedometer went quiet, and the two people were smiling by the roadside."
        ))
    else:
        qa.append(QAItem(
            question="Why was the ending bad?",
            answer=f"{driver.label} did not slow down in time, so the beckon was missed and the chance to talk was gone. Nobody got hurt, but the moment ended in a sad silence."
        ))
        qa.append(QAItem(
            question="Could they fix it right away?",
            answer="No. The misunderstanding was already past them, so the day ended badly even though it was a small, ordinary mistake."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"speedometer", "beckon", "slim", "road", "calm"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
        if e.slim:
            bits.append("slim=True")
        if e.moving:
            bits.append("moving=True")
        if e.parked:
            bits.append("parked=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
happy :- response(R), sense(R, S), sense_min(M), S >= M.
bad :- signal(beckon), scene(Scene), response(R), sense(R, S), S < 2.
valid(Scene, beckon, R) :- scene(Scene), response(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for sig in SIGNALS:
        lines.append(asp.fact("signal", sig))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
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
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: smoke test and ASP parity passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a slim car, a beckon, and a speedometer misunderstanding."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--driver-name")
    ap.add_argument("--passerby-name")
    ap.add_argument("--driver-gender", choices=["boy", "girl"])
    ap.add_argument("--passerby-gender", choices=["boy", "girl"])
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
    scene = args.scene or rng.choice(list(SCENES))
    response = args.response or rng.choice(list(RESPONSES))
    driver_gender = args.driver_gender or rng.choice(["boy", "girl"])
    passerby_gender = args.passerby_gender or ("girl" if driver_gender == "boy" else "boy")
    driver_name = args.driver_name or rng.choice(["Ari", "June", "Milo", "Nina", "Theo", "Luna"])
    passerby_name = args.passerby_name or rng.choice(["Mina", "Owen", "Iris", "Kai", "Ruby", "Noah"])
    return StoryParams(scene, "beckon", response, driver_name, driver_gender, passerby_name, passerby_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], SIGNALS[params.signal], RESPONSES[params.response],
                 happy=(params.response != "wave_back" or params.scene != "driveway"),
                 driver_name=params.driver_name, passerby_name=params.passerby_name,
                 driver_gender=params.driver_gender, passerby_gender=params.passerby_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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

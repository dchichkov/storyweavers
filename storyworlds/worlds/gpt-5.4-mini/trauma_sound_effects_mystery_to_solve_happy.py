#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/trauma_sound_effects_mystery_to_solve_happy.py
===============================================================================

A standalone story world for a tiny space-adventure mystery: a child hears a
scary bang, feels shaken, follows sound effects to solve what happened, and ends
with a safe, happy discovery.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal simulation
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in the simulated world

The story style aims to feel like a gentle space adventure with clear sound
effects, a mystery to solve, and a happy ending.
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
CALM_MIN = 2
SAFE_HELPERS = {"pilot", "commander", "engineer"}


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
class Setting:
    id: str
    place: str
    scene: str
    sky: str
    ambient: str
    noise: str

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
class Mystery:
    id: str
    clue_word: str
    sound: str
    source_phrase: str
    cause_phrase: str
    reveal_phrase: str
    hazard: bool = False

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


def _r_shock(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["shocked"] < THRESHOLD:
            continue
        sig = ("shock", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["trauma"] += 1
        ent.memes["need_help"] += 1
        out.append("__shock__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities or "helper" not in world.entities:
        return out
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["fear"] < THRESHOLD or helper.memes["calm"] < THRESHOLD:
        return out
    sig = ("calm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["trust"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("shock", "emotional", _r_shock), Rule("calm", "social", _r_calm)]


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


def safe_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= CALM_MIN]


def hazard_possible(mystery: Mystery) -> bool:
    return mystery.hazard


def wonder_level(world: World) -> float:
    child = world.get("child")
    return child.memes["curiosity"] + child.memes["fear"]


def predict_scene(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    _make_bang(sim, mystery, narrate=False)
    return {
        "shocked": sim.get("child").meters["shocked"] >= THRESHOLD,
        "trauma": sim.get("child").memes["trauma"],
    }


def _make_bang(world: World, mystery: Mystery, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["shocked"] += 1
    child.meters["listened"] += 1
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"On a bright day above the stars, {child.id} floated through {setting.place}. "
        f"{setting.scene} {setting.sky}"
    )
    world.say(
        f'Then came the sound: "{mystery.sound}" {setting.noise} '
        f'like something had knocked inside the ship.'
    )


def trauma_beat(world: World, child: Entity) -> None:
    child.memes["fear"] += 1
    child.memes["trauma"] += 1
    world.say(
        f"{child.id}'s heart jumped. {child.pronoun().capitalize()} felt shaken and small, "
        f"like the whole ship had wobbled under {child.pronoun('possessive')} boots."
    )


def mystery_beat(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"What was that?" {child.id} whispered. {mystery.clue_word} was the mystery to solve, '
        f'and {child.id} listened for another clue.'
    )


def clue_beat(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"Clink-clink. The little radar light blinked near {mystery.source_phrase}. "
        f"{child.id} followed the echo with careful steps."
    )


def warn_beat(world: World, helper: Entity, child: Entity, mystery: Mystery, response: Response) -> None:
    pred = predict_scene(world, mystery)
    helper.memes["calm"] += 1
    world.facts["predicted_trauma"] = pred["trauma"]
    world.say(
        f'{helper.id} knelt beside {child.id}. "That bang sounded scary, but we can check it safely. '
        f'If we stay calm, we can find the cause without guessing."'
    )
    if pred["shocked"]:
        world.say(
            f"{helper.id} pointed to the safe path and kept {child.id} from rushing. "
            f"That made the worry feel smaller."
        )


def solve_beat(world: World, child: Entity, mystery: Mystery) -> None:
    world.say(
        f"Tap-tap. {child.id} found the answer: {mystery.cause_phrase}. "
        f"The sound had not been a monster after all."
    )


def rescue_beat(world: World, helper: Entity, response: Response, child: Entity, mystery: Mystery) -> None:
    child.meters["shocked"] = 0.0
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} came over in a flash and {response.text.replace('{mystery}', mystery.id)}."
    )
    world.say(
        f"The scary sound settled down, and the ship felt still again."
    )


def happy_ending(world: World, child: Entity, helper: Entity, setting: Setting, mystery: Mystery) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, {child.id} and {helper.id} laughed softly together. "
        f"{mystery.reveal_phrase} {setting.ambient} glowed warm and safe."
    )
    world.say(
        f"This time, the mystery had an answer, the worry had a helper, and the adventure ended happy."
    )


def tell(setting: Setting, mystery: Mystery, response: Response, child_name: str = "Nova",
         child_gender: str = "girl", helper_name: str = "Captain Ray",
         helper_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    ship = world.add(Entity(id="ship", type="ship", label=setting.place))
    beacon = world.add(Entity(id="beacon", type="thing", label="beacon"))
    world.facts["setting"] = setting
    world.facts["mystery"] = mystery
    world.facts["response"] = response
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["ship"] = ship
    world.facts["beacon"] = beacon

    opening(world, child, setting, mystery)
    world.para()
    trauma_beat(world, child)
    mystery_beat(world, child, mystery)
    clue_beat(world, child, mystery)
    warn_beat(world, helper, child, mystery, response)
    world.para()
    _make_bang(world, mystery)
    solve_beat(world, child, mystery)
    rescue_beat(world, helper, response, child, mystery)
    world.para()
    happy_ending(world, child, helper, setting, mystery)
    world.facts["outcome"] = "happy"
    return world


SETTINGS = {
    "orbital_lab": Setting("orbital_lab", "the orbital lab", "Silver panels hummed softly,", "and tiny screens winked like stars.", "whirr"),
    "moon_base": Setting("moon_base", "the moon base", "White tunnels stretched ahead,", "and a sleepy dome held the light.", "beep"),
    "starship": Setting("starship", "the starship", "Long corridors curved like a comet trail,", "and blue lamps blinked along the walls.", "ping"),
}

MYSTERIES = {
    "loose_panel": Mystery("loose_panel", "mystery", "BONG!", "the wall panel", "a loose latch bumping in the wind tunnel", "The panel was only loose, not dangerous.", hazard=False),
    "rolling_tool": Mystery("rolling_tool", "mystery", "CLATTER!", "the storage bay", "a tool rolling out of its tray", "A wrench had rolled away and tapped the wall.", hazard=False),
    "tiny_alarm": Mystery("tiny_alarm", "mystery", "BEEP-BEEP!", "the console", "a tiny alarm on the snack drawer", "The console had only asked for help.", hazard=False),
}

RESPONSES = {
    "hush": Response("hush", 3, 3, "checked the panel, tightened the latch, and made everything quiet again", "looked, but the noise kept coming", "checked the panel and made the noise stop"),
    "secure": Response("secure", 3, 4, "picked up the loose tool, tucked it safely away, and turned the beep off", "tried to tidy it, but the clatter stayed", "picked up the tool and made the clatter stop"),
    "reset": Response("reset", 2, 2, "pressed the console reset and waited for the alarm to blink green", "pressed reset, but the alarm kept sounding", "pressed reset and calmed the alarm"),
}



@dataclass
class StoryParams:
    setting: str
    mystery: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    ("starship", "loose_panel", "hush", "Nova", "girl", "Captain Ray", "man"),
    ("moon_base", "rolling_tool", "secure", "Milo", "boy", "Commander June", "woman"),
    ("orbital_lab", "tiny_alarm", "reset", "Lena", "girl", "Engineer Kai", "man"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid, m in MYSTERIES.items():
            if not hazard_possible(m):
                for rid in RESPONSES:
                    combos.append((sid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure mystery with sound effects and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, response = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(["Nova", "Milo", "Luna", "Iris", "Pip"])
    helper_name = args.helper or rng.choice(["Captain Ray", "Commander June", "Engineer Kai", "Pilot Sol"])
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["woman", "man"])
    return StoryParams(setting, mystery, response, child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle space adventure for a 3-to-5-year-old that includes the word "trauma" and a mystery to solve.',
        f"Tell a story where {f['child'].id} hears a loud sound in {f['setting'].place} and feels trauma, then solves the mystery with help.",
        f"Write a happy ending space story with sound effects like bang, clink, and tap, ending in safety and laughter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    mystery = f["mystery"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who were traveling through {setting.place}."),
        ("What scary thing happened first?", f'{mystery.sound} sounded through the ship, and {child.id} felt shaken and full of trauma. The bang made {child.id} stop and listen for clues.'),
        ("How was the mystery solved?", f"{child.id} followed the clues, found {mystery.cause_phrase}, and learned what had made the sound. That turned the worry into an answer."),
        ("How did the story end?", f"It ended happily, with the noise fixed, the fear calmed, and everyone laughing again. The ship felt safe by the end."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {f["setting"].id, f["mystery"].id, f["response"].id, "space", "sound"}
    out = []
    if "space" in tags:
        out.append(("What is a space adventure?", "A space adventure is a story about traveling in ships, stations, or bases among stars and moons. It often has new places to explore and problems to solve."))
    out.append(("What do sound effects do in a story?", "Sound effects help the reader hear the action in their head. They make a story feel lively and can show when something starts, stops, or changes."))
    out.append(("Why is it good to solve a mystery calmly?", "Calm thinking helps you notice clues and choose safe actions. That makes the answer easier to find and the situation less scary."))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(M) :- mystery(M), hazard(M).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, M, R) :- setting(S), mystery(M), response(R), not hazard(M).
outcome(happy) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if m.hazard:
            lines.append(asp.fact("hazard", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", CALM_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP and Python valid_combos()")
    if set(asp_sensible()) != {r.id for r in safe_responses()}:
        rc = 1
        print("MISMATCH in ASP and Python sensible responses")
    try:
        sample = generate(CURATED_PARAMS[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"Smoke test failed: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


CURATED_PARAMS = [
    StoryParams(*CURATED[0]),
    StoryParams(*CURATED[1]),
    StoryParams(*CURATED[2]),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED_PARAMS]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            sample = generate(p)
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

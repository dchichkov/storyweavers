#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/west_cork_cautionary_sound_effects_dialogue_space.py
====================================================================================

A standalone storyworld for a tiny space-adventure cautionary tale:
a child astronaut hears a strange sound in the west corridor of a ship,
tries something curious with a cork seal, gets a small leak warning, and a
calm grown-up fixes the problem while explaining why the cork must stay in place.

The world is intentionally small and constraint-checked. It models:
- typed entities with physical meters and emotional memes,
- a forward-chained rule engine,
- a reasonableness gate,
- an inline ASP twin,
- generated prompts and two QA sets based on world state.

Run:
    python storyworlds/worlds/gpt-5.4-mini/west_cork_cautionary_sound_effects_dialogue_space.py
    python storyworlds/worlds/gpt-5.4-mini/west_cork_cautionary_sound_effects_dialogue_space.py --verify
    python storyworlds/worlds/gpt-5.4-mini/west_cork_cautionary_sound_effects_dialogue_space.py --qa --json
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
SOUND_MIN = 2


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
    leak_prone: bool = False
    plugs_holes: bool = False
    safe_tool: bool = False

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
    label: str
    west_place: str
    sound: str
    sky: str
    cue: str

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
class Hazard:
    id: str
    label: str
    trigger: str
    where: str
    sound: str
    risk: str
    makes_leak: bool = True

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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_leak(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    for e in list(world.entities.values()):
        if e.meters["leak"] < THRESHOLD:
            continue
        sig = ("leak", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ship:
            ship.meters["risk"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["worry"] += 1
        out.append("__leak__")
    return out


CAUSAL_RULES = [Rule("leak", "physical", _r_leak)]


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


def leak_risk(hazard: Hazard, setting: Setting) -> bool:
    return hazard.makes_leak and "west" in setting.id and "seal" in hazard.label


def contains(response: Response, severity: int) -> bool:
    return response.power >= severity


def severity(delay: int) -> int:
    return 1 + delay


def predict_leak(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get("cork").meters["leak"] += 1
    propagate(sim, narrate=False)
    return {"risk": sim.get("ship").meters["risk"], "leak": sim.get("cork").meters["leak"] >= THRESHOLD}


def do_tap(world: World, hazard: Hazard) -> None:
    world.get("cork").meters["leak"] += 1
    propagate(world, narrate=False)
    world.say(f"{hazard.sound} went the tiny seal as it loosened.")


def rescue(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    world.get("cork").meters["leak"] = 0.0
    world.get("ship").meters["risk"] = 0.0
    body = response.text.replace("{hazard}", hazard.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say("The little leak stopped at once, and the corridor grew quiet again.")


def rescue_fail(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    world.get("ship").meters["risk"] += 1
    body = response.fail.replace("{hazard}", hazard.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say("The leak kept whispering out into the ship.")


def lesson(world: World, parent: Entity, kid: Entity, hazard: Hazard) -> None:
    kid.memes["lesson"] += 1
    kid.memes["relief"] += 1
    world.say("For a moment, nobody talked.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside {kid.id} and said, "
        f"\"The cork is a seal, not a toy. If you hear a warning sound, call me.\""
    )
    world.say(f"\"I will,\" whispered {kid.id}.")
    world.say("The child nodded and kept both hands away from the hatch.")


def ending(world: World, parent: Entity, kid: Entity, setting: Setting) -> None:
    kid.memes["joy"] += 1
    world.say(
        f"The next watch, {parent.label_word.capitalize()} showed {kid.id} how to "
        f"check the hatch from the west side of the ship without touching the seal."
    )
    world.say(
        f"Together they watched the stars slide past the west window, safe and calm."
    )


def tell(setting: Setting, hazard: Hazard, response: Response,
         kid_name: str = "Mila", kid_gender: str = "girl",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    kid = world.add(Entity(id=kid_name, kind="character", type=kid_gender, role="child",
                           traits=["curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    cork = world.add(Entity(id="cork", kind="thing", type="seal", label="the cork seal",
                            leak_prone=True))
    safe = world.add(Entity(id="patch", kind="thing", type="tool", label="a patch kit",
                            plugs_holes=True, safe_tool=True))

    world.say(
        f"On a bright day in space, {kid.id} and {parent.label_word} were on {setting.label}."
    )
    world.say(
        f"{setting.cue} {setting.sky} {setting.sound} drifted through the corridor, "
        f"and everyone looked toward the west."
    )
    world.say(
        f"{kid.id} saw {hazard.label} near {hazard.where} and said, "
        f"\"Look, {hazard.trigger}!\""
    )

    world.para()
    pred = predict_leak(world, hazard)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["delay"] = delay
    world.say(f"{kid.id} leaned closer to the cork seal, and the warning sound grew louder.")
    do_tap(world, hazard)

    if contains(response, severity(delay)):
        world.para()
        rescue(world, parent, response, hazard)
        lesson(world, parent, kid, hazard)
        world.para()
        ending(world, parent, kid, setting)
        outcome = "contained"
    else:
        world.para()
        rescue_fail(world, parent, response, hazard)
        world.say("The crew had to back away and call for help before the leak spread farther.")
        lesson(world, parent, kid, hazard)
        outcome = "warned"

    world.facts.update(
        kid=kid, parent=parent, ship=ship, cork=cork, safe=safe,
        setting=setting, hazard=hazard, response=response, outcome=outcome
    )
    return world


SETTINGS = {
    "west_corridor": Setting("west_corridor", "the west corridor", "west",
                             "hiss-hiss", "The blue lights hummed softly.",
                             "A thin echo"),
    "west_window": Setting("west_window", "the west window", "west",
                           "whirr-whirr", "The stars winked back.",
                           "A low warning"),
}

HAZARDS = {
    "cork_seal": Hazard("cork_seal", "the cork seal", "a loose fitting", "the hatch",
                        "hiss-hiss", "leak"),
    "cargo_port": Hazard("cargo_port", "the cargo port", "a tiny crack", "the port wall",
                         "whisper-whisper", "leak"),
}

RESPONSES = {
    "patch_kit": Response("patch_kit", 3, 3,
                          "used the patch kit to seal the opening",
                          "tried to use the patch kit, but the leak was already bigger than the patch",
                          "sealed the opening with the patch kit"),
    "call_crew": Response("call_crew", 3, 2,
                          "called the crew and brought over the right tools",
                          "called the crew, but the leak had already grown too much for a quick fix",
                          "called the crew for help"),
    "glove_press": Response("glove_press", 2, 2,
                            "pressed a gloved hand over the opening long enough to stop the leak",
                            "pressed down, but the leak pushed right through",
                            "pressed the leak closed with a gloved hand"),
    "paper_towel": Response("paper_towel", 1, 1,
                            "used a paper towel and hoped it would help",
                            "used a paper towel, but it soaked through at once",
                            "used a paper towel"),
}

KID_NAMES = ["Mila", "Nora", "Theo", "Finn", "Zoe", "Ari"]
TRAITS = ["curious", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            if leak_risk(hazard, setting):
                combos.append((sid, hid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    hazard: str
    response: str
    kid: str
    kid_gender: str
    parent: str
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
        f'Write a space-adventure cautionary story that includes the words "west" and "{f["hazard"].label_word if hasattr(f["hazard"], "label_word") else f["hazard"].label}".',
        f"Tell a short dialogue story set on {f['setting'].label} where {f['kid'].id} hears a warning sound from the west and gets told not to touch the cork seal.",
        "Write a child-friendly space story with sound effects, a calm warning, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, parent, hazard, setting = f["kid"], f["parent"], f["hazard"], f["setting"]
    out = [
        QAItem("Who is the story about?", f"It is about {kid.id} and {parent.label_word} on {setting.label}. They were near the west side of the ship when the warning sound began."),
        QAItem("What did the child hear?", f"{kid.id} heard a warning sound near the west corridor. It was the kind of sound that meant something needed careful help, not curious fingers."),
    ]
    if f["outcome"] == "contained":
        out.append(QAItem("How was the problem fixed?", f"{parent.label_word.capitalize()} sealed the opening and kept the leak from spreading. That was the safest way because the cork stayed where it belonged."))
    else:
        out.append(QAItem("What did the crew do?", f"The crew backed away and called for help, because the leak was too much for a fast fix. That kept everyone safe while the adults handled it."))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a cork do?", "A cork can work like a seal or stopper. It helps keep air or liquid from slipping through an opening."),
        QAItem("Why is a warning sound useful?", "A warning sound tells people to slow down and pay attention. It can help them notice danger before it gets bigger."),
        QAItem("What should you do if something in space starts leaking?", "You should move back, call a grown-up or crew member, and use the right tool. That is safer than touching it alone."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    lines += ["", "== (3) World knowledge =="]
    for item in sample.world_qa:
        lines += [f"Q: {item.question}", f"A: {item.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.leak_prone:
            bits.append("leak_prone")
        if e.safe_tool:
            bits.append("safe_tool")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("west_corridor", "cork_seal", "patch_kit", "Mila", "girl", "mother", 0),
    StoryParams("west_window", "cargo_port", "call_crew", "Theo", "boy", "father", 1),
    StoryParams("west_corridor", "cargo_port", "glove_press", "Nora", "girl", "mother", 0),
]


ASP_RULES = r"""
hazard(F) :- hazard(F, _).
valid(S, H, R) :- setting(S), hazard(H), response(R), compatible(S, H).
outcome(contained) :- chosen_response(R), resp_power(R, P), severity(D), P >= D.
outcome(warned) :- chosen_response(R), resp_power(R, P), severity(D), P < D.
compatible(S, H) :- westish(S), leakish(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("westish", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("leakish", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("resp_power", rid, r.power))
    lines.append(asp.fact("sound_min", SOUND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_response", params.response), asp.fact("severity", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary storyworld with dialogue and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--kid")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.setting and args.hazard and not leak_risk(HAZARDS[args.hazard], SETTINGS[args.setting]):
        raise StoryError("No story: that hazard and setting do not make a reasonable leak risk.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    kid = args.kid or rng.choice([n for n in KID_NAMES if True])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, hazard, response, kid, kid_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.kid, params.kid_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(x.question, x.answer) for x in story_qa(world)]],
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
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mar_panel_cautionary_sound_effects_space_adventure.py
======================================================================================

A standalone tiny storyworld for a Space Adventure cautionary tale with sound
effects.  The story is built from a small simulation: a curious child aboard a
spaceship notices a glowing panel, a cautious friend warns about it, a risky
button press may trigger a loud ship alarm, and a careful adult fixes the problem
with a calm reset and a safer job for the children.

Seed words and style anchors:
- words: mar, panel
- features: cautionary, sound effects
- style: space adventure
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Panel:
    id: str
    label: str
    risky: bool = True
    alarmed: bool = False
    resettable: bool = True

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


@dataclass
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
@dataclass
class StoryParams:
    mar_name: str
    friend_name: str
    captain_name: str
    panel: str
    response: str
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


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_alarm(world: World) -> list[str]:
    out = []
    p = world.get("panel")
    if p.meters["pressed"] < THRESHOLD or p.meters["alarm"] >= THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    p.meters["alarm"] += 1
    world.get("ship").meters["danger"] += 1
    for eid in ("mar", "friend"):
        world.get(eid).memes["fear"] += 1
    out.append("__alarm__")
    return out


RULES = [Rule("alarm", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
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


def is_valid(panel: Panel, response: Response) -> bool:
    return panel.risky and response.sense >= SENSE_MIN


def ship_severity(delay: int) -> int:
    return 1 + delay


def contained(response: Response, delay: int) -> bool:
    return response.power >= ship_severity(delay)


def _press_panel(world: World, narrate: bool = True) -> None:
    panel = world.get("panel")
    panel.meters["pressed"] += 1
    propagate(world, narrate=narrate)


def predict_alarm(world: World) -> bool:
    sim = world.copy()
    _press_panel(sim, narrate=False)
    return sim.get("panel").meters["alarm"] >= THRESHOLD


def setup(world: World, mar: Entity, friend: Entity, captain: Entity) -> None:
    mar.memes["curiosity"] += 1
    friend.memes["care"] += 1
    world.say(
        f"On the starship {mar.id} and {friend.id} floated past a glowing {world.get('panel').label_word}."
    )
    world.say(
        f"The little ship hummed with a soft {SFX['hum']}, and the corridor lights blinked {SFX['blink']}."
    )
    world.say(
        f'"{mar.id}, stay with me," {friend.id} said. "{captain.label_word.capitalize()} said that {world.get("panel").label_word} is not for playing."'
    )


def tempt(world: World, mar: Entity) -> None:
    mar.memes["bravado"] += 1
    world.say(
        f'{mar.id} leaned closer. "{SFX["tap"]} {SFX["tap"]} What does this {world.get("panel").label_word} do?"'
    )
    world.say("The tiny lights on it pulsed like a secret map to the stars.")


def warn(world: World, friend: Entity, mar: Entity) -> None:
    pred = predict_alarm(world)
    friend.memes["caution"] += 1
    if pred:
        world.say(
            f'"No," {friend.id} said quickly. "If you press that {world.get("panel").label_word}, the ship will go {SFX["beep"]} and the alarm will scream."'
        )
    else:
        world.say(
            f'"No," {friend.id} said. "That {world.get("panel").label_word} is for grown-ups, not explorers."'
        )


def defy(world: World, mar: Entity) -> None:
    mar.memes["defiance"] += 1
    world.say(f'"I just want to see," {mar.id} said, and pressed the {world.get("panel").label_word}.')


def rescue(world: World, captain: Entity, response: Response) -> None:
    panel = world.get("panel")
    panel.meters["pressed"] = 0
    panel.meters["alarm"] = 0
    world.get("ship").meters["danger"] = 0
    world.say(
        f"{captain.label_word.capitalize()} came in at once and {response.text}."
    )
    world.say(
        f"The alarm stopped with a final {SFX['stop']}, and the corridor went quiet again."
    )


def rescue_fail(world: World, captain: Entity, response: Response) -> None:
    world.get("ship").meters["danger"] += 1
    world.say(
        f"{captain.label_word.capitalize()} came running and {response.fail}."
    )
    world.say(
        f"The ship kept hollering {SFX['alarm']}, and the red lights spun around the hallway."
    )


def lesson(world: World, captain: Entity, mar: Entity, friend: Entity) -> None:
    mar.memes["fear"] += 1
    friend.memes["relief"] += 1
    mar.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {captain.label_word.capitalize()} knelt beside them. "
        f'"Thank you for calling me," {captain.pronoun()} said. '
        f'"Buttons like that are not toys. A ship can get dangerous fast."'
    )
    world.say(f'"We promise," whispered {mar.id} and {friend.id}.')
    world.say(
        f"After that, the {world.get('panel').label_word} stayed quiet and the children kept to the star charts."
    )


def safe_job(world: World, mar: Entity, friend: Entity, captain: Entity) -> None:
    world.say(
        f"The next day, {captain.label_word.capitalize()} gave them a safer job: counting stars on the map and checking the navigation lights."
    )
    world.say(
        f'{mar.id} traced a bright route with {SFX["swish"]}, and {friend.id} watched the tiny blinking dots.'
    )
    world.say(
        f'This time the adventure stayed calm, and the ship slid on through space with a soft {SFX["hum"]}.'
    )


def tell(params: StoryParams) -> World:
    world = World()
    mar = world.add(Entity(id="mar", kind="character", type="girl", role="instigator"))
    friend = world.add(Entity(id="friend", kind="character", type="boy", role="cautioner"))
    captain = world.add(Entity(id="captain", kind="character", type="adult", role="parent", label=params.captain_name))
    panel = world.add(Entity(id="panel", type="panel", label="panel"))
    ship = world.add(Entity(id="ship", type="ship", label="starship"))

    setup(world, mar, friend, captain)
    world.para()
    tempt(world, mar)
    warn(world, friend, mar)
    world.para()
    if params.delay <= 0:
        defy(world, mar)
        _press_panel(world)
        world.say(f"The {world.get('panel').label_word} flashed {SFX['zap']}, and the whole hallway went bright red.")
        world.para()
        if contained(RESPONSES[params.response], params.delay):
            rescue(world, captain, RESPONSES[params.response])
            lesson(world, captain, mar, friend)
            world.para()
            safe_job(world, mar, friend, captain)
            outcome = "contained"
        else:
            rescue_fail(world, captain, RESPONSES[params.response])
            world.say("The ship had to slow down until the trouble was under control.")
            lesson(world, captain, mar, friend)
            outcome = "burned"
    else:
        mar.memes["bravado"] += 0.5
        friend.memes["caution"] += 1
        world.say(f"{friend.id} took one more look and {SFX['pause']} shook {friend.pronoun('possessive')} head.")
        world.say(
            f'{mar.id} stopped, thought about the warning, and let the {world.get("panel").label_word} be.'
        )
        world.para()
        safe_job(world, mar, friend, captain)
        outcome = "averted"

    world.facts.update(
        mar=mar,
        friend=friend,
        captain=captain,
        panel=panel,
        ship=ship,
        response=RESPONSES[params.response],
        outcome=outcome,
    )
    return world


THEMES = {"space": "space"}
SFX = {
    "hum": "hummmm",
    "blink": "blink-blink",
    "tap": "tap-tap",
    "beep": "beep-beep",
    "alarm": "WEE-OOO WEE-OOO",
    "zap": "zrrt!",
    "stop": "click.",
    "swish": "swish",
    "pause": "...",
}


RESPONSES = {
    "reset": Response("reset", 3, 2, "hit the reset switch and brought the panel back to calm lights", "could not calm the panel down", "hit the reset switch"),
    "shield": Response("shield", 2, 1, "closed the safety cover and silenced the warning lights", "could not close the cover in time", "closed the safety cover"),
    "crew_call": Response("crew_call", 3, 3, "called the crew and they fixed the panel right away", "called for help, but the crew could not reach the panel soon enough", "called the crew"),
    "tape": Response("tape", 1, 1, "stuck tape over the panel, which did not really help", "stuck tape over the panel, but the alarm kept going", "stuck tape over the panel"),
}


CURATED = [
    StoryParams("Mar", "Pip", "Captain Raya", "panel", "reset", 0),
    StoryParams("Mar", "Finn", "Captain Sol", "panel", "shield", 0),
    StoryParams("Mar", "Ari", "Captain Nia", "panel", "crew_call", 1),
]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for panel_id, panel in PANELS.items():
        for rid, resp in RESPONSES.items():
            if is_valid(panel, resp):
                out.append((panel_id, rid))
    return out


def explain_rejection(panel: Panel, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return f"(No story: '{response.id}' is too weak a response for a cautionary space story.)"
    return f"(No story: the {panel.label} would not make a meaningful cautionary scene.)"


PANELS = {"panel": Panel("panel", "panel")}


@dataclass
class BuildInfo:
    place: str = "starship"

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure cautionary storyworld with sound effects.")
    ap.add_argument("--panel", choices=PANELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': too weak.)")
    combos = [c for c in valid_combos() if (args.panel is None or c[0] == args.panel) and (args.response is None or c[1] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    panel, response = rng.choice(sorted(combos))
    return StoryParams("Mar", "Pip", "Captain Raya", panel, response, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a cautionary space adventure story about Mar and a glowing panel with sound effects.",
        "Tell a child-friendly story where a curious child wants to press a panel, but a cautious friend warns them first.",
        "Write a space adventure with the words mar and panel, plus loud sound effects and a safe ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mar = f["mar"]
    friend = f["friend"]
    captain = f["captain"]
    panel = f["panel"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?", f"It is about {mar.id} and {friend.id} on a starship, with {captain.label_word} helping them keep safe."),
        ("What did Mar want to do?", f"{mar.id} wanted to press the {panel.label_word}, because it looked bright and mysterious."),
        ("Why did the friend warn Mar?", f"{friend.id} knew the {panel.label_word} belonged to the ship, not to play. A wrong press could make the ship alarm go {SFX['alarm']}."),
    ]
    if out == "averted":
        qa.append(("How did the story end?", "Mar stopped before pressing the panel, and the children used a safer job on the ship instead. The ending is calm and bright.")) 
    elif out == "contained":
        qa.append(("How was the problem fixed?", f"{captain.label_word.capitalize()} used {RESPONSES[params.response].qa_text if False else 'a calm reset'} to stop the alarm, and the ship quieted down again."))
        qa.append(("How did Mar feel at the end?", f"Mar felt sorry, then relieved, and promised not to touch the panel again. The scary sound effects ended with quiet and safety."))
    else:
        qa.append(("How did the story end?", "The alarm kept going for a while, but the crew stayed safe and the children learned the warning the hard way."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a panel?", "A panel is a flat part of a machine or wall that can hold buttons, lights, or controls."),
        ("What should you do if a ship alarm starts?", "You should stop, listen to the grown-up crew, and move carefully so everyone stays safe."),
        ("Why are sound effects used in stories?", "Sound effects help make the action feel lively, loud, or surprising, so the scene is easier to imagine."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(panel).
sensible(reset).
sensible(shield).
sensible(crew_call).
valid(panel, R) :- risk(panel), sensible(R).
outcome(averted) :- delay(1).
outcome(contained) :- not delay(1), chosen(response), sensible(response).
outcome(burned) :- not delay(1), chosen(response), response(tape).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("panel", "panel")]
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
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
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is too weak for a cautionary space story.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program(show="#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

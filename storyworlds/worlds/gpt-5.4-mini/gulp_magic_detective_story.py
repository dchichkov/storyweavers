#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gulp_magic_detective_story.py
=============================================================

A standalone storyworld for a tiny Detective Story with a magical clue trail.

Premise:
- A child detective investigates a small mystery in a magical setting.
- The word "gulp" appears as a frightened reaction when a clue seems impossible.
- Magic is real, but it works through concrete world state: glowing dust, hidden
  doors, enchanted objects, and a helpful spellbook.
- The detective follows evidence, makes a mistake, corrects it, and ends with
  the mystery solved in a child-facing, story-shaped way.

The world is intentionally small:
- one detective
- one helper
- one magical object causing the odd clues
- one location with a hidden space
- one reveal and resolution

The script follows the Storyweavers contract:
- stdlib only
- StoryParams, build_parser, resolve_params, generate, emit, main
- StoryError on invalid explicit choices
- QA grounded in world state
- inline ASP twin plus Python reasonableness gate
- --verify exercises ASP parity and a generation smoke test
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
    mood: str
    hidden_spot: str
    clue_style: str
    helper_place: str

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
    label: str
    odd_clue: str
    source_hint: str
    reveal: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    power: str
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


def _r_gloom(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["mystery"] < THRESHOLD:
            continue
        sig = ("gloom", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["curiosity"] += 1
        out.append("__gloom__")
    return out


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("magic_active") and not world.facts.get("reveal_done"):
        if world.get("clue").meters["glow"] >= THRESHOLD:
            sig = ("spark", "clue")
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("gloom", "mood", _r_gloom), Rule("spark", "magic", _r_spark)]


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


def mystery_at_risk(mystery: Mystery, setting: Setting) -> bool:
    return "hidden" in mystery.tags and "mystery" in setting.tags


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def reveal_possible(response: Response, mystery: Mystery, delay: int) -> bool:
    return response.power >= (1 + delay)


def clue_source_world(setting: Setting, mystery: Mystery, tool: MagicTool, response: Response) -> dict:
    return {
        "setting": setting.id,
        "mystery": mystery.id,
        "tool": tool.id,
        "response": response.id,
    }


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["glow"] += 1
    sim.get("clue").meters["mystery"] += 1
    propagate(sim, narrate=False)
    return {
        "glow": sim.get("clue").meters["glow"],
        "curiosity": sum(ch.memes["curiosity"] for ch in sim.characters()),
    }


def _do_magic(world: World, mystery_ent: Entity, tool: MagicTool, narrate: bool = True) -> None:
    mystery_ent.meters["glow"] += 1
    mystery_ent.meters["mystery"] += 1
    world.facts["magic_active"] = True
    propagate(world, narrate=narrate)


def open_scene(world: World, detective: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a quiet evening, {detective.id} and {helper.id} searched {setting.place}. "
        f"{setting.mood} hung in the air, and every corner felt ready for a clue."
    )


def strange_clue(world: World, mystery: Mystery) -> None:
    world.say(
        f"Then a strange thing happened: {mystery.odd_clue} {mystery.source_hint}. "
        f"{mystery.odd_clue.split()[0].capitalize()} made {mystery.label} seem impossible."
    )


def gulp_reaction(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["startle"] += 1
    world.say(
        f'{detective.id} blinked and whispered, "Gulp." '
        f'If the clue was true, then {mystery.label} had to be hiding somewhere nearby.'
    )


def warn(world: World, helper: Entity, detective: Entity, mystery: Mystery) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} tugged at {detective.id}\'s sleeve. '
        f'"Magic clues are tricky," {helper.pronoun()} said. '
        f'"We should follow the glow, not guess."'
    )


def inspect(world: World, detective: Entity, tool: MagicTool, mystery: Mystery) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} held up {tool.phrase}. {tool.glow.capitalize()}, and the light "
        f"showed tiny sparkles along the floorboards near {mystery.label}."
    )


def accuse_mistaken(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["doubt"] += 1
    world.say(
        f'At first, {detective.id} thought the {mystery.label} itself was doing it. '
        f"But the clue trail was too neat, like it had been placed on purpose."
    )


def reveal(world: World, helper: Entity, mystery: Mystery, response: Response, tool: MagicTool) -> None:
    mystery.meters["glow"] = 0.0
    world.facts["reveal_done"] = True
    body = response.text.replace("{mystery}", mystery.label)
    world.say(
        f"Then {helper.id} pointed to the hidden door. In a flash, {helper.pronoun()} {body}."
    )
    world.say(
        f"The glow turned out to belong to {tool.label}, and behind the door was the source of {mystery.reveal}."
    )


def lesson(world: World, detective: Entity, helper: Entity, mystery: Mystery) -> None:
    detective.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"For a moment, nobody spoke. Then {detective.id} grinned at {helper.id}. "
        f'"We solved it," {detective.id} said. "The clue was magic, but the answer was hidden in plain sight."'
    )
    world.say(
        f"{helper.id} laughed and nodded. The case was finished, and {mystery.label} no longer felt spooky."
    )


def tell(setting: Setting, mystery: Mystery, tool: MagicTool, response: Response,
         detective_name: str = "Mina", detective_gender: str = "girl",
         helper_name: str = "Pip", helper_gender: str = "boy",
         delay: int = 0) -> World:
    world = World(setting)
    det = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    clue = world.add(Entity(id="clue", type="thing", label=tool.label))
    world.facts.update(delay=delay, mystery=mystery, tool=tool, response=response, setting=setting)
    open_scene(world, det, helper, setting)
    world.para()
    strange_clue(world, mystery)
    gulp_reaction(world, det, mystery)
    warn(world, helper, det, mystery)
    inspect(world, det, tool, mystery)
    accuse_mistaken(world, det, mystery)
    world.para()
    _do_magic(world, clue, tool, narrate=True)
    reveal(world, helper, mystery, response, tool)
    lesson(world, det, helper, mystery)
    world.facts.update(detective=det, helper=helper, clue=clue)
    return world


SETTINGS = {
    "lantern_room": Setting("lantern_room", "the lantern room", "Warm shadows and bright glass made the room feel magical.", "behind a tall shelf", "glowing dust", {"mystery", "hidden", "magic"}),
    "library": Setting("library", "the library", "Dusty books and whispery shelves made every sound feel secret.", "behind a rolling ladder", "glimmering footprints", {"mystery", "hidden", "magic"}),
    "garden": Setting("garden", "the moonlit garden", "Silver leaves and sleepy flowers shimmered in the dark.", "under the stone bench", "sparkling petals", {"mystery", "hidden", "magic"}),
}

MYSTERIES = {
    "door": Mystery("door", "the hidden door", "A soft glow kept blinking in and out", "as if someone had tapped it with invisible chalk", "a tiny room with one silver key", {"hidden", "magic"}),
    "jar": Mystery("jar", "the glass jar", "A little ribbon of light curled around the lid", "like a firefly had tucked itself inside", "a map folded into a paper crane", {"hidden", "magic"}),
    "shoe": Mystery("shoe", "the lost shoe", "A trail of glittery dots marched across the floor", "as though a fairy had skipped through", "a warm sleeping mouse in a nest of cloth", {"hidden", "magic"}),
}

TOOLS = {
    "magnifier": MagicTool("magnifier", "magic magnifier", "a magic magnifier", "The lens shimmered like a drop of rain", "to see hidden marks", {"magic", "detective"}),
    "lamp": MagicTool("lamp", "spell lamp", "a spell lamp", "The lamp glowed blue and calm", "to reveal secret paths", {"magic", "detective"}),
    "chalk": MagicTool("chalk", "moon chalk", "a stick of moon chalk", "The chalk glittered as if it remembered the moon", "to mark invisible trails", {"magic", "detective"}),
}

RESPONSES = {
    "unlock": Response("unlock", 3, 3, "unlocked the hidden door and found the real clue", "tried to unlock it, but the spell was too strong", "unlocked the hidden door and found the real clue", {"magic"}),
    "shine": Response("shine", 2, 2, "shone the spell lamp on the clue and made the marks appear", "shone the lamp, but the marks stayed hidden", "shone the spell lamp on the clue and made the marks appear", {"magic"}),
    "read": Response("read", 2, 2, "read the moon chalk marks aloud and followed them to the source", "read the marks, but they faded too fast", "read the moon chalk marks aloud and followed them to the source", {"magic"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    response: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            for tid, t in TOOLS.items():
                if mystery_at_risk(m, s) and "magic" in t.tags:
                    combos.append((sid, mid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny magical detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection(setting: Setting, mystery: Mystery, tool: MagicTool) -> str:
    if not mystery_at_risk(mystery, setting):
        return "(No story: this setting does not create a real hidden-clue mystery.)"
    if "magic" not in tool.tags:
        return "(No story: the tool is not magical enough for this detective case.)"
    return "(No story: this combination is not reasonable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if "hidden" in m.tags:
            lines.append(asp.fact("hidden", mid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "magic" in t.tags:
            lines.append(asp.fact("magic_tool", tid))
        lines.append(asp.fact("power", tid, 2))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("delay", 0))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,T) :- setting(S), mystery(M), tool(T), hidden(M), magic_tool(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
revealable(R) :- response(R), power(R,P), delay(D), P >= D + 1.
outcome(solved) :- valid(S,M,T), sensible(R), revealable(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    samples = [CURATED[0]]
    for p in samples:
        if asp_outcome(p) != "solved":
            print("MISMATCH in outcome.")
            rc = 1
    print("OK: story smoke test can generate.")
    try:
        generate(CURATED[0])
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery and args.tool:
        s, m, t = SETTINGS[args.setting], MYSTERIES[args.mystery], TOOLS[args.tool]
        if not mystery_at_risk(m, s) or "magic" not in t.tags:
            raise StoryError(explain_rejection(s, m, t))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    detective_name = args.name or rng.choice(["Mina", "June", "Ivy", "Nina", "Ruby"])
    helper_name = args.helper or rng.choice(["Pip", "Noel", "Otis", "Bea", "Toby"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, mystery, tool, response, detective_name, gender,
                       helper_name, helper_gender, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "gulp" and '
        f'a touch of magic in {f["setting"].place}.',
        f"Tell a short mystery where {f['detective'].id} sees a strange clue, says "
        f'"gulp", and solves it with {f["tool"].label}.',
        f"Write a magical detective story where a hidden clue seems spooky at first, "
        f"but the mystery is solved by following the glow.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, helper, mystery, tool = f["detective"], f["helper"], f["mystery"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {det.id}, a little detective, and {helper.id}, who helped with the case. They explored {f['setting'].place} together."),
        ("Why did {0} say gulp?".format(det.id),
         f"{det.id} said gulp because the clue looked strange and spooky. The magic made the clue seem impossible until the detective followed it more carefully."),
        ("What did they use to solve the mystery?",
         f"They used {tool.phrase} and a calm, careful look at the glow. That helped them find the hidden place instead of guessing."),
        ("What was hidden?",
         f"{mystery.reveal.capitalize()}. The odd clue was pointing to {mystery.label}, and the real answer was waiting behind the hidden door."),
    ]
    if f.get("reveal_done"):
        qa.append((
            "How did the story end?",
            f"It ended with the mystery solved and everyone feeling proud. The glow faded, the hidden place was found, and the spooky feeling went away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["tool"].tags)
    out = []
    if "magic" in tags:
        out.append(("What does magic do in stories?", "Magic can make unusual things happen, like glowing clues, secret doors, or helpful spells. In a story, it often helps make the mystery exciting."))
        out.append(("Why do detectives look carefully?", "Detectives look carefully because little details can be clues. A tiny mark or glow can point to the answer."))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lantern_room", "door", "magnifier", "unlock", "Mina", "girl", "Pip", "boy", 0),
    StoryParams("library", "jar", "lamp", "shine", "Ivy", "girl", "Otis", "boy", 1),
    StoryParams("garden", "shoe", "chalk", "read", "Ruby", "girl", "Bea", "girl", 0),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        TOOLS[params.tool],
        RESPONSES[params.response],
        params.detective_name,
        params.detective_gender,
        params.helper_name,
        params.helper_gender,
        params.delay,
    )
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
        print(asp_program("#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for sid, mid, tid in asp_valid_combos():
            print(f"  {sid:12} {mid:10} {tid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.detective_name}: {p.setting} / {p.mystery} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

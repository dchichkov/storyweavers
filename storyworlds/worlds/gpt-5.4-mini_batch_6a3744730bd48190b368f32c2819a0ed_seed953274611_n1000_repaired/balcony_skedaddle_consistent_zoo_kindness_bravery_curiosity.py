#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/balcony_skedaddle_consistent_zoo_kindness_bravery_curiosity.py
==============================================================================================

A small heartwarming zoo storyworld about a curious child on a balcony who nearly
skedaddles toward a risky enclosure, then chooses kindness, bravery, and a
consistent, gentle plan instead.

Seed words:
- balcony
- skedaddle
- consistent

Setting:
- zoo

Features:
- Kindness
- Bravery
- Curiosity

Style:
- Heartwarming
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
    safe: bool = False
    animal: bool = False
    helper: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Habitat:
    id: str
    label: str
    place: str
    animal_name: str
    animal_sound: str
    risky: bool = False
    tags: set[str] = field(default_factory=set)
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


@dataclass
class HelpfulTool:
    id: str
    label: str
    phrase: str
    use_text: str
    safe_light: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
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
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if e.meters["safe_plan"] >= THRESHOLD:
            e.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def reasonable(habitat: Habitat, tool: HelpfulTool) -> bool:
    return habitat.risky and tool.safe_light


def consistent_choice(name: str) -> bool:
    return name in {"flashlight", "lantern", "signal_whistle"}


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_safe_plan(response: Response, delay: int) -> bool:
    return response.power >= 1 + delay


def predict_risk(world: World, habitat_id: str) -> dict:
    sim = world.copy()
    _enter_habitat(sim, sim.get("child"), sim.get(habitat_id), narrate=False)
    return {"worry": sim.get("child").memes["worry"], "calm": sim.get("child").memes["calm"]}


def _enter_habitat(world: World, child: Entity, habitat: Entity, narrate: bool = True) -> None:
    habitat.meters["busy"] += 1
    child.memes["curiosity"] += 1
    child.meters["near"] += 1
    if habitat.attrs.get("risk"):
        child.meters["risky"] += 1
    if narrate:
        propagate(world, narrate=True)


def setup(world: World, child: Entity, helper: Entity, habitat: Habitat) -> None:
    child.memes["kindness"] += 1
    child.memes["bravery"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"On a bright morning at the zoo, {child.id} stood on the balcony and "
        f"looked down at the busy paths below."
    )
    world.say(
        f"{helper.id} stayed close, and the two of them watched {habitat.label} "
        f"near {habitat.place}."
    )


def wonder(world: World, child: Entity, habitat: Habitat) -> None:
    world.say(
        f"{child.id}'s eyes went wide with curiosity. {child.pronoun().capitalize()} "
        f"wanted to see how {habitat.animal_name} could move so quietly."
    )


def warn(world: World, helper: Entity, child: Entity, habitat: Habitat) -> None:
    pred = predict_risk(world, "habitat")
    child.memes["worry"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} gave a gentle reminder. "We can watch from the balcony, '
        f'but we should not skedaddle too close to the enclosure. '
        f'{habitat.animal_name} needs calm space, too."'
    )


def choose_kindness(world: World, child: Entity, helper: Entity, habitat: Habitat) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} took a breath and nodded. Being kind meant listening "
        f"to the animals, the helper, and the people around them."
    )
    world.say(
        f"So instead of a wild skedaddle, {child.id} chose a consistent little "
        f"plan: watch, wait, and wave."
    )


def explore_safely(world: World, child: Entity, tool: HelpfulTool, habitat: Habitat) -> None:
    child.meters["safe_plan"] += 1
    world.say(
        f"{helper_for_story(world).id} handed over {tool.phrase}, and it {tool.use_text}."
    )
    world.say(
        f"{child.id} used it to notice every detail from the balcony while "
        f"staying safely back from {habitat.place}."
    )


def helper_for_story(world: World) -> Entity:
    return world.get("helper")


def ending(world: World, child: Entity, helper: Entity, habitat: Habitat, tool: HelpfulTool) -> None:
    child.memes["calm"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At last, {child.id} smiled at {helper.id} and kept watching. "
        f"{habitat.animal_name} ambled by, and the little whistle {tool.use_text} "
        f"like a friendly secret."
    )
    world.say(
        f"The balcony stayed peaceful, {child.id} stayed brave and kind, and "
        f"the zoo felt full of warm, steady light."
    )


def tell(habitat: Habitat, tool: HelpfulTool, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Aunt Rae", helper_gender: str = "aunt") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    hab_ent = world.add(Entity(
        id="habitat", type="habitat", label=habitat.label, attrs={"risk": habitat.risky},
        meters=defaultdict(float), animal=True
    ))
    world.add(Entity(id=tool.id, type="tool", label=tool.label, helper=True, safe=True))

    setup(world, child, helper, habitat)
    world.para()
    wonder(world, child, habitat)
    warn(world, helper, child, habitat)

    if not reasonable(habitat, tool):
        raise StoryError("This zoo story needs a risky enclosure and a safe calming tool.")

    world.para()
    choose_kindness(world, child, helper, habitat)
    explore_safely(world, child, tool, habitat)
    ending(world, child, helper, habitat, tool)

    world.facts.update(
        child=child, helper=helper, habitat=habitat, tool=tool, response=response,
        consistent=tool.id, bravery=child.memes["bravery"], curiosity=child.memes["curiosity"],
        kindness=child.memes["kindness"], ended_calm=True
    )
    return world


@dataclass
class StoryParams:
    setting: str
    habitat: str
    tool: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {"zoo": "zoo"}

HABITATS = {
    "monkeys": Habitat(
        id="monkeys",
        label="the monkey balcony",
        place="the monkey house",
        animal_name="the monkeys",
        animal_sound="chatter",
        risky=True,
        tags={"balcony", "zoo"},
    ),
    "birds": Habitat(
        id="birds",
        label="the bird balcony",
        place="the aviary",
        animal_name="the birds",
        animal_sound="chirp",
        risky=True,
        tags={"balcony", "zoo"},
    ),
    "giraffes": Habitat(
        id="giraffes",
        label="the giraffe balcony",
        place="the tall viewing deck",
        animal_name="the giraffes",
        animal_sound="hum",
        risky=True,
        tags={"balcony", "zoo"},
    ),
}

TOOLS = {
    "flashlight": HelpfulTool(
        id="flashlight",
        label="a flashlight",
        phrase="a small flashlight",
        use_text="shone steady and bright",
        safe_light=True,
        tags={"consistent"},
    ),
    "lantern": HelpfulTool(
        id="lantern",
        label="a lantern",
        phrase="a little battery lantern",
        use_text="glowed warm and steady",
        safe_light=True,
        tags={"consistent"},
    ),
    "signal_whistle": HelpfulTool(
        id="signal_whistle",
        label="a whistle",
        phrase="a tiny signal whistle",
        use_text="gave one neat, consistent peep",
        safe_light=True,
        tags={"consistent"},
    ),
}

RESPONSES = {
    "watch": Response(
        id="watch",
        sense=3,
        power=3,
        text="watched from the balcony and kept everyone calm",
        fail="tried to hurry, but that only made the moment feel wobbly",
        qa_text="watched from the balcony and kept the moment calm",
        tags={"kindness", "curiosity"},
    ),
    "wait": Response(
        id="wait",
        sense=3,
        power=3,
        text="waited for the right moment and listened carefully",
        fail="waited too little and missed the gentle chance to do it well",
        qa_text="waited for the right moment and listened carefully",
        tags={"kindness", "consistency"},
    ),
    "guide": Response(
        id="guide",
        sense=4,
        power=4,
        text="guided the child back to the safe path with a warm smile",
        fail="guided too late, and the busy path had already grown confusing",
        qa_text="guided the child back to the safe path with a warm smile",
        tags={"kindness", "bravery"},
    ),
    "skedaddle_late": Response(
        id="skedaddle_late",
        sense=1,
        power=1,
        text="skedaddled after the problem, but the chance for a safe fix had passed",
        fail="skedaddled the wrong way and could not help in time",
        qa_text="skedaddled after the problem too late",
        tags={"bravery"},
    ),
}

GIRL_NAMES = ["Mina", "Tess", "Lily", "Ava", "Nora"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Max", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hab in HABITATS:
            for tool in TOOLS:
                if reasonable(HABITATS[hab], TOOLS[tool]):
                    combos.append((setting, hab, tool))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming zoo storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.habitat is None or c[1] == args.habitat)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, habitat, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or rng.choice(["aunt", "uncle", "mother", "father"])
    helper_name = args.helper_name or rng.choice(["Aunt Rae", "Uncle Ben", "Mom", "Dad"])
    return StoryParams(
        setting=setting,
        habitat=habitat,
        tool=tool,
        response=response,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming zoo story that includes the words "balcony", "skedaddle", and "consistent".',
        f"Tell a story where {f['child'].id} is curious at the zoo, nearly wants to skedaddle, and then chooses a consistent safe plan.",
        f"Write a gentle story about kindness, bravery, and curiosity at a zoo balcony, ending with a calm shared choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, habitat, tool = f["child"], f["helper"], f["habitat"], f["tool"]
    return [
        QAItem(
            question="Where did the story take place?",
            answer="It took place at the zoo, where the child stood on a balcony and watched the animals below."
        ),
        QAItem(
            question=f"What did {child.id} want to do at first?",
            answer=f"{child.id} wanted to skedaddle closer so {child.pronoun()} could see {habitat.animal_name} better. Curiosity pulled hard, but the child had to choose a safer way."
        ),
        QAItem(
            question="How did the child show kindness?",
            answer="The child listened to the helper, stayed calm, and chose a safe plan that respected the animals and the people nearby."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} staying on the balcony, using {tool.label} to keep the plan consistent and peaceful. The child felt brave without making the zoo unsafe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a balcony?",
            answer="A balcony is a raised place you can stand on and look out from. It gives a clear view while keeping you up and away."
        ),
        QAItem(
            question="What does skedaddle mean?",
            answer="Skedaddle means to hurry off quickly. It sounds playful, but it is still important to move carefully when safety matters."
        ),
        QAItem(
            question="What does consistent mean?",
            answer="Consistent means doing something the same careful way again and again. A consistent plan helps people feel steady and know what to expect."
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.safe:
            bits.append("safe=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="zoo", habitat="monkeys", tool="flashlight", response="guide",
                child_name="Mina", child_gender="girl", helper_name="Aunt Rae", helper_gender="aunt"),
    StoryParams(setting="zoo", habitat="birds", tool="lantern", response="watch",
                child_name="Eli", child_gender="boy", helper_name="Mom", helper_gender="mother"),
    StoryParams(setting="zoo", habitat="giraffes", tool="signal_whistle", response="wait",
                child_name="Tess", child_gender="girl", helper_name="Dad", helper_gender="father"),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is too weak for this story shape, sense={r.sense}.)"


ASP_RULES = r"""
valid(S,H,T) :- setting(S), habitat(H), tool(T), risky(H), safe_light(T).
kind_path(C) :- child(C), kindness(C), bravery(C), curiosity(C).
ended_calm(C) :- kind_path(C), consistent(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HABITATS.items():
        lines.append(asp.fact("habitat", hid))
        if h.risky:
            lines.append(asp.fact("risky", hid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.safe_light:
            lines.append(asp.fact("safe_light", tid))
        if tid == "flashlight" or tid == "lantern" or tid == "signal_whistle":
            lines.append(asp.fact("consistent", tid))
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
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, habitat=None, tool=None, response=None, child_name=None,
            child_gender=None, helper_name=None, helper_gender=None
        ), random.Random(0)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: story generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.habitat not in HABITATS or params.tool not in TOOLS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(HABITATS[params.habitat], TOOLS[params.tool], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

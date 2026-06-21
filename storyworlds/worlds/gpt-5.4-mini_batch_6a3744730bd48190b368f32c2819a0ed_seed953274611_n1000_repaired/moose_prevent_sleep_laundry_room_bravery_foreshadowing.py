#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moose_prevent_sleep_laundry_room_bravery_foreshadowing.py
==========================================================================================

A small nursery-rhyme storyworld in a laundry room: a curious child spots a moose
toy near the washer, feels a brave little tingle, notices foreshadowing signs
(the dryer hum, a lumpy towel, a sleepy cat), and chooses a safe way to prevent
trouble before sleep. The world supports a few close variations while staying
child-facing, concrete, and state-driven.

The story premise is simple:
- a laundry room feels cozy and a little mysterious,
- curiosity pulls the child toward a risky nook,
- bravery helps the child act before sleepy trouble grows,
- foreshadowing is paid off by a calm, safe ending image.

This script is standalone and stdlib-only except for the shared repo modules:
storyworlds/results.py and storyworlds/asp.py (imported lazily only for ASP).
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
BRAVERY_INIT = 4.0
CURIOSITY_INIT = 3.0
SLEEPINESS_INIT = 0.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    cozy_line: str
    dark_corner: str
    sounds: str
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky: bool = False
    makes_noise: bool = False
    can_hide: bool = False
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
class ActionCfg:
    id: str
    label: str
    verb: str
    result: str
    prevent_text: str
    success_text: str
    fail_text: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_drowsy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["sleepy"] < THRESHOLD:
            continue
        sig = ("drowsy", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["slow"] += 1
        out.append(f"{e.id} got a little slower and softer.")
    return out


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["risk"] < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"A worry woke up in {e.id}'s heart.")
    return out


CAUSAL_RULES = [Rule("drowsy", _r_drowsy), Rule("alarm", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def curiously_inspects(world: World, child: Entity, obj: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was a little curious child, and {setting.label} was a little "
        f"cozy place. {setting.cozy_line}"
    )
    world.say(
        f"Near the washer sat {obj.phrase}, and from the corner came {setting.sounds}."
    )


def foreshadow(world: World, child: Entity, setting: Setting, obj: Entity) -> None:
    child.memes["foreshadowing"] += 1
    world.say(
        f"{child.id} noticed something first: the dryer hummed, a towel sat in a "
        f"lumpy heap, and {setting.dark_corner} looked extra shadowy."
    )
    if obj.makes_noise:
        world.say(f"Even {obj.label} seemed to make a tiny thump when the floor shook.")


def tempt_sleep(world: World, child: Entity, obj: Entity) -> None:
    child.memes["bravery"] += 1
    child.meters["risk"] += 1
    world.say(
        f"Then {child.id} felt brave enough to reach toward {obj.phrase}, though "
        f"{child.pronoun('possessive')} eyelids were getting sleepy."
    )


def prevent(world: World, child: Entity, obj: Entity, action: ActionCfg) -> None:
    child.memes["bravery"] += 1
    child.meters["risk"] = 0.0
    world.say(
        f"But {child.id} remembered how to prevent trouble. "
        f"{action.prevent_text.format(obj=obj.label, child=child.id)}"
    )


def finish(world: World, child: Entity, setting: Setting, obj: Entity, action: ActionCfg) -> None:
    child.memes["joy"] += 1
    world.say(
        f"So {child.id} {action.success_text.format(obj=obj.label)} "
        f"The laundry room stayed calm and warm, and sleepy time came gently."
    )
    world.say(
        f"By the end, the moose toy was safe, the basket was neat, and the whole "
        f"{setting.label} sighed like a hush-hush song."
    )


def tell(setting: Setting, obj: ObjectCfg, action: ActionCfg, name: str, gender: str,
         parent: str = "mother", role: str = "child") -> World:
    world = World()
    child = world.add(Entity(
        id=name, kind="character", type=gender, role=role,
        attrs={"parent": parent},
    ))
    grown = world.add(Entity(id="Grownup", kind="character", type=parent, role="parent"))
    toy = world.add(Entity(id="moose", type="toy", label=obj.label, tags=set(obj.tags)))
    child.memes["bravery"] = BRAVERY_INIT
    child.memes["curiosity"] = CURIOSITY_INIT
    child.meters["sleepy"] = SLEEPINESS_INIT

    curiously_inspects(world, child, toy, setting)
    world.para()
    foreshadow(world, child, setting, toy)
    tempt_sleep(world, child, toy)
    if obj.risky:
        prevent(world, child, toy, action)
    world.para()
    finish(world, child, setting, toy, action)
    world.facts.update(child=child, grown=grown, toy=toy, setting=setting,
                       obj=obj, action=action, prevented=obj.risky)
    return world


SETTINGS = {
    "laundry_room": Setting(
        id="laundry_room",
        label="laundry room",
        cozy_line="The washer blinked, the dryer hummed, and the folded towels made soft hills.",
        dark_corner="behind the basket",
        sounds="a soft whirr and a sleepy click-clack",
        tags={"laundry_room"},
    )
}

OBJECTS = {
    "moose": ObjectCfg(
        id="moose",
        label="moose",
        phrase="a plush moose by the folding table",
        risky=True,
        makes_noise=False,
        can_hide=True,
        tags={"moose"},
    ),
    "basket": ObjectCfg(
        id="basket",
        label="basket",
        phrase="a wicker basket full of socks",
        risky=False,
        makes_noise=False,
        can_hide=True,
        tags={"basket"},
    ),
}

ACTIONS = {
    "sleep": ActionCfg(
        id="sleep",
        label="sleep",
        verb="curl up for sleep",
        result="drifted off",
        prevent_text="{child} put {obj} back on the shelf and tucked the blankets straight.",
        success_text="curled up for sleep after setting the room right.",
        fail_text="fell asleep next to the laundry basket.",
        tags={"sleep"},
    )
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ruby"]
BOY_NAMES = ["Ben", "Theo", "Max", "Leo", "Finn", "Owen"]
TRAITS = ["brave", "curious", "gentle", "sly", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for oid, obj in OBJECTS.items():
            for aid, action in ACTIONS.items():
                if setting.id == "laundry_room" and obj.risky and action.id == "sleep":
                    combos.append((sid, oid, aid))
    return combos


@dataclass
class StoryParams:
    setting: str
    object: str
    action: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "moose": [("What is a moose?",
               "A moose is a big wild animal with long legs and wide antlers. It is not a toy, but a toy moose is a soft stuffed animal.")],
    "sleep": [("Why do children need sleep?",
               "Sleep helps a child rest their body and mind so they can wake up strong and bright again.")],
    "curiosity": [("What is curiosity?",
                  "Curiosity is the feeling that makes you want to look, ask, and learn more about something.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing the right thing even when you feel a little worried or unsure.")],
    "foreshadowing": [("What is foreshadowing?",
                      "Foreshadowing is a tiny clue that hints something important may happen soon.")],
    "prevent": [("What does prevent mean?",
                 "To prevent something means to stop it before it causes trouble.")],
    "laundry_room": [("What is a laundry room?",
                      "A laundry room is where people wash and dry clothes, and often keep baskets, soap, and towels.")],
}
KNOWLEDGE_ORDER = ["laundry_room", "moose", "sleep", "curiosity", "bravery", "foreshadowing", "prevent"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a nursery-rhyme story in a laundry room that includes the words moose, prevent, and sleep.",
        f"Tell a small story where {child.id} feels curious and brave in the laundry room, notices a foreshadowing clue, and prevents a sleep-time problem.",
        f"Write a gentle rhyme-like story about a moose toy, curiosity, bravery, and a safe ending before sleep.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, toy, setting = f["child"], f["toy"], f["setting"]
    action = f["action"]
    return [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens in the {setting.label}. That is where the washer, the towels, and the little moose toy are waiting."
        ),
        QAItem(
            question="Why does the child pause before sleep?",
            answer=f"{child.id} notices clues that something might go wrong, so {child.pronoun()} slows down and thinks. The foreshadowing helps {child.id} prevent trouble before sleep."
        ),
        QAItem(
            question="What did the child do to keep things safe?",
            answer=f"{child.id} put the {toy.label} back on the shelf and straightened the blankets. That simple move prevented a sleepy mix-up and let the room stay calm."
        ),
        QAItem(
            question="How did bravery help?",
            answer=f"Bravery helped {child.id} do the right thing instead of rushing ahead. It made room for careful hands and a safer ending."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["setting"].tags) | set(world.facts["obj"].tags) | set(world.facts["action"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="laundry_room", object="moose", action="sleep", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="laundry_room", object="moose", action="sleep", name="Ben", gender="boy", parent="father", trait="brave"),
]


def explain_rejection(setting: Setting, obj: ObjectCfg, action: ActionCfg) -> str:
    if setting.id != "laundry_room":
        return "(No story: this tiny world only lives in a laundry room.)"
    if not obj.risky or action.id != "sleep":
        return "(No story: the seed wants a moose, a prevent turn, and sleep-time trouble that can be safely stopped.)"
    return "(No story: the chosen pieces do not make a meaningful little problem to prevent.)"


def outcome_of(params: StoryParams) -> str:
    return "prevented" if params.setting == "laundry_room" and params.object == "moose" and params.action == "sleep" else "unknown"


ASP_RULES = r"""
valid_story(S,O,A) :- setting(S), object(O), action(A), laundry_room(S), risky(O), sleep_action(A).
prevented :- valid_story(S,O,A), setting(S), object(O), action(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("laundry_room", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.risky:
            lines.append(asp.fact("risky", oid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        if aid == "sleep":
            lines.append(asp.fact("sleep_action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object=None, action=None, name=None, gender=None, parent=None, trait=None), random.Random(7)))
        assert sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme laundry-room storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.action and args.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if args.setting and args.object and args.action:
        if (args.setting, args.object, args.action) not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.setting], OBJECTS[args.object], ACTIONS[args.action]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, object=obj, action=action, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object not in OBJECTS or params.action not in ACTIONS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], ACTIONS[params.action],
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3.\n#show prevented/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

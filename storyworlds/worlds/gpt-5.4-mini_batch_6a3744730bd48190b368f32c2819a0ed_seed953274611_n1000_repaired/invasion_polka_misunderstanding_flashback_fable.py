#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/invasion_polka_misunderstanding_flashback_fable.py
==================================================================================

A small fable-style storyworld about a countryside misunderstanding: a rabbit
hears the word "invasion" and imagines danger, but a flashback explains why the
word makes everyone nervous. In the end, the "invasion" turns out to be a joyful
polka parade, and the village learns to ask before it panics.

The world is built as a compact simulation with typed entities, physical meters,
emotional memes, a reasonableness gate, a Python/ASP twin, and child-facing Q&A.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "hare", "mouse", "fox", "bird"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "father", "owl"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Mood:
    id: str
    label: str
    level: int
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
class Trigger:
    id: str
    label: str
    makes_alarm: bool
    kind: str
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
class EventKind:
    id: str
    label: str
    act: str
    sound: str
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
class StoryParams:
    setting: str
    trigger: str
    event: str
    listener: str
    guide: str
    mood: str = "wary"
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_alarm(world: World) -> list[str]:
    out = []
    if world.facts.get("misunderstood") and "crowd" in world.entities:
        crowd = world.get("crowd")
        if crowd.meters.get("panic", 0.0) < THRESHOLD:
            sig = ("alarm",)
            if sig not in world.fired:
                world.fired.add(sig)
                crowd.meters["panic"] = crowd.meters.get("panic", 0.0) + 1
                for ent in list(world.entities.values()):
                    if ent.kind == "character":
                        ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1
                out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def is_reasonable(trigger: Trigger, event: EventKind) -> bool:
    return trigger.makes_alarm and event.id in {"polka_parade", "polka_band"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for trig_id, trig in TRIGGERS.items():
            for event_id, ev in EVENTS.items():
                if is_reasonable(trig, ev):
                    combos.append((setting, trig_id, event_id))
    return combos


def choose_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


class Setup:
    pass


def flashback(world: World, listener: Entity, guide: Entity, trigger: Trigger) -> None:
    listener.memes["memory"] = listener.memes.get("memory", 0.0) + 1
    guide.memes["patience"] = guide.memes.get("patience", 0.0) + 1
    world.say(
        f"Long before that morning, {listener.id} had heard a real warning in the fields. "
        f"The word {trigger.label} once meant trouble, so {listener.id} still flinched at it."
    )
    world.say(
        f"But {guide.id} remembered the old scare and said, \"A word can wear two faces. "
        f"We should look before we judge.\""
    )


def misunderstanding(world: World, listener: Entity, guide: Entity, trigger: Trigger,
                     event: EventKind) -> None:
    listener.memes["worry"] = listener.memes.get("worry", 0.0) + 1
    world.say(
        f"One bright morning, a messenger cried about an {trigger.label}. "
        f"{listener.id} froze and imagined boots, smoke, and hurried doors."
    )
    world.say(
        f"{listener.id} tugged at {guide.id}'s sleeve. \"If there is an {trigger.label}, "
        f"we must hide!\" {listener.pronoun().capitalize()} had not yet seen that the sound "
        f"was only {event.label} music coming over the hill."
    )


def reveal(world: World, event: EventKind) -> None:
    world.say(
        f"Then the dust cleared, and the truth stepped out in little hops: it was a {event.label}, "
        f"not a raid. Fiddles chirped, a drum kept time, and the whole lane bounced with a polka."
    )


def lesson(world: World, listener: Entity, guide: Entity) -> None:
    listener.memes["relief"] = listener.memes.get("relief", 0.0) + 1
    listener.memes["joy"] = listener.memes.get("joy", 0.0) + 1
    guide.memes["joy"] = guide.memes.get("joy", 0.0) + 1
    world.say(
        f"{guide.id} laughed softly and said, \"Ask first, and fear grows smaller.\" "
        f"{listener.id} nodded, feeling brave enough to listen before leaping."
    )


def ending(world: World, setting: str, event: EventKind) -> None:
    world.say(
        f"By sunset, the lane was full of dancing feet, and even the worried ears were wagging. "
        f"The village learned that not every {setting} cry is an invasion; sometimes it is only a polka "
        f"coming to invite the heart outside."
    )


def tell(setting: str, trigger: Trigger, event: EventKind, listener_name: str,
         guide_name: str, mood: Mood) -> World:
    world = World()
    listener = world.add(Entity(id=listener_name, kind="character", type="rabbit", role="listener"))
    guide = world.add(Entity(id=guide_name, kind="character", type="owl", role="guide"))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label="the village lane"))
    listener.memes["wary"] = float(mood.level)
    crowd.meters["panic"] = 0.0

    world.say(
        f"In a little meadow village, {listener.id} lived by a lane where bells, boots, and birdcalls "
        f"could carry far."
    )
    world.say(
        f"{listener.id} was a small {mood.label} rabbit, and {guide.id} was the old owl who liked to "
        f"explain things twice if needed."
    )

    world.para()
    flashback(world, listener, guide, trigger)
    world.para()
    misunderstanding(world, listener, guide, trigger, event)
    world.facts["misunderstood"] = True
    propagate(world, narrate=False)
    world.para()
    reveal(world, event)
    lesson(world, listener, guide)
    world.para()
    ending(world, setting, event)

    world.facts.update(
        setting=setting,
        trigger=trigger,
        event=event,
        listener=listener,
        guide=guide,
        crowd=crowd,
        mood=mood,
        outcome="gentle",
    )
    return world


SETTINGS = {
    "lane": "lane",
    "village": "village",
    "meadow": "meadow",
}

MOODS = {
    "wary": Mood(id="wary", label="wary", level=1, tags={"fear"}),
    "nervous": Mood(id="nervous", label="nervous", level=2, tags={"fear"}),
    "careful": Mood(id="careful", label="careful", level=3, tags={"caution"}),
}

TRIGGERS = {
    "invasion": Trigger(id="invasion", label="invasion", makes_alarm=True, kind="warning", tags={"alarm", "fear"}),
    "drift": Trigger(id="drift", label="drift", makes_alarm=False, kind="noise", tags={"music"}),
}

EVENTS = {
    "polka_parade": EventKind(id="polka_parade", label="polka parade", act="dance", sound="polka", tags={"polka", "music"}),
    "polka_band": EventKind(id="polka_band", label="polka band", act="play", sound="polka", tags={"polka", "music"}),
}

LISTENERS = ["Pip", "Milo", "Tansy", "Bram", "Wren"]
GUIDES = ["Hoot", "Iris", "Sage", "Mira"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trig = f["trigger"]
    ev = f["event"]
    return [
        f'Write a fable for a child that includes the words "{trig.label}" and "polka".',
        f"Tell a story about a misunderstanding in which {f['listener'].id} thinks an {trig.label} is coming, but it turns out to be a {ev.label}.",
        "Use a flashback to explain why the listener is frightened, and end with a gentle lesson about asking before panicking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    listener = f["listener"]
    guide = f["guide"]
    trig = f["trigger"]
    ev = f["event"]
    return [
        QAItem(
            question="What did the rabbit think was happening at first?",
            answer=(
                f"{listener.id} thought an {trig.label} was coming. "
                f"{listener.id} was mistaken because the loud sound was really a {ev.label} and not danger."
            ),
        ),
        QAItem(
            question="Why did the rabbit react so strongly?",
            answer=(
                f"A flashback showed that {listener.id} had once heard a real warning, so the word {trig.label} still felt scary. "
                f"That old memory made {listener.id} jump before looking closely."
            ),
        ),
        QAItem(
            question="How did the misunderstanding end?",
            answer=(
                f"{guide.id} helped {listener.id} slow down and look again, and then everyone saw the polka parade. "
                f"The fear turned into relief, and the rabbit learned to ask first."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a polka?",
            answer="A polka is a lively kind of dance music with a quick, bouncy beat.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment that shows something from earlier in time so readers understand why a character feels the way they do.",
        ),
        QAItem(
            question="Why should you ask before you panic?",
            answer="Asking helps you learn the truth sooner, and that can keep a small worry from turning into a big one.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="lane", trigger="invasion", event="polka_parade", listener="Pip", guide="Hoot", mood="wary"),
    StoryParams(setting="village", trigger="invasion", event="polka_band", listener="Tansy", guide="Iris", mood="nervous"),
]


def explain_rejection(trigger: Trigger, event: EventKind) -> str:
    if not trigger.makes_alarm:
        return "(No story: this trigger is too quiet to create a misunderstanding.)"
    if "polka" not in event.tags:
        return "(No story: the event does not carry the polka needed for the tale.)"
    return "(No story: this combination does not make a believable misunderstanding.)"


def valid_story(params: StoryParams) -> bool:
    return params.trigger in TRIGGERS and params.event in EVENTS and is_reasonable(TRIGGERS[params.trigger], EVENTS[params.event])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trigger and args.event:
        trig = TRIGGERS[args.trigger]
        ev = EVENTS[args.event]
        if not is_reasonable(trig, ev):
            raise StoryError(explain_rejection(trig, ev))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.event is None or c[2] == args.event)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, trigger, event = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    listener = args.listener or rng.choice(LISTENERS)
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(setting=setting, trigger=trigger, event=event, listener=listener, guide=guide, mood=mood)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.trigger not in TRIGGERS or params.event not in EVENTS or params.mood not in MOODS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], TRIGGERS[params.trigger], EVENTS[params.event], params.listener, params.guide, MOODS[params.mood])
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


ASP_RULES = r"""
trigger_alarm(T) :- trigger(T), makes_alarm(T).
polka_event(E) :- event(E), has_polka(E).
misunderstood :- trigger_alarm(invasion), polka_event(E).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MOODS.items():
        lines.append(asp.fact("mood", mid))
        lines.append(asp.fact("level", mid, m.level))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
        if t.makes_alarm:
            lines.append(asp.fact("makes_alarm", tid))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("has_polka", eid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show trigger/1.\n#show event/1."))
    settings = [a[0] for a in asp.atoms(model, "setting")]
    triggers = [a[0] for a in asp.atoms(model, "trigger")]
    events = [a[0] for a in asp.atoms(model, "event")]
    return [(s, t, e) for s in settings for t in triggers for e in events if is_reasonable(TRIGGERS[t], EVENTS[e])]


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python gates differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style story world about invasion, polka, misunderstanding, and flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--listener")
    ap.add_argument("--guide")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show trigger/1.\n#show event/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

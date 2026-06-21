#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/event_tug_patch_dialogue_quest_adventure.py
===========================================================================

A tiny adventure storyworld about a child-led quest, a noisy village event,
and a patch that keeps a little tugboat ready for the next trip.

Seed words:
- event
- tug
- patch

Features:
- Dialogue
- Quest

Style:
- Adventure

This world generates one of a few constraint-checked story paths:
1) A harbor event is coming, and a child spots a torn patch on a tugboat sail.
2) A helper warns that the tear will catch wind and spoil the quest.
3) The crew searches for a patch kit, patches the sail, and sails to the event.
4) The ending image proves the change: the tugboat arrives with a neat patch,
   the child keeps the promise, and the event goes well.

It also supports a cautious fail-closed gate and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class Setting:
    id: str
    place: str
    event_name: str
    mood: str
    water: str
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
class Quest:
    id: str
    goal: str
    clue: str
    route: str
    end_image: str
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
class Patch:
    id: str
    label: str
    material: str
    size: str
    fix_text: str
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


@dataclass
class DialogueBeat:
    speaker: str
    line: str
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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "Harbor Day", "bright and windy", "salt water", {"event", "harbor"}),
    "festival": Setting("festival", "the town square", "Lantern Festival", "busy and cheerful", "fountain water", {"event", "festival"}),
}

QUESTS = {
    "sail": Quest("sail", "reach the event on time", "a torn sail patch", "follow the quay to the pier", "the tug arrived with its patched sail shining in the sun", {"quest", "adventure"}),
    "relay": Quest("relay", "carry the message to the event", "a damp envelope patch", "cross the bridge and the market", "the messenger arrived with the message kept dry and safe", {"quest", "adventure"}),
}

PATCHES = {
    "cloth": Patch("cloth", "cloth patch", "cloth", "small", "pressed the cloth patch over the tear", "tried the cloth patch, but the tear opened wider", {"patch", "repair"}),
    "canvas": Patch("canvas", "canvas patch", "canvas", "small", "smoothed the canvas patch across the rip", "used the canvas patch, but the wind yanked it loose", {"patch", "repair"}),
}

GIRL_NAMES = ["Lina", "Mara", "Tia", "Suki", "Nina"]
BOY_NAMES = ["Pico", "Jori", "Ren", "Oli", "Milo"]
HELPERS = ["captain", "dockhand", "older cousin", "harbor guide"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    patch: str
    name: str
    gender: str
    helper: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for pid, patch in PATCHES.items():
                if "event" in setting.tags and "patch" in patch.tags and "adventure" in quest.tags:
                    combos.append((sid, qid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An adventure storyworld about a quest to reach an event by patching a tugboat.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.patch is None or c[2] == args.patch)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, patch = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or rng.choice(HELPERS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, quest=quest, patch=patch, name=name, gender=gender, helper=helper, delay=delay)


def _story_can_succeed(params: StoryParams) -> bool:
    return params.delay <= 1 or params.patch == "canvas"


def tell(world: World, params: StoryParams) -> None:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    patch = PATCHES[params.patch]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="hero", traits=["brave"]))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", role="helper", label=f"the {params.helper}"))
    tug = world.add(Entity(id="tug", kind="vehicle", type="tug", label="the tugboat"))
    torn = world.add(Entity(id="patch", kind="thing", type="patch", label="the torn patch"))
    hero.memes["curiosity"] = 1
    hero.memes["hope"] = 1
    tug.meters["tear"] = 1

    world.say(f"At {setting.place}, {setting.event_name} was coming soon, and the air felt {setting.mood}.")
    world.say(f"{hero.id} saw {quest.clue} on {quest.route}, right beside {tug.label_word} with a torn patch on its sail.")
    world.say(f'"If the sail tears more, will the tug still reach the event?" {hero.id} asked.')
    world.say(f'"Not safely," said {helper.label_word}. "But we can make a patch and try the quest the careful way."')

    world.para()
    hero.memes["resolve"] = 1
    world.say(f"{hero.id} nodded. " + f'"Then let us go," {hero.pronoun()} said, and the quest began.')

    if _story_can_succeed(params):
        world.para()
        tug.meters["patched"] = 1
        tug.meters["tear"] = 0
        world.say(f"They found {patch.label} tools and {patch.fix_text}.")
        world.say(f'"Good," said {helper.label_word}. "Now the wind can tug at the sail without stealing the trip."')
        world.say(f"{hero.id} climbed aboard, and the tug chugged along {quest.route} toward the event.")
        world.para()
        world.say(f"When they reached the square, {setting.event_name} was already bright with banners and song.")
        world.say(f"{quest.end_image.capitalize()}. {hero.id} smiled at the patched sail, knowing the patch had kept the whole quest together.")
        ending = "succeeded"
    else:
        world.para()
        tug.meters["patched"] = 0
        tug.meters["tear"] = 1
        world.say(f"They tried to use {patch.label}, but {patch.fail_text}.")
        world.say(f'"We need a stronger patch or more time," said {helper.label_word}, as the wind kept worrying the torn sail.')
        world.say(f"The tug had to turn back, and the event waited without them.")
        world.para()
        world.say(f"By dusk, the little crew still stood at the dock, planning a better repair for tomorrow.")
        ending = "delayed"

    world.facts.update(setting=setting, quest=quest, patch=patch, hero=hero, helper=helper, tug=tug, ending=ending, delay=params.delay)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.quest not in QUESTS or params.patch not in PATCHES:
        raise StoryError("Invalid parameter key.")
    world = World()
    tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "event", "tug", and "patch".',
        f"Tell a quest story where {f['hero'].id} helps a tugboat reach {f['setting'].event_name} by using a patch.",
        f"Write a dialogue-rich adventure about a child, a helper, and a patched tugboat arriving at an event.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    quest = f["quest"]
    patch = f["patch"]
    tug = f["tug"]
    qa = [
        ("What was the child trying to do?",
         f"{hero.id} was trying to help the tugboat complete a quest so it could reach {setting.event_name}. The trip mattered because the event was waiting and the wind could spoil the sail."),
        ("What was wrong with the tugboat?",
         "The sail had a torn patch, so the tugboat needed a repair before it could go safely. Without the fix, the wind would tug harder and make the trip risky."),
        ("Who helped with the repair?",
         f"{helper.label_word.capitalize()} helped by giving calm advice and watching the patch work. That help mattered because the child could focus on the quest instead of rushing."),
    ]
    if f["ending"] == "succeeded":
        qa.append((
            "How did the story end?",
            f"It ended happily: they used the {patch.label} and the tugboat reached {setting.event_name}. The patched sail proved the repair worked because the boat arrived ready for the celebration."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a delay: the patch did not hold, so the tugboat had to turn back. The crew stayed safe, but they had to plan a better repair for the next day."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a patch?",
         "A patch is a piece of material used to cover a hole or tear. It can help fix something so it lasts longer."),
        ("What is a tugboat?",
         "A tugboat is a small, strong boat that helps move bigger boats or carries people along a harbor. It can also be part of a small adventure story."),
        ("What is a quest?",
         "A quest is a trip or task where someone tries to reach a goal. In stories, quests often have a problem to solve along the way."),
        ("Why can wind be a problem for a torn sail?",
         "Wind can pull on a torn sail and make the tear wider. That is why a strong patch or careful repair matters."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, P) :- setting(S), quest(Q), patch(P).
success(P) :- patch(P), P = canvas.
end(succeeded) :- success(canvas).
end(delayed) :- not success(canvas).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for pid in PATCHES:
        lines.append(asp.fact("patch", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    # smoke test with curated/default params
    try:
        sample = generate(StoryParams(setting="harbor", quest="sail", patch="canvas", name="Lina", gender="girl", helper="captain", delay=0))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection() -> str:
    return "(No story: this combination cannot produce a sensible adventure quest.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.patch is None or c[2] == args.patch)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, quest, patch = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    helper = args.helper or rng.choice(HELPERS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, quest=quest, patch=patch, name=name, gender=gender, helper=helper, delay=delay)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="harbor", quest="sail", patch="canvas", name="Lina", gender="girl", helper="captain", delay=0),
    StoryParams(setting="festival", quest="relay", patch="cloth", name="Milo", gender="boy", helper="dockhand", delay=1),
    StoryParams(setting="harbor", quest="sail", patch="cloth", name="Nina", gender="girl", helper="older cousin", delay=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

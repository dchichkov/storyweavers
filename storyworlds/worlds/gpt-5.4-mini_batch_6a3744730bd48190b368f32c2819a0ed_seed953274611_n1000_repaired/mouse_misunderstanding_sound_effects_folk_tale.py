#!/usr/bin/env python3
"""
A standalone storyworld for a folk-tale style mouse misunderstanding sounds.

Premise:
A small mouse hears strange sound effects at night in a cottage barnyard and
misunderstands what they mean. The mouse gathers courage, follows the sounds,
discovers an ordinary source, and the village peace is restored.

This file is self-contained except for the shared results containers and the
lazy ASP helper, as required by the Storyweavers contract.
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "damp": 0.0, "rattled": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "courage": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    hush: str
    sounds: list[str] = field(default_factory=list)
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


@dataclass
class SoundSource:
    id: str
    label: str
    onomatopoeia: str
    source_kind: str
    harmless: bool
    explains: str
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
class Response:
    id: str
    sense: int
    text: str
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
    sound: str
    response: str
    mouse_name: str = "Milo"
    helper_name: str = "Mara"
    helper_role: str = "miller"
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "cottage": Setting(id="cottage", place="a little cottage", hush="the hearth was warm and low", sounds=["barn", "kettle", "attic"]),
    "barn": Setting(id="barn", place="a sleepy barn", hush="the rafters were full of shadows", sounds=["hay", "lantern", "door"]),
    "mill": Setting(id="mill", place="a river mill", hush="the wheel kept a steady turn", sounds=["water", "wheel", "loft"]),
}

SOUNDS = {
    "kettle": SoundSource(
        id="kettle",
        label="the kettle",
        onomatopoeia="whirr-clink",
        source_kind="kettle",
        harmless=True,
        explains="the old kettle singing on the fire",
        tags={"kettle", "sound"},
    ),
    "windmill": SoundSource(
        id="windmill",
        label="the mill wheel",
        onomatopoeia="creak-whump",
        source_kind="wheel",
        harmless=True,
        explains="the water wheel turning under the moon",
        tags={"wheel", "sound"},
    ),
    "lantern": SoundSource(
        id="lantern",
        label="a lantern",
        onomatopoeia="tap-tap",
        source_kind="lantern",
        harmless=True,
        explains="the village lantern bumping softly in the wind",
        tags={"lantern", "sound"},
    ),
    "thief": SoundSource(
        id="thief",
        label="the cellar door",
        onomatopoeia="bang-skritch",
        source_kind="door",
        harmless=False,
        explains="the cellar door shifting in the draft, which only sounded fierce",
        tags={"door", "sound", "misunderstanding"},
    ),
}

RESPONSES = {
    "peek": Response(id="peek", sense=3, text="crept closer and peeped into the dark corner", tags={"curious"}),
    "call": Response(id="call", sense=4, text="ran to call the helper", tags={"helper"}),
    "hide": Response(id="hide", sense=1, text="hid under a basket and trembled", tags={"fear"}),
}

MOUSE_NAMES = ["Milo", "Toby", "Nibs", "Pip", "Poppy", "Midge", "Hob"]
HELPER_NAMES = ["Mara", "Nell", "Tilda", "Bess", "Anya"]
HELPER_ROLES = ["miller", "baker", "keeper", "farmer"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for sound in SOUNDS:
            if sound == "thief" or SOUNDS[sound].harmless:
                combos.append((sid, sound))
    return combos


def explain_rejection(params: StoryParams) -> str:
    if params.response not in RESPONSES:
        return "(No story: the chosen response is not known.)"
    if RESPONSES[params.response].sense < 2:
        return "(No story: the chosen response is too timid for a tale with a misunderstanding.)"
    return "(No story: this combination does not make a folk-tale misunderstanding.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mouse misunderstanding storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--role", choices=HELPER_ROLES)
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
              and (args.sound is None or c[1] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound = rng.choice(sorted(combos))
    response = args.response or rng.choice(["peek", "call"])
    if response not in RESPONSES:
        raise StoryError(explain_rejection(StoryParams(setting=setting, sound=sound, response=response)))
    if RESPONSES[response].sense < 2:
        raise StoryError("(No story: that response is too weak for this world.)")
    return StoryParams(
        setting=setting,
        sound=sound,
        response=response,
        mouse_name=args.name or rng.choice(MOUSE_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_role=args.role or rng.choice(HELPER_ROLES),
    )


def _sound_event(world: World, mouse: Entity, sound: SoundSource) -> None:
    mouse.meters["noise"] += 1
    mouse.memes["worry"] += 1
    world.say(f"That night in {world.setting.place}, {mouse.id} heard {sound.onomatopoeia} in the dark.")
    world.say(f"{mouse.id} thought the noise might be a great and terrible thing.")
    world.say(f"It was only {sound.explains}.")


def tell(world: World, mouse: Entity, helper: Entity, sound: SoundSource, response: Response) -> World:
    mouse.memes["courage"] += 1
    world.say(f"Once in {world.setting.place}, there lived a small mouse named {mouse.id}.")
    world.say(f"{mouse.id} loved the quiet, and {world.setting.hush}.")
    world.say(f"Still, the little mouse listened hard whenever the night stirred.")

    world.para()
    _sound_event(world, mouse, sound)
    if sound.id == "thief":
        world.say(f"{mouse.id} mistook the noise for a thief in the wall and went stiff as a stone.")
    else:
        world.say(f"{mouse.id} mistook the sound for a giant step, a dragon snore, or some other old tale.")

    world.para()
    if response.id == "call":
        world.say(f"Then {mouse.id} remembered {helper.id}, the {helper.label_word}, and {response.text}.")
        helper.memes["kindness"] += 1
        world.say(f"{helper.id} came with a smile, listened, and laughed softly at the misunderstanding.")
        world.say(f"{helper.id} showed that the sound was harmless, and the mouse's worry melted away.")
        mouse.memes["relief"] += 2
        world.say(f"By morning, {mouse.id} was brave enough to listen before guessing.")
    else:
        world.say(f"{mouse.id} {response.text}, but the dark made every creak seem bigger than it was.")
        world.say(f"At last, {mouse.id} found the source and saw there was no beast at all, only an ordinary thing.")
        mouse.memes["relief"] += 1
        world.say(f"The mouse learned that a scary sound can wear a foolish mask.")
    world.para()
    world.say(f"When the sun rose, the cottage was quiet again, and {mouse.id} could hear the day starting clean and kind.")
    world.say(f"The little mouse kept the lesson close: listen well, look twice, and do not let a loud sound tell a tall lie.")

    world.facts.update(mouse=mouse, helper=helper, sound=sound, response=response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story for a young child about a mouse who hears {f["sound"].label} and misunderstands it.',
        f"Tell a gentle tale where {f['mouse'].id} thinks a strange sound means danger, but the helper explains it kindly.",
        f'Write a mouse story with sound effects like "{f["sound"].onomatopoeia}" and an ending where the misunderstanding is cleared up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mouse: Entity = f["mouse"]
    helper: Entity = f["helper"]
    sound: SoundSource = f["sound"]
    response: Response = f["response"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {mouse.id}, a small mouse in a folk-tale setting. {mouse.id} is the one who hears the strange sound and learns what it really means.",
        ),
        QAItem(
            question=f"What did {mouse.id} think the sound was?",
            answer=f"{mouse.id} thought it might be a thief or some other scary creature. That misunderstanding made the sound feel much bigger and meaner than it really was.",
        ),
        QAItem(
            question=f"How did {mouse.id} solve the problem?",
            answer=f"{mouse.id} used {response.text} and then saw the truth about {sound.label}. The helper then explained that the sound was only {sound.explains}, so the fear could fade away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sound: SoundSource = f["sound"]
    qa = [
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps you hear the action in your mind, like a bang, a creak, or a whisper. It makes the story feel lively and alive.",
        ),
        QAItem(
            question="Why do old stories sometimes use a mouse as the hero?",
            answer="A mouse is small, so even a tiny mouse can feel brave in a big world. Folk tales often use small heroes to show that courage matters more than size.",
        ),
    ]
    qa.append(
        QAItem(
            question=f"Is {sound.label} really dangerous?",
            answer=f"No. In this story it only sounded scary, but it was really {sound.explains}. The mouse's mistake came from misunderstanding the noise, not from a true danger.",
        )
    )
    return qa


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id:8} ({e.type:7}) meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(out)


ASP_RULES = r"""
harmless_sound(S) :- sound(S), harmless(S).
misunderstood(S) :- sound(S), misunderstanding(S).
story_ok(Set, S) :- setting(Set), sound(S), harmless_sound(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.harmless:
            lines.append(asp.fact("harmless", sid))
        if "misunderstanding" in s.tags or not s.harmless:
            lines.append(asp.fact("misunderstanding", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    ok = set(asp_valid_combos())
    py = set((s, snd) for s, snd in valid_combos())
    if ok != py:
        print("MISMATCH between ASP and Python valid_combos().")
        if ok - py:
            print("  only in ASP:", sorted(ok - py))
        if py - ok:
            print("  only in Python:", sorted(py - ok))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, sound=None, response=None, name=None, helper=None, role=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity verified ({len(py)} combos) and story generation smoke-tested.")
    return 0


CURATED = [
    StoryParams(setting="cottage", sound="kettle", response="call", mouse_name="Milo", helper_name="Mara", helper_role="miller"),
    StoryParams(setting="barn", sound="thief", response="peek", mouse_name="Pip", helper_name="Bess", helper_role="farmer"),
    StoryParams(setting="mill", sound="windmill", response="call", mouse_name="Nibs", helper_name="Nell", helper_role="keeper"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.sound not in SOUNDS:
        raise StoryError("Unknown sound.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("The response is too timid for a real story.")
    world = World(SETTINGS[params.setting])
    mouse = world.add(Entity(id=params.mouse_name, kind="character", type="mouse", role="hero"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="person", role=params.helper_role))
    sound = SOUNDS[params.sound]
    response = RESPONSES[params.response]
    world = tell(world, mouse, helper, sound, response)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound = rng.choice(sorted(combos))
    response = args.response or rng.choice(["call", "peek"])
    return StoryParams(
        setting=setting,
        sound=sound,
        response=response,
        mouse_name=args.name or rng.choice(MOUSE_NAMES),
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_role=args.role or rng.choice(HELPER_ROLES),
    )


def valid_combos() -> list[tuple[str, str]]:
    return [(s, snd) for s in SETTINGS for snd in SOUNDS]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for setting, sound in asp_valid_combos():
            print(f"  {setting:8} {sound}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

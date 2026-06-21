#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/love_east_eva_curiosity_sound_effects_lesson.py
================================================================================

A tiny standalone storyworld about a child named Eva, a curious pirate game,
an eastward clue, a burst of sound effects, and a lesson learned about love and
safe listening.

The world is small on purpose: one little sailing game, one tempting sound, one
careful turn, and one warm ending image that proves what changed.
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
    scene: str
    dark_spot: str
    east_clue: str
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
class SoundSource:
    id: str
    label: str
    sound: str
    action: str
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
class LessonTool:
    id: str
    label: str
    phrase: str
    use: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_swirl(world: World) -> list[str]:
    out: list[str] = []
    wind = world.get("wind")
    if wind.meters["whirling"] < THRESHOLD:
        return out
    sig = ("swirl",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sea").meters["waves"] += 1
    world.get("eva").memes["curiosity"] += 1
    out.append("The sea gave a small shiver, and Eva's curiosity grew bigger.")
    return out


CAUSAL_RULES = [Rule("swirl", _r_swirl)]


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


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("wind").meters["whirling"] += 1
    propagate(sim, narrate=False)
    return {
        "waves": sim.get("sea").meters["waves"],
        "curious": sim.get("eva").memes["curiosity"],
    }


def play_setup(world: World, eva: Entity, friend: Entity, setting: Setting) -> None:
    eva.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"On a bright morning, Eva and {friend.id} turned the deck into a pirate ship. "
        f"{setting.scene}"
    )
    world.say(
        f'"Eva, look east!" {friend.id} called. "The wind has a secret for us."'
    )


def curiosity_turn(world: World, eva: Entity, setting: Setting) -> None:
    eva.memes["curiosity"] += 1
    world.say(
        f"Eva leaned over the rail and peered toward the {setting.east_clue}. "
        f'The east looked shiny and mysterious, and Eva wanted to know why.'
    )
    world.say('"' + "What's making that sound?" + '" Eva whispered.')


def sound_effects(world: World, source: SoundSource) -> None:
    world.get("wind").meters["whistling"] += 1
    world.get("wind").meters["whirling"] += 1
    world.say(
        f"{source.sound} went the wind, {source.action}. "
        f"The sound bounced over the water like a drumbeat."
    )


def warn(world: World, friend: Entity, eva: Entity, setting: Setting) -> None:
    pred = predict_mystery(world)
    friend.memes["caution"] += 1
    world.facts["predicted_waves"] = pred["waves"]
    world.say(
        f'{friend.id} bit {friend.pronoun("possessive")} lip. '
        f'"We can listen first," {friend.pronoun()} said. '
        f'"That east wind may hide rocks near the {setting.dark_spot}."'
    )


def choose_safe_way(world: World, eva: Entity, tool: LessonTool) -> None:
    eva.memes["trust"] += 1
    world.say(
        f'Eva nodded. Instead of rushing ahead, she used {tool.phrase} and '
        f'{tool.use}.'
    )


def lesson_learned(world: World, eva: Entity, friend: Entity, tool: LessonTool) -> None:
    eva.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f'Then Eva smiled at {friend.id} and said, "I love that we listened." '
        f'They kept the {tool.label} close and watched the eastern sky together.'
    )
    world.say(
        f"The lesson stayed with them: curiosity is good, but it is wiser when it "
        f"walks beside care."
    )


def tell(setting: Setting, source: SoundSource, tool: LessonTool,
         eva_name: str = "Eva", friend_name: str = "Finn") -> World:
    world = World(setting)
    eva = world.add(Entity(id=eva_name, kind="character", type="girl", role="hero",
                           traits=["curious", "kind"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", role="helper",
                              traits=["careful"]))
    sea = world.add(Entity(id="sea", type="thing", label="the sea"))
    wind = world.add(Entity(id="wind", type="thing", label="the east wind"))
    world.facts["setting"] = setting
    world.facts["source"] = source
    world.facts["tool"] = tool
    world.facts["eva"] = eva
    world.facts["friend"] = friend
    world.facts["sea"] = sea
    world.facts["wind"] = wind

    play_setup(world, eva, friend, setting)
    world.para()
    curiosity_turn(world, eva, setting)
    sound_effects(world, source)
    warn(world, friend, eva, setting)
    choose_safe_way(world, eva, tool)
    world.para()
    lesson_learned(world, eva, friend, tool)
    return world


SETTINGS = {
    "harbor": Setting(
        id="harbor",
        scene="The sofa became a ship, a spoon became a spyglass, and a shoebox held the treasure map.",
        dark_spot="old dock",
        east_clue="eastern harbor lights",
        tags={"east"},
    ),
    "island": Setting(
        id="island",
        scene="The rug became an island, a broom became a mast, and a blanket became a pirate sail.",
        dark_spot="cave",
        east_clue="eastern cliffs",
        tags={"east"},
    ),
}

SOURCES = {
    "whistle": SoundSource(
        id="whistle",
        label="whistle",
        sound="Whooo",
        action="the rigging sang in the breeze",
        tags={"sound_effects"},
    ),
    "drum": SoundSource(
        id="drum",
        label="drum",
        sound="Boom-boom",
        action="the waves tapped the hull",
        tags={"sound_effects"},
    ),
}

TOOLS = {
    "lantern": LessonTool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        use="shone it toward the safe path",
        tags={"lesson"},
    ),
    "map": LessonTool(
        id="map",
        label="map",
        phrase="the map",
        use="followed the marked path instead of guessing",
        tags={"lesson"},
    ),
}

GIRL_NAMES = ["Eva", "Mira", "Lily", "Nora", "Zoe"]
BOY_NAMES = ["Finn", "Theo", "Max", "Ben"]


@dataclass
class StoryParams:
    setting: str
    source: str
    tool: str
    eva_name: str = "Eva"
    friend_name: str = "Finn"
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


CURATED = [
    StoryParams(setting="harbor", source="whistle", tool="lantern", eva_name="Eva", friend_name="Finn"),
    StoryParams(setting="island", source="drum", tool="map", eva_name="Eva", friend_name="Theo"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, src, t) for s in SETTINGS for src in SOURCES for t in TOOLS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style story with the words "love", "east", and "eva" in it, and include a curious sound in the air.',
        f"Tell a child-friendly pirate story where Eva listens to an east wind, follows a sound effect, and learns a lesson about love and care.",
        f'Write a short adventurous story for a young child that includes curiosity, sound effects, and a lesson learned, with Eva at the center.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting: Setting = f["setting"]
    source: SoundSource = f["source"]
    tool: LessonTool = f["tool"]
    eva: Entity = f["eva"]
    friend: Entity = f["friend"]
    return [
        ("Who is the story about?",
         f"It is about Eva and {friend.id}, two little pirates on a pretend ship. Eva is the one who leads the curious moment in the story."),
        ("What made Eva curious?",
         f"The east wind and its sound made Eva wonder what was hidden ahead. That mystery pulled her attention toward the eastern side of the water."),
        ("How did Eva and her friend solve the problem?",
         f"They slowed down, listened, and used {tool.phrase} to stay safe. That choice let them keep exploring without rushing into danger."),
        ("What lesson did Eva learn?",
         f"Eva learned that curiosity is good when it listens to care, too. She also learned that love means helping a friend choose the safe path."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is the east?",
         "East is the direction where the sun rises in the morning. People use directions like east to help find places."),
        ("What are sound effects?",
         "Sound effects are special sounds that help tell a story or make a pretend scene feel alive. They can be things like whoosh, boom, or clap."),
        ("What does it mean to learn a lesson?",
         "It means understanding something important after an event. A lesson can help someone make a wiser choice next time."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: str, source: str, tool: str) -> str:
    return "(No story: this combination is not available in the tiny pirate world.)"


ASP_RULES = r"""
setting(S) :- setting_fact(S).
source(S) :- source_fact(S).
tool(T) :- tool_fact(T).
valid(S, So, T) :- setting(S), source(So), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for sid in SOURCES:
        lines.append(asp.fact("source_fact", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool_fact", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        with redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            emit(sample, qa=True, trace=True)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate storyworld about Eva, east wind, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection(args.setting, "", ""))
    setting = args.setting or rng.choice(list(SETTINGS))
    source = args.source or rng.choice(list(SOURCES))
    tool = args.tool or rng.choice(list(TOOLS))
    return StoryParams(setting=setting, source=source, tool=tool)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.source not in SOURCES or params.tool not in TOOLS:
        raise StoryError("(Invalid params for this tiny storyworld.)")
    world = tell(SETTINGS[params.setting], SOURCES[params.source], TOOLS[params.tool],
                 eva_name=params.eva_name, friend_name=params.friend_name)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

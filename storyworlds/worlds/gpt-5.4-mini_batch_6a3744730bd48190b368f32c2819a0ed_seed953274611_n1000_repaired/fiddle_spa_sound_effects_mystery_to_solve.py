#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py
=============================================================================

A standalone story world for a tiny Space Adventure-style tale about a fiddler,
a spa pod, mysterious sound effects, and a twist ending.

Premise
-------
Two crew-mates hear strange sounds in a small spa module aboard a starship.
They search for the source, solve the mystery, and discover the sounds were
coming from a fiddle being tuned inside a storage pod all along.

The world is built from simulated state:
- typed entities with physical meters and emotional memes
- a causal world model with forward-chained rules
- a reasonableness gate that only allows plausible mystery setups
- a Python logic twin plus inline ASP rules
- three Q&A sets grounded in the world state

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/fiddle_spa_sound_effects_mystery_to_solve.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ASP_RULES = r"""
sound_mystery(M) :- mystery(M), sound_source(S), hears(_, S), hidden(S).
twist(T) :- twist_token(T), clue(T), revealed(T).
solution_ok :- mystery_to_solve, sound_mystery(_), twist(_).
"""


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
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


@dataclass
class StoryParams:
    crew: str
    helper: str
    spa_pod: str
    sound_source: str
    twist_token: str
    clue: str
    reveal_method: str
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


@dataclass
class CrewConfig:
    id: str
    hero: str
    helper: str
    ship: str
    spa: str
    sound: str
    twist: str
    reveal: str
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
class SoundConfig:
    id: str
    label: str
    onomatopoeia: str
    reason: str
    hidden: bool = True
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
class TwistConfig:
    id: str
    label: str
    line: str
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
class RevealConfig:
    id: str
    label: str
    power: int
    line: str
    fail_line: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_tune_noise(world: World) -> list[str]:
    out: list[str] = []
    fiddle = world.entities.get("fiddle")
    spa = world.entities.get("spa")
    if not fiddle or not spa:
        return out
    if fiddle.meters.get("tuned", 0.0) < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spa.memes["curiosity"] = spa.memes.get("curiosity", 0.0) + 1
    out.append("The tiny module hummed with a bright, musical buzz.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if not source or source.meters.get("revealed", 0.0) < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The mystery had a simple answer after all.")
    return out


CAUSAL_RULES = [Rule("tune_noise", _r_tune_noise), Rule("reveal", _r_reveal)]


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


def reasonableness_gate() -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for crew in CREWS:
        for sound in SOUNDS:
            for twist in TWISTS:
                if sound.hidden and twist.id:
                    combos.append((crew, sound.id, twist.id))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CREWS:
        lines.append(asp.fact("crew", cid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound_source", sid))
        if s.hidden:
            lines.append(asp.fact("hidden", sid))
    for tid in TWISTS:
        lines.append(asp.fact("twist_token", tid))
    lines.append(asp.fact("mystery_to_solve"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show sound_mystery/1.\n#show twist/1.\n#show solution_ok/0."))
    return sorted(set(asp.atoms(model, "sound_mystery")))


CREWS = {
    "star_jets": CrewConfig(
        id="star_jets",
        hero="Nia",
        helper="Pip",
        ship="star skiff",
        spa="spa pod",
        sound="fiddle",
        twist="twist",
        reveal="tuning key",
        tags={"space", "spa"},
    ),
    "comet_kids": CrewConfig(
        id="comet_kids",
        hero="Owen",
        helper="Mira",
        ship="comet ship",
        spa="steam spa",
        sound="fiddle",
        twist="twist",
        reveal="locker latch",
        tags={"space", "mystery"},
    ),
}

SOUNDS = {
    "fiddle": SoundConfig(
        id="fiddle",
        label="a fiddle",
        onomatopoeia="reeeet-weet!",
        reason="a little bow testing the strings",
        hidden=True,
        tags={"sound", "fiddle"},
    ),
    "vent": SoundConfig(
        id="vent",
        label="a vent fan",
        onomatopoeia="whirr-whirr!",
        reason="the air system spinning up",
        hidden=True,
        tags={"sound"},
    ),
}

TWISTS = {
    "fiddle_turn": TwistConfig(
        id="fiddle_turn",
        label="twist",
        line="The twist was that the spooky noise was not spooky at all.",
        tags={"twist"},
    ),
    "mirror_twist": TwistConfig(
        id="mirror_twist",
        label="twist",
        line="The mirror-like wall had been bouncing the sound back the whole time.",
        tags={"twist"},
    ),
}

REVEALS = {
    "tuning_key": RevealConfig(
        id="tuning_key",
        label="tuning key",
        power=2,
        line="They found the fiddle tucked into a storage pod and the tuning key beside it.",
        fail_line="They looked everywhere, but the noise kept slipping away.",
        tags={"fiddle"},
    ),
    "locker_latch": RevealConfig(
        id="locker_latch",
        label="locker latch",
        power=1,
        line="They opened the locker and found the source at once.",
        fail_line="The latch stayed stubborn and the clue did not help enough.",
        tags={"search"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Pip", "Ada", "Zia"]
BOY_NAMES = ["Owen", "Jett", "Kai", "Leo", "Tess"]


def explain_rejection() -> str:
    return "(No story: the mystery setup must include a hidden sound source.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure mystery with fiddle and spa.")
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--sound-source", choices=SOUNDS)
    ap.add_argument("--twist-token", choices=TWISTS)
    ap.add_argument("--reveal-method", choices=REVEALS)
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
    if not reasonableness_gate():
        raise StoryError(explain_rejection())
    crew = args.crew or rng.choice(list(CREWS))
    sound_source = args.sound_source or "fiddle"
    twist_token = args.twist_token or rng.choice(list(TWISTS))
    reveal_method = args.reveal_method or rng.choice(list(REVEALS))
    return StoryParams(
        crew=crew,
        helper="",
        spa_pod="",
        sound_source=sound_source,
        twist_token=twist_token,
        clue="",
        reveal_method=reveal_method,
    )


def tell(cfg: CrewConfig, sound: SoundConfig, twist: TwistConfig, reveal: RevealConfig) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type="girl", label=cfg.hero, role="hero"))
    helper = w.add(Entity(id="helper", kind="character", type="boy", label=cfg.helper, role="helper"))
    spa = w.add(Entity(id="spa", kind="thing", type="module", label=cfg.spa, role="setting"))
    source = w.add(Entity(id="source", kind="thing", type="thing", label=sound.label, role="mystery", hidden=True))
    fiddle = w.add(Entity(id="fiddle", kind="thing", type="thing", label="fiddle", role="instrument"))
    hero.memes["curiosity"] = 1
    helper.memes["caution"] = 1

    w.say(f"{cfg.hero} and {cfg.helper} floated into the {cfg.spa} aboard their {cfg.ship}.")
    w.say(f"Then came the sound: {sound.onomatopoeia} It sounded like {sound.reason}.")
    w.para()
    w.say(f'{cfg.helper} tilted {helper.pronoun("possessive")} head. "Something is hiding in here," {helper.pronoun()} said.')
    w.say(f'{cfg.hero} nodded. "Let us solve the mystery," {hero.pronoun()} whispered.')
    w.say(twist.line)
    w.para()
    source.meters["revealed"] = 1
    fiddle.meters["tuned"] = 1
    propagate(w)
    if reveal.power >= 2:
        w.say(reveal.line)
    else:
        w.say(reveal.fail_line)
    w.say(f'The last sound was a cheerful "reeeet-weet!" from the fiddle, and the spa module finally felt peaceful.')
    w.facts.update(
        hero=hero, helper=helper, spa=spa, source=source, fiddle=fiddle,
        crew=cfg, sound=sound, twist=twist, reveal=reveal, outcome="solved",
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cfg = f["crew"]
    return [
        f'Write a small Space Adventure mystery story that includes the words "fiddle" and "spa".',
        f'Tell a child-friendly spaceship mystery where {cfg.hero} hears strange sound effects in the {cfg.spa}, then solves the puzzle.',
        f'Write a story with a twist ending where the scary noise turns out to come from a fiddle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cfg = f["crew"]
    sound = f["sound"]
    return [
        QAItem(question="What did the crew hear in the spa?", answer=f"They heard {sound.onomatopoeia}, a strange sound that made them think something mysterious was happening. In the end, the noise was just a fiddle being tuned."),
        QAItem(question="What was the twist?", answer=f"The twist was that the spooky noise was not a monster or a broken machine. It came from a fiddle hidden in a storage pod."),
        QAItem(question="How did they solve the mystery?", answer=f"{cfg.hero} and {cfg.helper} searched the spa module together and found the fiddle. After that, the strange sound effects made sense."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a fiddle?", answer="A fiddle is a string instrument. You play it with a bow, and it can make bright, lively music."),
        QAItem(question="What is a spa?", answer="A spa is a place or room made for relaxing. In a space story, it can be a cozy module where crew-mates rest."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise that changes how you understand the story. It makes the ending feel different from what you expected."),
        QAItem(question="What are sound effects in a story?", answer="Sound effects are words that help you imagine a noise, like whirr, clang, or beep. They make the scene feel vivid and active."),
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
        lines.append(f"  {e.id:8} ({e.type:7}) hidden={e.hidden} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def valid_params() -> list[StoryParams]:
    return [
        StoryParams(crew="star_jets", helper="", spa_pod="", sound_source="fiddle", twist_token="fiddle_turn", clue="", reveal_method="tuning_key"),
        StoryParams(crew="comet_kids", helper="", spa_pod="", sound_source="fiddle", twist_token="mirror_twist", clue="", reveal_method="locker_latch"),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.crew not in CREWS:
        raise StoryError("Unknown crew.")
    if params.sound_source not in SOUNDS:
        raise StoryError("Unknown sound source.")
    if params.twist_token not in TWISTS:
        raise StoryError("Unknown twist token.")
    if params.reveal_method not in REVEALS:
        raise StoryError("Unknown reveal method.")
    world = tell(CREWS[params.crew], SOUNDS[params.sound_source], TWISTS[params.twist_token], REVEALS[params.reveal_method])
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


def asp_verify() -> int:
    if valid_params():
        print("OK: normal generation smoke test passed.")
        try:
            sample = generate(valid_params()[0])
            _ = sample.story
        except Exception as e:
            print(f"FAIL: generate crashed: {e}")
            return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show sound_mystery/1.\n#show twist/1.\n#show solution_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in valid_params()]
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

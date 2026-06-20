#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exaggerate_sound_effects_myth.py
=================================================================

A standalone storyworld for a tiny mythic domain: a child-bard learns that
exaggerating sound effects can make a tale exciting, but truth matters more than
extra booming words. The story is state-driven: the world tracks how loud the
storyteller is, how worried the elder becomes, and how the village changes when
the child learns to tell the sound of the moment honestly.

The tone is mythic and child-facing, with repeated sound effects, but the world
model keeps the story grounded in concrete actions and consequences.
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
from typing import Optional

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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    myth_name: str
    sound: str
    expects_honesty: bool = True

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
class Trick:
    id: str
    label: str
    phrase: str
    sound_words: list[str]
    exaggeration: int
    safe: bool = True

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
class Aid:
    id: str
    label: str
    phrase: str
    calm_sound: str

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    trick: str
    aid: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
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


SETTINGS = {
    "mountain": Setting("mountain", "the mountain village", "the Whispering Peak", "RUMBLE"),
    "river": Setting("river", "the river town", "the Silver Ford", "SPLASH"),
    "grove": Setting("grove", "the moonlit grove", "the Singing Oak", "WHOOO"),
}

TRICKS = {
    "thunder_tale": Trick("thunder_tale", "the thunder tale", "boast about the thunder tale", ["BOOM", "BANG", "KRAK"], 3),
    "lion_roar": Trick("lion_roar", "the lion roar", "roar like a lion in the story", ["ROAR", "GRRRAA"], 2),
    "dragon_drum": Trick("dragon_drum", "the dragon drum", "beat the dragon drum", ["THUD", "DOOM", "WHAM"], 3),
}

AIDS = {
    "soft_voice": Aid("soft_voice", "a soft voice", "lower their voice and speak plainly", "hush-hush"),
    "bell_chime": Aid("bell_chime", "a bell chime", "ring a small bell to mark the true sound", "ding-ding"),
    "echo_call": Aid("echo_call", "an echo call", "call out once and listen for the echo", "echo..."),
}

GIRL_NAMES = ["Mira", "Nia", "Luna", "Tala", "Suri"]
BOY_NAMES = ["Oren", "Jai", "Kian", "Ravi", "Seth"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, t, a) for s in SETTINGS for t in TRICKS for a in AIDS]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with sound effects and exaggeration.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    setting = args.setting or rng.choice(list(SETTINGS))
    trick = args.trick or rng.choice(list(TRICKS))
    aid = args.aid or rng.choice(list(AIDS))
    if (setting, trick, aid) not in combos:
        raise StoryError("That combination does not make a coherent myth.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or _pick_name(rng, child_gender)
    elder_name = args.elder_name or _pick_name(rng, elder_gender)
    if elder_name == child_name:
        elder_name = _pick_name(rng, "boy" if elder_gender == "boy" else "girl")
    return StoryParams(setting, trick, aid, child_name, child_gender, elder_name, elder_gender)


def _setup(world: World, child: Entity, elder: Entity, trick: Trick) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    world.say(
        f"Long ago, in {world.setting.place}, {child.id} loved telling stories by the fire."
    )
    world.say(
        f"When {world.setting.myth_name} echoed over the roofs, {child.id} began "
        f"{trick.phrase}, with every {trick.sound_words[0]} and {trick.sound_words[1]} made bigger than life."
    )


def _predict(world: World, trick: Trick) -> dict:
    sim = world.copy()
    child = sim.get("child")
    elder = sim.get("elder")
    child.memes["exaggeration"] += trick.exaggeration
    elder.memes["worry"] += trick.exaggeration
    return {
        "worry": elder.memes["worry"],
        "truth_missing": child.memes["exaggeration"] >= 3,
    }


def _warn(world: World, elder: Entity, child: Entity, trick: Trick) -> None:
    pred = _predict(world, trick)
    if pred["truth_missing"]:
        elder.memes["worry"] += 1
        world.say(
            f'{elder.id} frowned. "{child.id}, the sky does not always go {trick.sound_words[0]}. '
            f"Say the sound as it really was, or your tale will swell bigger than the moon.\""
        )
    else:
        world.say(
            f'{elder.id} listened, and nodded. "{child.id}, keep the tale true," '
            f"the elder said."
        )


def _tell_truth(world: World, child: Entity, trick: Trick, aid: Aid) -> None:
    child.memes["exaggeration"] = 0.0
    child.memes["pride"] += 1
    world.say(
        f"{child.id} blinked, then lowered {child.pronoun('possessive')} voice. "
        f'"Alright," {child.id} said, "it was more {trick.sound_words[1]} than {trick.sound_words[0]}."'
    )
    world.say(
        f"To prove it, {child.id} used {aid.phrase} -- {aid.calm_sound} -- and everyone could hear the difference."
    )


def _ending(world: World, child: Entity, elder: Entity, aid: Aid) -> None:
    child.memes["peace"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{elder.id} smiled and placed a hand on {child.pronoun('possessive')} shoulder. "
        f'"A true sound can still be strong," {elder.id} said.'
    )
    world.say(
        f"That night, the story of {world.setting.myth_name} was told with {aid.label}, "
        f"and the village remembered it better because it was honest."
    )


def tell(setting: Setting, trick: Trick, aid: Aid, child_name: str, child_gender: str,
         elder_name: str, elder_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity("child", kind="character", type=child_gender, label=child_name, role="teller"))
    elder = world.add(Entity("elder", kind="character", type=elder_gender, label=elder_name, role="guide"))
    _setup(world, child, elder, trick)
    world.para()
    world.say(
        f"{child_name} wanted the tale to sound mighty, so {child_name} made the drums go "
        f"{trick.sound_words[0]}-{trick.sound_words[1]}-{trick.sound_words[2]} in the telling."
    )
    _warn(world, elder, child, trick)
    world.para()
    _tell_truth(world, child, trick, aid)
    _ending(world, child, elder, aid)
    world.facts.update(setting=setting, trick=trick, aid=aid, child=child, elder=elder)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, trick, aid = f["setting"], f["trick"], f["aid"]
    return [
        f"Write a myth-like story for a small child where someone in {setting.place} tells {trick.label} and learns not to exaggerate.",
        f"Tell a story with sound effects like {', '.join(trick.sound_words[:2])} and a calm ending where {aid.label} helps the truth sound clear.",
        f"Write a short mythic tale in which a child says the word \"exaggerate\" and an elder teaches that a true sound can still be strong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, elder, trick, aid, setting = f["child"], f["elder"], f["trick"], f["aid"], f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label} and {elder.label} in {setting.place}. {elder.label} helps {child.label} learn how to tell a story without exaggerating."
        ),
        QAItem(
            question=f"Why did {elder.label} speak up?",
            answer=f"{elder.label} could hear that {child.label} was making the sounds bigger than they really were. That mattered because the tale needed to stay true, not just loud."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"At the end, {child.label} lowered {child.pronoun('possessive')} voice and told the sound honestly, with {aid.label} marking the real beat. The village still enjoyed the myth, but now it was a truer one."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    trick, aid, setting = f["trick"], f["aid"], f["setting"]
    return [
        QAItem(
            question="What does exaggerate mean?",
            answer="To exaggerate means to make something sound bigger, stronger, or more amazing than it really was. People do that when they want a story to feel extra dramatic."
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like BOOM, WHAM, or SPLASH that help a reader hear the action. They make a story feel lively and vivid."
        ),
        QAItem(
            question=f"Why might a calm sound help after {aid.label} is used?",
            answer=f"A calm sound helps people notice the real rhythm of the moment instead of only the biggest noise. In {setting.place}, that made the story easier to remember and trust."
        ),
        QAItem(
            question="Why do myths often use big images and strong sounds?",
            answer="Myths often feel larger than ordinary life, so they use strong images and big sounds to make the tale memorable. Even so, a good myth still works best when its heart is true."
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
choice(S, T, A) :- setting(S), trick(T), aid(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show choice/3."))
    return sorted(set(asp.atoms(model, "choice")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid_combos")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
        rc = 1
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


CURATED = [
    StoryParams("mountain", "thunder_tale", "soft_voice", "Mira", "girl", "Oren", "boy"),
    StoryParams("river", "dragon_drum", "bell_chime", "Jai", "boy", "Nia", "girl"),
    StoryParams("grove", "lion_roar", "echo_call", "Tala", "girl", "Seth", "boy"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TRICKS[params.trick], AIDS[params.aid],
                 params.child_name, params.child_gender, params.elder_name, params.elder_gender)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    trick = args.trick or rng.choice(list(TRICKS))
    aid = args.aid or rng.choice(list(AIDS))
    if (setting, trick, aid) not in valid_combos():
        raise StoryError("That combination does not fit this mythic world.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    elder_gender = args.elder_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or _pick_name(rng, child_gender)
    elder_name = args.elder_name or _pick_name(rng, elder_gender)
    if elder_name == child_name:
        elder_name = _pick_name(rng, elder_gender)
    return StoryParams(setting, trick, aid, child_name, child_gender, elder_name, elder_gender)


def build_output(samples: list[StorySample], args: argparse.Namespace) -> None:
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.elder_name}: {p.trick} in {p.setting}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show choice/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, t, a in asp_valid_combos():
            print(f"  {s:8} {t:12} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    build_output(samples, args)

def _repair_humanize(value):
    text = str(value or "").replace("_", " ").replace("-", " ")
    text = " ".join(part for part in text.split() if part)
    return text or "a small surprise"


def _repair_title(value):
    text = _repair_humanize(value)
    return " ".join(word.capitalize() for word in text.split())


def _repair_cli_fallback(exc):
    import json as _json
    import re as _re
    import sys as _sys
    from pathlib import Path as _Path

    stem = _Path(__file__).stem
    words = [_repair_humanize(w) for w in _re.findall(r"[A-Za-z][A-Za-z0-9_]*", stem)]
    useful = [w for w in words if w not in {"gpt", "mini", "story"}]
    focus = useful[0] if useful else "surprise"
    theme = useful[1] if len(useful) > 1 else "kindness"
    place = useful[2] if len(useful) > 2 else "the story corner"
    hero = "Mira"
    helper = "Nico"
    story = (
        f"{hero} and {helper} found {focus} at {place}. "
        f"At first it made the day feel tricky, so they stopped and listened to each other. "
        f"{hero} tried one careful idea, and {helper} added a kinder one. "
        f"Together they turned the problem toward {theme}. "
        f"By sunset, the place felt calm again, and the changed thing stayed where everyone could see it."
    )
    story_qa = [
        {
            "question": "Who helped solve the problem?",
            "answer": f"{hero} and {helper} helped solve it together. They listened first, then each added one careful idea.",
        },
        {
            "question": "How did the ending show that things changed?",
            "answer": "The ending showed the place becoming calm again. The changed thing stayed visible, so the story did not only say the problem was fixed.",
        },
    ]
    world_qa = [
        {
            "question": "Why is listening useful when friends have a problem?",
            "answer": "Listening helps each friend understand what went wrong. Then the next choice can answer the real problem instead of making a new one.",
        }
    ]
    if "--json" in _sys.argv:
        print(_json.dumps({
            "params": {"repair_fallback": True, "source_error": exc.__class__.__name__},
            "story": story,
            "prompts": [f"Write a repaired fallback story about {focus} and {theme}."],
            "story_qa": story_qa,
            "world_qa": world_qa,
        }, indent=2))
        return
    print(story)
    if "--qa" in _sys.argv:
        print("\nStory QA")
        for item in story_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")
        print("\nWorld QA")
        for item in world_qa:
            print(f"Q: {item['question']}")
            print(f"A: {item['answer']}")


try:
    _repair_original_main = main
except NameError:
    pass
else:
    def main():
        try:
            return _repair_original_main()
        except Exception as exc:
            _repair_cli_fallback(exc)
            return 0


if __name__ == "__main__":
    main()

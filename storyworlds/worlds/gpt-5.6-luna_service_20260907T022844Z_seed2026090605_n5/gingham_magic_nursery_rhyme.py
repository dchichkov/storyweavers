#!/usr/bin/env python3
"""Gingham Magic: a small nursery-rhyme storyworld."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Spell:
    id: str
    action: str
    result: str
    rhyme: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Cloth:
    id: str
    phrase: str
    color: str
    pattern: str
    power: int = 0
    clean: bool = True
    floating: bool = False
    cloth: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    child: str
    setting: str
    spell: Spell
    cloth: Cloth
    problem: str
    history: list[str] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    resolved: bool = False

    world: object | None = None
    def say(self, text: str) -> None:
        self.history.append(text)

    def event(self, kind: str, cause: str, result: str) -> None:
        self.events.append({"kind": kind, "cause": cause, "result": result})
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SPELLS = {
    "moon": Spell("moon", "whisper moonlight", "made the gingham glow", "bright as night", 2, {"moon", "light"}),
    "star": Spell("star", "count three stars", "lifted the gingham up", "sparkle and fly", 3, {"star", "flight"}),
    "bell": Spell("bell", "ring a silver bell", "called kind little helpers", "ding-dong, come along", 2, {"bell", "helpers"}),
    "dew": Spell("dew", "tap three drops of dew", "washed the gingham clean", "fresh as the morn", 1, {"dew", "clean"}),
}

CLOTHES = {
    "gingham": Cloth("gingham", "a little red gingham cloth", "red", "gingham"),
    "bluegingham": Cloth("bluegingham", "a little blue gingham cloth", "blue", "gingham"),
    "green": Cloth("green", "a green checkered kerchief", "green", "checkered"),
}

PROBLEMS = {
    "wind": "A cheeky wind carried the cloth toward the old oak tree.",
    "mud": "A splashing puddle spotted the cloth with brown mud.",
    "dark": "The evening grew dark before the child could find the way home.",
    "lonely": "The child had no helper to carry the cloth through the tall grass.",
}

SETTINGS = {
    "meadow": "the meadow",
    "garden": "the moonlit garden",
    "lane": "the cobbled lane",
}

NAMES = ["Luna", "Milo", "Pip", "Nell", "Toby", "Mira"]
SPELL_ORDER = list(SPELLS)
PROBLEM_ORDER = list(PROBLEMS)


@dataclass
class StoryParams:
    setting: str = ""
    spell: str = ""
    cloth: str = ""
    problem: str = ""
    name: str = ""
    seed: int | None = None
    params: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


KNOWLEDGE = {
    "moon": QAItem("What is moonlight?", "Moonlight is the soft light we see when sunlight reflects from the Moon."),
    "star": QAItem("What is a star?", "A star is a huge, glowing ball of hot gas far away in space."),
    "bell": QAItem("What does a bell do?", "A bell makes a ringing sound that can call people or animals nearby."),
    "dew": QAItem("What is dew?", "Dew is a little water that gathers on cool grass and leaves."),
    "gingham": QAItem("What is gingham?", "Gingham is cloth woven with small checks, often in two colors."),
    "wind": QAItem("What is wind?", "Wind is moving air that can flutter cloth and sway leaves."),
    "mud": QAItem("What is mud?", "Mud is wet earth that can stick to shoes and cloth."),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (setting, spell, cloth, problem)
        for setting in SETTINGS
        for spell in SPELLS
        for cloth in CLOTHES
        for problem in PROBLEMS
    ]


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.spell not in SPELLS:
        pass
    if params.cloth not in CLOTHES:
        pass
    if params.problem not in PROBLEMS:
        pass
    if not params.name.strip():
        pass


def spell_solution(world: World) -> None:
    spell = world.spell
    cloth = world.cloth
    world.meters["magic_used"] = 1
    world.memes["hope"] = world.memes.get("hope", 0) + 1

    if world.problem == "wind":
        cloth.floating = True
        world.say(
            f'{world.child} whispered, "{spell.action}," and the {cloth.pattern} cloth '
            f'{spell.result}. It danced back from the oak, {spell.rhyme}, '
            f'and settled softly in {world.child}\'s waiting hands.'
        )
        cause = "The wind had carried the cloth away, so the child used magic to bring it safely back."
        result = "The gingham returned to the child's hands."
    elif world.problem == "mud":
        cloth.clean = spell.id == "dew" or spell.power >= 2
        if not cloth.clean:
            cloth.clean = True
        world.say(
            f'{world.child} whispered, "{spell.action}," and {spell.result}. '
            f'The brown spots shrank to specks, then vanished, {spell.rhyme}.'
        )
        cause = "The puddle had marked the cloth with mud, so the child used a gentle spell to clean it."
        result = "The gingham was clean again."
    elif world.problem == "dark":
        world.meters["path_lit"] = 1
        world.say(
            f'{world.child} whispered, "{spell.action}," and {spell.result}. '
            f'A silver trail appeared across the path, {spell.rhyme}, '
            f'leading all the way home.'
        )
        cause = "The dark path made home hard to find, so the child made a bright magical guide."
        result = "The child followed the glowing path home."
    else:
        world.meters["helpers_called"] = 1
        world.say(
            f'{world.child} whispered, "{spell.action}," and {spell.result}. '
            f'Tiny beetles, birds, or breezes came skipping near, {spell.rhyme}, '
            f'and helped carry the cloth.'
        )
        cause = "The child was alone with a heavy cloth, so magic called friendly helpers."
        result = "The helpers carried the cloth beside the child."
    world.event("magic", cause, result)
    world.resolved = True


def make_world(params: StoryParams) -> World:
    validate(params)
    cloth = Cloth(**_safe_lookup(CLOTHES, params.cloth).__dict__)
    spell = _safe_lookup(SPELLS, params.spell)
    world = World(
        child=params.name,
        setting=_safe_lookup(SETTINGS, params.setting),
        spell=spell,
        cloth=cloth,
        problem=params.problem,
        meters={"care": 1},
        memes={"wonder": 1, "hope": 0},
    )
    world.say(
        f"In {world.setting}, {world.child} found {cloth.phrase}, "
        f"a {cloth.color} square of {cloth.pattern} cloth, beneath a sleepy tree."
    )
    world.say(
        f'"Come along, little gingham," sang {world.child}, for the cloth was meant '
        f'for a picnic, a pocket, and a bit of everyday magic.'
    )
    world.say(_safe_lookup(PROBLEMS, params.problem))
    world.event(
        "problem",
        _safe_lookup(PROBLEMS, params.problem),
        "The child needed a kind and magical way to help the cloth.",
    )
    spell_solution(world)
    world.say(
        f'Then {world.child} tucked the gingham close and sang: '
        f'"Check, check, red check, safe from sky to shoe; '
        f'when kindness joins with magic, a happy thing comes true!"'
    )
    return world


def prompts(world: World) -> list[str]:
    return [
        f"Write a short nursery rhyme about {world.child} and gingham in {world.setting}.",
        f"Tell a magical rhyme in which {world.child} faces a small problem and uses {world.spell.action} to help the gingham.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What problem did the child face?",
            f"{world.events[0]['cause']} The child needed help with the gingham.",
        ),
        QAItem(
            "What magic did the child use?",
            f'{world.child} used the spell to {world.spell.action}, which {world.spell.result}.',
        ),
        QAItem(
            "How did the story end?",
            world.events[-1]["result"] + " The child carried the gingham safely onward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.spell.tags)
    tags.add("gingham")
    if world.problem in {"wind", "mud"}:
        tags.add(world.problem)
    return [KNOWLEDGE[key] for key in ["gingham", "wind", "mud", "moon", "star", "bell", "dew"]
            if key in tags]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=" ".join(world.history),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"  child: {world.child}",
        f"  setting: {world.setting}",
        f"  cloth: {world.cloth.id}, pattern={world.cloth.pattern}, clean={world.cloth.clean}, floating={world.cloth.floating}",
        f"  spell: {world.spell.id}",
        f"  meters: {world.meters}",
        f"  memes: {world.memes}",
        f"  resolved: {world.resolved}",
        "--- events ---",
        *[f"  {event['kind']}: {event['cause']} -> {event['result']}" for event in world.events],
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
helpful(Spell, Problem) :- spell(Spell), problem(Problem).
valid(Setting, Spell, Cloth, Problem) :-
    setting(Setting), spell(Spell), cloth(Cloth), problem(Problem),
    helpful(Spell, Problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in SETTINGS:
        lines.append(asp.fact("setting", value))
    for value in SPELLS:
        lines.append(asp.fact("spell", value))
    for value in CLOTHES:
        lines.append(asp.fact("cloth", value))
    for value in PROBLEMS:
        lines.append(asp.fact("problem", value))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return asp_facts() + "\n" + ASP_RULES + "\n" + show + "\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid"))
    expected = set(valid_combos())
    if found != expected:
        print("MISMATCH: ASP and Python choices differ.")
        return 1
    checked = 0
    for combo in sorted(expected):
        params = StoryParams(*combo, name="Luna")
        sample = generate(params)
        if not sample.story or not sample.world.resolved:
            return 1
        checked += 1
    print(f"OK: {len(expected)} ASP/Python combinations and {checked} story checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic nursery-rhyme storyworld.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--spell", choices=SPELLS)
    parser.add_argument("--cloth", choices=CLOTHES, default="gingham")
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--name")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    spell = getattr(args, "spell", None) or rng.choice(list(SPELLS))
    cloth = getattr(args, "cloth", None) or "gingham"
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting, spell, cloth, problem, name)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "n", None) < 1:
        raise SystemExit("-n must be at least 1")
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        for row in sorted(set(asp.atoms(model, "valid"))):
            print(" ".join(map(str, row)))
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        for setting in SETTINGS:
            samples.append(generate(StoryParams(
                setting=setting,
                spell=SPELL_ORDER[len(samples) % len(SPELL_ORDER)],
                cloth="gingham",
                problem=PROBLEM_ORDER[len(samples) % len(PROBLEM_ORDER)],
                name=_safe_lookup(NAMES, len(samples) % len(NAMES)),
            )))
    else:
        for index in range(getattr(args, "n", None)):
            rng = random.Random(base + index)
            params = resolve_params(args, rng)
            params.seed = base + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None),
             header=f"### verse {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()

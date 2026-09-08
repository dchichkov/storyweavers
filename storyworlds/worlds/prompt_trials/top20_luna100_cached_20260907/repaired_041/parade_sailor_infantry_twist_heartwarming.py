#!/usr/bin/env python3
"""
A standalone Storyweavers world about a heartwarming parade, a sailor, and an
infantry drummer whose quiet twist changes the whole celebration.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "harbor parade"
SEED_WORDS = {"parade", "sailor", "infantry"}



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    location: str = "harbor"
    carried_by: Optional[str] = None

    banner: object | None = None
    drum: object | None = None
    hero: object | None = None
    infantry: object | None = None
    lighthouse: object | None = None
    sailor: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for key in ("distance", "wind", "damage", "weight", "visibility"):
            self.meters.setdefault(key, 0.0)
        for key in ("hope", "worry", "pride", "kindness", "belonging", "courage"):
            self.memes.setdefault(key, 0.0)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class StoryParams:
    hero: str = "Luna"
    sailor: str = "Marin"
    infantry: str = "Corporal Reed"
    trial: int = 0
    voice: int = 0
    ending: int = 0
    seed: Optional[int] = None
    params: object | None = None
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
        return None


@dataclass
class Trial:
    banner: str
    trouble: str
    clue: str
    false_lead: str
    twist: str
    action: str
    confession: str
    repair: str
    proof: str
    lesson: str
    image: str
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
        return None


TRIALS = [
    Trial(
        banner="a great blue-and-gold banner",
        trouble="a sudden gust tore the parade banner from its pole",
        clue="a small brass button caught in the banner's torn edge",
        false_lead="the empty supply cart seemed to have carried the banner away",
        twist="the sailor was not a careless visitor at all: the banner had been cut loose on purpose so it would not drag an elderly veteran into the street",
        action="followed the button trail to the pier and found the sailor holding the banner above a puddle",
        confession="I pulled it free when the wind caught the pole, but I was afraid everyone would think I ruined the parade",
        repair="stitched the torn edge with gold thread while the infantry band held the pole steady",
        proof="the banner rose again and its repaired corner fluttered without pulling the pole",
        lesson="A surprising choice may hide kindness, so a team should ask what danger someone was trying to prevent.",
        image="the banner waved over the harbor, its golden stitches shining like little promises",
    ),
    Trial(
        banner="a long red welcome pennant",
        trouble="the welcome pennant vanished just before the infantry march",
        clue="salt crystals and a blue thread marked the path toward the lighthouse",
        false_lead="a stack of parade boxes looked large enough to hide the pennant",
        twist="the sailor had carried it to the lighthouse so a frightened child on the balcony could see a familiar flag",
        action="climbed the lighthouse steps and found the sailor wrapping the pennant around the child's railing",
        confession="I borrowed it because the child was lonely and could not come down for the parade",
        repair="brought the pennant back, then made a smaller matching flag for the balcony",
        proof="both flags flew safely, and the child waved when the infantry passed below",
        lesson="Making room for someone who cannot join in can turn a parade into a welcome.",
        image="two red flags waved together, one above the street and one high beside the lighthouse window",
    ),
    Trial(
        banner="a silver harbor standard",
        trouble="the standard bent when the parade cart rolled over a hidden stone",
        clue="a sailor's rope knot lay beside the wheel",
        false_lead="the infantry drum wagon had a loose wheel that drew everyone's attention",
        twist="the sailor had bent the standard deliberately to catch a falling lantern before it struck the marching children",
        action="found the sailor beside the fish market, carefully straightening the standard around a wooden crate",
        confession="I grabbed the pole when the lantern fell, and I bent it while keeping the children safe",
        repair="straightened the standard, secured the lanterns, and gave the sailor the place of honor beside the drum wagon",
        proof="the lanterns hung firmly and the standard stood tall through the final turn",
        lesson="Protecting people matters more than keeping an object perfect.",
        image="the silver standard gleamed beside a row of safe lanterns as the parade entered the square",
    ),
    Trial(
        banner="a bright green flag for the harbor school",
        trouble="the flag's painted sun was smeared before the children reached the pier",
        clue="yellow paint dotted a sailor's folded map",
        false_lead="the art table had an open jar that made everyone suspect a clumsy brush",
        twist="the sailor had used the flag to cover a wet bench so a tired nurse could sit without staining her uniform",
        action="found the sailor at the dock, washing the flag while the nurse rested on a clean cloth",
        confession="I saw the wet paint on the bench and grabbed the nearest cloth. I should have asked first",
        repair="painted a new sun together and made a sign saying WET PAINT",
        proof="the new sun dried brightly while the sign kept every passerby safe",
        lesson="Kind intentions still need careful tools, but mistakes can become better plans.",
        image="the new green flag carried a golden sun, and beneath it stood a bright new safety sign",
    ),
]


@dataclass
class World:
    hero: Entity
    sailor: Entity
    infantry: Entity
    banner: Entity
    drum: Entity
    lighthouse: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
        return None
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_world(params: StoryParams, trial: Trial) -> World:
    world = World(
        hero=Entity(params.hero, "character", "child", "the parade helper"),
        sailor=Entity(params.sailor, "character", "sailor", "the sailor"),
        infantry=Entity(params.infantry, "character", "infantry", "the infantry leader"),
        banner=Entity("banner", "object", "flag", trial.banner),
        drum=Entity("drum", "object", "drum", "the marching drum"),
        lighthouse=Entity("lighthouse", "place", "tower", "the lighthouse"),
    )
    world.facts["theme"] = THEME
    return world


def tell(params: StoryParams) -> World:
    trial = _safe_lookup(TRIALS, params.trial % len(TRIALS))
    world = build_world(params, trial)
    h, s, i = world.hero, world.sailor, world.infantry
    b, d = world.banner, world.drum

    h.memes["hope"] = 1
    h.memes["worry"] = 1
    s.memes["kindness"] = 2
    i.memes["pride"] = 1
    b.meters["visibility"] = 1
    d.meters["weight"] = 2

    openings = [
        f"The harbor woke to bells and bright ribbons as {h.id} helped prepare {trial.banner} for the morning parade.",
        f"Along the sunny quay, {h.id} checked the flags while {i.id} practiced a gentle beat for the infantry march.",
        f"Boats rocked beside the pier, and the town filled with music. {h.id} had one important job: carry {trial.banner}.",
        f"Everyone in the harbor was getting ready for the parade. {s.id} polished the rails, {i.id} tuned the drum, and {h.id} guarded {trial.banner}.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"The parade was meant to begin when {trial.trouble}.")
    world.say(f"Without the banner, the marching route felt strangely empty, and {h.id}'s worry grew.")

    world.para()
    world.say(f"Near the parade stand, {trial.clue}. At the same time, {trial.false_lead}.")
    world.say(f"{h.id} whispered, 'The boxes are tempting to check, but that clue seems to point somewhere else.'")
    world.say(f"{i.id} replied, 'Then let us follow the evidence together, and ask before we blame anyone.'")
    world.say(f"{s.id} added, 'I may know part of this, but I want to explain it properly.'")
    world.say(f"The three helpers agreed to search carefully. {h.id} would {trial.action}.")

    world.para()
    h.memes["courage"] += 1
    h.memes["curiosity"] += 1
    world.say(f"The first search found only ordinary parade gear. Then the small clue led them onward, and {trial.action}.")
    world.say(f"The discovery brought an unexpected twist: {trial.twist}.")
    b.meters["damage"] = 1
    world.say(f"{s.id} lowered their eyes and said, 'There is something I should tell you. {trial.confession}.'")
    world.say(f"{h.id} answered, 'I am glad you told us. Let us solve the danger and mend what was harmed.'")
    world.say(f"{i.id} lifted the drum and called the infantry to help. Together they {trial.repair}.")
    b.meters["damage"] = 0
    h.memes["kindness"] += 2
    s.memes["belonging"] += 2
    i.memes["belonging"] += 1

    world.para()
    world.say(f"They tested the repair: {trial.proof}.")
    world.say(f"{h.id} said, 'The parade is not only about looking perfect. It is about making people feel safe and remembered.'")
    world.say(f"{s.id} smiled. 'Then I belong in this parade too?'")
    world.say(f"{i.id} answered, 'You helped protect its heart. March beside us.'")
    world.say(f"The band began again, and {trial.lesson}")
    world.say(f"As the parade passed the water, {trial.image}.")

    world.facts.update(
        trial=trial,
        resolved=True,
        twist=trial.twist,
        clue=trial.clue,
        trouble=trial.trouble,
        action=trial.action,
        confession=trial.confession,
        repair=trial.repair,
        proof=trial.proof,
        lesson=trial.lesson,
        image=trial.image,
        banner=trial.banner,
        hero=h,
        sailor=s,
        infantry=i,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, s, i = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sailor"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "infantry")
    return [
        QAItem(
            question="What went wrong before the parade?",
            answer=f"The trouble was that {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trouble")}. This left the parade without its important banner or flag.",
        ),
        QAItem(
            question="What clue helped the helpers search?",
            answer=f"They followed {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue")}. That physical clue led {h.id}, {s.id}, and {i.id} toward the real location.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist")}. The missing object was connected to an attempt to help someone.",
        ),
        QAItem(
            question=f"What did {s.id} admit?",
            answer=f"{s.id} admitted, '{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "confession")}.' The admission helped everyone understand the choice instead of guessing.",
        ),
        QAItem(
            question="How did the group repair the problem?",
            answer=f"They {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "repair")}. Then they checked that {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "proof")}.",
        ),
        QAItem(
            question="What did the parade teach the characters?",
            answer=f"It taught them that {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lesson")}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people move along a route while music, flags, costumes, or special vehicles help celebrate something.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works or travels on a boat or ship and learns how to stay safe on the water.",
        ),
        QAItem(
            question="What does infantry mean?",
            answer="Infantry means soldiers who serve and move on foot rather than mainly using ships, aircraft, or vehicles.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is an unexpected change or discovery that makes earlier events look different.",
        ),
        QAItem(
            question="Why is asking before blaming someone helpful?",
            answer="Asking first can reveal facts, protect people from unfair guesses, and make it easier to repair a mistake together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming child-friendly parade story involving a sailor, infantry, and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "banner")}.",
        f"Build a story around this twist: {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist")}. Include a clue, honest dialogue, teamwork, and a concrete ending image.",
        "Tell a gentle story in which asking questions reveals that a surprising action was meant to help someone.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{n}. {p}" for n, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (
        world.hero,
        world.sailor,
        world.infantry,
        world.banner,
        world.drum,
        world.lighthouse,
    ):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:16} ({entity.kind:9}) "
            f"meters={meters} memes={memes} location={entity.location}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor_parade).
has_role(harbor_parade, sailor).
has_role(harbor_parade, infantry).
has_role(harbor_parade, parade).
has_feature(harbor_parade, twist).
has_style(harbor_parade, heartwarming).

valid_world(S) :-
    setting(S),
    has_role(S, sailor),
    has_role(S, infantry),
    has_role(S, parade),
    has_feature(S, twist),
    has_style(S, heartwarming).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "harbor_parade"),
            asp.fact("has_role", "harbor_parade", "sailor"),
            asp.fact("has_role", "harbor_parade", "infantry"),
            asp.fact("has_role", "harbor_parade", "parade"),
            asp.fact("has_feature", "harbor_parade", "twist"),
            asp.fact("has_style", "harbor_parade", "heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_world/1."))
    if any(atom.name == "valid_world" for atom in models):
        for index in range(len(TRIALS)):
            params = StoryParams(trial=index, seed=index)
            sample = generate(params)
            if not sample.story or "parade" not in sample.story.lower():
                print("MISMATCH: generated story failed the parade exercise.")
                return 1
        print("OK: ASP and Python recognize the parade, sailor, infantry, twist, and heartwarming domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming parade story world with a sailor, infantry, and a twist."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--sailor", default=None)
    parser.add_argument("--infantry", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(["Luna", "Mara", "Nia", "Poppy", "Suri"])
    sailor = getattr(args, "sailor", None) or rng.choice(["Marin", "Blue", "Tide", "Ari", "Skipper"])
    infantry = getattr(args, "infantry", None) or rng.choice(
        ["Corporal Reed", "Sergeant Vale", "Captain Moss", "Lieutenant Gray"]
    )
    if len({hero, sailor, infantry}) != 3:
        pass
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        sailor=sailor,
        infantry=infantry,
        trial=offset % len(TRIALS),
        voice=(offset // len(TRIALS)) % 4,
        ending=(offset // (len(TRIALS) * 4)) % 3,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="Luna", sailor="Marin", infantry="Corporal Reed", trial=0),
    StoryParams(hero="Mara", sailor="Tide", infantry="Sergeant Vale", trial=1),
    StoryParams(hero="Nia", sailor="Blue", infantry="Captain Moss", trial=2),
    StoryParams(hero="Poppy", sailor="Ari", infantry="Lieutenant Gray", trial=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_world/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_world/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, getattr(args, "n", None) * 50)
        while len(samples) < getattr(args, "n", None) and attempt < limit:
            sample_seed = base_seed + attempt
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

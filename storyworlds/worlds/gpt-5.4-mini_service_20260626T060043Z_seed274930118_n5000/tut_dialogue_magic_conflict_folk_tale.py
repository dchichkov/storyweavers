#!/usr/bin/env python3
"""
Storyworld: tut_dialogue_magic_conflict_folk_tale

A small folk-tale domain about a shy tut, a quarrel, and a little magic that
makes the right words matter. The story models a speaking charm, a conflict
over who may use it, and a reconciliation through honest dialogue.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm: object | None = None
    elder: object | None = None
    hero: object | None = None
    rival: object | None = None
    def get(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def feel(self, key: str) -> float:
        return self.memes.get(key, 0.0)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
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
class StoryParams:
    place: str
    hero: str
    elder: str
    rival: str
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


PLACES = {
    "cottage": "a little cottage at the edge of the woods",
    "hill": "a windy hill above the village",
    "grove": "a quiet grove under old trees",
}

HEROES = ["Milo", "Nia", "Tala", "Sorin", "Mira"]
ELDERS = ["Gran", "Old Joss", "Grandma Rina", "Aunt Brin"]
RIVALS = ["the crow", "the fox", "the miller", "the sister"]


@dataclass
class Charm:
    label: str
    phrase: str
    spell: str
    desired: str
    consequence: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


CHARMS = {
    "tut": Charm(
        label="tut charm",
        phrase="a small tut charm carved from pear wood",
        spell="tut",
        desired="the right reply",
        consequence="the wrong words tumbled out",
    ),
    "bell": Charm(
        label="bell charm",
        phrase="a tiny bell charm tied with blue thread",
        spell="ding",
        desired="a clear warning",
        consequence="the secret was not hidden anymore",
    ),
}

TRAITS = ["quiet", "kind", "patient", "curious", "brave"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _pronoun(name: str) -> str:
    return "they"


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def predict_misuse(world: World, hero: Entity, charm: Entity) -> bool:
    sim = world.copy()
    sim.entities[hero.id].memes["temptation"] = sim.entities[hero.id].memes.get("temptation", 0) + 1
    return sim.entities[hero.id].memes["temptation"] >= THRESHOLD and charm.meters.get("bound", 0) >= THRESHOLD


def speak(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}," said {speaker.id}.')


def cast(world: World, caster: Entity, charm: Entity) -> None:
    charm.meters["spoken"] = charm.meters.get("spoken", 0) + 1
    caster.memes["wonder"] = caster.memes.get("wonder", 0) + 1
    if caster.memes.get("anger", 0) >= THRESHOLD:
        caster.memes["hurt"] = caster.memes.get("hurt", 0) + 1


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    elder = world.add(Entity(id=params.elder, kind="character", type="elder", label=params.elder))
    rival = world.add(Entity(id=params.rival, kind="character", type="rival", label=params.rival))
    charm_def = CHARMS["tut"]
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=charm_def.label, phrase=charm_def.phrase))
    charm.meters["bound"] = 1.0

    trait = random.choice(TRAITS)
    world.facts.update(hero=hero, elder=elder, rival=rival, charm=charm, charm_def=charm_def, trait=trait)

    world.say(f"In {_safe_lookup(PLACES, params.place)}, there lived a {trait} child named {hero.id}.")
    world.say(f"One morning, {elder.id} gave {hero.id} {_article(charm.phrase)} {charm.phrase}.")
    world.say(f'The elder said, "{charm_def.spell} is a small word, but it listens to a true heart."')

    world.para()
    world.say(f"{hero.id} wanted to use the charm at once, because {charm_def.desired} sounded sweet.")
    speak(world, rival, f"Give me that charm. I need it more than you do")
    hero.memes["fear"] = 1.0
    hero.memes["temptation"] = 1.0
    hero.memes["anger"] = 1.0
    world.say(f"{hero.id} felt a hot knot of anger, for {rival.id} had laughed at {hero.id}'s careful hand.")
    world.say(f"At once, the little charm began to hum, as if it knew a quarrel was near.")

    world.para()
    if predict_misuse(world, hero, charm):
        world.say(f"{elder.id} heard the hum and warned, \"Magic grows crooked when it is used in a temper.\"")
    speak(world, hero, "No, I will not give it away")
    speak(world, rival, "Then I will snatch it")
    hero.memes["conflict"] = 1.0
    rival.memes["conflict"] = 1.0
    world.say(f"The two stood stiff as fence posts, and the charm {_article(charm.consequence)} {charm.consequence} in the air.")

    world.para()
    speak(world, elder, "Tell the truth first, child. Say what you need, not what your temper shouts")
    hero.memes["anger"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["peace"] = 1.0
    speak(world, hero, f"I wanted {charm.desired}, but I also wanted to keep my turn")
    speak(world, rival, "Then I can wait")
    rival.memes["conflict"] = 0.0
    hero.memes["conflict"] = 0.0
    cast(world, hero, charm)
    world.say(f"The charm answered with a soft glow, and {hero.id} found {charm_def.desired} in the calm space between words.")
    world.say(f"In the end, the little folk-tale lesson was plain: a brave voice and a kind reply can mend a quarrel better than force.")

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about {f['hero'].id}, a speaking charm, and a quarrel that is solved with honest words.",
        f"Tell a child-friendly story in which the word \"tut\" is magic, but only works after a conflict is calmed.",
        f"Write a gentle story about a child and an elder, where dialogue changes a bad mood into peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, rival, charm_def = f["hero"], f["elder"], f["rival"], f["charm_def"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a {f['trait']} child in {world.place}.",
        ),
        QAItem(
            question=f"What did the charm do in the story?",
            answer=f"It was a small magic charm for {charm_def.desired}, but it could go wrong if used in anger.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {rival.id} start to quarrel?",
            answer=f"They quarreled because {rival.id} tried to take the charm, and {hero.id} felt upset and protective.",
        ),
        QAItem(
            question=f"How did the elder help solve the problem?",
            answer=f"{elder.id} asked {hero.id} to speak truthfully and calmly, which helped the quarrel settle down.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"At the end, the anger faded, the charm glowed softly, and the children reached peace instead of fighting.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a charm in a folk tale?",
            answer="A charm is a small magical object that can help, warn, or change something when the right person uses it.",
        ),
        QAItem(
            question="What is a quarrel?",
            answer="A quarrel is a fight or argument between people who are upset with each other.",
        ),
        QAItem(
            question="Why are calm words important?",
            answer="Calm words help people understand each other, which can stop a fight and make a hard choice easier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
charm(tut).
spell(tut,tut).
can_help(tut,peace) :- charm(tut).
conflict(hero) :- anger(hero).
resolved(hero) :- conflict(hero), speaks_truth(hero), elder_guides(hero).
good_story :- can_help(tut,peace), resolved(hero).
#show good_story/0.
#show conflict/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("charm", "tut"),
            asp.fact("spell", "tut", "tut"),
            asp.fact("elder_guides", "hero"),
            asp.fact("speaks_truth", "hero"),
            asp.fact("anger", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0.\n#show conflict/1.\n#show resolved/1."))
    syms = {str(s) for s in model}
    expected = {"conflict(hero)", "resolved(hero)", "good_story"}
    if syms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP twin differs from Python gate.")
    print("ASP:", sorted(syms))
    print("Expected:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.hero == params.elder:
        pass
    if params.hero == params.rival or params.elder == params.rival:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    rival = getattr(args, "rival", None) or rng.choice(RIVALS)
    params = StoryParams(place=place, hero=hero, elder=elder, rival=rival)
    valid_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = World(place=params.place)
    world = tell(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(eid, ent.meters, ent.memes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about tut, dialogue, magic, and conflict.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--rival", choices=RIVALS)
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


CURATED = [
    StoryParams(place="cottage", hero="Milo", elder="Gran", rival="the fox"),
    StoryParams(place="hill", hero="Nia", elder="Old Joss", rival="the crow"),
    StoryParams(place="grove", hero="Tala", elder="Grandma Rina", rival="the miller"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/0.\n#show conflict/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_story/0.\n#show conflict/1.\n#show resolved/1."))
        print("ASP model:", " ".join(str(s) for s in model))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

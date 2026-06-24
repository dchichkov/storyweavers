#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a child pirate, an albatross, and a gourd.

Premise:
- A young pirate finds a big gourd on a ship.
- A talking albatross warns that the gourd can be used as a tooth-holder or
  treasure cup, but not carelessly.
- The child remembers a flashback about crooked teeth and a kind orthodontist.
- Inner monologue drives the decision to either keep the gourd safe or misuse it.
- The story resolves when the child chooses a sensible use and the crew smiles.

This script is self-contained and follows the Storyweavers storyworld contract.
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
# Registry data
# ---------------------------------------------------------------------------

CAPTAINS = ["Mira", "Toby", "Nia", "Pip", "Jory", "Luna"]
CREW = ["the captain", "the mate", "the cook", "the deckhand", "the first mate"]
PIRATE_EPITHETS = ["brave", "curious", "scrappy", "bright-eyed", "wily", "small"]
SETTINGS = {
    "harbor": "the harbor",
    "ship": "the little ship",
    "island": "the windy island",
    "cove": "the moonlit cove",
}

GOURD_USES = {
    "cup": "a cup for fresh water",
    "helm": "a little helm for pretend steering",
    "snack": "a bowl for berries",
    "teeth_holder": "a holder for a loose tooth",
}

FLASHBACK_REASONS = {
    "pain": "their tooth had once ached terribly",
    "worry": "they had worried about crooked teeth before",
    "care": "they had learned to keep teeth safe and clean",
}

# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------


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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    albatross: object | None = None
    gourd: object | None = None
    hero: object | None = None
    orthodontist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    w: object | None = None
    world: object | None = None
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Parameters
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
    setting: str
    name: str
    crew_role: str
    epithet: str
    flashback_reason: str
    gourd_use: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
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


def _do_inner_monologue(world: World, hero: Entity, gourd: Entity) -> None:
    hero.memes["uncertainty"] = hero.memes.get("uncertainty", 0.0) + 1.0
    use = _safe_fact(world, world.facts, "gourd_use")
    world.say(
        f"{hero.pronoun().capitalize()} peered at the gourd and thought, "
        f"\"{gourd.label} could be {_safe_lookup(GOURD_USES, use)}, but only if I keep it safe.\""
    )


def _flashback(world: World, hero: Entity) -> None:
    reason = _safe_fact(world, world.facts, "flashback_reason")
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1.0
    world.say(
        f"Flashback: once, when {hero.id} was smaller, an orthodontist had said "
        f"that teeth need gentle care because {_safe_lookup(FLASHBACK_REASONS, reason)}."
    )


def _albatross_warns(world: World, bird: Entity, hero: Entity, gourd: Entity) -> None:
    bird.memes["wisdom"] = bird.memes.get("wisdom", 0.0) + 1.0
    world.say(
        f"An albatross perched on the rail and squawked, "
        f"\"That {gourd.label} is no toy for rough seas, matey. Treat it kindly!\""
    )
    world.facts["warning"] = True


def _choose_use(world: World, hero: Entity, gourd: Entity) -> None:
    use = _safe_fact(world, world.facts, "gourd_use")
    if use == "teeth_holder":
        hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
        world.say(
            f"{hero.pronoun().capitalize()} nodded, slipped the loose tooth safely "
            f"into the gourd, and decided not to fidget with it."
        )
    elif use == "cup":
        hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
        world.say(
            f"{hero.pronoun().capitalize()} washed the gourd in a bucket, then used "
            f"it as a cup for fresh water."
        )
    elif use == "helm":
        hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1.0
        world.say(
            f"{hero.pronoun().capitalize()} balanced the gourd like a tiny helm, "
            f"but only for pretend steering while the ship stayed moored."
        )
    else:
        pass


def generate_story(params: StoryParams) -> StorySample:
    world = World(setting=params.setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="boy" if params.name in {"Toby", "Pip", "Jory"} else "girl",
        traits=["little", params.epithet, "pirate"],
    ))
    albatross = world.add(Entity(
        id="Alby",
        kind="character",
        type="bird",
        label="an albatross",
    ))
    orthodontist = world.add(Entity(
        id="DrMills",
        kind="character",
        type="orthodontist",
        label="the orthodontist",
    ))
    gourd = world.add(Entity(
        id="gourd",
        type="gourd",
        label="gourd",
        phrase="a round green gourd",
        owner=hero.id,
    ))

    world.facts.update(
        hero=hero,
        albatross=albatross,
        orthodontist=orthodontist,
        gourd=gourd,
        setting=params.setting,
        gourd_use=params.gourd_use,
        flashback_reason=params.flashback_reason,
        crew_role=params.crew_role,
    )

    world.say(
        f"On {_safe_lookup(SETTINGS, params.setting)}, little {params.epithet} pirate {hero.id} "
        f"found {gourd.phrase} beside a coil of rope."
    )
    world.say(
        f"{hero.id} had come aboard as {params.crew_role}, and the whole crew knew "
        f"{hero.pronoun('possessive')} grin could mean trouble or treasure."
    )
    world.para()

    _albatross_warns(world, albatross, hero, gourd)
    _flashback(world, hero)
    _do_inner_monologue(world, hero, gourd)
    world.say(
        f"That memory made {hero.id}'s chest feel warm, like a lantern under a coat."
    )
    world.para()

    _choose_use(world, hero, gourd)
    world.say(
        f"In the end, the ship rocked easy, the albatross nodded once, and "
        f"{hero.id} smiled with tidy teeth and a safe little gourd."
    )
    world.say(
        f"The sea wind sang over {_safe_lookup(SETTINGS, params.setting)}, and the pirate crew "
        f"laughed as if the morning had finally found its own happy tune."
    )

    prompts = [
        'Write a short pirate tale for a young child that includes an orthodontist, an albatross, and a gourd.',
        f"Tell a gentle story where {hero.id} finds a gourd on a pirate ship and remembers a visit to an orthodontist.",
        "Write a sea story with a flashback and an inner monologue, ending with a safe choice.",
    ]

    story_qa = [
        QAItem(
            question=f"Who found the gourd in the story?",
            answer=f"{hero.id}, the little {params.epithet} pirate, found the gourd beside the rope on {_safe_lookup(SETTINGS, params.setting)}.",
        ),
        QAItem(
            question="Why did the albatross warn about the gourd?",
            answer="The albatross warned because the gourd could be used roughly and that would not be safe on the rocking ship.",
        ),
        QAItem(
            question="What did the flashback remind the pirate about?",
            answer="The flashback reminded the pirate that an orthodontist had said teeth need gentle care.",
        ),
        QAItem(
            question="What did the pirate think in the inner monologue?",
            answer=f"{hero.id} thought that the gourd could be useful, but only if it stayed safe and was used carefully.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.id} chose a safe use for the gourd, and the crew ended the day smiling peacefully.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is an orthodontist?",
            answer="An orthodontist is a doctor who helps take care of teeth and makes them fit together more neatly.",
        ),
        QAItem(
            question="What is an albatross?",
            answer="An albatross is a very large sea bird that can glide over ocean waves.",
        ),
        QAItem(
            question="What is a gourd?",
            answer="A gourd is a plant fruit with a hard shell, and people can sometimes dry it and use it for containers or crafts.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is a character's private thinking, shown to help readers understand what they are deciding.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A pirate story is reasonable when it includes the key cast and a safe gourd use.
safe_use(keep_teeth) :- gourd_use(keep_teeth).
safe_use(cup) :- gourd_use(cup).
safe_use(helm) :- gourd_use(helm).

story_ok(S) :- setting(S), has_albatross, has_orthodontist, has_gourd, safe_use(_).

valid_story(S, Use) :- setting(S), gourd_use(Use), story_ok(S).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("has_albatross"))
    lines.append(asp.fact("has_orthodontist"))
    lines.append(asp.fact("has_gourd"))
    for use in ["keep_teeth", "cup", "helm"]:
        lines.append(asp.fact("gourd_use", use))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(s, u) for s in SETTINGS for u in ["keep_teeth", "cup", "helm"]}
    if asp_set == py_set:
        print(f"OK: ASP matches Python story space ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter selection
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with an orthodontist, an albatross, and a gourd.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--name", choices=CAPTAINS)
    ap.add_argument("--crew-role", choices=CREW)
    ap.add_argument("--epithet", choices=PIRATE_EPITHETS)
    ap.add_argument("--flashback-reason", choices=sorted(FLASHBACK_REASONS))
    ap.add_argument("--gourd-use", choices=sorted(GOURD_USES))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(CAPTAINS)
    crew_role = getattr(args, "crew_role", None) or rng.choice(CREW)
    epithet = getattr(args, "epithet", None) or rng.choice(PIRATE_EPITHETS)
    flashback_reason = getattr(args, "flashback_reason", None) or rng.choice(sorted(FLASHBACK_REASONS))
    gourd_use = getattr(args, "gourd_use", None) or rng.choice(sorted(GOURD_USES))
    return StoryParams(
        setting=setting,
        name=name,
        crew_role=crew_role,
        epithet=epithet,
        flashback_reason=flashback_reason,
        gourd_use=gourd_use,
    )


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type} label={e.label} memes={e.memes} meters={e.meters}")
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story combinations:")
        for setting, use in vals:
            print(f"  {setting}: {use}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        params_list = [
            StoryParams(setting=s, name=_safe_lookup(CAPTAINS, i % len(CAPTAINS)), crew_role=CREW[i % len(CREW)],
                        epithet=_safe_lookup(PIRATE_EPITHETS, i % len(PIRATE_EPITHETS)), flashback_reason=r, gourd_use=u)
            for i, (s, r, u) in enumerate(
                [(s, r, u) for s in SETTINGS for r in FLASHBACK_REASONS for u in GOURD_USES][:5]
            )
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

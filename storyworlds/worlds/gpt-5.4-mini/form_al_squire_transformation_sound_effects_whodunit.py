#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/form_al_squire_transformation_sound_effects_whodunit.py
======================================================================================

A small, self-contained storyworld for a child-friendly whodunit built from the
seed words "form-al" and "squire", with transformation and sound-effect beats.

Premise
-------
A formal little pageant is being prepared at a castle museum. Someone keeps
making strange sounds, then a costume transformation happens, and the children
must figure out who caused the confusion. The story stays grounded in a tiny
simulated world: typed entities have physical meters and emotional memes, events
change state, and the ending proves what changed.

Style notes
-----------
- Whodunit tone: clues, suspicion, reveal, and a clear culprit.
- Transformation feature: a costume change and a role-change from helper to
  "squire" are modeled in world state.
- Sound-effects feature: each important action has a concrete onomatopoeic sound.
- The words "form-al" and "squire" appear in the story.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/form_al_squire_transformation_sound_effects_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/form_al_squire_transformation_sound_effects_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4-mini/form_al_squire_transformation_sound_effects_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/form_al_squire_transformation_sound_effects_whodunit.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king", "knight", "squire"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    detail: str
    clue: str
    audience: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    role: str
    transform_into: str = ""
    suspicious: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Sound:
    id: str
    onomatopoeia: str
    cause: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for prop in list(world.entities.values()):
        if prop.meters["tampered"] < THRESHOLD:
            continue
        sig = ("noise", prop.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["unease"] += 1
        out.append("__noise__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["changed"] < THRESHOLD:
            continue
        sig = ("transform", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["transformed"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("noise", "social", _r_noise),
    Rule("transform", "physical", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def reasonableness_gate(setting: Setting, prop: Prop) -> bool:
    return setting.id in {"hall", "gallery", "court"} and prop.suspicious


def predict(world: World, prop_id: str) -> dict:
    sim = world.copy()
    sim.get(prop_id).meters["tampered"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sum(e.memes["unease"] for e in sim.entities.values() if e.kind == "character"),
        "transformed": sim.get(prop_id).meters["transformed"] >= THRESHOLD,
    }


def start(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["duty"] += 1
    world.say(
        f"At {world.setting.place}, the children entered a quiet room full of clues. "
        f"{world.setting.detail}"
    )
    world.say(
        f"On the table sat a form-al cape, a silver badge, and a toy sword that made the room look ready for a mystery."
    )
    world.say(
        f"{hero.id} and {helper.id} promised to keep their eyes open, because every good whodunit needs careful looking."
    )


def hear_sound(world: World, sound: Sound, prop: Prop) -> None:
    world.say(
        f"Then came {sound.onomatopoeia}! {sound.clue} Everyone froze and looked at {prop.label}."
    )


def suspect(world: World, accuser: Entity, suspecter: Entity, prop: Prop) -> None:
    accuser.memes["suspicion"] += 1
    world.say(
        f'"That sound came from the {prop.label}," {accuser.id} whispered. '
        f'"Maybe {suspecter.id} knows more than they are saying."'
    )


def investigate(world: World, helper: Entity, prop: Prop) -> None:
    pred = predict(world, prop.id)
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f"{helper.id} knelt beside the {prop.label} and found a tiny smear of glitter. "
        f"That clue suggested someone had touched it recently."
    )


def transform_clue(world: World, prop: Prop, hero: Entity) -> None:
    prop.meters["tampered"] += 1
    prop.meters["changed"] += 1
    hero.meters["costumed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Click-clack, the cape slipped over {hero.id}'s shoulders. "
        f"With a soft swoosh, the costume changed the whole look of the scene."
    )


def reveal(world: World, culprit: Entity, prop: Prop, sound: Sound) -> None:
    culprit.memes["relief"] += 1
    culprit.memes["pride"] += 1
    world.say(
        f"At last, the clue fit. {culprit.id} had been hiding behind the curtain, trying to copy {sound.cause}. "
        f"When the cape snagged loose, it made {sound.onomatopoeia} and gave the game away."
    )
    world.say(
        f"The mystery was simple after all: {culprit.id} had wanted to become a squire for the pretend knight game, and the noisy cape had betrayed the secret."
    )


def ending(world: World, hero: Entity, helper: Entity, prop: Prop) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, the room felt bright again. {hero.id} wore the cape as a squire, {helper.id} kept the badge, and the form-al show could begin with a neat bow."
    )
    world.say(
        f"The only sound left was a happy rustle of cloth, and the little whodunit ended with a solved clue and a safe costume."
    )


def tell(setting: Setting, prop: Prop, sound: Sound, hero_name: str, helper_name: str,
         culprit_name: str, hero_type: str = "boy", helper_type: str = "girl",
         culprit_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="detective", traits=["careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["calm"]))
    culprit = world.add(Entity(id=culprit_name, kind="character", type=culprit_type, role="culprit", traits=["sneaky"]))
    prop_ent = world.add(Entity(id=prop.id, type="thing", label=prop.label, role=prop.role, attrs={"sound": sound.id}))
    world.facts.update(hero=hero, helper=helper, culprit=culprit, prop=prop, sound=sound)

    start(world, hero, helper)
    world.para()
    hear_sound(world, sound, prop)
    suspect(world, hero, culprit, prop)
    investigate(world, helper, prop)
    world.para()
    transform_clue(world, prop_ent, hero)
    reveal(world, culprit, prop, sound)
    world.para()
    ending(world, hero, helper, prop)
    world.facts.update(outcome="solved", transformed=prop_ent.meters["transformed"] >= THRESHOLD)
    return world


SETTINGS = {
    "hall": Setting("hall", "the castle hall", "A long banner said 'Welcome to the formal pageant.'", "A polished floor reflected every candle.", "the guests"),
    "gallery": Setting("gallery", "the museum gallery", "Glass cases held old helmets and bright ribbons.", "A tiny bell hung near the door.", "the visitors"),
    "court": Setting("court", "the moonlit court", "Silk flags flapped over the stones.", "A trumpet stand waited beside the wall.", "the courtiers"),
}

PROPS = {
    "cape": Prop("cape", "cape", "a form-al cape", "swish", "costume", transform_into="squire cloak", suspicious=True),
    "badge": Prop("badge", "badge", "a brass badge", "ding", "clue", suspicious=True),
    "mask": Prop("mask", "mask", "a velvet mask", "fap", "clue", suspicious=True),
}

SOUNDS = {
    "swish": Sound("swish", "swish", "the cape was swung around too fast", "A soft cloth sound drifted from the corner.", {"cloth"}),
    "ding": Sound("ding", "ding-ding", "someone tapped the badge against the tray", "A bright metal ring bounced off the wall.", {"metal"}),
    "fap": Sound("fap", "fap-fap", "the mask was flapped like a fan", "A fluttering sound came from the curtain.", {"cloth"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tia"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Jude", "Pax"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    prop: str
    sound: str
    hero: str
    helper: str
    culprit: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, prop in PROPS.items():
            if reasonableness_gate(setting, prop):
                for snd in SOUNDS:
                    combos.append((sid, pid, snd))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld with transformation and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--culprit")
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
              and (args.prop is None or c[1] == args.prop)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, sound = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    culprit = args.culprit or rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n not in {hero, helper}])
    return StoryParams(setting, prop, sound, hero, helper, culprit)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the word "form-al" and the word "squire".',
        f"Tell a mystery story where {f['hero'].id} hears a strange sound, notices a costume change, and figures out who caused it.",
        f"Write a simple formal-castle mystery with a clue, a sound effect, and a reveal that explains why the cape changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, culprit, prop, sound = f["hero"], f["helper"], f["culprit"], f["prop"], f["sound"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about a strange sound near the {prop.label} and a costume that changed in the middle of a formal game. The children had to follow the clue and figure out who touched it."
        ),
        QAItem(
            question=f"What did {sound.onomatopoeia} tell the children?",
            answer=f"It told them that someone had moved the {prop.label} and made a noise on purpose. That clue helped them look in the right place instead of guessing wildly."
        ),
        QAItem(
            question=f"Who was the culprit?",
            answer=f"{culprit.id} was the one behind the curtain, trying to turn the game into a squire story. When the cape slipped, the clue gave the secret away."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The cape had been transformed into a squire cloak, and the room went from confused to solved. The mystery ended with everyone calm and ready for the formal show."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone tries to figure out who caused a problem. The reader follows clues until the truth is revealed."
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect helps the reader hear the action in their mind. It can make a scene feel lively, funny, or mysterious."
        ),
        QAItem(
            question="What is a squire?",
            answer="A squire is a helper for a knight in old stories. In pretend play, a child can act like a squire and help with a costume or a quest."
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("hall", "cape", "swish", "Mina", "Owen", "Pax"),
    StoryParams("gallery", "badge", "ding", "Theo", "Ivy", "Jude"),
    StoryParams("court", "mask", "fap", "Lena", "Finn", "Owen"),
]


ASP_RULES = r"""
valid(S, P, T) :- setting(S), prop(P), sound(T), suspicious(P).
solve(S, P, T) :- valid(S, P, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.suspicious:
            lines.append(asp.fact("suspicious", pid))
    for snd in SOUNDS:
        lines.append(asp.fact("sound", snd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    sample = generate(CURATED[0])
    if not sample.story or "squire" not in sample.story:
        rc = 1
        print("MISMATCH: ordinary generation smoke test failed.")
    else:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], SOUNDS[params.sound],
                 params.hero, params.helper, params.culprit)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a}, {b}, {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

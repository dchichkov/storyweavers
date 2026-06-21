#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fortyniner_moral_value_suspense_curiosity_whodunit.py
====================================================================================

A small storyworld about a curious little whodunit in a gold-rush camp: a lost
gold nugget, a whispery suspicion, a moral choice to tell the truth, and a final
reveal that shows who really took it. The world is built around typed entities
with accumulating physical meters and emotional memes, a forward-chained causal
engine, a reasonableness gate, and an inline ASP twin for parity checks.

The required seed word appears in the world and story: fortyniner.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 2
MORAL_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class CampSetting:
    id: str
    place: str
    detail: str
    hiding_spot: str
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
class Clue:
    id: str
    label: str
    phrase: str
    suspicious: bool = False
    hidden: bool = False
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Suspect:
    id: str
    label: str
    can_take: bool
    motive: str
    alibi: str
    clues: set[str] = field(default_factory=set)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["missing"] >= THRESHOLD and e.memes["worry"] < THRESHOLD:
            e.memes["worry"] += 1
            out.append("The camp grew quiet, and everyone started wondering who had taken the nugget.")
    return out


def _r_confession(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("truth_told") and not world.facts.get("confession_said"):
        world.facts["confession_said"] = True
        out.append("At last, the truth came out of the dark, and the mystery had a shape.")
    return out


CAUSAL_RULES = [Rule("suspicion", _r_suspicion), Rule("confession", _r_confession)]


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


def moral_choice(keep_secret: bool) -> bool:
    return not keep_secret


def reasonable_choice(clue: Clue, suspect: Suspect) -> bool:
    return clue.hidden and suspect.can_take


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for p in SUSPECTS:
                if reasonable_choice(CLUES[c], SUSPECTS[p]):
                    combos.append((s, c, p))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    hero: str
    hero_gender: str
    sheriff: str
    keep_secret: bool = False
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


SETTINGS = {
    "camp": CampSetting(
        id="camp",
        place="the gold-rush camp",
        detail="Lanterns glowed between canvas tents, and the wind kept tugging at the ropes.",
        hiding_spot="a cracked tin cup by the fire ring",
    ),
    "mine": CampSetting(
        id="mine",
        place="the mine yard",
        detail="Shovels leaned against a pile of boards, and dust hung in the air like sleepy fog.",
        hiding_spot="a bucket beside the water pump",
    ),
    "river": CampSetting(
        id="river",
        place="the riverbank",
        detail="The river flashed silver, and pebbles clicked under every careful step.",
        hiding_spot="a mossy stone near the bank",
    ),
}

CLUES = {
    "nugget": Clue(
        id="nugget",
        label="gold nugget",
        phrase="a shiny little gold nugget",
        suspicious=True,
        hidden=True,
    ),
    "map": Clue(
        id="map",
        label="folded map",
        phrase="a folded map with a corner torn off",
        suspicious=True,
        hidden=True,
    ),
    "note": Clue(
        id="note",
        label="ink note",
        phrase="a tiny ink note",
        suspicious=True,
        hidden=True,
    ),
}

SUSPECTS = {
    "cook": Suspect(
        id="cook",
        label="the cook",
        can_take=True,
        motive="wanted the nugget for a lamp on the table",
        alibi="had been stirring soup when the bell rang",
        clues={"nugget"},
    ),
    "fortyniner": Suspect(
        id="fortyniner",
        label="the fortyniner",
        can_take=True,
        motive="wanted to hide the nugget until morning",
        alibi="said he was mending his boot by the fire",
        clues={"map"},
    ),
    "carpenter": Suspect(
        id="carpenter",
        label="the carpenter",
        can_take=False,
        motive="wanted nails, not gold",
        alibi="was planing wood the whole time",
        clues={"note"},
    ),
}

NAMES_GIRL = ["Maya", "Lily", "Nora", "Zoe", "Anna"]
NAMES_BOY = ["Theo", "Ben", "Max", "Finn", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with moral value, suspense, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sheriff")
    ap.add_argument("--keep-secret", action="store_true")
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


def explain_rejection(clue: Clue, suspect: Suspect) -> str:
    return f"(No story: the clue and suspect must make a real whodunit; try a hidden clue and a suspect who could have taken it.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.suspect:
        if not reasonable_choice(CLUES[args.clue], SUSPECTS[args.suspect]):
            raise StoryError(explain_rejection(CLUES[args.clue], SUSPECTS[args.suspect]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    sheriff = args.sheriff or rng.choice(["Sheriff June", "Marshal Pike", "Deputy Rose"])
    keep_secret = args.keep_secret if args.keep_secret else rng.choice([False, True])
    return StoryParams(setting=setting, clue=clue, suspect=suspect, hero=hero, hero_gender=gender, sheriff=sheriff, keep_secret=keep_secret)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="child"))
    sheriff = world.add(Entity(id="sheriff", kind="character", type="woman", label=params.sheriff, role="law"))
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    world.add(Entity(id="clue", label=clue.label))
    world.add(Entity(id="suspect", label=suspect.label))
    world.facts.update(hero=hero, sheriff=sheriff, setting=setting, clue=clue, suspect=suspect)
    hero.memes["curiosity"] += 1
    world.say(f"In {setting.place}, {hero.id} noticed {clue.phrase} tucked near {setting.hiding_spot}. {setting.detail}")
    world.say(f"{hero.id} could not stop wondering who had left it there, because the little clue felt like a secret trying to speak.")
    world.para()
    hero.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(f"{hero.id} followed the tiny trail of hints. One by one, the possibilities got smaller, and the camp felt more and more still.")
    world.say(f"At last {hero.id} asked the right questions, and the answer pointed toward {suspect.label}.")
    world.para()
    if params.keep_secret and not moral_choice(True):
        pass
    if params.keep_secret:
        hero.memes["guilt"] += 1
        world.say(f"{hero.id} almost kept the answer secret, but that would have been wrong.")
        world.say(f"Instead, {hero.id} told {params.sheriff} the truth, even though it made {hero.pronoun('possessive')} cheeks warm.")
    else:
        world.say(f"{hero.id} told {params.sheriff} the truth at once, because a fair answer mattered more than a clever guess.")
    world.facts["truth_told"] = True
    if suspect.id == "fortyniner":
        world.say(f"{params.sheriff} listened carefully, then checked the fortyniner's story by the fire.")
    else:
        world.say(f"{params.sheriff} listened carefully, then checked the suspect's story by the fire.")
    world.say(f"The missing gold nugget was found hidden where the clue had hinted, and the mystery finally made sense.")
    world.say(f"{params.sheriff} thanked {hero.id} for being brave enough to tell the truth, not just brave enough to chase a secret.")
    world.say(f"By the end, the camp was calm again, and {hero.id} watched the lantern light glint on the returned nugget like a tiny star.")
    return world


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.clue not in CLUES or params.suspect not in SUSPECTS:
        raise StoryError("Unknown clue or suspect.")
    world = tell(params)
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
        f'Write a whodunit for a child that includes the word "fortyniner" and a hidden clue in {f["setting"].place}.',
        f"Tell a suspenseful little mystery where {f['hero'].id} follows a clue, suspects {f['suspect'].label}, and chooses to tell the truth.",
        "Write a moral-value mystery story about curiosity, honesty, and a missing gold nugget.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    suspect = f["suspect"]
    sheriff = f["sheriff"]
    qa = [
        ("What did the child find?", f"{hero.id} found {clue.phrase} in the camp, and it seemed to point toward a hidden mystery."),
        ("What did the child do with the clue?", f"{hero.id} followed the hints, thought carefully, and asked questions instead of guessing wildly."),
        ("What choice showed moral value?", f"{hero.id} told {sheriff.label} the truth, because honesty mattered more than keeping a secret."),
        ("Who was the story about?", f"It was about {hero.id}, the sheriff, and the suspicious little trail that led to {suspect.label}."),
    ]
    qa.append(("How did the story end?", "The missing gold nugget was found, the camp grew calm again, and the truth made the mystery clear."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?", "A clue is a small piece of information that can help solve a mystery."),
        ("What does a sheriff do?", "A sheriff helps keep order and listens when people need help with a problem."),
        ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn more."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hidden_clue(C) :- clue(C), hidden(C).
can_take(S) :- suspect(S), taker(S).
valid(Setting, Clue, Suspect) :- setting(Setting), hidden_clue(Clue), can_take(Suspect).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.hidden:
            lines.append(asp.fact("hidden", cid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        if s.can_take:
            lines.append(asp.fact("taker", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp as aspmod
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        rc = 1
    return rc


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
    StoryParams(setting="camp", clue="nugget", suspect="fortyniner", hero="Maya", hero_gender="girl", sheriff="Sheriff June", keep_secret=False),
    StoryParams(setting="mine", clue="map", suspect="cook", hero="Theo", hero_gender="boy", sheriff="Marshal Pike", keep_secret=True),
    StoryParams(setting="river", clue="note", suspect="fortyniner", hero="Nora", hero_gender="girl", sheriff="Deputy Rose", keep_secret=False),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()

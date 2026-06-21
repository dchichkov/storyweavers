#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cherokee_rhyme_transformation_moral_value_pirate_tale.py
========================================================================================

A small standalone storyworld for a pirate-tale style story about a child who
meets a Cherokee rhyme, faces a tempting selfish choice, transforms through a
kind act, and ends with a clear moral value.

The story aims for:
- pirate-tale flavor
- the word "cherokee"
- rhyme in dialogue / narration
- transformation as a state change, not a frozen paraphrase
- a simple moral lesson with a concrete ending image

The world is intentionally small and classical:
- one child pirate
- one wise helper
- one wanted prize
- one magical rhyme-token
- one turn from greed to sharing

It follows the shared Storyweavers contract with:
- StoryParams
- build_parser
- resolve_params
- generate
- emit
- main
- QA sets from world state
- Python reasonableness gate
- inline ASP_RULES twin
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
    transformed: bool = False
    shiny: bool = False
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class PirateTheme:
    id: str
    scene: str
    ship: str
    treasure_word: str
    dark_place: str
    ending_image: str
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
class RhymeToken:
    id: str
    label: str
    phrase: str
    rhyme_line: str
    makes_shine: bool = True
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
class Prize:
    id: str
    label: str
    phrase: str
    needs_sharing: bool = True
    shiny: bool = False
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
class HelperChoice:
    id: str
    line: str
    moral: str
    power: int
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
    tag: str
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


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    charm = world.entities.get("rhyme")
    prize = world.entities.get("prize")
    if not hero or not charm or not prize:
        return out
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.transformed = True
    prize.transformed = True
    prize.shiny = True
    hero.meters["glow"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("transform", "moral", _r_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def valid_choice(theme: PirateTheme, prize: Prize, rhyme: RhymeToken) -> bool:
    return bool(theme.id and prize.needs_sharing and rhyme.makes_shine)


def reason_gate(theme: PirateTheme, prize: Prize, helper: HelperChoice) -> bool:
    return helper.power >= 1 and prize.needs_sharing and "moral" in helper.tags


def story_seed_line(hero: Entity, theme: PirateTheme) -> str:
    return f"On {theme.scene}, {hero.id} rode the little ship like a bold young pirate."


def prompt_line(theme: PirateTheme, rhyme: RhymeToken, prize: Prize) -> str:
    return (
        f"Write a pirate tale for a young child that includes the word cherokee, "
        f"a rhyme, and a moral lesson about sharing {prize.label} on {theme.ship}."
    )


def tell(theme: PirateTheme, rhyme: RhymeToken, prize: Prize, helper: HelperChoice,
         hero_name: str = "Mira", hero_gender: str = "girl",
         helper_name: str = "Auntie", helper_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name,
                            role="pirate", traits=["bold"], attrs={"name": hero_name}))
    guide = world.add(Entity(id="guide", kind="character", type=helper_gender, label=helper_name,
                             role="wise_helper", traits=["steady"], attrs={"name": helper_name}))
    rhyme_ent = world.add(Entity(id="rhyme", kind="thing", type="rhyme", label=rhyme.label,
                                 shiny=True, safe=True))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="treasure", label=prize.label,
                                 shiny=prize.shiny, safe=False))
    hero.memes["greed"] = 1.0
    guide.memes["wisdom"] = 1.0

    world.say(story_seed_line(hero, theme))
    world.say(f"{hero.id} found {rhyme.phrase}, and the air seemed to hum with a pirate tune.")
    world.say(f'“{rhyme.rhyme_line}” sang {guide.label}. “That is a Cherokee rhyme, bright and true.”')

    world.para()
    world.say(f"{hero.id} wanted {prize.phrase} all to {hero.pronoun('possessive')} self.")
    world.say(f'“{helper.line}” said {guide.id}. “A chest that is shared can make two hearts glad.”')
    if helper.moral:
        world.say(f"The moral sat there like a lantern: {helper.moral}.")

    world.para()
    hero.memes["curiosity"] += 1
    guide.memes["trust"] += 1
    world.say(f"{hero.id} frowned, then listened to the rhyme again: “{rhyme.rhyme_line}.”")
    if reason_gate(theme, prize, helper):
        hero.memes["kindness"] += 1
        world.say(f"{hero.id} took a breath and chose the kinder path.")
        propagate(world, narrate=False)
        world.say(f"Together they opened the chest, and the {prize.label} began to gleam like sunrise on the sea.")
        world.say(f"{hero.id} split the treasure fairly, and {guide.id} smiled as the deck grew bright and still.")
        world.say(f"By the end, the old pirate tale had changed into a gentler song of sharing.")
    else:
        world.say(f"{hero.id} kept the treasure close, and the rhyme grew quiet.")
        world.say(f"The deck stayed heavy, and the moral was missed.")

    world.facts.update(
        hero=hero,
        guide=guide,
        rhyme=rhyme_ent,
        prize=prize_ent,
        theme=theme,
        helper=helper,
        outcome="transformed" if hero.transformed else "unchanged",
        shared=hero.transformed,
    )
    return world


THEMES = {
    "sea": PirateTheme(
        id="sea",
        scene="a moonlit deck",
        ship="the little ship",
        treasure_word="treasure",
        dark_place="the dark hold",
        ending_image="the deck glimmering under a warm lamp",
    ),
    "harbor": PirateTheme(
        id="harbor",
        scene="a sleepy harbor",
        ship="the bright boat",
        treasure_word="coin",
        dark_place="the shadowy dock",
        ending_image="the harbor shining after the choice",
    ),
}

RHYMES = {
    "cherokee": RhymeToken(
        id="cherokee",
        label="a little drum charm",
        phrase="a little drum charm marked with the word cherokee",
        rhyme_line="Soft tide, wide sky, choose the kind side",
    ),
    "star": RhymeToken(
        id="star",
        label="a shell star",
        phrase="a shell star with a silver edge",
        rhyme_line="Little star, near and far, share the light for who you are",
    ),
}

PRIZES = {
    "pearls": Prize(id="pearls", label="pearls", phrase="the pearly shells"),
    "map": Prize(id="map", label="map", phrase="the glittering map"),
}

HELPERS = {
    "aunt": HelperChoice(
        id="aunt",
        line="A treasure kept alone grows cold",
        moral="sharing can make treasure sweeter",
        power=2,
        tags={"moral"},
    ),
    "captain": HelperChoice(
        id="captain",
        line="A true pirate helps the crew",
        moral="a kind choice can change the whole day",
        power=2,
        tags={"moral"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lena", "Sara", "Tia"]
BOY_NAMES = ["Noah", "Eli", "Toby", "Finn", "Kai"]


@dataclass
class StoryParams:
    theme: str
    rhyme: str
    prize: str
    helper: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for t in THEMES:
        for r in RHYMES:
            for p in PRIZES:
                for h in HELPERS:
                    if valid_choice(THEMES[t], PRIZES[p], RHYMES[r]) and reason_gate(THEMES[t], PRIZES[p], HELPERS[h]):
                        combos.append((t, r, p, h))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with rhyme, transformation, and moral value.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.rhyme is None or c[1] == args.rhyme)
              and (args.prize is None or c[2] == args.prize)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, rhyme, prize, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    helper_name = args.helper_name or rng.choice(["Auntie", "Captain", "Marin", "Sage"])
    return StoryParams(
        theme=theme,
        rhyme=rhyme,
        prize=prize,
        helper=helper,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme: PirateTheme = f["theme"]
    prize: Prize = f["helper"] if False else f["prize"]
    rhyme: RhymeToken = f["rhyme"]
    return [
        f"Write a pirate story that includes the word cherokee and uses the rhyme '{rhyme.rhyme_line}'.",
        f"Tell a moral tale on {theme.scene} where a young pirate learns to share {prize.label}.",
        f"Create a rhyme-filled pirate adventure that turns greedy treasure-hunting into a kinder choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    guide: Entity = f["guide"]
    prize: Entity = f["prize"]
    rhyme: Entity = f["rhyme"]
    qa = [
        QAItem(
            question="What did the pirate child first want?",
            answer=f"{hero.label} wanted to keep the {prize.label} all to {hero.pronoun('possessive')} self. That showed the greedy choice the story had to change."
        ),
        QAItem(
            question="What was special about the rhyme?",
            answer=f"It was a Cherokee rhyme tied to {rhyme.label}. The song helped turn the story from wanting more into acting kindly."
        ),
        QAItem(
            question="How did the story change at the end?",
            answer="The child chose to share, and that changed the mood of the whole deck. The ending proves the moral value by showing kindness made the treasure brighter."
        ),
    ]
    if f.get("shared"):
        qa.append(QAItem(
            question="What transformation happened?",
            answer=f"{hero.label} transformed from greedy to kind, and the {prize.label} became shiny and shared. That change was not just in words; the world state marked the turn."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    theme: PirateTheme = f["theme"]
    rhyme: RhymeToken = f["rhyme"]
    qa = [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words or lines sound alike at the ends. Rhymes can make a story feel like a song."
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes in a clear way, like a mood, an object, or a character. In this world, the child changes from greedy to kind."
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a lesson about how to act well, like sharing, honesty, or kindness. Stories often show it through choices and consequences."
        ),
        QAItem(
            question="Why do pirates like treasure?",
            answer="In pirate tales, treasure is a prize that makes the adventure exciting. It gives the characters something to chase, protect, or share."
        ),
    ]
    if theme.id == "sea" or rhyme.id == "cherokee":
        qa.append(QAItem(
            question="Why is the word cherokee included?",
            answer="It is part of the story prompt and becomes part of the rhyme charm in the tale. The word helps anchor the poem-like pirate adventure."
        ))
    return qa


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
        if e.transformed:
            bits.append("transformed=True")
        if e.shiny:
            bits.append("shiny=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="sea", rhyme="cherokee", prize="pearls", helper="aunt",
                hero_name="Mira", hero_gender="girl", helper_name="Auntie", helper_gender="woman"),
    StoryParams(theme="harbor", rhyme="star", prize="map", helper="captain",
                hero_name="Kai", hero_gender="boy", helper_name="Captain Sage", helper_gender="man"),
]


def explain_rejection() -> str:
    return "(No story: this combo does not support the rhyme-driven transformation and moral turn.)"


ASP_RULES = r"""
valid(T,R,P,H) :- theme(T), rhyme(R), prize(P), helper(H), fit(T,R,P,H).
shared :- kindness.
transformed :- shared.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for r in RHYMES:
        lines.append(asp.fact("rhyme", r))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("fit", "sea", "cherokee", "pearls", "aunt"))
    lines.append(asp.fact("fit", "harbor", "star", "map", "captain"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python valid-combo gates match.")
    else:
        rc = 1
        print("MISMATCH in valid-combo gates.")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, rhyme=None, prize=None, helper=None,
                                                            name=None, gender=None, helper_name=None, helper_gender=None),
                                          random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.rhyme not in RHYMES or params.prize not in PRIZES or params.helper not in HELPERS:
        raise StoryError("Invalid params.")
    world = tell(THEMES[params.theme], RHYMES[params.rhyme], PRIZES[params.prize],
                 HELPERS[params.helper], params.hero_name, params.hero_gender,
                 params.helper_name, params.helper_gender)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
